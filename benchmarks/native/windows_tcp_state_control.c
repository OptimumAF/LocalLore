/* Independent native owned-socket control; never an existing-service probe.
 * Build as x64 C11 using pinned Microsoft compiler/SDK, Ws2_32.lib and
 * Iphlpapi.lib. Import/build does not run this executable.
 * Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
 */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0601
#define _CRT_SECURE_NO_WARNINGS
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <iphlpapi.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>

#if !defined(_MSC_VER) || !defined(_M_X64)
#error This diagnostic requires the admitted Microsoft x64 C11 build.
#endif

#define CAP_BYTES (1024u * 1024u)
#define CAP_ROWS 16384u
#define SELECTED_ROWS 8u
#define WORKER_MS 10000u
#define PAYLOAD_BYTES 17u
#define ASSERT_OFFSET(type, member, expected) \
    _Static_assert(offsetof(type, member) == (expected), #type "." #member)

_Static_assert(sizeof(void *) == 8, "x64 pointer ABI");
_Static_assert(sizeof(DWORD) == 4 && sizeof(ULONG) == 4, "native DWORD ABI");
_Static_assert(sizeof(MIB_TCPROW_OWNER_PID) == 24, "owner PID row ABI");
_Static_assert(sizeof(MIB_TCPROW) == 20, "basic row ABI");
_Static_assert(sizeof(MIB_TCPROW2) == 28, "owner2 row ABI");
_Static_assert(sizeof(TCP_CONNECTION_OFFLOAD_STATE) == 4, "offload ABI");
ASSERT_OFFSET(MIB_TCPTABLE_OWNER_PID, table, 4);
ASSERT_OFFSET(MIB_TCPTABLE, table, 4);
ASSERT_OFFSET(MIB_TCPTABLE2, table, 4);
ASSERT_OFFSET(MIB_TCPROW_OWNER_PID, dwState, 0);
ASSERT_OFFSET(MIB_TCPROW_OWNER_PID, dwLocalAddr, 4);
ASSERT_OFFSET(MIB_TCPROW_OWNER_PID, dwLocalPort, 8);
ASSERT_OFFSET(MIB_TCPROW_OWNER_PID, dwRemoteAddr, 12);
ASSERT_OFFSET(MIB_TCPROW_OWNER_PID, dwRemotePort, 16);
ASSERT_OFFSET(MIB_TCPROW_OWNER_PID, dwOwningPid, 20);
ASSERT_OFFSET(MIB_TCPROW, dwState, 0);
ASSERT_OFFSET(MIB_TCPROW, dwLocalAddr, 4);
ASSERT_OFFSET(MIB_TCPROW, dwLocalPort, 8);
ASSERT_OFFSET(MIB_TCPROW, dwRemoteAddr, 12);
ASSERT_OFFSET(MIB_TCPROW, dwRemotePort, 16);
ASSERT_OFFSET(MIB_TCPROW2, dwState, 0);
ASSERT_OFFSET(MIB_TCPROW2, dwLocalAddr, 4);
ASSERT_OFFSET(MIB_TCPROW2, dwLocalPort, 8);
ASSERT_OFFSET(MIB_TCPROW2, dwRemoteAddr, 12);
ASSERT_OFFSET(MIB_TCPROW2, dwRemotePort, 16);
ASSERT_OFFSET(MIB_TCPROW2, dwOwningPid, 20);
ASSERT_OFFSET(MIB_TCPROW2, dwOffloadState, 24);
_Static_assert(TCP_TABLE_OWNER_PID_LISTENER == 3 && TCP_TABLE_OWNER_PID_ALL == 5,
               "native table class ABI");

static const unsigned char PAYLOAD[] = "LL_NTCP_CONTROL1!";
static const char BARRIER[] = "LL_NATIVE_TCP_STATE_V1\n";
_Static_assert(sizeof(PAYLOAD) - 1 == PAYLOAD_BYTES, "fixed payload length");

/* These are bounded report containers, not replacements for Windows structs. */
typedef struct {
    DWORD ordinal;
    unsigned char raw[sizeof(MIB_TCPROW2)];
} Selected;
typedef struct {
    DWORD initial_code, final_code, allocated_bytes, returned_bytes, count;
    size_t selected_count, stride;
    Selected rows[SELECTED_ROWS];
} Query;
typedef struct {
    int acceptconn;
    size_t query_count;
    Query queries[4];
} Stage;
typedef struct {
    DWORD pid;
    ULONGLONG creation_filetime, started;
    unsigned short listener_port, client_port;
    size_t stage_count;
    Stage stages[3];
    unsigned int client_sent, server_received, server_sent, client_received;
    unsigned char server_data[PAYLOAD_BYTES], client_data[PAYLOAD_BYTES];
    unsigned int created_mask, close_attempted_mask, closed_mask;
    int winsock_started, winsock_cleanup_attempted, winsock_cleanup_succeeded;
    int acquisition_completed;
    const char *reason;
} Report;

static const char *QUERY_NAMES[4] = {"owner_listener", "owner_all", "basic", "owner2"};
static const char *STAGE_NAMES[3] = {"after_listen", "connected", "exchanged"};

static int refuse(Report *r, const char *reason) {
    if (r->reason == NULL) r->reason = reason;
    return 0;
}

static DWORD remaining(Report *r) {
    ULONGLONG elapsed = GetTickCount64() - r->started;
    if (elapsed >= WORKER_MS) { refuse(r, "deadline"); return 0; }
    return (DWORD)(WORKER_MS - elapsed);
}

/* Noninterruptible OS calls/barrier are additionally bounded by the parent's
 * 30-second job. A terminated child never supplies explicit closure evidence. */
static int ready(Report *r, SOCKET socket, int writing, const char *reason) {
    fd_set readset, writeset, errors;
    struct timeval timeout;
    DWORD left = remaining(r);
    int result;
    if (left == 0) return 0;
    FD_ZERO(&readset); FD_ZERO(&writeset); FD_ZERO(&errors);
    if (writing) FD_SET(socket, &writeset); else FD_SET(socket, &readset);
    FD_SET(socket, &errors);
    timeout.tv_sec = (long)(left / 1000u);
    timeout.tv_usec = (long)((left % 1000u) * 1000u);
    result = select(0, &readset, &writeset, &errors, &timeout);
    if (remaining(r) == 0) return 0;
    if (result <= 0 || FD_ISSET(socket, &errors)) return refuse(r, reason);
    if (!(writing ? FD_ISSET(socket, &writeset) : FD_ISSET(socket, &readset)))
        return refuse(r, reason);
    return 1;
}

static int configure(Report *r, SOCKET socket, int exclusive) {
    u_long nonblocking = 1;
    BOOL enabled = TRUE;
    DWORD timeout = 1000;
    if (remaining(r) == 0) return 0;
    if ((exclusive && setsockopt(socket, SOL_SOCKET, SO_EXCLUSIVEADDRUSE,
            (const char *)&enabled, (int)sizeof(enabled)) == SOCKET_ERROR) ||
        setsockopt(socket, SOL_SOCKET, SO_SNDTIMEO, (const char *)&timeout,
            (int)sizeof(timeout)) == SOCKET_ERROR ||
        setsockopt(socket, SOL_SOCKET, SO_RCVTIMEO, (const char *)&timeout,
            (int)sizeof(timeout)) == SOCKET_ERROR ||
        ioctlsocket(socket, FIONBIO, &nonblocking) == SOCKET_ERROR)
        return refuse(r, "socket");
    return remaining(r) != 0;
}

static int local_endpoint(Report *r, SOCKET socket, unsigned short *port) {
    struct sockaddr_in address;
    int size = (int)sizeof(address);
    memset(&address, 0, sizeof(address));
    if (getsockname(socket, (struct sockaddr *)&address, &size) == SOCKET_ERROR ||
        size != (int)sizeof(address) || address.sin_family != AF_INET ||
        address.sin_addr.s_addr != htonl(INADDR_LOOPBACK)) return refuse(r, "endpoint");
    *port = ntohs(address.sin_port);
    if (*port == 0 || *port == 5037) return refuse(r, "endpoint");
    return remaining(r) != 0;
}

static int peer_endpoint(Report *r, SOCKET socket, unsigned short expected_port) {
    struct sockaddr_in address;
    int size = (int)sizeof(address);
    memset(&address, 0, sizeof(address));
    if (getpeername(socket, (struct sockaddr *)&address, &size) == SOCKET_ERROR ||
        size != (int)sizeof(address) || address.sin_family != AF_INET ||
        address.sin_addr.s_addr != htonl(INADDR_LOOPBACK) ||
        ntohs(address.sin_port) != expected_port) return refuse(r, "endpoint");
    return remaining(r) != 0;
}

static DWORD native_table(unsigned int which, void *data, DWORD *size) {
    if (which < 2)
        return GetExtendedTcpTable(data, size, FALSE, AF_INET,
            which == 0 ? TCP_TABLE_OWNER_PID_LISTENER : TCP_TABLE_OWNER_PID_ALL, 0);
    if (which == 2) return GetTcpTable((PMIB_TCPTABLE)data, size, FALSE);
    return GetTcpTable2((PMIB_TCPTABLE2)data, size, FALSE);
}

static int capture_query(Report *r, Stage *stage, unsigned int which) {
    Query *query = &stage->queries[stage->query_count];
    DWORD size = 0, ordinal;
    size_t offset = which < 2 ? offsetof(MIB_TCPTABLE_OWNER_PID, table) :
        which == 2 ? offsetof(MIB_TCPTABLE, table) : offsetof(MIB_TCPTABLE2, table);
    void *data;
    int ok = 1;
    if (remaining(r) == 0) return 0;
    query->stride = which < 2 ? sizeof(MIB_TCPROW_OWNER_PID) :
        which == 2 ? sizeof(MIB_TCPROW) : sizeof(MIB_TCPROW2);
    query->initial_code = native_table(which, NULL, &size); /* Exactly one sizing call. */
    if (remaining(r) == 0) return 0;
    if ((query->initial_code != ERROR_INSUFFICIENT_BUFFER && query->initial_code != NO_ERROR) ||
        size < offset || size > CAP_BYTES) return refuse(r, "api");
    query->allocated_bytes = size;
    data = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, size);
    if (data == NULL) return refuse(r, "api");
    query->final_code = native_table(which, data, &size); /* Exactly one data call; never retry. */
    query->returned_bytes = size;
    ++stage->query_count; /* Only a genuinely performed pair has final_code evidence. */
    if (remaining(r) == 0) ok = 0;
    if (query->final_code != NO_ERROR || size < offset || size > query->allocated_bytes || size > CAP_BYTES)
        ok = refuse(r, "api");
    if (ok) {
        query->count = which < 2 ? ((PMIB_TCPTABLE_OWNER_PID)data)->dwNumEntries :
            which == 2 ? ((PMIB_TCPTABLE)data)->dwNumEntries : ((PMIB_TCPTABLE2)data)->dwNumEntries;
        if (query->count > CAP_ROWS || query->count > (size - offset) / query->stride)
            ok = refuse(r, "api");
    }
    for (ordinal = 0; ok && ordinal < query->count; ++ordinal) {
        const unsigned char *raw = (const unsigned char *)data + offset + ordinal * query->stride;
        DWORD address, port;
        if (which < 2) {
            const MIB_TCPROW_OWNER_PID *row = (const MIB_TCPROW_OWNER_PID *)raw;
            address = row->dwLocalAddr; port = row->dwLocalPort;
        } else if (which == 2) {
            const MIB_TCPROW *row = (const MIB_TCPROW *)raw;
            address = row->dwLocalAddr; port = row->dwLocalPort;
        } else {
            const MIB_TCPROW2 *row = (const MIB_TCPROW2 *)raw;
            address = row->dwLocalAddr; port = row->dwLocalPort;
        }
        /* Retain all matching rows, including foreign/unknown state or PID.
         * Raw native DWORDs are never corrected, normalized or prefiltered. */
        if (address == htonl(INADDR_LOOPBACK) &&
            (ntohs((u_short)(port & 0xffffu)) == r->listener_port ||
             (r->client_port != 0 && ntohs((u_short)(port & 0xffffu)) == r->client_port))) {
            Selected *selected;
            if (query->selected_count == SELECTED_ROWS) { ok = refuse(r, "api"); break; }
            selected = &query->rows[query->selected_count++];
            selected->ordinal = ordinal;
            memcpy(selected->raw, raw, query->stride);
        }
    }
    if (!HeapFree(GetProcessHeap(), 0, data)) { r->reason = "cleanup"; ok = 0; }
    return ok && remaining(r) != 0;
}

