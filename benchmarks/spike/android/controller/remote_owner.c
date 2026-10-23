// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development experiment only. Own one trusted child, never signal a host-supplied PID.
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t interrupted;
static void interrupt(int sig) { (void)sig; interrupted = 1; }
static double now(void) {
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC, &value)) _exit(125);
    return (double)value.tv_sec + (double)value.tv_nsec / 1000000000.0;
}
static void pause_poll(void) {
    struct timespec duration = {0, 10000000};
    nanosleep(&duration, NULL);
}
static int present(const char *name) {
    struct stat value;
    return lstat(name, &value) == 0 && S_ISREG(value.st_mode) && value.st_size == 0;
}
static int record(const char *name, const char *text) {
    char temporary[64];
    if (snprintf(temporary, sizeof temporary, "%s.tmp", name) >= (int)sizeof temporary) return -1;
    int fd = open(temporary, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (fd < 0) return -1;
    size_t size = strlen(text), written = 0;
    while (written < size) {
        ssize_t count = write(fd, text + written, size - written);
        if (count < 0 && errno == EINTR) continue;
        if (count <= 0) { close(fd); return -1; }
        written += (size_t)count;
    }
    if (close(fd)) return -1;
    return rename(temporary, name);
}
static int owned_run(const char *path) {
    const char *prefix = "/data/local/tmp/locallore-m01/runs/";
    size_t size = strlen(prefix);
    if (strncmp(path, prefix, size) || strlen(path + size) != 32) return 0;
    return strspn(path + size, "0123456789abcdef") == 32;
}
int main(int argc, char **argv) {
    if (argc < 4 || !owned_run(argv[1])) return 125;
    char *end = NULL;
    long seconds = strtol(argv[2], &end, 10);
    if (!end || *end || seconds < 1 || seconds > 90) return 125;
    char worker[160];
    if (snprintf(worker, sizeof worker, "%s/worker", argv[1]) >= (int)sizeof worker ||
        strcmp(argv[3], worker) || chdir(argv[1])) return 125;
    umask(077);
    struct sigaction handler;
    memset(&handler, 0, sizeof handler);
    handler.sa_handler = interrupt;
    sigemptyset(&handler.sa_mask);
    for (int i = 0; i < 3; ++i) {
        int sig = i == 0 ? SIGTERM : (i == 1 ? SIGINT : SIGHUP);
        if (sigaction(sig, &handler, NULL)) return 125;
    }
    handler.sa_handler = SIG_DFL;
    if (sigaction(SIGCHLD, &handler, NULL)) return 125;
    sigset_t signals;
    sigemptyset(&signals);
    sigaddset(&signals, SIGCHLD);
    sigaddset(&signals, SIGTERM);
    sigaddset(&signals, SIGINT);
    sigaddset(&signals, SIGHUP);
    if (sigprocmask(SIG_UNBLOCK, &signals, NULL)) return 125;
    double start = now(), deadline = start + seconds;
    char owner[64];
    snprintf(owner, sizeof owner, "%ld\n", (long)getpid());
    if (record("owner", owner)) return 125;
    const char *reason = NULL;
    while (!present("release")) {
        if (interrupted || present("cancel")) { reason = "cancelled"; break; }
        if (now() >= deadline || now() - start >= 15) { reason = "timeout"; break; }
        pause_poll();
    }
    if (!reason && (interrupted || present("cancel"))) reason = "cancelled";
    if (!reason && now() >= deadline) reason = "timeout";
    if (reason) {
        char output[64];
        snprintf(output, sizeof output, "%s 124\n", reason);
        return record("done", output) ? 125 : 0;
    }
    int input = open("request", O_RDONLY | O_NONBLOCK | O_CLOEXEC | O_NOFOLLOW);
    struct stat info;
    if (input < 0 || fstat(input, &info) || !S_ISREG(info.st_mode) ||
        info.st_size < 0 || info.st_size > 131072) {
        if (input >= 0) close(input);
        return record("done", "failed 125\n") ? 125 : 0;
    }
    pid_t child = fork();
    if (child == 0) {
        handler.sa_handler = SIG_DFL;
        sigaction(SIGTERM, &handler, NULL);
        sigaction(SIGINT, &handler, NULL);
        sigaction(SIGHUP, &handler, NULL);
        if (dup2(input, STDIN_FILENO) < 0) _exit(126);
        close(input);
        execv(argv[3], argv + 3);
        _exit(127);
    }
    close(input);
    if (child < 0) return record("done", "failed 125\n") ? 125 : 0;
    int status = 0, term_sent = 0, kill_sent = 0;
    double terminate_at = 0;
    for (;;) {
        pid_t waited = waitpid(child, &status, WNOHANG);
        if (waited == child) break; // Never signal again after reaping: PID may now be reused.
        if (waited < 0) {
            if (errno == EINTR) continue;
            record("done", "cleanup_failed 125\n");
            return 125;
        }
        if (!reason && (interrupted || present("cancel"))) reason = "cancelled";
        if (!reason && now() >= deadline) reason = "timeout";
        if (reason && !term_sent) {
            // Our direct child has not been reaped, so its PID cannot be recycled.
            kill(child, SIGTERM);
            term_sent = 1;
            terminate_at = now();
        }
        if (term_sent && !kill_sent && now() - terminate_at >= 0.5) {
            kill(child, SIGKILL);
            kill_sent = 1;
        }
        if (kill_sent && now() - terminate_at >= 5) {
            record("done", "cleanup_failed 125\n");
            return 125; // Cannot claim that an uninterruptible OS task was reclaimed.
        }
        pause_poll();
    }
    int code = WIFEXITED(status) ? WEXITSTATUS(status) : 128 + WTERMSIG(status);
    char output[64];
    snprintf(output, sizeof output, "%s %d\n", reason ? reason : (code == 0 ? "completed" : "failed"), code);
    return record("done", output) ? 125 : 0;
}
