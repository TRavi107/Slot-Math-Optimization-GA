cmake_minimum_required(VERSION 3.20)
project(MyProject LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  # helps IntelliSense

# Single-config generators (Makefiles, Ninja) build with no optimisation at all when
# no build type is given. The optimizer calls the simulator thousands of times, so
# default to Release. Override with -DCMAKE_BUILD_TYPE=Debug when debugging.
get_property(_multi_config GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(NOT _multi_config AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
    message(STATUS "No CMAKE_BUILD_TYPE given - building Release")
endif()

find_package(Threads REQUIRED)

add_executable(simulator src/main.cpp)

target_link_libraries(simulator PRIVATE Threads::Threads)

target_compile_definitions(simulator PRIVATE
    SOURCE_DIR="${CMAKE_SOURCE_DIR}"
    SIM_BUILD_TYPE="$<CONFIG>")     # recorded in every result as build.buildType
