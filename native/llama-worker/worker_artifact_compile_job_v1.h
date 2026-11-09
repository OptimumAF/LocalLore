// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#pragma once

#if !defined(_WIN64) || !defined(_M_X64) || !defined(LOCALLORE_COMPILE_JOB_V1_TEST_OWNER)
#error The compiler Job owner is private Windows x64 development source.
#endif

#include <Windows.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace locallore::compile_job_v1 {

struct Request {
    std::wstring compiler, worker, upstream, output, windows, path, include, temp;
    std::vector<std::wstring> arguments;
};

enum class Stop { none, request, cancelled, deadline, setup, io, overflow, drain };

template <std::size_t Capacity>
struct Capture {
    std::array<unsigned char, Capacity> bytes{};
    std::size_t size = 0;
    bool overflow = false;
    bool eof = false;
};

struct Result {
    Stop stop = Stop::none;
    DWORD pid = 0;
    std::optional<DWORD> exit, active_processes;
    DWORD error = ERROR_SUCCESS;
    bool member = false;
    bool resumed = false;
    bool signaled = false;
    bool kill_attempted = false;
    bool kill_failed = false;
    bool io_error = false;
    bool process_handle_closed = false;
    bool handles_closed = true;
    long long elapsed_ms = 0;
    Capture<65536> out;
    Capture<4096> err;

    bool closed() const { return signaled && exit.has_value() && process_handle_closed; }
    bool job_and_pipes_closed() const {
        return member && active_processes == 0 && out.eof && err.eof && handles_closed;
    }
};

namespace detail {

using Clock = std::chrono::steady_clock;
using namespace std::chrono_literals;
constexpr auto run_window = 120s;
constexpr auto drain_window = 5s;
constexpr DWORD kill_exit = 1;

inline void stop(Result& result, Stop reason, DWORD error = ERROR_SUCCESS) {
    if (result.stop == Stop::none) {
        result.stop = reason;
        result.error = error;
    }
    result.io_error |= reason == Stop::io;
}

struct Handle {
    HANDLE value = nullptr;
    Handle() = default;
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;

    bool valid() const { return value && value != INVALID_HANDLE_VALUE; }
    bool close() {
        const bool owned = valid();
        const HANDLE old = std::exchange(value, nullptr);
        return !owned || CloseHandle(old);
    }
    ~Handle() { close(); }
};

inline void close(Handle& handle, Result& result) {
    if (!handle.close()) {
        result.handles_closed = false;
        stop(result, Stop::io, GetLastError());
    }
}

struct Attributes {
    std::vector<std::max_align_t> storage;
    LPPROC_THREAD_ATTRIBUTE_LIST list = nullptr;

    bool init() {
        SIZE_T bytes = 0;
        if (InitializeProcThreadAttributeList(nullptr, 2, 0, &bytes) ||
            GetLastError() != ERROR_INSUFFICIENT_BUFFER || !bytes || bytes > 16384) {
            SetLastError(ERROR_INVALID_DATA);
            return false;
        }
        storage.resize((bytes + sizeof(std::max_align_t) - 1) / sizeof(std::max_align_t));
        const auto candidate = reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(storage.data());
        if (!InitializeProcThreadAttributeList(candidate, 2, 0, &bytes)) return false;
        list = candidate;
        return true;
    }

