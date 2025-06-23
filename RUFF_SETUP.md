# Ruff Setup & Usage

## Installation
```bash
cd Windows
pip install ruff
```

## Usage

### Check for issues:
```bash
ruff check .
```

### Auto-fix issues:
```bash
ruff check --fix .
```

### Format code:
```bash
ruff format .
```

### Run both linting and formatting:
```bash
ruff check --fix . && ruff format .
```

## What Ruff will improve:

1. **Import sorting** - Organize imports alphabetically and by groups
2. **Remove unused imports** - Clean up imports that aren't used
3. **Code formatting** - Consistent spacing, quotes, line length
4. **Simple bugs** - Catch undefined variables, unused variables
5. **Modern Python** - Suggest newer Python syntax when appropriate

## Example improvements it might make:

**Before:**
```python
import os
import webbrowser
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List
from google import genai
from google.genai import types
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QVBoxLayout
from ui.UIUtils import colorMode, get_resource_path
```

**After:**
```python
import logging
import os
import webbrowser
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from google import genai
from google.genai import types
from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QVBoxLayout

from ui.UIUtils import colorMode, get_resource_path
```

## Integration with your build

Add to `pyinstaller-build-script.py` before building:
```python
import subprocess
print("Running ruff...")
subprocess.run(["ruff", "check", "--fix", "."], cwd="Windows")
subprocess.run(["ruff", "format", "."], cwd="Windows")
```