static int capture_stage(Report *r, SOCKET listener) {
    Stage *stage = &r->stages[r->stage_count];
    int size = (int)sizeof(stage->acceptconn);
    unsigned int which;
    if (remaining(r) == 0) return 0;
    if (getsockopt(listener, SOL_SOCKET, SO_ACCEPTCONN,
            (char *)&stage->acceptconn, &size) == SOCKET_ERROR || size != (int)sizeof(stage->acceptconn))
        return refuse(r, "socket");
    ++r->stage_count;
    for (which = 0; which < 4; ++which) if (!capture_query(r, stage, which)) return 0;
    return remaining(r) != 0;
}

static int send_prefix(Report *r, SOCKET socket, const unsigned char *data, unsigned int *count) {
    while (*count < PAYLOAD_BYTES) {
        int sent;
        if (!ready(r, socket, 1, "exchange")) return 0;
        sent = send(socket, (const char *)data + *count, (int)(PAYLOAD_BYTES - *count), 0);
        if (sent == SOCKET_ERROR && WSAGetLastError() == WSAEWOULDBLOCK) continue;
        if (sent <= 0 || (unsigned int)sent > PAYLOAD_BYTES - *count) return refuse(r, "exchange");
        *count += (unsigned int)sent;
    }
    return remaining(r) != 0;
}

