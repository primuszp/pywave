# Linux build

**Cél**: `libViscoWave.so` fordítása CMake alapú builddel.

**Előfeltételek (Ubuntu/Debian példa)**
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build
```

**Build lépések**
```bash
cd /path/to/pywave/csrc/ViscoWave_portable
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

**Eredmény**
- `build/libViscoWave.so`

**Megjegyzés OpenMP-hez**
- Ha a rendszereden elérhető az OpenMP, a build automatikusan használja.
