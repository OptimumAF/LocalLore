cmake_minimum_required(VERSION 3.22)
project(locallore_llama_android_spike LANGUAGES C CXX)

if(NOT ANDROID OR NOT ANDROID_PLATFORM_LEVEL EQUAL 28)
  message(FATAL_ERROR "This isolated experiment requires the Android NDK toolchain and API 28")
endif()
if(NOT ANDROID_ABI MATCHES "^(x86_64|arm64-v8a)$")
  message(FATAL_ERROR "Only x86_64 and arm64-v8a are reviewed by this experiment")
endif()
if(NOT ANDROID_STL STREQUAL "c++_static")
  message(FATAL_ERROR "Use one statically linked libc++ in this standalone executable")
endif()

# Reuse the reviewed host API helper unchanged. No downloader, server, JNI,
# app dependency or alternate gameplay authority is introduced here.
foreach(OPTION GGML_OPENMP GGML_OPENMP_FETCH GGML_LLAMAFILE GGML_NATIVE
    GGML_CPU_ALL_VARIANTS GGML_CPU_KLEIDIAI GGML_SSE42 GGML_AVX GGML_AVX2
    GGML_AVX_VNNI GGML_AVX512 GGML_AVX512_VBMI GGML_AVX512_VNNI
    GGML_AVX512_BF16 GGML_FMA GGML_F16C GGML_BMI2 GGML_AMX_TILE
    GGML_AMX_INT8 GGML_AMX_BF16)
  set(${OPTION} OFF CACHE BOOL "" FORCE)
endforeach()
if(ANDROID_ABI STREQUAL "arm64-v8a")
  set(GGML_CPU_ARM_ARCH "armv8-a" CACHE STRING "" FORCE)
endif()
set(FETCHCONTENT_FULLY_DISCONNECTED ON CACHE BOOL "" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_link_options("-Wl,-z,max-page-size=16384")
add_subdirectory("${CMAKE_CURRENT_LIST_DIR}/../../llama" host-helper)
