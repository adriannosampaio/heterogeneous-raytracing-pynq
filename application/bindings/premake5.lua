
workspace "DarkRendererBindings"
   configurations { "x32", "x64", "ARM"}

project "tests"
    kind "ConsoleApp"
    language "C++"
    targetdir "tests/bin"

    filter "configurations:Debug"
        architecture "x64"
        defines { "DEBUG" }
        symbols "On"

    filter "configurations:x64"
        architecture "x64"
        defines { "NDEBUG" }
        optimize "On"

    files { "main.cpp", "tracer.cpp", "tracer.hpp"}

project "tracer"
    kind "SharedLib"
    language "C++"

    buildoptions "-std=c++11"

    conda_dir = os.getenv("CONDA_PREFIX")

    includedirs {
        "deps/pybind11/include", 
        conda_dir .. "/include"
    }

    libdirs {
        conda_dir .. "/libs"
    }

    filter {"action:vs*"}
        targetextension (".pyd")

    files { "binding.cpp", "tracer.cpp", "tracer.hpp"}

    filter "configurations:x32"
        architecture "x86"
        optimize "On"

    filter "configurations:x64"
        architecture "x64"
        optimize "On"

    filter "configurations:ARM"
        architecture "ARM"
        optimize "On"