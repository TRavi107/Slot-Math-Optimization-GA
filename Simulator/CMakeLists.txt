cmake_minimum_required(VERSION 3.20)
project(MyProject LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)  # helps IntelliSense


add_executable(simulator src/main.cpp)

target_compile_definitions(simulator PRIVATE SOURCE_DIR="${CMAKE_SOURCE_DIR}")