static int receive_prefix(Report *r, SOCKET socket, unsigned char *data, unsigned int *count) {
    while (*count < PAYLOAD_BYTES) {
        int received;
        if (!ready(r, socket, 0, "exchange")) return 0;
        received = recv(socket, (char *)data + *count, (int)(PAYLOAD_BYTES - *count), 0);
        if (received == SOCKET_ERROR && WSAGetLastError() == WSAEWOULDBLOCK) continue;
        if (received <= 0 || (unsigned int)received > PAYLOAD_BYTES - *count) return refuse(r, "exchange");
        *count += (unsigned int)received;
    }
    return remaining(r) != 0;
}

static void close_owned(Report *r, SOCKET socket, unsigned int bit) {
    if (socket == INVALID_SOCKET) return;
    r->close_attempted_mask |= bit;
    if (closesocket(socket) == 0) r->closed_mask |= bit;
    else r->reason = "cleanup";
}

static void hex(const unsigned char *data, size_t count) {
    static const char digits[] = "0123456789abcdef";
    size_t i;
    for (i = 0; i < count; ++i) { putchar(digits[data[i] >> 4]); putchar(digits[data[i] & 15]); }
}

static const char *boolean(int value) { return value ? "true" : "false"; }

static void print_abi(void) {
    printf("\"abi\":{\"owner_pid\":{\"row_bytes\":%zu,\"row_offset\":%zu,\"field_offsets\":[%zu,%zu,%zu,%zu,%zu,%zu]},",
        sizeof(MIB_TCPROW_OWNER_PID), offsetof(MIB_TCPTABLE_OWNER_PID, table),
        offsetof(MIB_TCPROW_OWNER_PID, dwState), offsetof(MIB_TCPROW_OWNER_PID, dwLocalAddr),
        offsetof(MIB_TCPROW_OWNER_PID, dwLocalPort), offsetof(MIB_TCPROW_OWNER_PID, dwRemoteAddr),
        offsetof(MIB_TCPROW_OWNER_PID, dwRemotePort), offsetof(MIB_TCPROW_OWNER_PID, dwOwningPid));
    printf("\"basic\":{\"row_bytes\":%zu,\"row_offset\":%zu,\"field_offsets\":[%zu,%zu,%zu,%zu,%zu]},",
        sizeof(MIB_TCPROW), offsetof(MIB_TCPTABLE, table), offsetof(MIB_TCPROW, dwState),
        offsetof(MIB_TCPROW, dwLocalAddr), offsetof(MIB_TCPROW, dwLocalPort),
        offsetof(MIB_TCPROW, dwRemoteAddr), offsetof(MIB_TCPROW, dwRemotePort));
    printf("\"owner2\":{\"row_bytes\":%zu,\"row_offset\":%zu,\"field_offsets\":[%zu,%zu,%zu,%zu,%zu,%zu,%zu]}},",
        sizeof(MIB_TCPROW2), offsetof(MIB_TCPTABLE2, table), offsetof(MIB_TCPROW2, dwState),
        offsetof(MIB_TCPROW2, dwLocalAddr), offsetof(MIB_TCPROW2, dwLocalPort),
        offsetof(MIB_TCPROW2, dwRemoteAddr), offsetof(MIB_TCPROW2, dwRemotePort),
        offsetof(MIB_TCPROW2, dwOwningPid), offsetof(MIB_TCPROW2, dwOffloadState));
}

