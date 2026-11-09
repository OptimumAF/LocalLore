// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
#pragma once

#include "worker_artifact_compile_job_v1.h"

#include <bcrypt.h>
#include <cstdint>
#include <deque>
#include <iterator>

namespace locallore::compile_parent_v1 {

struct Pin {
    std::wstring path;
    std::uint64_t bytes = 0;
    std::string sha256;
};

struct Plan {
    Pin node, entry, helper;
    std::wstring evidence, temp;
    std::string scope, spend, writer_policy, namespace_proof;
};

struct Report {
    compile_job_v1::Result child;
    std::string ready_sha256;
    long long elapsed_ms = 0;
    bool lease_closed = false;
    bool quarantined = false;
};

namespace detail {

namespace job = compile_job_v1::detail;
using job::Clock;
using job::Handle;
using namespace std::chrono_literals;
constexpr auto parent_window = 180s;
constexpr std::uint64_t node_max = 128 * 1024 * 1024;
constexpr std::uint64_t entry_max = 2 * 1024 * 1024;
constexpr std::uint64_t helper_max = 8 * 1024 * 1024;
constexpr DWORD expected_flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

inline bool digest(std::string_view text) {
    return text.size() == 64 && text.find_first_not_of("0123456789abcdef") == text.npos &&
           text.find_first_not_of('0') != text.npos;
}

inline bool same(std::wstring_view a, std::wstring_view b) {
    return CompareStringOrdinal(a.data(), static_cast<int>(a.size()), b.data(),
                                static_cast<int>(b.size()), TRUE) == CSTR_EQUAL;
}

inline bool below(std::wstring_view path, std::wstring_view root) {
    return path.size() >= root.size() && same(path.substr(0, root.size()), root) &&
           (path.size() == root.size() || path[root.size()] == L'/');
}

inline bool pin_shape(const Pin& pin, std::wstring_view leaf, std::uint64_t cap) {
    const std::wstring_view path = pin.path;
    return job::path(path, true) && path.size() > leaf.size() &&
           path.substr(path.size() - leaf.size()) == leaf &&
           pin.bytes > 0 && pin.bytes <= cap && digest(pin.sha256);
}

inline bool valid(const Plan& plan) {
    if (!pin_shape(plan.node, L"/node.exe", node_max) ||
        !pin_shape(plan.entry, L"/worker_artifact_compile_attempt_v1.mjs", entry_max) ||
        !pin_shape(plan.helper, L"/locallore-compile-host-v1.exe", helper_max) ||
        !job::path(plan.evidence, true) || !job::path(plan.temp, true) ||
        !digest(plan.scope) || !digest(plan.spend) || !digest(plan.writer_policy) ||
        !digest(plan.namespace_proof) || below(plan.evidence, plan.temp) || below(plan.temp, plan.evidence))
        return false;
    for (const auto* pin : {&plan.node, &plan.entry, &plan.helper}) {
        const auto dir = std::wstring_view(pin->path).substr(0, pin->path.rfind(L'/'));
        for (const auto* writable : {&plan.evidence, &plan.temp}) {
            if (below(*writable, dir) || below(dir, *writable)) return false;
        }
    }
    return true;
}

inline bool mounted_volume(HANDLE root) {
    std::array<wchar_t, 80> mounted{}, resolved{};
    if (!GetVolumeNameForVolumeMountPointW(L"D:\\", mounted.data(), static_cast<DWORD>(mounted.size())))
        return false;
    const DWORD size = GetFinalPathNameByHandleW(root, resolved.data(), static_cast<DWORD>(resolved.size()),
                                                 FILE_NAME_NORMALIZED | VOLUME_NAME_GUID);
    if (!size || size >= resolved.size()) return false;
    auto a = std::wstring_view(mounted.data()), b = std::wstring_view(resolved.data(), size);
    if (!a.empty() && a.back() == L'\\') a.remove_suffix(1);
    if (!b.empty() && b.back() == L'\\') b.remove_suffix(1);
    return same(a, b);
}

inline bool exact_name(HANDLE file, const std::wstring& path) {
    std::array<wchar_t, 1100> name{};
    const DWORD length = GetFinalPathNameByHandleW(file, name.data(), static_cast<DWORD>(name.size()),
                                                   FILE_NAME_NORMALIZED | VOLUME_NAME_DOS);
    return length && length < name.size() && same(std::wstring_view(name.data(), length), L"\\\\?\\" + path);
}

struct Fact {
    FILE_ID_INFO id{};
    FILE_STANDARD_INFO standard{};
    FILE_BASIC_INFO basic{};
};

inline bool observe(HANDLE handle, const std::wstring& path, bool directory, Fact& fact) {
    FILE_ATTRIBUTE_TAG_INFO tag{};
    return GetFileType(handle) == FILE_TYPE_DISK &&
           GetFileInformationByHandleEx(handle, FileAttributeTagInfo, &tag, sizeof(tag)) &&
           !(tag.FileAttributes & FILE_ATTRIBUTE_REPARSE_POINT) &&
           bool(tag.FileAttributes & FILE_ATTRIBUTE_DIRECTORY) == directory &&
           GetFileInformationByHandleEx(handle, FileIdInfo, &fact.id, sizeof(fact.id)) &&
           GetFileInformationByHandleEx(handle, FileStandardInfo, &fact.standard, sizeof(fact.standard)) &&
           GetFileInformationByHandleEx(handle, FileBasicInfo, &fact.basic, sizeof(fact.basic)) &&
           !fact.standard.DeletePending && (directory || fact.standard.NumberOfLinks == 1) &&
           exact_name(handle, path);
}

inline bool same_id(const Fact& a, const Fact& b) {
    return a.id.VolumeSerialNumber == b.id.VolumeSerialNumber &&
           std::equal(std::begin(a.id.FileId.Identifier), std::end(a.id.FileId.Identifier),
                      std::begin(b.id.FileId.Identifier));
}

inline bool same_file(const Fact& a, const Fact& b) {
    return same_id(a, b) && a.standard.EndOfFile.QuadPart == b.standard.EndOfFile.QuadPart &&
           a.basic.LastWriteTime.QuadPart == b.basic.LastWriteTime.QuadPart &&
           a.basic.ChangeTime.QuadPart == b.basic.ChangeTime.QuadPart;
}

inline std::string hex(const unsigned char* data, std::size_t size) {
    constexpr std::string_view digits = "0123456789abcdef";
    std::string output;
    output.reserve(size * 2);
    for (std::size_t i = 0; i < size; ++i) {
        output.push_back(digits[data[i] >> 4]);
        output.push_back(digits[data[i] & 15]);
    }
    return output;
}

inline std::string id_text(const Fact& fact) {
    return std::to_string(fact.id.VolumeSerialNumber) + ":" +
           hex(fact.id.FileId.Identifier, sizeof(fact.id.FileId.Identifier));
}

struct Sha256 {
    BCRYPT_ALG_HANDLE algorithm = nullptr;
    BCRYPT_HASH_HANDLE hash = nullptr;

