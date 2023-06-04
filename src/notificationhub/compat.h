/* Copyright 2023 Michael Davidsaver
 * See LICENSE
 * SPDX-License-Identifier: BSD
 */
#ifndef NOTIFICATIONHUB_COMPAT_H_INC
#define NOTIFICATIONHUB_COMPAT_H_INC

#ifdef _WIN32
#  define VC_EXTRALEAN
#  define STRICT
#  include <winsock2.h>
#  include <windows.h>
#else
/* POSIX */
#  include <sys/types.h>
#  include <sys/socket.h>
#  include <pthread.h>
#endif

#ifdef _WIN32
typedef struct Mutex {
    CRITICAL_SECTION impl;
} Mutex;

static inline
int MutexInit(Mutex* lock) {
    InitializeCriticalSection(&lock->impl);
    return 0;
}

static inline
void MutexFinalize(Mutex* lock) {
    DeleteCriticalSection(&lock->impl);
}

static inline
void MutexLock(Mutex* lock) {
    EnterCriticalSection(&lock->impl);
}

static inline
void MutexUnlock(Mutex* lock) {
    LeaveCriticalSection(&lock->impl);
}

#else 
/* POSIX */

typedef int SOCKET;
#define INVALID_SOCKET (-1)

typedef struct Mutex {
    pthread_mutex_t impl;
} Mutex;

static inline
int MutexInit(Mutex* lock) {
    return pthread_mutex_init(&lock->impl, NULL);
}

static inline
void MutexFinalize(Mutex* lock) {
    (void)pthread_mutex_destroy(&lock->impl);
}

static inline
void MutexLock(Mutex* lock) {
    (void)pthread_mutex_lock(&lock->impl);
}

static inline
void MutexUnlock(Mutex* lock) {
    (void)pthread_mutex_unlock(&lock->impl);
}
#endif /* WIN32 or POSIX */

static inline
int SockSend(SOCKET tx, void* buf, size_t size)
{
    return send(tx, buf, size, 0);
}


#endif /* NOTIFICATIONHUB_COMPAT_H_INC */
