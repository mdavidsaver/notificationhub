/* Copyright 2023 Michael Davidsaver
 * See LICENSE
 * SPDX-License-Identifier: BSD
 */
#ifndef NOTIFICATIONHUB_H_INC
#define NOTIFICATIONHUB_H_INC

#include <Python.h>
#include <string.h>

#define NOTIFICATIONHUB_ABI_VERSION (0)

#ifdef __cplusplus
extern "C" {
#endif

/** Handle for asynchronous callbacks from non-python threads, without locking the GIL.
 */
struct notifier;
typedef struct notifier notifier;

typedef struct notificationhub_vtable_t {
    notifier* (*notifier_handle)(PyObject*);
    int (*notifier_poke)(notifier*);
} notificationhub_vtable_t;

static
notificationhub_vtable_t _notificationhub_vtable;

static
int _notificationhub_check_version(PyObject* mod)
{
    int ret = -1;
    PyObject *buildver = PyLong_FromLongLong(NOTIFICATIONHUB_ABI_VERSION);
    PyObject *runver = PyObject_GetAttrString(mod, "abi_version");
    if(buildver && runver) {
        if(PyObject_RichCompareBool(buildver, runver, Py_EQ)) {
            ret = 0;
        } else {
            PyErr_Format(PyExc_RuntimeError, "Unable to import notificationhub.  buildver=%R != runver=%R",
                        buildver, runver);
        }
    }
    Py_XDECREF(buildver);
    Py_XDECREF(runver);
    return ret;
}

static
int _notificationhub_import_func(PyObject* mod, void(**fn)(void), const char *fname, const char *sig) {
    int ret = -1;
    union {
        void (*fn)(void);
        void *ptr;
    } pun;
    PyObject *cap = PyObject_GetAttrString(mod, fname);
    if(cap && PyCapsule_IsValid(cap, sig) && (pun.ptr = PyCapsule_GetPointer(cap, sig))) {
        *fn = pun.fn;
        ret = 0;
    } else {
        PyErr_Format(PyExc_TypeError, "Unable to import C func %s w/ %s", fname, sig);
    }
    Py_XDECREF(cap);
    return ret;
}

/** Prepare to use notificationhub API.
 *
 * Must be called prior to use of any ``notifier_*`` functions.
 * Must be called with python GIL locked.
 *
 * Idempotent.
 */
static inline
int notificationhub_import(void) {
    int ret = -1;
    PyObject* mod;
    notificationhub_vtable_t vtable;
    if(_notificationhub_vtable.notifier_handle)
        return 0;
    mod = PyImport_ImportModule("notificationhub._nh");
    if(mod) {
        ret = _notificationhub_check_version(mod);
        if(!ret)
            ret = _notificationhub_import_func(mod, (void (**)(void))&vtable.notifier_handle,
                                              "notifier_handle", "notifier* (PyObject*)");
        if(!ret)
            ret = _notificationhub_import_func(mod, (void (**)(void))&vtable.notifier_poke,
                                               "notifier_poke", "int (notifier*)");
    }
    Py_XDECREF(mod);
    if(!ret)
        memcpy(&_notificationhub_vtable, &vtable, sizeof(vtable));
    return ret;
}

/** Get C handle from a Notifier object.
 *
 * Must be called with python GIL locked.
 *
 * Returns a borrowed reference.
 *
 * Caller must ensure that the associated Notifier object remains valid
 * as long as notifier_poke() may be called.
 *
 * @param notif A Notifier object
 */
static inline
notifier* notifier_handle(PyObject* notif)
{
    return _notificationhub_vtable.notifier_handle(notif);
}

/** Trigger a notifier object.
 * 
 * Python GIL does _not_ need to be locked.
 * Fully reentrant.
 * May be called from a signal handler.
 */
static inline
int notifier_poke(notifier* notif)
{
    return _notificationhub_vtable.notifier_poke(notif);
}

#ifdef __cplusplus
} // extern "C"
#endif

#endif /* NOTIFICATIONHUB_H_INC */
