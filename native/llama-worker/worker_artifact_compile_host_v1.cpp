// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#if defined(_M_ARM64EC)
#error The compile helper requires native x64, not ARM64EC.
#endif

#if !defined(_MT) || defined(_DLL) || defined(_DEBUG)
#error The compile helper requires the static MSVC release runtime.
#endif

#include "worker_artifact_compile_job_v1.h"

#include <cstdint>

namespace {

using locallore::compile_job_v1::Request;
using locallore::compile_job_v1::Result;
using locallore::compile_job_v1::Stop;
using Clock = std::chrono::steady_clock;
using namespace std::chrono_literals;
using Byte = unsigned char;
constexpr std::string_view request_magic = "LLCLV1\r\n";
constexpr std::string_view result_magic = "LLCLR1\r\n";
constexpr std::size_t binding_size = 32, field_count = 8, argument_count = 31;
constexpr std::size_t request_cap = 65536;
constexpr DWORD poll_chunk = 4096;

std::uint32_t u32(const Byte* bytes) {
    return std::uint32_t{bytes[0]} | (std::uint32_t{bytes[1]} << 8) |
           (std::uint32_t{bytes[2]} << 16) | (std::uint32_t{bytes[3]} << 24);
}

template <typename Unsigned>
void put(Byte*& destination, Unsigned number) {
    for (std::size_t i = 0; i < sizeof(number); ++i) {
        *destination++ = static_cast<Byte>(number & 0xff);
        number >>= 8;
    }
}

// The one-use host is single-threaded and is the only consumer of this pipe.
bool read_exact(HANDLE input, Byte* target, std::size_t remaining, Clock::time_point deadline) {
    while (remaining && Clock::now() < deadline) {
        DWORD available = 0;
        if (!PeekNamedPipe(input, nullptr, 0, nullptr, &available, nullptr)) return false;
        if (!available) {
            Sleep(1);
            continue;
        }
        const auto count = static_cast<DWORD>(
            (std::min)({std::size_t{available}, remaining, std::size_t{poll_chunk}}));
        DWORD received = 0;
        if (!ReadFile(input, target, count, &received, nullptr) || !received) return false;
        target += received;
        remaining -= received;
    }
    return !remaining && Clock::now() < deadline;
}

bool write_exact(HANDLE output, const Byte* data, std::size_t remaining) {
    while (remaining) {
        DWORD written = 0;
        const auto count = static_cast<DWORD>((std::min)(remaining, std::size_t{poll_chunk}));
        if (!WriteFile(output, data, count, &written, nullptr) || !written) return false;
        data += written;
        remaining -= written;
    }
    return true;
}

struct Cursor {
    const Byte* bytes;
    std::size_t left;

    bool take(std::wstring& value) {
        if (left < 2) return false;
        const auto length = std::size_t{bytes[0]} | (std::size_t{bytes[1]} << 8);
        bytes += 2;
        left -= 2;
        if (!length || length > left) return false;
        const auto* text = reinterpret_cast<const char*>(bytes);
        const int input_size = static_cast<int>(length);
        const int chars = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text, input_size, nullptr, 0);
        if (!chars) return false;
        value.resize(static_cast<std::size_t>(chars));
        if (MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text, input_size,
                                value.data(), chars) != chars ||
            value.find(L'\0') != std::wstring::npos) return false;
        bytes += length;
        left -= length;
        return true;
    }
};

bool parse(const std::vector<Byte>& body, Request& request) {
    Cursor cursor{body.data() + binding_size, body.size() - binding_size};
    if (std::none_of(body.begin(), body.begin() + binding_size, [](Byte value) { return value != 0; }))
        return false;
    const std::array<std::wstring*, field_count> fields{
        &request.compiler, &request.worker, &request.upstream, &request.output,
        &request.windows, &request.path, &request.include, &request.temp
    };
    for (auto* field : fields) if (!cursor.take(*field)) return false;
    request.arguments.resize(argument_count);
    for (auto& argument : request.arguments) if (!cursor.take(argument)) return false;
    return cursor.left == 0;
}

bool write_result(HANDLE output, const Byte* binding, const Result& result) {
    static_assert(static_cast<unsigned>(Stop::none) == 0 && static_cast<unsigned>(Stop::request) == 1 &&
                  static_cast<unsigned>(Stop::cancelled) == 2 && static_cast<unsigned>(Stop::deadline) == 3 &&
                  static_cast<unsigned>(Stop::setup) == 4 && static_cast<unsigned>(Stop::io) == 5 &&
                  static_cast<unsigned>(Stop::overflow) == 6 && static_cast<unsigned>(Stop::drain) == 7);
    const std::array flags{result.exit.has_value(), result.active_processes.has_value(),
        result.member, result.resumed, result.signaled, result.kill_attempted,
        result.kill_failed, result.io_error, result.process_handle_closed, result.handles_closed,
        result.out.overflow, result.err.overflow, result.out.eof, result.err.eof};
    std::uint32_t bits = 0;
    for (std::size_t index = 0; index < flags.size(); ++index)
        if (flags[index]) bits |= std::uint32_t{1} << index;

    std::array<Byte, 80> frame{};
    auto* cursor = std::copy(result_magic.begin(), result_magic.end(), frame.data());
    cursor = std::copy_n(binding, binding_size, cursor);
    put(cursor, static_cast<std::uint32_t>(result.stop));
    put(cursor, static_cast<std::uint32_t>(result.pid));
    put(cursor, static_cast<std::uint32_t>(result.error));
    put(cursor, static_cast<std::uint32_t>(result.exit.value_or(0)));
    put(cursor, static_cast<std::uint32_t>(result.active_processes.value_or(0)));
    put(cursor, bits);
    put(cursor, static_cast<std::uint64_t>(result.elapsed_ms));
    put(cursor, static_cast<std::uint32_t>(result.out.size));
    put(cursor, static_cast<std::uint32_t>(result.err.size));
    return cursor == frame.data() + frame.size() &&
           write_exact(output, frame.data(), frame.size()) &&
           write_exact(output, result.out.bytes.data(), result.out.size) &&
           write_exact(output, result.err.bytes.data(), result.err.size);
}

int run() {
    const auto input = GetStdHandle(STD_INPUT_HANDLE);
    const auto output = GetStdHandle(STD_OUTPUT_HANDLE);
    if (GetFileType(input) != FILE_TYPE_PIPE || GetFileType(output) != FILE_TYPE_PIPE || input == output)
        return 2;
    const auto deadline = Clock::now() + 5s;
    std::array<Byte, 12> header{};
    if (!read_exact(input, header.data(), header.size(), deadline) ||
        !std::equal(request_magic.begin(), request_magic.end(), header.begin())) return 2;
    const auto length = u32(header.data() + request_magic.size());
    if (length <= binding_size || length > request_cap) return 2;
    std::vector<Byte> body(length);
    Request request;
    if (!read_exact(input, body.data(), body.size(), deadline) || !parse(body, request) ||
        Clock::now() >= deadline) return 2;
    bool stopped = false;
    const auto cancelled = [&]() {
        if (!stopped) {
            DWORD available = 0;
            stopped = !PeekNamedPipe(input, nullptr, 0, nullptr, &available, nullptr) || available != 0;
        }
        return stopped;
    };
    const auto result = locallore::compile_job_v1::detail::launch_with_cancel(request, cancelled);
    return write_result(output, body.data(), result) ? 0 : 3;
}

} // namespace

int wmain(int argc, wchar_t**) {
    if (argc != 1) return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
    try { return run(); }
    catch (...) { return 4; }
}