static int print_report(const Report *r) {
    size_t s, q, i;
    printf("{\"version\":1,\"protocol\":\"windows-native-owned-tcp-state-v1\",\"pid\":%lu,\"creation_filetime\":%llu,",
        (unsigned long)r->pid, (unsigned long long)r->creation_filetime);
    print_abi();
    printf("\"listener_port\":%u,\"client_port\":%u,\"stages\":[", (unsigned int)r->listener_port, (unsigned int)r->client_port);
    for (s = 0; s < r->stage_count; ++s) {
        const Stage *stage = &r->stages[s];
        if (s != 0) putchar(',');
        printf("{\"stage\":\"%s\",\"acceptconn\":%d,\"queries\":[", STAGE_NAMES[s], stage->acceptconn);
        for (q = 0; q < stage->query_count; ++q) {
            const Query *query = &stage->queries[q];
            if (q != 0) putchar(',');
            printf("{\"name\":\"%s\",\"initial_code\":%lu,\"final_code\":%lu,\"allocated_bytes\":%lu,\"returned_bytes\":%lu,\"count\":%lu,\"rows\":[",
                QUERY_NAMES[q], (unsigned long)query->initial_code, (unsigned long)query->final_code,
                (unsigned long)query->allocated_bytes, (unsigned long)query->returned_bytes, (unsigned long)query->count);
            for (i = 0; i < query->selected_count; ++i) {
                if (i != 0) putchar(',');
                printf("{\"ordinal\":%lu,\"raw_hex\":\"", (unsigned long)query->rows[i].ordinal);
                hex(query->rows[i].raw, query->stride); printf("\"}");
            }
            printf("]}");
        }
        printf("]}");
    }
    printf("],\"exchange\":{\"client_sent\":%u,\"server_received\":%u,\"server_sent\":%u,\"client_received\":%u,\"server_hex\":\"",
        r->client_sent, r->server_received, r->server_sent, r->client_received);
    hex(r->server_data, r->server_received); printf("\",\"client_hex\":\"");
    hex(r->client_data, r->client_received);
    printf("\"},\"resources\":{\"created_mask\":%u,\"close_attempted_mask\":%u,\"closed_mask\":%u,\"winsock_started\":%s,\"winsock_cleanup_attempted\":%s,\"winsock_cleanup_succeeded\":%s},",
        r->created_mask, r->close_attempted_mask, r->closed_mask, boolean(r->winsock_started),
        boolean(r->winsock_cleanup_attempted), boolean(r->winsock_cleanup_succeeded));
    printf("\"acquisition_completed\":%s,\"reason\":", boolean(r->acquisition_completed));
    if (r->reason == NULL) printf("null"); else printf("\"%s\"", r->reason);
    printf(",\"elapsed_ms\":%llu}\n", (unsigned long long)(GetTickCount64() - r->started));
    return fflush(stdout) == 0 && !ferror(stdout);
}