    ~Attributes() { if (list) DeleteProcThreadAttributeList(list); }
};

inline bool device_name(std::wstring_view part) {
    auto stem = part.substr(0, part.find(L'.'));
    while (!stem.empty() && stem.back() == L' ') stem.remove_suffix(1);
    if (stem.size() < 3 || stem.size() > 7) return false;
    std::array<wchar_t, 7> lower{};
    std::transform(stem.begin(), stem.end(), lower.begin(), [](wchar_t ch) {
        return ch >= L'A' && ch <= L'Z' ? static_cast<wchar_t>(ch + (L'a' - L'A')) : ch;
    });
    const std::wstring_view name{lower.data(), stem.size()};
    if (name == L"con" || name == L"prn" || name == L"aux" || name == L"nul" ||
        name == L"conin$" || name == L"conout$") return true;
    return name.size() == 4 && (name.substr(0, 3) == L"com" || name.substr(0, 3) == L"lpt") &&
           std::wstring_view{L"123456789\u00b9\u00b2\u00b3"}.find(name.back()) != name.npos;
}

inline bool path(std::wstring_view value, bool project = false) {
    if (value.size() < 4 || value.size() > 1024 ||
        (value.front() != L'D' && (project || value.front() != L'C')) ||
        value.substr(1, 2) != L":/") return false;
    value.remove_prefix(3);
    constexpr std::wstring_view forbidden = L"\"\\:*?=,;#\x60<>|&";
    while (!value.empty()) {
        const auto slash = value.find(L'/');
        const auto part = value.substr(0, slash);
        if (part.empty() || part.size() > 255 || part.back() == L'.' || part.back() == L' ' ||
            part.find_first_of(forbidden) != part.npos || device_name(part)) return false;
        for (wchar_t ch : part) {
            if (ch < 32 || ch == 127) return false;
        }
        if (slash == value.npos) return true;
        value.remove_prefix(slash + 1);
    }
    return false;
}

inline bool paths(std::wstring_view value) {
    if (value.size() > 16384) return false;
    for (;;) {
        const auto semi = value.find(L';');
        if (!path(value.substr(0, semi))) return false;
        if (semi == value.npos) return true;
        value.remove_prefix(semi + 1);
    }
}

inline std::wstring slash_to_windows(std::wstring path) {
    std::replace(path.begin(), path.end(), L'/', L'\\');
    return path;
}

inline std::vector<std::wstring> compile_arguments(const Request& request) {
    std::vector<std::wstring> args{
        L"/nologo", L"/TP", L"-DGGML_USE_CPU", L"/DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1"
    };
    for (const auto* part : {L"common/.", L"vendor/nlohmann/..", L"vendor/sheredom/..",
                              L"src/../include", L"ggml/src/../include"}) {
        args.push_back(L"-I" + request.upstream + L"/" + part);
    }
    args.insert(args.end(), {L"/DWIN32", L"/D_WINDOWS", L"/EHsc", L"/O2", L"/Ob2",
                            L"/DNDEBUG", L"-MD", L"/Brepro", L"/experimental:deterministic"});
    for (const auto& [source, target] : std::array<std::pair<const std::wstring*, const wchar_t*>, 3>{
             {{&request.worker, L"X:\\locallore\\worker"},
              {&request.upstream, L"X:\\locallore\\llama"},
              {&request.output, L"X:\\locallore\\build"}}}) {
        args.push_back(L"/pathmap:" + *source + L"=" + target);
        args.push_back(L"/pathmap:" + slash_to_windows(*source) + L"=" + target);
    }
    args.insert(args.end(), {L"-std:c++17", L"/showIncludes", L"/Fo" + request.output + L"/main.cpp.obj",
                            L"/Fd" + request.output + L"/compile.pdb", L"/FS", L"-c", L"main.cpp"});
    return args;
}

inline bool valid(const Request& request) {
    constexpr std::wstring_view tool = L"/cl.exe";
    constexpr std::wstring_view output = L"/worker-author-b2-candidate-a";
    const std::wstring_view compiler = request.compiler, root = request.output;
    return path(compiler) && compiler.size() > tool.size() &&
           compiler.substr(compiler.size() - tool.size()) == tool &&
           path(request.worker, true) && path(request.upstream, true) && path(root, true) &&
           root.size() > 3 + output.size() && root.substr(root.size() - output.size()) == output &&
           path(request.windows) && path(request.temp, true) &&
           paths(request.path) && paths(request.include) &&
           request.arguments == compile_arguments(request);
}

inline std::wstring command(const Request& request) {
    std::wstring line = L"\"" + slash_to_windows(request.compiler) + L"\"";
    for (const auto& arg : request.arguments) {
        // Exact recipe arguments have no quote and never end in backslash.
        line += L" \"" + arg + L"\"";
    }
    return line;
}

inline std::wstring environment(const Request& request) {
    std::wstring block;
    for (const auto& [key, value] : std::array<std::pair<const wchar_t*, const std::wstring*>, 6>{
             {{L"INCLUDE", &request.include}, {L"PATH", &request.path},
              {L"SYSTEMROOT", &request.windows}, {L"TEMP", &request.temp},
              {L"TMP", &request.temp}, {L"WINDIR", &request.windows}}}) {
        block += key;
        block += L'=';
        auto native = slash_to_windows(*value);
        block += native;
        block += L'\0';
    }
    return block; // std::wstring adds the final second NUL.
}

inline bool pipe(Handle& read, Handle& write, SECURITY_ATTRIBUTES& inherit) {
    static std::atomic<unsigned long long> serial{0};
    const auto owner = GetCurrentProcessId();
    const auto name = L"\\\\.\\pipe\\LocalLoreCompileJobV1-" + std::to_wstring(owner) + L"-" +
                      std::to_wstring(GetTickCount64()) + L"-" + std::to_wstring(++serial);
    read.value = CreateNamedPipeW(name.c_str(), PIPE_ACCESS_INBOUND | FILE_FLAG_FIRST_PIPE_INSTANCE,
                                 PIPE_TYPE_BYTE | PIPE_READMODE_BYTE | PIPE_NOWAIT | PIPE_REJECT_REMOTE_CLIENTS,
                                 1, 0, 4096, 0, nullptr);
    if (!read.valid()) return false;
    write.value = CreateFileW(name.c_str(), GENERIC_WRITE, 0, &inherit, OPEN_EXISTING,
                              SECURITY_SQOS_PRESENT | SECURITY_IDENTIFICATION, nullptr);
    if (!write.valid()) return false;
    if (ConnectNamedPipe(read.value, nullptr)) {
        SetLastError(ERROR_INVALID_DATA);
        return false;
    }
    if (GetLastError() != ERROR_PIPE_CONNECTED) return false;
    ULONG client = 0;
    if (!GetNamedPipeClientProcessId(read.value, &client)) return false;
    if (client == owner) return true;
    SetLastError(ERROR_INVALID_DATA);
    return false;
}

template <std::size_t Capacity>
bool poll_pipe(const Handle& pipe, Capture<Capacity>& stream, Result& result) {
    // Stop reading a stream after its one-byte overflow probe. This
    // deliberately forfeits its EOF proof and forces writer quarantine.
    if (stream.eof || stream.overflow || !pipe.valid()) return false;
    const auto room = Capacity - stream.size;
    unsigned char extra = 0;
    auto* buffer = room ? stream.bytes.data() + stream.size : &extra;
    DWORD got = 0;
    const auto count = static_cast<DWORD>(room ? (std::min)(room, std::size_t{4096}) : 1);
    if (!ReadFile(pipe.value, buffer, count, &got, nullptr)) {
        const DWORD error = GetLastError();
        if (error == ERROR_BROKEN_PIPE) stream.eof = true;
        else if (error != ERROR_NO_DATA) stop(result, Stop::io, error);
        return false;
    }
    if (!room && got) {
        stream.overflow = true;
        stop(result, Stop::overflow);
    } else {
        stream.size += got;
    }
    return got != 0;
}

inline void observe_process(const Handle& process, Result& result) {
    if (result.signaled) return;
    const DWORD wait = WaitForSingleObject(process.value, 0);
    if (wait == WAIT_TIMEOUT) return;
    if (wait != WAIT_OBJECT_0) {
        stop(result, Stop::io, GetLastError());
        return;
    }
    result.signaled = true;
    DWORD exit = 0;
    if (GetExitCodeProcess(process.value, &exit)) result.exit = exit;
    else stop(result, Stop::io, GetLastError());
}

inline void observe_job(const Handle& job, Result& result) {
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION info{};
    if (!QueryInformationJobObject(job.value, JobObjectBasicAccountingInformation,
                                   &info, sizeof(info), nullptr)) {
        result.active_processes.reset();
        stop(result, Stop::io, GetLastError());
    } else {
        result.active_processes = info.ActiveProcesses;
    }
}

inline void terminate(const Handle& job, const Handle& process, Result& result) {
    if (result.kill_attempted) return;
    result.kill_attempted = true;
    if (result.member) {
        result.kill_failed = !TerminateJobObject(job.value, kill_exit);
    } else {
        // The only unverified direct process is still suspended.
        result.kill_failed = !result.signaled && !TerminateProcess(process.value, kill_exit);
    }
}

template <typename Cancelled>
inline Clock::time_point settle(const Handle& process, const Handle& job, const Handle& out,
                                const Handle& err, const Cancelled& cancelled,
                                Clock::time_point run_deadline, Result& result) {
    std::optional<Clock::time_point> drain_deadline;
    const auto needs_termination = [&]() {
        return !result.signaled || result.active_processes != 0;
    };
    for (;;) {
        const auto now = Clock::now();
        if (cancelled()) stop(result, Stop::cancelled);
        if (!drain_deadline && now >= run_deadline) stop(result, Stop::deadline);
        if (!drain_deadline && result.stop != Stop::none)
            drain_deadline = (std::min)(now, run_deadline) + drain_window;
        if (drain_deadline && now >= *drain_deadline) break;
        if (result.stop != Stop::none && needs_termination()) terminate(job, process, result);

        const bool stdout_progress = poll_pipe(out, result.out, result);
        const bool stderr_progress = poll_pipe(err, result.err, result);
        observe_process(process, result);
        if (cancelled()) stop(result, Stop::cancelled);
        const auto observed = Clock::now();
        // A poll begun in time can still return after the cutoff.
        if (!drain_deadline && observed >= run_deadline) stop(result, Stop::deadline);
        if (!drain_deadline && (result.signaled || result.stop != Stop::none))
            drain_deadline = (std::min)(observed, run_deadline) + drain_window;

        if (drain_deadline) {
            if (observed >= *drain_deadline) break;
            observe_job(job, result);
            if (cancelled()) stop(result, Stop::cancelled);
            if (Clock::now() >= *drain_deadline) break;
            const bool stdout_done = result.out.eof || result.out.overflow;
            const bool stderr_done = result.err.eof || result.err.overflow;
            if (result.signaled && result.active_processes == 0 && stdout_done && stderr_done)
                return *drain_deadline;
        }
        if (!stdout_progress && !stderr_progress) Sleep(1);
    }
    stop(result, Stop::drain);
    if (needs_termination()) terminate(job, process, result);
    return *drain_deadline;
}

struct Quarantine {
    Handle job, process;
};

template <typename Cancelled, typename Ready>
Result launch_owned(const std::wstring& executable, std::wstring cmd, std::wstring env,
                    const std::wstring& cwd, Clock::time_point started, Clock::time_point deadline,
                    const Cancelled& cancelled, const Ready& ready, Quarantine* quarantine = nullptr) {
    Result result;
    Handle job, in, stdin_writer, out, stdout_writer, err, stderr_writer, process, thread;
    const auto start = [&]() {
        if (cancelled()) {
            stop(result, Stop::cancelled);
            return;
        }
        if (cmd.size() >= 32767 || env.size() >= 32767) {
            stop(result, Stop::request);
            return;
        }

        job.value = CreateJobObjectW(nullptr, nullptr);
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        SECURITY_ATTRIBUTES inherit{sizeof(inherit), nullptr, TRUE};
        if (!job.valid() || !SetInformationJobObject(job.value, JobObjectExtendedLimitInformation,
                                                       &limits, sizeof(limits)) ||
            !CreatePipe(&in.value, &stdin_writer.value, &inherit, 0) ||
            !pipe(out, stdout_writer, inherit) || !pipe(err, stderr_writer, inherit)) {
            stop(result, Stop::setup, GetLastError());
            return;
        }
        close(stdin_writer, result);
        if (result.io_error) return;
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION observed{};
        if (!QueryInformationJobObject(job.value, JobObjectExtendedLimitInformation,
                                       &observed, sizeof(observed), nullptr)) {
            stop(result, Stop::setup, GetLastError());
            return;
        }
        if (observed.BasicLimitInformation.LimitFlags != JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE) {
            stop(result, Stop::setup, ERROR_INVALID_DATA);
            return;
        }

        HANDLE child_handles[]{in.value, stdout_writer.value, stderr_writer.value};
        HANDLE jobs[]{job.value};
        Attributes attributes;
        if (!attributes.init() ||
            !UpdateProcThreadAttribute(attributes.list, 0, PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                                       child_handles, sizeof(child_handles), nullptr, nullptr) ||
            !UpdateProcThreadAttribute(attributes.list, 0, PROC_THREAD_ATTRIBUTE_JOB_LIST,
                                       jobs, sizeof(jobs), nullptr, nullptr)) {
            stop(result, Stop::setup, GetLastError());
            return;
        }
        STARTUPINFOEXW startup{};
        startup.StartupInfo.cb = sizeof(startup);
        startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES;
        startup.StartupInfo.hStdInput = in.value;
        startup.StartupInfo.hStdOutput = stdout_writer.value;
        startup.StartupInfo.hStdError = stderr_writer.value;
        startup.lpAttributeList = attributes.list;
        PROCESS_INFORMATION info{};
        if (cancelled()) stop(result, Stop::cancelled);
        if (Clock::now() >= deadline) stop(result, Stop::deadline);
        if (result.stop != Stop::none) return;
        if (!CreateProcessW(executable.c_str(), cmd.data(), nullptr, nullptr, TRUE,
                            CREATE_SUSPENDED | CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT |
                                EXTENDED_STARTUPINFO_PRESENT,
                            env.data(), cwd.c_str(), &startup.StartupInfo, &info)) {
            stop(result, Stop::setup, GetLastError());
            return;
        }
        process.value = info.hProcess;
        thread.value = info.hThread;
        result.pid = info.dwProcessId;
        BOOL member = FALSE;
        if (!IsProcessInJob(process.value, job.value, &member)) stop(result, Stop::setup, GetLastError());
        else if (!member) stop(result, Stop::setup, ERROR_INVALID_DATA);
        else result.member = true;
        close(in, result);
        close(stdout_writer, result);
        close(stderr_writer, result);
        if (cancelled()) stop(result, Stop::cancelled);
        if (Clock::now() >= deadline) stop(result, Stop::deadline);
        if (result.stop == Stop::none) {
            try {
                if (!ready(job.value, process.value, result.pid)) stop(result, Stop::setup, ERROR_INVALID_DATA);
            } catch (...) {
                stop(result, Stop::setup, ERROR_INVALID_DATA);
            }
        }
        if (cancelled()) stop(result, Stop::cancelled);
        if (Clock::now() >= deadline) stop(result, Stop::deadline);
        if (result.stop != Stop::none) return;
        const DWORD previous = ResumeThread(thread.value);
        if (previous == 1) result.resumed = true;
        else stop(result, Stop::setup, previous == DWORD(-1) ? GetLastError() : ERROR_INVALID_DATA);
    };

    start();
    std::optional<Clock::time_point> drain_deadline;
    if (process.valid()) {
        drain_deadline = settle(process, job, out, err, cancelled, deadline, result);
        if (quarantine && !(result.signaled && result.exit.has_value())) {
            quarantine->process.value = std::exchange(process.value, nullptr);
            result.handles_closed = false;
        } else {
            result.process_handle_closed = process.close();
            if (!result.process_handle_closed) {
                result.handles_closed = false;
                stop(result, Stop::io, GetLastError());
            }
        }
    }
    for (Handle* handle : {&thread, &in, &stdin_writer, &stdout_writer, &stderr_writer, &out, &err})
        close(*handle, result);
    if (quarantine && result.pid &&
        !(result.closed() && result.job_and_pipes_closed() && !result.io_error)) {
        quarantine->job.value = std::exchange(job.value, nullptr);
        result.handles_closed = false;
    }
    close(job, result);
    if (cancelled()) stop(result, Stop::cancelled);
    const auto finished = Clock::now();
    if (drain_deadline && finished >= *drain_deadline) stop(result, Stop::drain);
    result.elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(finished - started).count();
    return result;
}

template <typename Cancelled>
Result launch_with_cancel(const Request& request, const Cancelled& cancelled) {
    const auto started = Clock::now();
    const bool was_cancelled = cancelled();
    if (was_cancelled || !valid(request)) {
        Result result;
        stop(result, was_cancelled ? Stop::cancelled : Stop::request);
        result.elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(Clock::now() - started).count();
        return result;
    }
    const auto ready = [](HANDLE, HANDLE, DWORD) { return true; };
    return launch_owned(slash_to_windows(request.compiler), command(request), environment(request),
                        slash_to_windows(request.worker), started, started + run_window, cancelled, ready);
}

} // namespace detail

inline Result launch(const Request& request, const std::atomic_bool& cancelled) {
    return detail::launch_with_cancel(request, [&]() { return cancelled.load(); });
}

} // namespace locallore::compile_job_v1
