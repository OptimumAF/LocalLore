/* Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0 */
/* Fixed read-only observation. No signal, process creation, model or file mutation. */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <linux/magic.h>
#include <poll.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/statfs.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>

#ifndef __NR_pidfd_open
#error "The pinned NDK must declare pidfd_open; no guessed syscall number."
#endif

enum observed_bool { UNKNOWN = -1, FALSE_VALUE = 0, TRUE_VALUE = 1 };
struct packet {
    const char *mode, *state, *error;
    char boot[37];
    bool boot_known, identity_arguments, uid_known, ticks_known, poll_known;
    int pid, expected_uid, observed_uid, poll_revents, native_errno;
    uint64_t start_ticks;
    uint64_t observed_boottime_ns;
    bool boottime_known;
    bool pidfd_opened, proc_opened;
    enum observed_bool pidfd_closed, proc_closed;
};

static void refuse(struct packet *p, const char *error, int native_errno) {
    p->state = "refused";
    /* A failed close is never hidden behind another error or retried. */
    if (p->error == NULL || strcmp(error, "close") == 0) {
        p->error = error;
        p->native_errno = native_errno;
    }
}

static bool close_once(struct packet *p, int *fd) {
    if (*fd < 0) return true;
    int owned = *fd;
    *fd = -1;
    if (close(owned) != 0) {
        int saved = errno;
        refuse(p, "close", saved);
        return false;
    }
    return true;
}

static const char *proc_error(int error) {
    if (error == EPERM || error == EACCES) return "proc_permission";
    if (error == ESRCH || error == ENOENT) return "proc_race";
    return "io";
}

static bool decimal(const char *text, uint64_t maximum, uint64_t *out) {
    if (text == NULL || text[0] < '1' || text[0] > '9') return false;
    uint64_t value = 0;
    for (size_t i = 0; text[i] != '\0'; ++i) {
        if (text[i] < '0' || text[i] > '9') return false;
        unsigned digit = (unsigned)(text[i] - '0');
        if (value > (maximum - digit) / 10) return false;
        value = value * 10 + digit;
    }
    *out = value;
    return true;
}

static bool procfs(struct packet *p, int fd) {
    struct statfs value;
    if (fstatfs(fd, &value) != 0) {
        int saved = errno;
        refuse(p, proc_error(saved), saved);
        return false;
    }
    if ((unsigned long)value.f_type != PROC_SUPER_MAGIC) {
        refuse(p, "malformed", 0);
        return false;
    }
    return true;
}

static bool read_owned(struct packet *p, int fd, char *buffer, size_t capacity) {
    size_t used = 0;
    bool ok = procfs(p, fd);
    while (ok && used < capacity - 1) {
        ssize_t count = read(fd, buffer + used, capacity - 1 - used);
        if (count < 0) {
            int saved = errno;
            refuse(p, proc_error(saved), saved);
            ok = false;
        } else if (count == 0) {
            break;
        } else {
            used += (size_t)count;
        }
    }
    if (ok && used == capacity - 1) {
        char extra;
        ssize_t count = read(fd, &extra, 1);
        if (count < 0) {
            int saved = errno;
            refuse(p, proc_error(saved), saved);
            ok = false;
        } else if (count != 0) {
            refuse(p, "malformed", 0);
            ok = false;
        }
    }
    if (ok && (used == 0 || memchr(buffer, '\0', used) != NULL)) {
        refuse(p, "malformed", 0);
        ok = false;
    }
    buffer[used] = '\0';
    if (!close_once(p, &fd)) ok = false;
    return ok;
}

static bool boot_id(struct packet *p) {
    int fd = open("/proc/sys/kernel/random/boot_id", O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) {
        int saved = errno;
        refuse(p, proc_error(saved), saved);
        return false;
    }
    char raw[65];
    if (!read_owned(p, fd, raw, sizeof(raw))) return false;
    size_t size = strlen(raw);
    if (size == 37 && raw[36] == '\n') raw[--size] = '\0';
    if (size != 36) { refuse(p, "malformed", 0); return false; }
    for (size_t i = 0; i < size; ++i) {
        bool dash = i == 8 || i == 13 || i == 18 || i == 23;
        if ((dash && raw[i] != '-') || (!dash && !((raw[i] >= '0' && raw[i] <= '9') ||
              (raw[i] >= 'a' && raw[i] <= 'f')))) {
            refuse(p, "malformed", 0);
            return false;
        }
    }
    memcpy(p->boot, raw, 37);
    p->boot_known = true;
    return true;
}