int main(int argc, char **argv) {
    Report r = {0};
    SOCKET listener = INVALID_SOCKET, client = INVALID_SOCKET, accepted = INVALID_SOCKET;
    WSADATA wsa;
    FILETIME creation, exit_time, kernel, user;
    ULARGE_INTEGER created;
    struct sockaddr_in address;
    unsigned char barrier[sizeof(BARRIER)];
    unsigned short port;
    int work_ok = 0, error, length;
    (void)argv;
    r.started = GetTickCount64(); r.pid = GetCurrentProcessId();
    if (_setmode(_fileno(stdout), _O_BINARY) == -1) return 1;
    if (!GetProcessTimes(GetCurrentProcess(), &creation, &exit_time, &kernel, &user)) {
        refuse(&r, "identity"); goto cleanup;
    }
    created.LowPart = creation.dwLowDateTime; created.HighPart = creation.dwHighDateTime;
    r.creation_filetime = created.QuadPart;
    if (r.pid == 0 || r.creation_filetime == 0) { refuse(&r, "identity"); goto cleanup; }
    if (argc != 1 || _setmode(_fileno(stdin), _O_BINARY) == -1 ||
        fread(barrier, 1, sizeof(barrier), stdin) != sizeof(BARRIER) - 1 ||
        ferror(stdin) || !feof(stdin) || memcmp(barrier, BARRIER, sizeof(BARRIER) - 1) != 0) {
        refuse(&r, "barrier"); goto cleanup;
    }
    if (remaining(&r) == 0) goto cleanup;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) { refuse(&r, "startup"); goto cleanup; }
    r.winsock_started = 1;
    if (LOBYTE(wsa.wVersion) != 2 || HIBYTE(wsa.wVersion) != 2) { refuse(&r, "startup"); goto cleanup; }
    listener = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (listener == INVALID_SOCKET) { refuse(&r, "socket"); goto cleanup; }
    r.created_mask |= 1;
    if (!configure(&r, listener, 1)) goto cleanup;
    memset(&address, 0, sizeof(address)); address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK); address.sin_port = htons(0);
    if (bind(listener, (const struct sockaddr *)&address, (int)sizeof(address)) == SOCKET_ERROR) { refuse(&r, "bind"); goto cleanup; }
    if (!local_endpoint(&r, listener, &r.listener_port)) goto cleanup;
    if (listen(listener, 1) == SOCKET_ERROR) { refuse(&r, "listen"); goto cleanup; }
    if (!capture_stage(&r, listener)) goto cleanup;
    client = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (client == INVALID_SOCKET) { refuse(&r, "socket"); goto cleanup; }
    r.created_mask |= 2;
    if (!configure(&r, client, 1)) goto cleanup;
    if (bind(client, (const struct sockaddr *)&address, (int)sizeof(address)) == SOCKET_ERROR) { refuse(&r, "bind"); goto cleanup; }
    if (!local_endpoint(&r, client, &r.client_port) || r.client_port == r.listener_port) { refuse(&r, "endpoint"); goto cleanup; }
    address.sin_port = htons(r.listener_port); /* The exact self-created loopback listener only. */
    error = connect(client, (const struct sockaddr *)&address, (int)sizeof(address));
    if (error == SOCKET_ERROR) {
        error = WSAGetLastError();
        if (error != WSAEWOULDBLOCK && error != WSAEINPROGRESS && error != WSAEALREADY) { refuse(&r, "connect"); goto cleanup; }
        if (!ready(&r, client, 1, "connect")) goto cleanup;
        length = (int)sizeof(error);
        if (getsockopt(client, SOL_SOCKET, SO_ERROR, (char *)&error, &length) == SOCKET_ERROR || length != (int)sizeof(error) || error != 0) { refuse(&r, "connect"); goto cleanup; }
    }
    if (!ready(&r, listener, 0, "accept")) goto cleanup;
    accepted = accept(listener, NULL, NULL); /* One accept; no connection retries. */
    if (accepted == INVALID_SOCKET) { refuse(&r, "accept"); goto cleanup; }
    r.created_mask |= 4;
    if (!configure(&r, accepted, 0)) goto cleanup;
    if (!local_endpoint(&r, client, &port) || port != r.client_port ||
        !local_endpoint(&r, accepted, &port) || port != r.listener_port ||
        !peer_endpoint(&r, client, r.listener_port) || !peer_endpoint(&r, accepted, r.client_port)) { refuse(&r, "endpoint"); goto cleanup; }
    if (!capture_stage(&r, listener)) goto cleanup;
    if (!send_prefix(&r, client, PAYLOAD, &r.client_sent) ||
        !receive_prefix(&r, accepted, r.server_data, &r.server_received)) goto cleanup;
    if (memcmp(r.server_data, PAYLOAD, PAYLOAD_BYTES) != 0) { refuse(&r, "exchange"); goto cleanup; }
    if (!send_prefix(&r, accepted, r.server_data, &r.server_sent) ||
        !receive_prefix(&r, client, r.client_data, &r.client_received)) goto cleanup;
    if (memcmp(r.client_data, PAYLOAD, PAYLOAD_BYTES) != 0) { refuse(&r, "exchange"); goto cleanup; }
    if (!capture_stage(&r, listener)) goto cleanup;
    work_ok = 1;
cleanup:
    close_owned(&r, accepted, 4); close_owned(&r, client, 2); close_owned(&r, listener, 1);
    if (r.winsock_started) {
        r.winsock_cleanup_attempted = 1;
        r.winsock_cleanup_succeeded = WSACleanup() == 0;
        if (!r.winsock_cleanup_succeeded) r.reason = "cleanup";
    }
    if (r.reason == NULL && remaining(&r) == 0) work_ok = 0;
    r.acquisition_completed = work_ok && r.reason == NULL && r.created_mask == 7 &&
        r.close_attempted_mask == 7 && r.closed_mask == 7 && r.winsock_cleanup_succeeded;
    if (!r.acquisition_completed && r.reason == NULL) r.reason = "cleanup";
    return print_report(&r) && r.acquisition_completed ? 0 : 1;
}
