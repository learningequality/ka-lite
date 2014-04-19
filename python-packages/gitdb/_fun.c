#include <Python.h>
#include "_delta_apply.h"

static PyObject *PackIndexFile_sha_to_index(PyObject *self, PyObject *args)
{
	const unsigned char *sha;
	const unsigned int sha_len;
	
	// Note: self is only set if we are a c type. We emulate an instance method, 
	// hence we have to get the instance as 'first' argument
	
	// get instance and sha
	PyObject* inst = 0;
	if (!PyArg_ParseTuple(args, "Os#", &inst, &sha, &sha_len))
		return NULL;
	
	if (sha_len != 20) {
		PyErr_SetString(PyExc_ValueError, "Sha is not 20 bytes long");
		return NULL;
	}
	
	if( !inst){
		PyErr_SetString(PyExc_ValueError, "Cannot be called without self");
		return NULL;
	}
	
	// read lo and hi bounds
	PyObject* fanout_table = PyObject_GetAttrString(inst, "_fanout_table");
	if (!fanout_table){
		PyErr_SetString(PyExc_ValueError, "Couldn't obtain fanout table");
		return NULL;
	}
	
	unsigned int lo = 0, hi = 0;
	if (sha[0]){
		PyObject* item = PySequence_GetItem(fanout_table, (const Py_ssize_t)(sha[0]-1));
		lo = PyInt_AS_LONG(item);
		Py_DECREF(item);
	}
	PyObject* item = PySequence_GetItem(fanout_table, (const Py_ssize_t)sha[0]);
	hi = PyInt_AS_LONG(item);
	Py_DECREF(item);
	item = 0;
	
	Py_DECREF(fanout_table);
	
	// get sha query function
	PyObject* get_sha = PyObject_GetAttrString(inst, "sha");
	if (!get_sha){
		PyErr_SetString(PyExc_ValueError, "Couldn't obtain sha method");
		return NULL;
	}
	
	PyObject *sha_str = 0;
	while (lo < hi) {
		const int mid = (lo + hi)/2;
		sha_str = PyObject_CallFunction(get_sha, "i", mid);
		if (!sha_str) {
			return NULL;
		}
		
		// we really trust that string ... for speed 
		const int cmp = memcmp(PyString_AS_STRING(sha_str), sha, 20);
		Py_DECREF(sha_str);
		sha_str = 0;
		
		if (cmp < 0){
			lo = mid + 1;
		}
		else if (cmp > 0) {
			hi = mid;
		}
		else {
			Py_DECREF(get_sha);
			return PyInt_FromLong(mid);
		}// END handle comparison
	}// END while lo < hi
	
	// nothing found, cleanup
	Py_DECREF(get_sha);
	Py_RETURN_NONE;
}

static PyMethodDef py_fun[] = {
	{ "PackIndexFile_sha_to_index", (PyCFunction)PackIndexFile_sha_to_index, METH_VARARGS, "TODO" },
	{ "connect_deltas", (PyCFunction)connect_deltas, METH_O, "See python implementation" },
	{ "apply_delta", (PyCFunction)apply_delta, METH_VARARGS, "See python implementation" },
	{ NULL, NULL, 0, NULL }
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC init_perf(void)
{
	PyObject *m;

	if (PyType_Ready(&DeltaChunkListType) < 0)
		return;
	
	m = Py_InitModule3("_perf", py_fun, NULL);
	if (m == NULL)
		return;
	
	Py_INCREF(&DeltaChunkListType);
	PyModule_AddObject(m, "DeltaChunkList", (PyObject *)&DeltaChunkListType);
}
