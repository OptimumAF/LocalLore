cmake_minimum_required(VERSION 3.22)

# This is a separate development build, not a target of the worker project.
if(NOT CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
  message(FATAL_ERROR "Configure the compile helper as a standalone project")
endif()
if(NOT CMAKE_HOST_WIN32 OR NOT CMAKE_GENERATOR STREQUAL "Ninja" OR
    NOT CMAKE_BUILD_TYPE STREQUAL "Release")
  message(FATAL_ERROR "The compile helper requires Windows, Ninja and Release")
endif()

file(REAL_PATH "${CMAKE_CURRENT_SOURCE_DIR}/.." HELPER_SOURCE_DIR)
file(REAL_PATH "${CMAKE_CURRENT_BINARY_DIR}" HELPER_BUILD_DIR)
string(TOLOWER "${HELPER_SOURCE_DIR}" HELPER_SOURCE_KEY)
string(TOLOWER "${HELPER_BUILD_DIR}" HELPER_BUILD_KEY)
cmake_path(IS_PREFIX HELPER_SOURCE_KEY "${HELPER_BUILD_KEY}" NORMALIZE HELPER_BUILD_IN_SOURCE)
cmake_path(IS_PREFIX HELPER_BUILD_KEY "${HELPER_SOURCE_KEY}" NORMALIZE HELPER_SOURCE_IN_BUILD)
if(NOT HELPER_SOURCE_KEY MATCHES "^d:/" OR NOT HELPER_BUILD_KEY MATCHES "^d:/" OR
    HELPER_BUILD_IN_SOURCE OR HELPER_SOURCE_IN_BUILD)
  message(FATAL_ERROR "Use D: source and a separate D: helper build directory")
endif()

project(locallore_compile_host_v1 LANGUAGES CXX)
if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "MSVC" OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "The compile helper requires MSVC x64")
endif()

add_executable(locallore-compile-host-v1 "${HELPER_SOURCE_DIR}/worker_artifact_compile_host_v1.cpp")
set_target_properties(locallore-compile-host-v1 PROPERTIES
  CXX_STANDARD 17
  CXX_STANDARD_REQUIRED ON
  CXX_EXTENSIONS OFF
  MSVC_RUNTIME_LIBRARY MultiThreaded
)
target_compile_definitions(locallore-compile-host-v1 PRIVATE
  LOCALLORE_COMPILE_JOB_V1_TEST_OWNER WINVER=0x0A00 _WIN32_WINNT=0x0A00
)
target_compile_options(locallore-compile-host-v1 PRIVATE /Brepro /utf-8)
target_link_options(locallore-compile-host-v1 PRIVATE /Brepro /INCREMENTAL:NO /MACHINE:X64)
