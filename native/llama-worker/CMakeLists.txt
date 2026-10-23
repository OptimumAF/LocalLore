cmake_minimum_required(VERSION 3.22)
project(locallore_llama_worker LANGUAGES C CXX)

# This experiment never fetches a dependency or introduces an Android backend.
if(NOT DEFINED LLAMA_SOURCE_DIR)
  message(FATAL_ERROR "Set LLAMA_SOURCE_DIR to the reviewed local llama.cpp checkout")
endif()
find_package(Git REQUIRED)
execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${LLAMA_SOURCE_DIR}" rev-parse HEAD
  OUTPUT_VARIABLE LLAMA_ACTUAL_COMMIT OUTPUT_STRIP_TRAILING_WHITESPACE
  COMMAND_ERROR_IS_FATAL ANY)
if(NOT LLAMA_ACTUAL_COMMIT STREQUAL "620d2225cc436ab0b001e3200e590e3b286ef9ab")
  message(FATAL_ERROR "Unreviewed llama.cpp revision")
endif()
execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${LLAMA_SOURCE_DIR}" diff --exit-code HEAD
  RESULT_VARIABLE LLAMA_DIRTY OUTPUT_QUIET)
if(NOT LLAMA_DIRTY EQUAL 0)
  message(FATAL_ERROR "Modified llama.cpp source")
endif()
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
foreach(OPTION LLAMA_BUILD_TESTS LLAMA_BUILD_EXAMPLES LLAMA_BUILD_TOOLS
    LLAMA_BUILD_SERVER LLAMA_BUILD_APP LLAMA_BUILD_UI LLAMA_USE_PREBUILT_UI
    LLAMA_OPENSSL LLAMA_BUILD_BORINGSSL LLAMA_BUILD_LIBRESSL LLAMA_SUBPROCESS
    LLAMA_LLGUIDANCE GGML_RPC GGML_CUDA GGML_VULKAN GGML_OPENCL GGML_SYCL
    GGML_METAL GGML_WEBGPU GGML_BLAS GGML_NATIVE GGML_BACKEND_DL)
  set(${OPTION} OFF CACHE BOOL "" FORCE)
endforeach()
set(LLAMA_BUILD_COMMON ON CACHE BOOL "" FORCE)
set(LLAMA_BUILD_IS_DEV OFF CACHE BOOL "" FORCE)
add_subdirectory("${LLAMA_SOURCE_DIR}" llama)
add_executable(locallore-llama-worker main.cpp)
target_compile_features(locallore-llama-worker PRIVATE cxx_std_17)
target_link_libraries(locallore-llama-worker PRIVATE llama-common llama vendor::nlohmann)

# Explicit development target only; never linked into or packaged with the application worker.
add_executable(locallore-schema-order-test EXCLUDE_FROM_ALL schema_order_test.cpp)
target_compile_features(locallore-schema-order-test PRIVATE cxx_std_17)
target_include_directories(locallore-schema-order-test PRIVATE "${LLAMA_SOURCE_DIR}/src")
target_link_libraries(locallore-schema-order-test PRIVATE llama-common llama vendor::nlohmann)

add_executable(locallore-worker-launch-test EXCLUDE_FROM_ALL worker_launch_test.cpp)
target_compile_features(locallore-worker-launch-test PRIVATE cxx_std_17)
