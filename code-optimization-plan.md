# Code Optimization Plan for Writing Tools

## Overview
The Writing Tools app currently has significant code duplication and unused code remnants. This document outlines specific optimization opportunities that could reduce the codebase by 685-885 lines (17-22% reduction) while improving maintainability.

## 1. Massive Code Duplication (HIGH PRIORITY)

### Issue: `get_resource_path()` Function Duplicated 11 Times
**Impact**: ~150 lines of identical code  
**Files affected**:
- ButtonEditDialog.py
- ButtonEditWindow.py  
- ConfigManager.py
- CustomPopupWindow.py
- UIUtils.py
- And 6 other files

**Current code in each file**:
```python
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(sys.argv[0])
    return os.path.join(base_path, relative_path)
```

**Solution**:
1. Keep only the version in UIUtils.py
2. Remove from all other files
3. Add `from ui.UIUtils import get_resource_path` to files that need it

---

## 2. Icon System Remnants (MEDIUM PRIORITY)

### Issue: Dead Icon Code Still Present  
**Impact**: ~100+ lines of unused code  
**Problem**: Icons were recently removed from buttons, but code references remain

**Files to clean**:
- `options.json` - Remove all `"icon": "..."` entries
- `ButtonEditDialog.py` - Remove icon references from DEFAULT_OPTIONS_JSON
- `UIUtils.py` - Remove background image loading code

**Example dead code**:
```python
# In DEFAULT_OPTIONS_JSON
"icon": "icons/magnifying-glass",
"icon": "icons/rewrite", 
# etc.
```

**Solution**:
1. Remove all icon references from DEFAULT_OPTIONS_JSON  
2. Clean options.json of icon entries
3. Remove background image handling from UIUtils.py

---

## 3. Styling Code Explosion (HIGH PRIORITY)

### Issue: 68 Instances of Repetitive `setStyleSheet()`
**Impact**: ~500+ lines of repetitive styling code  
**Problem**: Same button/input styling repeated across multiple files

**Common patterns repeated everywhere**:
```python
# Button styling - repeated ~20 times
f"""
QPushButton {{
    background-color: {"#444" if colorMode == "dark" else "white"};
    border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
    color: {"#fff" if colorMode == "dark" else "#000"};
    ...
}}
"""

# Input styling - repeated ~15 times  
f"""
QLineEdit {{
    padding: 8px;
    border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
    background-color: {"#333" if colorMode == "dark" else "white"};
    color: {"#fff" if colorMode == "dark" else "#000"};
    ...
}}
"""
```

**Solution**: Create reusable style functions in UIUtils.py:
```python
def get_button_style(variant="default"):
    # Returns appropriate button style
    
def get_input_style():
    # Returns input field style
    
def get_label_style(bold=False):
    # Returns label style
```

---

## 4. DEFAULT_OPTIONS_JSON Duplication (MEDIUM PRIORITY)

### Issue: 84-Line JSON String Hardcoded
**Impact**: Maintenance nightmare - two sources of truth  
**Problem**: ButtonEditDialog.py has hardcoded DEFAULT_OPTIONS_JSON when options.json already exists

**Current situation**:
- `options.json` (84 lines) - The actual config file
- `DEFAULT_OPTIONS_JSON` in ButtonEditDialog.py (84 lines) - Hardcoded copy

**Solution**:
1. Remove DEFAULT_OPTIONS_JSON constant
2. Load defaults from options.json file instead
3. Create function to load default options when needed

---

## 5. Background Image Dead Code (LOW PRIORITY)

### Issue: References to Non-Existent Images
**Impact**: ~15 lines of dead code  
**Files**: UIUtils.py

**Dead code**:
```python
# References to files that don't exist:
background_popup_dark.png
background_popup.png  
background_dark.png
background.png
```

**Solution**:
1. Remove gradient theme support
2. Keep only simple solid color backgrounds
3. Clean up image loading functions

---

## Implementation Strategy

### Phase 1: Utility Consolidation (~150 lines saved)
- [ ] Centralize `get_resource_path()` in UIUtils.py
- [ ] Remove duplicates from all other files
- [ ] Add proper imports

### Phase 2: Icon System Cleanup (~100 lines saved) ✅ COMPLETED
- [x] Remove icon references from DEFAULT_OPTIONS_JSON
- [x] Clean options.json of icon entries  
- [x] Remove background image code

### Phase 3: Style System Refactor (~400 lines saved)
- [ ] Create reusable style functions
- [ ] Replace inline setStyleSheet() calls
- [ ] Consolidate color mode logic

### Phase 4: Configuration Cleanup (~85 lines saved)
- [ ] Remove DEFAULT_OPTIONS_JSON constant
- [ ] Load from options.json instead
- [ ] Update reset functionality

### Phase 5: Dead Code Removal (~15 lines saved)
- [ ] Remove background image references
- [ ] Clean up unused image loading code

---

## Expected Results

**Total Reduction**: 685-885 lines (~17-22% of current codebase)

**Benefits**:
- ✅ **Single source of truth** for styles and configurations
- ✅ **Easier maintenance** - change style in one place
- ✅ **Better consistency** across UI components  
- ✅ **Improved performance** due to less redundant code
- ✅ **Cleaner codebase** for future development

**Risk Level**: LOW - These are primarily code organization improvements that don't change functionality