static bool process_file(struct packet *p, int directory, const char *name, char *raw, size_t cap) {
    int fd = openat(directory, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) {
        int saved = errno;
        refuse(p, proc_error(saved), saved);
        return false;
    }
    return read_owned(p, fd, raw, cap);
}

static bool uid_line(struct packet *p, const char *status, int *uid) {
    const char *line = status;
    bool found = false;
    while (*line != '\0') {
        const char *end = strchr(line, '\n');
        if (end == NULL) end = line + strlen(line);
        if ((size_t)(end - line) >= 4 && memcmp(line, "Uid:", 4) == 0) {
            if (found) return false;
            const char *cursor = line + 4;
            uint64_t ids[4];
            for (int i = 0; i < 4; ++i) {
                while (cursor < end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
                const char *start = cursor;
                while (cursor < end && *cursor >= '0' && *cursor <= '9') ++cursor;
                size_t size = (size_t)(cursor - start);
                char token[12];
                if (size == 0 || size >= sizeof(token)) return false;
                memcpy(token, start, size); token[size] = '\0';
                if (strcmp(token, "0") == 0) ids[i] = 0;
                else if (!decimal(token, INT_MAX, &ids[i])) return false;
            }
            while (cursor < end && (*cursor == ' ' || *cursor == '\t')) ++cursor;
            if (cursor != end) return false;
            *uid = (int)ids[0];
            p->observed_uid = *uid;
            p->uid_known = true;
            if (ids[0] != ids[1] || ids[0] != ids[2] || ids[0] != ids[3] || *uid != p->expected_uid) {
                refuse(p, "uid_mismatch", 0);
                return false;
            }
            found = true;
        }
        line = *end == '\0' ? end : end + 1;
    }
    return found;
}

static bool ticks_line(struct packet *p, const char *stat, uint64_t *ticks) {
    const char *space = strchr(stat, ' ');
    const char *last = strrchr(stat, ')');
    if (space == NULL || last == NULL || space[1] != '(' || last <= space) return false;
    char pid[12];
    size_t length = (size_t)(space - stat);
    uint64_t parsed_pid;
    if (length == 0 || length >= sizeof(pid)) return false;
    memcpy(pid, stat, length); pid[length] = '\0';
    if (!decimal(pid, INT_MAX, &parsed_pid) || parsed_pid != (uint64_t)p->pid) return false;
    const char *cursor = last + 1;
    for (unsigned field = 3; field <= 22; ++field) {
        if (*cursor != ' ') return false;
        while (*cursor == ' ') ++cursor;
        const char *begin = cursor;
        while (*cursor != '\0' && *cursor != ' ' && *cursor != '\n') ++cursor;
        if (cursor == begin) return false;
        if (field == 22) {
            char token[32];
            length = (size_t)(cursor - begin);
            if (length >= sizeof(token)) return false;
            memcpy(token, begin, length); token[length] = '\0';
            if (!decimal(token, UINT64_MAX, ticks)) return false;
            p->start_ticks = *ticks;
            p->ticks_known = true;
            return true;
        }
    }
    return false;
}

static void snapshot(struct packet *p) {
    char path[64];
    int length = snprintf(path, sizeof(path), "/proc/%d", p->pid);
    if (length <= 0 || (size_t)length >= sizeof(path)) { refuse(p, "malformed", 0); return; }
    /* An open proc directory stays attached to its original struct pid, including after PID reuse. */
    int directory = open(path, O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    int directory_errno = directory < 0 ? errno : 0;
    int pidfd = -1;
    if (directory < 0 && directory_errno != ENOENT) { refuse(p, proc_error(directory_errno), directory_errno); return; }
    if (directory >= 0) {
        p->proc_opened = true;
        if (!procfs(p, directory)) goto done;
    }
    pidfd = (int)syscall(__NR_pidfd_open, p->pid, 0);
    if (pidfd < 0) {
        int saved = errno;
        if (saved == ESRCH) { p->state = "absent"; p->native_errno = saved; }
        else if (saved == ENOSYS || saved == EOPNOTSUPP) refuse(p, "pidfd_unsupported", saved);
        else if (saved == EPERM || saved == EACCES) refuse(p, "pidfd_permission", saved);
        else refuse(p, "io", saved);
        goto done;
    }
    p->pidfd_opened = true;
    if (directory < 0) { refuse(p, "proc_race", directory_errno); goto done; }
    char status[16385], stat[16385];
    int uid = 0;
    uint64_t ticks = 0;
    if (!process_file(p, directory, "status", status, sizeof(status)) || !uid_line(p, status, &uid) ||
        !process_file(p, directory, "stat", stat, sizeof(stat)) || !ticks_line(p, stat, &ticks)) {
        refuse(p, "malformed", 0); goto done;
    }
    /* A changed credential/start observation refuses; no second observation repairs it. */
    int uid_after = 0;
    uint64_t ticks_after = 0;
    if (!process_file(p, directory, "status", status, sizeof(status)) || !uid_line(p, status, &uid_after) ||
        !process_file(p, directory, "stat", stat, sizeof(stat)) || !ticks_line(p, stat, &ticks_after) ||
        uid != uid_after || ticks != ticks_after) {
        refuse(p, "proc_race", 0); goto done;
    }
    struct pollfd observation = { .fd = pidfd, .events = POLLIN, .revents = 0 };
    int count = poll(&observation, 1, 0);
    if (count < 0) { int saved = errno; refuse(p, "io", saved); goto done; }
    p->poll_known = true;
    p->poll_revents = observation.revents;
    if (count == 0 && observation.revents == 0) p->state = "alive";
    else if (count == 1 && (observation.revents == POLLIN || observation.revents == POLLHUP ||
                           observation.revents == (POLLIN | POLLHUP))) p->state = "exited";
    else refuse(p, "malformed", 0);
done:
    if (pidfd >= 0) p->pidfd_closed = close_once(p, &pidfd) ? TRUE_VALUE : UNKNOWN;
    if (directory >= 0) p->proc_closed = close_once(p, &directory) ? TRUE_VALUE : UNKNOWN;
}

static const char *boolean(enum observed_bool value) {
    return value == TRUE_VALUE ? "true" : value == FALSE_VALUE ? "false" : "null";
}

static int emit(const struct packet *p, int result) {
    char boot[40] = "null", pid[16] = "null", expected[16] = "null", observed[16] = "null";
    char ticks[32] = "null", revents[16] = "null", error[64] = "null", output[4096];
    if (p->boot_known) (void)snprintf(boot, sizeof(boot), "\"%s\"", p->boot);
    if (p->identity_arguments) {
        (void)snprintf(pid, sizeof(pid), "%d", p->pid);
        (void)snprintf(expected, sizeof(expected), "%d", p->expected_uid);
    }
    if (p->uid_known) (void)snprintf(observed, sizeof(observed), "%d", p->observed_uid);
    if (p->ticks_known) (void)snprintf(ticks, sizeof(ticks), "%" PRIu64, p->start_ticks);
    if (p->poll_known) (void)snprintf(revents, sizeof(revents), "%d", p->poll_revents);
    if (p->error != NULL) (void)snprintf(error, sizeof(error), "\"%s\"", p->error);
    int size = snprintf(output, sizeof(output),
        "{\"version\":1,\"protocol\":\"android-author-process-probe-v1\",\"mode\":\"%s\","
        "\"boot_id\":%s,\"pid\":%s,\"expected_uid\":%s,\"observed_uid\":%s,\"start_ticks\":%s,"
        "\"state\":\"%s\",\"pidfd_opened\":%s,\"poll_revents\":%s,\"pidfd_closed\":%s,"
        "\"proc_opened\":%s,\"proc_closed\":%s,\"error\":%s,\"errno\":%d}\n",
        p->mode, boot, pid, expected, observed, ticks, p->state, p->pidfd_opened ? "true" : "false",
        revents, boolean(p->pidfd_closed), p->proc_opened ? "true" : "false", boolean(p->proc_closed), error, p->native_errno);
    if (size <= 0 || (size_t)size >= sizeof(output)) return 74;
    return write(STDOUT_FILENO, output, (size_t)size) == size ? result : 74;
}


/* CLOCK_BOOTTIME shares Android elapsedRealtimeNanos' suspend-inclusive clock.
 * Sample only after snapshot has attempted all owned descriptor closures. */
static void observe_boottime(struct packet *p) {
    struct timespec now;
    if (clock_gettime(CLOCK_BOOTTIME, &now) != 0) {
        int saved = errno;
        refuse(p, "io", saved);
        return;
    }
    if (now.tv_sec < 0 || now.tv_nsec < 0 || now.tv_nsec >= 1000000000L ||
        (uint64_t)now.tv_sec > ((uint64_t)INT64_MAX - (uint64_t)now.tv_nsec) / UINT64_C(1000000000)) {
        refuse(p, "malformed", 0);
        return;
    }
    uint64_t value = (uint64_t)now.tv_sec * UINT64_C(1000000000) + (uint64_t)now.tv_nsec;
    if (value == 0) { refuse(p, "malformed", 0); return; }
    p->observed_boottime_ns = value;
    p->boottime_known = true;
}

static int emit_v2(const struct packet *p, int result) {
    char boot[40] = "null", pid[16] = "null", expected[16] = "null", observed[16] = "null";
    char ticks[32] = "null", revents[16] = "null", error[64] = "null", output[4096];
    char boottime[32] = "null";
    if (p->boottime_known) (void)snprintf(boottime, sizeof(boottime), "%" PRIu64, p->observed_boottime_ns);
    if (p->boot_known) (void)snprintf(boot, sizeof(boot), "\"%s\"", p->boot);
    if (p->identity_arguments) {
        (void)snprintf(pid, sizeof(pid), "%d", p->pid);
        (void)snprintf(expected, sizeof(expected), "%d", p->expected_uid);
    }
    if (p->uid_known) (void)snprintf(observed, sizeof(observed), "%d", p->observed_uid);
    if (p->ticks_known) (void)snprintf(ticks, sizeof(ticks), "%" PRIu64, p->start_ticks);
    if (p->poll_known) (void)snprintf(revents, sizeof(revents), "%d", p->poll_revents);
    if (p->error != NULL) (void)snprintf(error, sizeof(error), "\"%s\"", p->error);
    int size = snprintf(output, sizeof(output),
        "{\"version\":2,\"protocol\":\"android-author-process-probe-v2\",\"mode\":\"%s\","
        "\"boot_id\":%s,\"pid\":%s,\"expected_uid\":%s,\"observed_uid\":%s,\"start_ticks\":%s,"
        "\"state\":\"%s\",\"pidfd_opened\":%s,\"poll_revents\":%s,\"pidfd_closed\":%s,"
        "\"proc_opened\":%s,\"proc_closed\":%s,\"error\":%s,\"errno\":%d,\"observed_boottime_ns\":%s}\n",
        p->mode, boot, pid, expected, observed, ticks, p->state, p->pidfd_opened ? "true" : "false",
        revents, boolean(p->pidfd_closed), p->proc_opened ? "true" : "false", boolean(p->proc_closed), error, p->native_errno, boottime);
    if (size <= 0 || (size_t)size >= sizeof(output)) return 74;
    return write(STDOUT_FILENO, output, (size_t)size) == size ? result : 74;
}

int main(int argc, char **argv) {
    struct packet packet = { .mode = "boot", .state = "refused", .pidfd_closed = UNKNOWN, .proc_closed = UNKNOWN };
    bool boot = argc == 2 && strcmp(argv[1], "--boot") == 0;
    bool v2 = argc >= 2 && strcmp(argv[1], "--snapshot-v2") == 0;
    if (!boot) {
        uint64_t pid = 0, uid = 0;
        packet.mode = "snapshot";
        if (argc != 4 || (strcmp(argv[1], "--snapshot") != 0 && !v2) || !decimal(argv[2], INT_MAX, &pid) ||
            !decimal(argv[3], INT_MAX, &uid) || uid < 10000) {
            refuse(&packet, "malformed", 0);
            return v2 ? emit_v2(&packet, 64) : emit(&packet, 64);
        }
        packet.pid = (int)pid;
        packet.expected_uid = (int)uid;
        packet.identity_arguments = true;
    }
    if (boot_id(&packet)) {
        if (boot) packet.state = "boot";
        else snapshot(&packet);
    }
    if (v2) { observe_boottime(&packet); return emit_v2(&packet, 0); }
    return emit(&packet, 0);
}
