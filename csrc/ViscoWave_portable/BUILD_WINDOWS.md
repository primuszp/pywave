# Windows build (MSYS2 + MinGW-w64, no Visual Studio)

**Cél**: `ViscoWave.dll` fordítása CMake alapú builddel, Visual Studio nélkül.

**Előfeltételek**
1. MSYS2 telepítve.
2. UCRT64 környezet használata.
3. Csomagok telepítése:

```bash
pacman -S --needed \
  mingw-w64-ucrt-x86_64-toolchain \
  mingw-w64-ucrt-x86_64-cmake \
  mingw-w64-ucrt-x86_64-ninja
```

**Build lépések**
1. Nyisd meg az MSYS2 UCRT64 shellt.
2. Lépj a projekt mappába:

```bash
cd /c/Users/primu/OneDrive/pyPAVE/pywave/csrc/ViscoWave_portable
```

3. Konfigurálás és build (Release):

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

**Eredmény**
- 64‑bit esetén: `build/ViscoWave_x64.dll`
- Import library: `build/ViscoWave_x64.dll.a`

**Futtatási függőségek (Windows)**
Alapértelmezésben a build **statikusan** linkeli a GCC/Stdlib/OpenMP runtime‑okat,
így nem kell külön `libgcc_s_seh-1.dll`, `libstdc++-6.dll`, `libgomp-1.dll`.
**Megjegyzés:** MinGW‑UCRT esetén a `libwinpthread-1.dll` továbbra is szükséges,
ezért ezt a csomagban mellékeljük.

Ha mégis dinamikus runtime kell, kapcsold ki:
```
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DPYWAVE_STATIC_RUNTIME=OFF
```

**Debug build**
```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

**Megjegyzések**
- Ha nem szeretnél Ninja-t használni, cseréld a generátort:
```bash
cmake -S . -B build -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build build
```
