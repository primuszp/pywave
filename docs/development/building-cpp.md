# Building C++ Libraries

This guide explains how to build the native C++ libraries (`ViscoWave` and `Relaxation_Sig_to_Prony`) from source.

**Note:** Pre-built binaries are included in the package for Windows and macOS. You only need to build from source if:
- You're developing on Linux
- You want to customize the build
- You're contributing to the C++ code
- The pre-built binaries don't work on your system

---

## 📋 Prerequisites

### All Platforms:
- **CMake >= 3.16**
- **C++14 compatible compiler**

### Platform-Specific:

#### macOS:
```bash
# Xcode Command Line Tools
xcode-select --install

# CMake
brew install cmake

# (Optional) OpenMP support
brew install libomp
```

#### Linux:
```bash
# Ubuntu/Debian
sudo apt-get install cmake build-essential

# (Optional) OpenMP support
sudo apt-get install libomp-dev

# Fedora/RHEL
sudo dnf install cmake gcc-c++ libomp-devel
```

#### Windows:
- **MinGW-w64** (UCRT64 recommended)
- **CMake** (via MinGW or standalone)

```bash
# Using MSYS2
pacman -S mingw-w64-ucrt-x86_64-cmake
pacman -S mingw-w64-ucrt-x86_64-gcc
```

---

## 🏗️ Build Instructions

### macOS - Universal Binary (Intel + Apple Silicon)

Build both architectures and create a universal binary:

#### 1. Intel (x86_64) Build:
```bash
cd /path/to/pywave/csrc/ViscoWave_portable

cmake -S . -B build_x86_64 \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=x86_64

cmake --build build_x86_64 --config Release
```

#### 2. Apple Silicon (ARM64) Build:
```bash
cmake -S . -B build_arm64 \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=arm64

cmake --build build_arm64 --config Release
```

#### 3. Create Universal Binary:
```bash
# Combine both architectures
lipo -create \
  build_x86_64/ViscoWave.dylib \
  build_arm64/ViscoWave.dylib \
  -output ViscoWave.dylib

# Verify
lipo -info ViscoWave.dylib
# Expected: Architectures in the fat file: ViscoWave.dylib are: x86_64 arm64
```

#### 4. Install to Python Package:
```bash
cp ViscoWave.dylib ../../viscowave/
```

#### Repeat for Relaxation_Sig_to_Prony:
```bash
cd ../Relaxation_Sig_to_Prony_portable
# ... same steps ...
cp Relaxation_Sig_to_Prony.dylib ../../viscowave/
```

#### OpenMP Support (Optional):
```bash
brew install libomp

# Then rebuild with:
cmake -S . -B build_x86_64 \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=x86_64 \
  -DOpenMP_ROOT=$(brew --prefix libomp)
```

---

### Linux

#### Standard Build:
```bash
cd /path/to/pywave/csrc/ViscoWave_portable

# Configure
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build --config Release -j$(nproc)

# Install to package
cp build/ViscoWave.so ../../viscowave/
```

#### For Relaxation_Sig_to_Prony:
```bash
cd ../Relaxation_Sig_to_Prony_portable

cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
cp build/Relaxation_Sig_to_Prony.so ../../viscowave/
```

#### With OpenMP:
OpenMP should be detected automatically on Linux with GCC. Verify:
```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
# Look for: "Found OpenMP: TRUE"
```

---

### Windows (MinGW-w64)

Using MSYS2 UCRT64 environment:

#### 1. Open UCRT64 Terminal:
```bash
# From MSYS2 launcher, select "UCRT64"
```

#### 2. Build ViscoWave:
```bash
cd /c/path/to/pywave/csrc/ViscoWave_portable

cmake -G "MinGW Makefiles" -S . -B build_x64 \
  -DCMAKE_BUILD_TYPE=Release \
  -DPYWAVE_STATIC_RUNTIME=ON

cmake --build build_x64 --config Release
```

#### 3. Install to Package:
```bash
cp build_x64/ViscoWave_x64.dll ../../viscowave/
```

#### 4. Repeat for Relaxation_Sig_to_Prony:
```bash
cd ../Relaxation_Sig_to_Prony_portable

cmake -G "MinGW Makefiles" -S . -B build_x64 \
  -DCMAKE_BUILD_TYPE=Release \
  -DPYWAVE_STATIC_RUNTIME=ON

cmake --build build_x64 --config Release
cp build_x64/Relaxation_Sig_to_Prony_x64.dll ../../viscowave/
```

#### Notes:
- `PYWAVE_STATIC_RUNTIME=ON` links GCC and OpenMP statically (recommended)
- Output: `ViscoWave_x64.dll` (note the `_x64` suffix)

---

## 🧪 Testing the Build

### 1. Check Library Files:
```bash
# macOS
ls -lh viscowave/*.dylib
lipo -info viscowave/ViscoWave.dylib

# Linux
ls -lh viscowave/*.so
ldd viscowave/ViscoWave.so

# Windows
ls -lh viscowave/*.dll
```

