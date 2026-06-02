cmake_minimum_required(VERSION 3.16)

project(ViscoWave LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

option(PYWAVE_STATIC_RUNTIME "Link GCC/Stdlib/OpenMP runtimes statically on MinGW (Windows)" ON)

set(VISCOWAVE_SOURCES
  src/alglibinternal.cpp
  src/alglibmisc.cpp
  src/ap.cpp
  src/Complex_1D_Array.cpp
  src/Complex_2D_Array.cpp
  src/dataanalysis.cpp
  src/diffequations.cpp
  src/fasttransforms.cpp
  src/GlobalStiffMatrix.cpp
  src/integration.cpp
  src/interpolation.cpp
  src/linalg.cpp
  src/optimization.cpp
  src/solvers.cpp
  src/specialfunctions.cpp
  src/statistics.cpp
  src/ViscoWave.cpp
  src/ViscoWaveEngine.cpp
)

add_library(ViscoWave SHARED ${VISCOWAVE_SOURCES})

target_include_directories(ViscoWave
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Remove "lib" prefix from library name on all platforms
set_target_properties(ViscoWave PROPERTIES PREFIX "")

if(WIN32)
  set_target_properties(ViscoWave PROPERTIES IMPORT_PREFIX "")
  if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set_target_properties(ViscoWave PROPERTIES OUTPUT_NAME "ViscoWave_x64")
  endif()
endif()

# On macOS, ensure static linking of C++ standard library when possible
if(APPLE)
  set_target_properties(ViscoWave PROPERTIES
    MACOSX_RPATH ON
    BUILD_WITH_INSTALL_RPATH ON
    INSTALL_NAME_DIR "@rpath"
  )
  # Link C++ standard library statically if using libc++
  target_link_options(ViscoWave PRIVATE -static-libstdc++)
endif()

target_compile_definitions(ViscoWave
  PRIVATE
    VISCOWAVE_BUILD
    $<$<PLATFORM_ID:Windows>:AE_OS=AE_WINDOWS>
    $<$<NOT:$<PLATFORM_ID:Windows>>:AE_OS=AE_POSIX>
)

find_package(OpenMP)
if(OpenMP_CXX_FOUND)
  if(MINGW AND PYWAVE_STATIC_RUNTIME)
    target_compile_options(ViscoWave PRIVATE ${OpenMP_CXX_FLAGS})
    set(_orig_suffixes ${CMAKE_FIND_LIBRARY_SUFFIXES})
    set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")
    find_library(GOMP_STATIC NAMES gomp PATHS
      "${CMAKE_CXX_IMPLICIT_LINK_DIRECTORIES}"
      "C:/msys64/ucrt64/lib"
      "/ucrt64/lib"
    )
    find_library(WINPTHREAD_STATIC NAMES winpthread PATHS
      "${CMAKE_CXX_IMPLICIT_LINK_DIRECTORIES}"
      "C:/msys64/ucrt64/lib"
      "/ucrt64/lib"
    )
    set(CMAKE_FIND_LIBRARY_SUFFIXES ${_orig_suffixes})
    target_link_options(ViscoWave PRIVATE -Wl,-Bstatic)
    if(GOMP_STATIC)
      target_link_libraries(ViscoWave PRIVATE ${GOMP_STATIC})
    else()
      target_link_libraries(ViscoWave PRIVATE gomp)
    endif()
    if(WINPTHREAD_STATIC)
      target_link_libraries(ViscoWave PRIVATE ${WINPTHREAD_STATIC})
    else()
      target_link_libraries(ViscoWave PRIVATE winpthread)
    endif()
    target_link_options(ViscoWave PRIVATE -Wl,-Bdynamic)
  else()
    target_link_libraries(ViscoWave PUBLIC OpenMP::OpenMP_CXX)
  endif()
endif()

if(MINGW AND PYWAVE_STATIC_RUNTIME)
  target_link_options(ViscoWave PRIVATE -static-libgcc -static-libstdc++)
endif()
