# Installation Guide

Complete installation guide for **ViscoWave 2.0** - Python wrapper for viscoelastic pavement analysis.

---

## 🚀 Quick Install (TL;DR)

```bash
# Recommended: Virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .

# Verify
python -c "import viscowave; print(f'✓ {viscowave.__version__}')"
```

Or use the automated script:
```bash
./install_dev.sh
source venv/bin/activate
```

---

## 📦 Installation Methods

Choose the method that best fits your needs:

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **[Virtual Environment](#method-1-virtual-environment-recommended)** | Development, Testing | ✅ Isolated, Clean | Need to activate |
| **[System Install](#method-2-system-install-macos)** | Quick access | ✅ Available everywhere | ⚠️ May conflict |
| **[PYTHONPATH](#method-3-no-install-pythonpath)** | Quick testing | ✅ No installation | Need to set PATH each time |

---

## Method 1: Virtual Environment (Recommended)

**Best for:** Development, production deployments, CI/CD

### Automated Installation:

```bash
# Run the install script
./install_dev.sh

# Activate the environment
source venv/bin/activate

# You're ready!
python examples/modern_api_demo.py
```

### Manual Installation:

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# 3. Install viscowave (editable mode)
pip install -e .

# 4. (Optional) Install extras
pip install -e ".[units]"         # pint for unit handling
pip install -e ".[dev]"           # development tools

# 5. Verify installation
python -c "import viscowave; print(viscowave.get_platform_info())"
```

### Deactivating:
```bash
deactivate
```

---

## Method 2: System Install (macOS)

**Best for:** Quick system-wide access

### User Install (Recommended for macOS):

```bash
python3 -m pip install --user --break-system-packages -e .
python3 -m pip install --user --break-system-packages pint  # optional
```

**Note:** The `--break-system-packages` flag is required on macOS Homebrew Python 3.9+. The `--user` flag ensures safe installation in your home directory.

**Installation location:**
```
~/Library/Python/3.14/lib/python/site-packages/
```

### Verification:
```bash
python3 -c "import viscowave; print(f'✓ v{viscowave.__version__} installed')"
```

---

## Method 3: No Install (PYTHONPATH)

**Best for:** Quick testing, no permanent installation needed

### Using Environment Variable:

```bash
# Set PYTHONPATH for one command
PYTHONPATH=. python3 examples/quick_start.py

# Or export for the session
export PYTHONPATH=/path/to/pywave:$PYTHONPATH
python3 examples/modern_api_demo.py
```

### Using the Helper Script:

```bash
# Run examples without installation
./run_example.sh quick_start
./run_example.sh modern_api_demo
./run_example.sh viscowave_basic
```

### In Python Scripts:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Now you can import
from viscowave import AnalysisBuilder
```

---

## 📋 Dependencies

### Core (Required):
- **numpy >= 1.20** - Array operations

### Optional:
- **pint >= 0.21** - Unit handling with physical quantities
  ```bash
  pip install -e ".[units]"
  ```

### Development Tools:
- **pytest >= 7.0** - Testing framework
- **pytest-cov >= 4.0** - Coverage reporting
- **mypy >= 1.0** - Static type checking
- **ruff >= 0.1.0** - Fast Python linter
- **black >= 23.0** - Code formatter

Install all dev tools:
```bash
pip install -e ".[dev]"
```

---

## 🔍 Verify Installation

### 1. Import Test:
```bash
python3 -c "import viscowave; print(f'✓ viscowave {viscowave.__version__}')"
```

### 2. Platform Check:
```bash
python3 -c "from viscowave import get_platform_info; import json; print(json.dumps(get_platform_info(), indent=2))"
```

Expected output:
```json
{
  "system": "Darwin",
  "architecture": "x86_64",
  "python_version": "3.14.2",
  "library_status": "loaded"
}
```

### 3. Run Examples:
```bash
# With virtual env
source venv/bin/activate
python examples/quick_start.py

# Or with PYTHONPATH
PYTHONPATH=. python3 examples/quick_start.py
```

### 4. Quick Functionality Test:
```bash
python3 test_installation.py
```

---

## ❓ Troubleshooting

### "ModuleNotFoundError: No module named 'viscowave'"

**Cause:** Package not installed or not in Python path

**Solution:**
```bash
# Option 1: Install in virtual env
source venv/bin/activate
pip install -e .

# Option 2: Use PYTHONPATH
PYTHONPATH=. python3 your_script.py

# Option 3: System install
python3 -m pip install --user --break-system-packages -e .
```

---

### "externally-managed-environment" Error

**Cause:** macOS/Homebrew Python 3.9+ protection (PEP 668)

**Solution:**
```bash
# Best: Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Or: System install with flags
python3 -m pip install --user --break-system-packages -e .
```

---

### "ImportError: No module named 'pint'"

**Cause:** pint is now optional (as of v2.0.0)

**Solution:**
```bash
# If you want pint support
pip install pint

# Or install with units extra
pip install -e ".[units]"
```

---

### C++ Library Not Found

**Cause:** Missing `.dylib`/`.dll`/`.so` files in `viscowave/` directory

**Check:**
```bash
ls -la viscowave/*.dylib    # macOS
ls -la viscowave/*.dll      # Windows
ls -la viscowave/*.so       # Linux
```

**Solution:** Rebuild libraries
```bash
cd csrc/ViscoWave_portable
mkdir build && cd build
cmake ..
cmake --build .

# Copy to package
cp ViscoWave.dylib ../../../viscowave/    # macOS
cp ViscoWave.dll ../../../viscowave/      # Windows
cp ViscoWave.so ../../../viscowave/       # Linux
```

See [Building C++ Libraries](../development/building-cpp.md) for detailed instructions.

---

### "Permission Denied" on macOS

**Cause:** Security restrictions on downloaded dylib files

**Solution:**
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine viscowave/*.dylib

# Or allow in System Settings
# System Settings → Privacy & Security → Allow anyway
```

---

## 🎯 Recommended Method by Use Case

| Use Case | Method | Command |
|----------|--------|---------|
| **Quick test** | PYTHONPATH | `./run_example.sh quick_start` |
| **Development** | Virtual env | `./install_dev.sh && source venv/bin/activate` |
| **Production** | Virtual env | `python3 -m venv venv && pip install .` |
| **System-wide** | User install | `pip3 install --user --break-system-packages -e .` |
| **CI/CD** | Direct install | `pip install .` (in clean environment) |

---

## 🔄 Updating

### Editable Install (Development):
No need to reinstall! Changes to Python code take effect immediately.

```bash
# Just pull latest changes
git pull

# Library still works automatically
python examples/quick_start.py
```

### Regular Install:
```bash
# Pull changes
git pull

# Reinstall
pip install --upgrade --force-reinstall -e .
```

---

## 🗑️ Uninstallation

### Remove Package:
```bash
pip uninstall viscowave
```

### Remove Virtual Environment:
```bash
rm -rf venv/
```

### System Install Cleanup:
```bash
# Remove from user site-packages
python3 -m pip uninstall viscowave

# Optional: remove dependencies
pip uninstall numpy pint
```

---

## 📚 Next Steps

After installation, check out:

- **[Quick Start Guide](quickstart.md)** - First examples
- **[Modern API Guide](../api/modern-api.md)** - Full API documentation
- **[Examples](../../examples/README.md)** - Working code samples
- **[Building C++ Libraries](../development/building-cpp.md)** - Advanced: rebuild native libraries

---

## 💡 Tips

### Editable Mode Benefits:

When you install with `pip install -e .`:
- ✅ Code changes take effect immediately
- ✅ No need to reinstall after editing
- ✅ Perfect for development
- ✅ Points to your project directory

### Multiple Python Versions:

```bash
# Python 3.9
python3.9 -m venv venv39
source venv39/bin/activate
pip install -e .

# Python 3.12
python3.12 -m venv venv312
source venv312/bin/activate
pip install -e .
```

### Jupyter Notebook:

```bash
# Install in virtual env
source venv/bin/activate
pip install -e .
pip install jupyter

# Launch notebook
jupyter notebook
```

In notebook:
```python
from viscowave import AnalysisBuilder, presets
# ... use normally
```

---

**Last updated:** 2026-02-16
**Version:** 2.0.0