    bool init() {
        return BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0 &&
               BCryptCreateHash(algorithm, &hash, nullptr, 0, nullptr, 0, 0) >= 0;
    }
    bool add(unsigned char* bytes, DWORD count) { return BCryptHashData(hash, bytes, count, 0) >= 0; }
    std::string finish() {
        std::array<unsigned char, 32> bytes{};
        return BCryptFinishHash(hash, bytes.data(), static_cast<ULONG>(bytes.size()), 0) >= 0
            ? hex(bytes.data(), bytes.size()) : std::string{};
    }
    ~Sha256() {
        if (hash) BCryptDestroyHash(hash);
        if (algorithm) BCryptCloseAlgorithmProvider(algorithm, 0);
    }
};

struct Held {
    std::wstring path;
    Handle file;
    Fact fact;
    bool directory;
    Held(const std::wstring& value, bool is_directory) : path(value), directory(is_directory) {}
};

class Lease {
public:
    bool add_directory(const std::wstring& path) {
        for (const auto& entry : files_)
            if (entry.directory && entry.path == path) return true;
        if (files_.size() >= 80) return false;
        auto& entry = files_.emplace_back(path, true);
        entry.file.value = CreateFileW(path.c_str(), FILE_READ_ATTRIBUTES,
                                      FILE_SHARE_READ | FILE_SHARE_WRITE, nullptr, OPEN_EXISTING,
                                      FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, nullptr);
        if (!entry.file.valid() || !observe(entry.file.value, path, true, entry.fact)) return false;
        if (path == L"D:\\") {
            if (!mounted_volume(entry.file.value)) return false;
            volume_ = entry.fact.id.VolumeSerialNumber;
        }
        return volume_ && entry.fact.id.VolumeSerialNumber == *volume_;
    }

