#ifndef _TRACER_H_
#define _TRACER_H_

typedef std::pair<std::vector<int>, std::vector<double>> intersectResults;

intersectResults computeIntersections(
	std::vector<double> rayData,
	std::vector<int> triangleIds,
	std::vector<double> triangleData); 
	
intersectResults computeIntersectionsParallel(
	std::vector<double> rayData,
	std::vector<int> triangleIds,
	std::vector<double> triangleData
);

#endif