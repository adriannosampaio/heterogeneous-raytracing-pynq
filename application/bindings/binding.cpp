#include "pybind11/pybind11.h"
#include "pybind11/stl.h"
#include "tracer.hpp"

namespace py = pybind11;

PYBIND11_MODULE(tracer, m) {
	m.doc() = "pybind11 example plugin"; // optional module docstring

	m.def("compute", &computeIntersections, "A function which adds two numbers");
	m.def("computeParallel", &computeIntersectionsParallel, "A function which adds two numbers");
}