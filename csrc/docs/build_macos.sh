#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "pywave macOS Universal Binary Builder"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VISCOWAVE_DIR="$PROJECT_ROOT/csrc/ViscoWave_portable"
RELAXATION_DIR="$PROJECT_ROOT/csrc/Relaxation_Sig_to_Prony_portable"
VISCOWAVE_MODULE="$PROJECT_ROOT/viscowave"

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v cmake &> /dev/null; then
    echo "Error: cmake not found. Please install: brew install cmake"
    exit 1
fi
echo -e "${GREEN}✓${NC} cmake found: $(cmake --version | head -n1)"

if ! xcode-select -p &> /dev/null; then
    echo "Error: Xcode Command Line Tools not found. Please install: xcode-select --install"
    exit 1
fi
echo -e "${GREEN}✓${NC} Xcode Command Line Tools found"
echo ""

# Build ViscoWave
echo -e "${BLUE}Building ViscoWave...${NC}"
cd "$VISCOWAVE_DIR"

echo "  Building x86_64..."
rm -rf build_x86_64
cmake -S . -B build_x86_64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=x86_64 > /dev/null
cmake --build build_x86_64 --config Release 2>&1 | grep -v "warning:" || true
echo -e "  ${GREEN}✓${NC} x86_64 build complete"

echo "  Building arm64..."
rm -rf build_arm64
cmake -S . -B build_arm64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 > /dev/null
cmake --build build_arm64 --config Release 2>&1 | grep -v "warning:" || true
echo -e "  ${GREEN}✓${NC} arm64 build complete"

echo "  Creating universal binary..."
lipo -create build_x86_64/ViscoWave.dylib build_arm64/ViscoWave.dylib -output ViscoWave.dylib
echo -e "  ${GREEN}✓${NC} Universal binary created"
lipo -info ViscoWave.dylib | sed 's/^/  /'
echo ""

# Build Relaxation_Sig_to_Prony
echo -e "${BLUE}Building Relaxation_Sig_to_Prony...${NC}"
cd "$RELAXATION_DIR"

echo "  Building x86_64..."
rm -rf build_x86_64
cmake -S . -B build_x86_64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=x86_64 > /dev/null
cmake --build build_x86_64 --config Release 2>&1 | grep -v "warning:" || true
echo -e "  ${GREEN}✓${NC} x86_64 build complete"

echo "  Building arm64..."
rm -rf build_arm64
cmake -S . -B build_arm64 -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 > /dev/null
cmake --build build_arm64 --config Release 2>&1 | grep -v "warning:" || true
echo -e "  ${GREEN}✓${NC} arm64 build complete"

echo "  Creating universal binary..."
lipo -create build_x86_64/Relaxation_Sig_to_Prony.dylib build_arm64/Relaxation_Sig_to_Prony.dylib -output Relaxation_Sig_to_Prony.dylib
echo -e "  ${GREEN}✓${NC} Universal binary created"
lipo -info Relaxation_Sig_to_Prony.dylib | sed 's/^/  /'
echo ""

# Copy libraries to Python module
echo -e "${BLUE}Installing libraries to viscowave module...${NC}"
cp "$VISCOWAVE_DIR/ViscoWave.dylib" "$VISCOWAVE_MODULE/"
echo -e "  ${GREEN}✓${NC} ViscoWave.dylib copied"
cp "$RELAXATION_DIR/Relaxation_Sig_to_Prony.dylib" "$VISCOWAVE_MODULE/"
echo -e "  ${GREEN}✓${NC} Relaxation_Sig_to_Prony.dylib copied"
echo ""

# Test the module
echo -e "${BLUE}Testing Python module...${NC}"
cd "$PROJECT_ROOT"
python3 -c "
from viscowave.api import ViscoWaveModel, RelaxationPronyModel
print('  ✓ Module import successful')
vw = ViscoWaveModel()
rel = RelaxationPronyModel()
print('  ✓ Model instances created successfully')
" || {
    echo "Error: Python module test failed"
    exit 1
}
echo ""

echo "========================================="
echo -e "${GREEN}Build completed successfully!${NC}"
echo "========================================="
echo ""
echo "Libraries installed in: $VISCOWAVE_MODULE/"
ls -lh "$VISCOWAVE_MODULE"/*.dylib | awk '{print "  - " $9 " (" $5 ")"}'
echo ""
echo "You can now use the viscowave Python module:"
echo "  python3 viscowave_example.py"
