#include <cmath>
#include <vector>
#include <tuple>

#include "tracer.hpp"

#ifdef DEBUG
#include <iostream>
#define PRINT_VAR(V) std::cout << #V << " = " << V << '\n'
#define PRINT_VEC3(VEC)  			\
	std::cout << #VEC << " = (";	\
	for(int i=0;i<3;i++) 			\
		std::cout << VEC[i] << " "; \
	std::cout << #VEC << ")\n" 		\
#else
#define PRINT_VAR(V)
#define PRINT_VEC3(VEC)
#endif

#define EPSILON 1.0e-6
#define INFINITY 1.0e9
#define TRIANGLE_ATTR_NUMBER 9
#define RAY_ATTR_NUMBER 6

#define COORDS 3
#define VEC3(NAME) double NAME[COORDS]
#define ASSIGN(VL, VR) (VL)[0] = (VR)[0]; (VL)[1] = (VR)[1]; (VL)[2] = (VR)[2]
#define DOT(V1, V2) (V1[0]*V2[0] + V1[1]*V2[1] + V1[2]*V2[2])
#define CROSS(VR, V1, V2) \
	VR[0] = V1[1] * V2[2] - V1[2] * V2[1], \
	VR[1] = V1[2] * V2[0] - V1[0] * V2[2], \
	VR[2] = V1[0] * V2[1] - V1[1] * V2[0]
#define SUB(VR, V1, V2) 	\
	VR[0] = V1[0] - V2[0]; 	\
	VR[1] = V1[1] - V2[1]; 	\
	VR[2] = V1[2] - V2[2]

bool rayIntersect(
	double& t, 
	const int ray, 
	const std::vector<double>& rayData, 
	const int tri,
	const std::vector<double>& triData
) {
	VEC3(origin); VEC3(direction);
	VEC3(v0); VEC3(v1); VEC3(v2);

	int rayBase = ray*RAY_ATTR_NUMBER;
	ASSIGN(origin, 	  &(rayData[rayBase])); 
	ASSIGN(direction, &(rayData[rayBase + COORDS]));
	
	int triBase = tri*TRIANGLE_ATTR_NUMBER;
	ASSIGN(v0, &(triData[triBase]));
	ASSIGN(v1, &(triData[triBase + COORDS]));
	ASSIGN(v2, &(triData[triBase + 2*COORDS]));

	VEC3(edge1); VEC3(edge2);
	SUB(edge1, v1, v0);
	SUB(edge2, v2, v0);

	VEC3(h);
	CROSS(h, direction, edge2);
	double a = DOT(edge1, h);

	if(fabs(a) < EPSILON)
	{
		return false;
	}

	double f = 1.0 / a;
	VEC3(s);
	SUB(s, origin, v0);
	double u = f * DOT(s, h);

	if(u < 0.0 || u > 1.0)
	{
		return false;
	}

	VEC3(q);
	CROSS(q, s, edge1);
	double v = f * DOT(direction, q);

	if(v < 0.0 || u + v > 1.0)
	{
		return false;
	}
	
	t = f * DOT(edge2, q);
	return true;
}

intersectResults computeIntersections(
	std::vector<double> rayData,
	std::vector<int> triangleIds,
	std::vector<double> triangleData
) {
	// Task information
	int numTriangles = triangleData.size() / TRIANGLE_ATTR_NUMBER ;
	int numRays = rayData.size() / RAY_ATTR_NUMBER;
	
	std::vector<int> outIds(numRays);
	std::vector<double> outInter(numRays);

	for(int ray = 0; ray < numRays; ray++)
	{
		outIds[ray]   = -1;
		outInter[ray] = INFINITY; 

		for(int tri = 0; tri < numTriangles; tri++)
		{
			double t;
			if(rayIntersect(t, ray, rayData, tri, triangleData)) 
			if(t < outInter[ray] && t > EPSILON)
			{
				outIds[ray] = triangleIds[tri];
				outInter[ray] = t;
			}
		}
	}

	return std::make_pair(outIds, outInter);
}

intersectResults computeIntersectionsParallel(
	std::vector<double> rayData,
	std::vector<int> triangleIds,
	std::vector<double> triangleData
) {
	// Task information
	int numTriangles = triangleData.size() / TRIANGLE_ATTR_NUMBER ;
	int numRays = rayData.size() / RAY_ATTR_NUMBER;
	
	std::vector<int> outIds(numRays);
	std::vector<double> outInter(numRays);

	#pragma omp parallel for
	for(int ray = 0; ray < numRays; ray++)
	{
		outIds[ray]   = -1;
		outInter[ray] = INFINITY; 

		for(int tri = 0; tri < numTriangles; tri++)
		{
			double t;
			if(rayIntersect(t, ray, rayData, tri, triangleData)) 
			if(t < outInter[ray] && t > EPSILON)
			{
				outIds[ray] = triangleIds[tri];
				outInter[ray] = t;
			}
		}
	}

	return std::make_pair(outIds, outInter);
}