    bool directories(const std::wstring& path) {
        if (!add_directory(path.substr(0, 3))) return false;
        for (auto next = path.find(L'\\', 3); next != path.npos; next = path.find(L'\\', next + 1))
            if (!add_directory(path.substr(0, next))) return false;
        return add_directory(path);
    }

    Held* add_file(const std::wstring& path) {
        if (files_.size() >= 80) return nullptr;
        auto& entry = files_.emplace_back(path, false);
        entry.file.value = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr,
                                      OPEN_EXISTING, FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_SEQUENTIAL_SCAN, nullptr);
        if (!entry.file.valid() || !observe(entry.file.value, path, false, entry.fact) ||
            !volume_ || entry.fact.id.VolumeSerialNumber != *volume_) return nullptr;
        return &entry;
    }

    const Fact* directory_fact(const std::wstring& path) const {
        for (const auto& entry : files_)
            if (entry.directory && entry.path == path) return &entry.fact;
        return nullptr;
    }

    bool current() const {
        for (const auto& entry : files_) {
            Fact now;
            if (!entry.file.valid() || !observe(entry.file.value, entry.path, entry.directory, now) ||
                !(entry.directory ? same_id(entry.fact, now) : same_file(entry.fact, now))) return false;
        }
        return true;
    }

    bool close() {
        bool known = true;
        for (auto entry = files_.rbegin(); entry != files_.rend(); ++entry)
            known = entry->file.close() && known;
        return known;
    }

private:
    std::deque<Held> files_;
    std::optional<ULONGLONG> volume_;
};

template <typename Live>
bool verify_pin(Held& entry, const Pin& pin, const Live& live) {
    if (entry.fact.standard.EndOfFile.QuadPart < 0 ||
        static_cast<std::uint64_t>(entry.fact.standard.EndOfFile.QuadPart) != pin.bytes) return false;
    Sha256 sha;
    if (!sha.init()) return false;
    std::array<unsigned char, 65536> bytes{};
    auto remaining = pin.bytes;
    while (remaining && live()) {
        const auto want = static_cast<DWORD>((std::min)(remaining, std::uint64_t{bytes.size()}));
        DWORD got = 0;
        if (!ReadFile(entry.file.value, bytes.data(), want, &got, nullptr) || !got || got > want ||
            !sha.add(bytes.data(), got)) return false;
        remaining -= got;
    }
    DWORD extra = 0;
    Fact after;
    return !remaining && live() && ReadFile(entry.file.value, bytes.data(), 1, &extra, nullptr) && !extra &&
           sha.finish() == pin.sha256 && observe(entry.file.value, entry.path, false, after) &&
           same_file(entry.fact, after);
}

inline bool missing(const std::wstring& path) {
    return GetFileAttributesW(path.c_str()) == INVALID_FILE_ATTRIBUTES && GetLastError() == ERROR_FILE_NOT_FOUND;
}

inline bool read_exact(HANDLE file, std::string_view expected) {
    if (expected.size() > 4096) return false;
    std::array<char, 4097> bytes{};
    DWORD total = 0;
    while (total < expected.size()) {
        const auto want = static_cast<DWORD>(expected.size() - total);
        DWORD got = 0;
        if (!ReadFile(file, bytes.data() + total, want, &got, nullptr) || !got || got > want) return false;
        total += got;
    }
    DWORD extra = 0;
    return ReadFile(file, bytes.data() + total, 1, &extra, nullptr) && !extra &&
           std::string_view(bytes.data(), total) == expected;
}

inline bool retain_ready(Lease& lease, const std::wstring& path, const std::string& bytes, std::string& digest) {
    if (bytes.empty() || bytes.size() > 4096) return false;
    Handle writer;
    writer.value = CreateFileW(path.c_str(), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ,
                               nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OPEN_REPARSE_POINT, nullptr);
    Fact initial, written;
    if (!writer.valid() || !observe(writer.value, path, false, initial) || initial.standard.EndOfFile.QuadPart != 0)
        return false;
    DWORD sent = 0;
    while (sent < bytes.size()) {
        const auto want = static_cast<DWORD>(bytes.size() - sent);
        DWORD wrote = 0;
        if (!WriteFile(writer.value, bytes.data() + sent, want, &wrote, nullptr) || !wrote || wrote > want)
            return false;
        sent += wrote;
    }
    LARGE_INTEGER zero{};
    if (!FlushFileBuffers(writer.value) || !SetFilePointerEx(writer.value, zero, nullptr, FILE_BEGIN) ||
        !read_exact(writer.value, bytes) || !observe(writer.value, path, false, written) ||
        !same_id(initial, written) || !writer.close()) return false;

    const auto retained = lease.add_file(path);
    if (!retained || !same_id(initial, retained->fact) || !read_exact(retained->file.value, bytes)) return false;
    Sha256 sha;
    std::string copy = bytes;
    if (!sha.init() || !sha.add(reinterpret_cast<unsigned char*>(copy.data()), static_cast<DWORD>(copy.size())))
        return false;
    digest = sha.finish();
    return !digest.empty();
}

inline bool exact_process(HANDLE process, const std::wstring& image) {
    std::array<wchar_t, 1100> name{};
    DWORD count = static_cast<DWORD>(name.size());
    return QueryFullProcessImageNameW(process, 0, name.data(), &count) && count < name.size() &&
           same(std::wstring_view(name.data(), count), image);
}

inline std::wstring environment(const std::wstring& ready, const std::wstring& temp) {
    std::array<wchar_t, 1024> windows{};
    const auto length = GetWindowsDirectoryW(windows.data(), static_cast<UINT>(windows.size()));
    if (!length || length >= windows.size()) return {};
    const std::wstring root(windows.data(), length);
    std::wstring block;
    for (const auto& [key, value] : std::array<std::pair<const wchar_t*, std::wstring>, 7>{
             {{L"LOCALLORE_COMPILE_PARENT_READY", ready}, {L"PATH", root + L"\\System32"},
              {L"SYSTEMDRIVE", root.substr(0, 2)}, {L"SYSTEMROOT", root}, {L"TEMP", temp},
              {L"TMP", temp}, {L"WINDIR", root}}}) {
        block += key;
        block += L'=';
        block += value;
        block += L'\0';
    }
    return block;
}

} // namespace detail