### 2. Test Python Import:
```bash
cd /path/to/pywave
python3 -c "import viscowave; print(viscowave.get_platform_info())"
```

Expected output:
```python
{
  'system': 'Darwin',  # or 'Linux', 'Windows'
  'architecture': 'x86_64',  # or 'arm64'
  'python_version': '3.x.x',
  'library_status': 'loaded'  # ← Should be 'loaded'
}
```

### 3. Run Quick Test:
```bash
python3 examples/quick_start.py
```

---

## 🔧 Build Options

### CMake Options:

| Option | Default | Description |
|--------|---------|-------------|
| `CMAKE_BUILD_TYPE` | Release | Build type (Release/Debug) |
| `CMAKE_OSX_ARCHITECTURES` | (auto) | macOS: x86_64, arm64, or both |
| `PYWAVE_STATIC_RUNTIME` | ON (Windows) | Link C++ runtime statically |
| `OpenMP_ROOT` | (auto) | Path to OpenMP installation |

### Example with All Options:
```bash
cmake -S . -B build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES="x86_64;arm64" \
  -DPYWAVE_STATIC_RUNTIME=ON \
  -DOpenMP_ROOT=/opt/homebrew/opt/libomp
```

---

## 🐛 Troubleshooting

### "Library not found" after build

**Check file exists:**
```bash
ls -la viscowave/*.dylib  # macOS
ls -la viscowave/*.so     # Linux
ls -la viscowave/*.dll    # Windows
```

**Check permissions:**
```bash
chmod +x viscowave/*.dylib
```

**macOS: Remove quarantine:**
```bash
xattr -d com.apple.quarantine viscowave/*.dylib
```

---

### "OpenMP not found"

**macOS:**
```bash
brew install libomp
export OpenMP_ROOT=$(brew --prefix libomp)
```

**Linux:**
```bash
sudo apt-get install libomp-dev  # Debian/Ubuntu
sudo dnf install libomp-devel    # Fedora/RHEL
```

**Windows:**
OpenMP should come with MinGW-w64. If not:
```bash
pacman -S mingw-w64-ucrt-x86_64-openmp
```

**Note:** OpenMP is optional. The library works without it (just slower).

---

### Build Warnings

#### "sprintf is deprecated"
This is from legacy ALGLIB code. Not critical, but should eventually be fixed:
```
warning: 'sprintf' is deprecated: ... use snprintf(3) instead
```
**Status:** Known issue, cosmetic only.

#### "static-libstdc++ not supported"
On macOS with Clang, this warning is expected:
```
clang++: warning: argument unused during compilation: '-static-libstdc++'
```
**Status:** Harmless, ignored by Clang.

---

### CMake can't find compiler

**Linux:**
```bash
sudo apt-get install build-essential
```

**macOS:**
```bash
xcode-select --install
```

**Windows:**
Make sure you're in the correct MSYS2 environment (UCRT64).

---

## 📦 Library Details

### ViscoWave Library:
- **Purpose:** Calculates pavement response (displacement) under vehicle loads
- **Sources:** ~30 C++ files including ALGLIB
- **Size:** ~3-6 MB (depending on platform and architecture)
- **Dependencies:** None (ALGLIB bundled)

### Relaxation_Sig_to_Prony Library:
- **Purpose:** Converts sigmoid relaxation modulus to Prony series
- **Sources:** Similar to ViscoWave, also uses ALGLIB
- **Size:** ~3-6 MB
- **Dependencies:** None (ALGLIB bundled)

### ALGLIB:
- **Version:** Bundled in csrc/*/src/
- **License:** GPL (included)
- **Features:** FFT, interpolation, optimization, statistics

---

## 🔄 Rebuilding After Code Changes

If you modify the C++ code:

```bash
# Clean build
rm -rf build_*

# Rebuild
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

# Install
cp build/ViscoWave.dylib ../../viscowave/  # adjust for your platform

# Test
cd ../../
python3 examples/quick_start.py
```

---

## 🚀 Automated Build Script (macOS)

For convenience, there's a build script:

```bash
cd csrc/docs
./build_macos.sh
```

This script:
1. Builds both libraries (x86_64 + ARM64)
2. Creates universal binaries
3. Copies to `viscowave/` directory
4. Tests the installation

---

## 📚 Additional Resources

- **CMakeLists.txt** - Build configuration
- **Platform-specific READMEs:**
  - [csrc/ViscoWave_portable/BUILD_MACOS.md](../../csrc/ViscoWave_portable/BUILD_MACOS.md)
  - [csrc/ViscoWave_portable/BUILD_LINUX.md](../../csrc/ViscoWave_portable/BUILD_LINUX.md)
  - [csrc/ViscoWave_portable/BUILD_WINDOWS.md](../../csrc/ViscoWave_portable/BUILD_WINDOWS.md)

---

## 🤝 Contributing

If you improve the build system or fix platform-specific issues, please contribute!

See the C++ source code in:
- `csrc/ViscoWave_portable/src/`
- `csrc/Relaxation_Sig_to_Prony_portable/src/`

---

**Last updated:** 2026-02-16
