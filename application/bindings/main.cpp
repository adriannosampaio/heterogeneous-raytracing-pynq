#include <iostream>
#include <vector>
#include "tracer.hpp"

int main(int argc, char const *argv[])
{
	std::vector<int> ids(1);
	std::vector<double> rays(6);
	std::vector<double> tris(9);

	auto res = computeIntersections(
		rays,
		ids,
		tris
	);

	std::cout << res.first[0] <<" " << res.second[0] <<"\n";

	return 0;
}