// The admitted caller owns this object until terminal evidence or quarantine.
class Parent {
public:
    Report run(const Plan& plan, const std::atomic_bool& cancelled) {
        using namespace detail;
        using compile_job_v1::Stop;
        Report report;
        if (used_.exchange(true)) {
            report.child.stop = Stop::request;
            return report;
        }
        const auto started = Clock::now();
        const auto deadline = started + parent_window;
        const auto abort = [&]() { return cancelled.load(); };
        const auto live = [&]() { return !abort() && Clock::now() < deadline; };
        const auto run_fixed = [&]() {
            if (!valid(plan) || GetDriveTypeW(L"D:\\") != DRIVE_FIXED || !live()) {
                report.child.stop = abort() ? Stop::cancelled : Clock::now() >= deadline ? Stop::deadline : Stop::request;
                return;
            }
            const auto node = job::slash_to_windows(plan.node.path);
            const auto entry = job::slash_to_windows(plan.entry.path);
            const auto helper = job::slash_to_windows(plan.helper.path);
            const auto evidence = job::slash_to_windows(plan.evidence), temp = job::slash_to_windows(plan.temp);
            const auto ready_path = evidence + L"\\parent-ready.json";
            auto env = environment(ready_path, temp);
            if (env.empty() || !lease_.directories(evidence) || !lease_.directories(temp)) {
                report.child.stop = Stop::setup;
                return;
            }

            const std::array paths{node, entry, helper};
            const std::array pins{&plan.node, &plan.entry, &plan.helper};
            std::array<Held*, 3> held{};
            for (std::size_t i = 0; i < paths.size(); ++i) {
                const auto parent = paths[i].substr(0, paths[i].rfind(L'\\'));
                if (!live() || !lease_.directories(parent) || !(held[i] = lease_.add_file(paths[i])) ||
                    !verify_pin(*held[i], *pins[i], live)) {
                    report.child.stop = abort() ? Stop::cancelled :
                        Clock::now() >= deadline ? Stop::deadline : Stop::setup;
                    return;
                }
            }
            if (!lease_.current() || !missing(helper + L".com") || !missing(helper + L".exe") ||
                !missing(ready_path)) {
                report.child.stop = Stop::setup;
                return;
            }

            const auto* evidence_fact = lease_.directory_fact(evidence);
            const auto* temp_fact = lease_.directory_fact(temp);
            if (!evidence_fact || !temp_fact) {
                report.child.stop = Stop::setup;
                return;
            }
            const auto ready = [&](HANDLE job_handle, HANDLE process, DWORD pid) {
                JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
                JOBOBJECT_BASIC_ACCOUNTING_INFORMATION accounting{};
                BOOL parent_in_job = FALSE;
                if (!live() || !QueryInformationJobObject(job_handle, JobObjectExtendedLimitInformation,
                                                           &limits, sizeof(limits), nullptr) ||
                    limits.BasicLimitInformation.LimitFlags != expected_flags ||
                    !QueryInformationJobObject(job_handle, JobObjectBasicAccountingInformation,
                                               &accounting, sizeof(accounting), nullptr) ||
                    accounting.ActiveProcesses != 1 || !exact_process(process, node) ||
                    !IsProcessInJob(GetCurrentProcess(), nullptr, &parent_in_job) ||
                    !lease_.current() || !missing(helper + L".com") || !missing(helper + L".exe")) return false;

                std::string record = "{\"version\":1,\"kind\":\"compile_parent_ready_v1\",\"scope\":\"" +
                    plan.scope + "\",\"spend\":\"" + plan.spend + "\",\"writerPolicy\":\"" + plan.writer_policy +
                    "\",\"namespace\":\"" + plan.namespace_proof + "\",\"evidenceId\":\"" + id_text(*evidence_fact) +
                    "\",\"tempId\":\"" + id_text(*temp_fact) + "\",\"parentPid\":" +
                    std::to_string(GetCurrentProcessId()) + ",\"nodePid\":" + std::to_string(pid) +
                    ",\"jobFlags\":" + std::to_string(limits.BasicLimitInformation.LimitFlags) +
                    ",\"parentInJob\":" + (parent_in_job ? "true" : "false") + ",\"activeProcesses\":1,\"pins\":[";
                for (std::size_t i = 0; i < pins.size(); ++i) {
                    if (i) record += ',';
                    record += "{\"id\":\"" + id_text(held[i]->fact) + "\",\"sha256\":\"" + pins[i]->sha256 +
                        "\",\"bytes\":" + std::to_string(pins[i]->bytes) + "}";
                }
                record += "]}";
                return retain_ready(lease_, ready_path, record, report.ready_sha256) && lease_.current();
            };
            const auto cmd = L"\"" + node + L"\" \"" + entry + L"\"";
            report.child = job::launch_owned(node, cmd, std::move(env), entry.substr(0, entry.rfind(L'\\')),
                                             started, deadline, abort, ready, &quarantine_job_);
            if (!lease_.current() || !missing(helper + L".com") || !missing(helper + L".exe"))
                job::stop(report.child, Stop::io, ERROR_INVALID_DATA);
        };

        try {
            run_fixed();
        } catch (...) {
            job::stop(report.child, Stop::setup, ERROR_INVALID_DATA);
        }
        const bool group_known = !report.child.pid ||
            (report.child.closed() && report.child.job_and_pipes_closed() && !report.child.io_error);
        if (group_known) report.lease_closed = lease_.close();
        report.quarantined = !group_known || !report.lease_closed;
        if (abort()) job::stop(report.child, Stop::cancelled);
        const auto finished = Clock::now();
        if (finished >= deadline + job::drain_window) job::stop(report.child, Stop::drain);
        report.elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(finished - started).count();
        return report;
    }

private:
    std::atomic_bool used_{false};
    detail::Lease lease_;
    detail::Handle quarantine_job_;
};

} // namespace locallore::compile_parent_v1
