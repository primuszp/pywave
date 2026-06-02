# macOS build - Universal Binary (Intel + Apple Silicon)

**Cél**: Universal `libViscoWave.dylib` fordítása, amely támogatja az Intel (x86_64) és Apple Silicon (ARM64) architektúrákat.

**Előfeltételek**
1. Xcode Command Line Tools:
```bash
xcode-select --install
```
2. CMake:
```bash
brew install cmake
```

**Build lépések - Universal Binary**

### 1. Intel (x86_64) build
```bash
cd /path/to/pywave/csrc/ViscoWave_portable
cmake -S . -B build_x86_64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=x86_64
cmake --build build_x86_64 --config Release
```

### 2. Apple Silicon (ARM64) build
```bash
cd /path/to/pywave/csrc/ViscoWave_portable
cmake -S . -B build_arm64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64
cmake --build build_arm64 --config Release
```

### 3. Universal binary létrehozása
```bash
cd /path/to/pywave/csrc/ViscoWave_portable
lipo -create build_x86_64/libViscoWave.dylib build_arm64/libViscoWave.dylib -output libViscoWave.dylib
```

### 4. Ellenőrzés
```bash
lipo -info libViscoWave.dylib
# Output: Architectures in the fat file: libViscoWave.dylib are: x86_64 arm64
```

**Eredmény**
- `libViscoWave.dylib` - Universal binary (x86_64 + arm64)
- Méret: ~5.5 MB

**Telepítés a Python modulba**
```bash
cp libViscoWave.dylib ../../viscowave/
```

**Megjegyzés OpenMP-hez**
- A jelenlegi build OpenMP nélkül készül (Apple Clang alapértelmezetten nem támogatja)
- Ha OpenMP-t szeretnél, telepítsd a `libomp` csomagot és módosítsd a CMakeLists.txt-t:
```bash
brew install libomp
```
