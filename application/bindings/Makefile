CC=g++ -std=c++11
FLAGS=-shared -fPIC -fopenmp
INCLUDES=-I./deps/pybind11/include -I/usr/include/python3.6
FILES=tracer.cpp binding.cpp
TARGET=tracer.so
TEST_TARGET=

$(TARGET) : $(FILES)
	$(CC) $(FLAGS) $(INCLUDES) $(FILES) -o $(TARGET)
	

