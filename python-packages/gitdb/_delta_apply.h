#include <Python.h>

extern PyObject* connect_deltas(PyObject *self, PyObject *dstreams);
extern PyObject* apply_delta(PyObject* self, PyObject* args);

extern PyTypeObject DeltaChunkListType;
