cmake_minimum_required(VERSION 3.16)

project(Relaxation_Sig_to_Prony LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

option(PYWAVE_STATIC_RUNTIME "Link GCC/Stdlib runtimes statically on MinGW (Windows)" ON)

set(RELAXATION_SIG_TO_PRONY_SOURCES
  src/alglibinternal.cpp
  src/alglibmisc.cpp
  src/ap.cpp
  src/dataanalysis.cpp
  src/diffequations.cpp
  src/fasttransforms.cpp
  src/integration.cpp
  src/interpolation.cpp
  src/linalg.cpp
  src/optimization.cpp
  src/Relaxation_Sig_to_Prony.cpp
  src/solvers.cpp
  src/specialfunctions.cpp
  src/statistics.cpp
)

add_library(Relaxation_Sig_to_Prony SHARED ${RELAXATION_SIG_TO_PRONY_SOURCES})

target_include_directories(Relaxation_Sig_to_Prony
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Remove "lib" prefix from library name on all platforms
set_target_properties(Relaxation_Sig_to_Prony PROPERTIES PREFIX "")

if(WIN32)
  set_target_properties(Relaxation_Sig_to_Prony PROPERTIES IMPORT_PREFIX "")
  if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    set_target_properties(Relaxation_Sig_to_Prony PROPERTIES OUTPUT_NAME "Relaxation_Sig_to_Prony_x64")
  endif()
endif()

# On macOS, ensure static linking of C++ standard library when possible
if(APPLE)
  set_target_properties(Relaxation_Sig_to_Prony PROPERTIES
    MACOSX_RPATH ON
    BUILD_WITH_INSTALL_RPATH ON
    INSTALL_NAME_DIR "@rpath"
  )
  # Link C++ standard library statically if using libc++
  target_link_options(Relaxation_Sig_to_Prony PRIVATE -static-libstdc++)
endif()

target_compile_definitions(Relaxation_Sig_to_Prony
  PRIVATE
    RELAXATION_SIG_TO_PRONY_BUILD
    $<$<PLATFORM_ID:Windows>:AE_OS=AE_WINDOWS>
    $<$<NOT:$<PLATFORM_ID:Windows>>:AE_OS=AE_POSIX>
)

if(MINGW AND PYWAVE_STATIC_RUNTIME)
  target_link_options(Relaxation_Sig_to_Prony PRIVATE -static-libgcc -static-libstdc++)
  set(_orig_suffixes_rel ${CMAKE_FIND_LIBRARY_SUFFIXES})
  set(CMAKE_FIND_LIBRARY_SUFFIXES ".a")
  find_library(WINPTHREAD_STATIC NAMES winpthread PATHS
    "${CMAKE_CXX_IMPLICIT_LINK_DIRECTORIES}"
    "C:/msys64/ucrt64/lib"
    "/ucrt64/lib"
  )
  set(CMAKE_FIND_LIBRARY_SUFFIXES ${_orig_suffixes_rel})
  if(WINPTHREAD_STATIC)
    target_link_libraries(Relaxation_Sig_to_Prony PRIVATE "-Wl,-Bstatic" ${WINPTHREAD_STATIC} "-Wl,-Bdynamic")
  else()
    target_link_libraries(Relaxation_Sig_to_Prony PRIVATE "-Wl,-Bstatic" winpthread "-Wl,-Bdynamic")
  endif()
endif()
