# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Writing Tools is an Apple Intelligence-inspired desktop application that provides AI-powered writing assistance system-wide. This version has been streamlined for Windows with English-only interface, Gemini AI integration, and simplified UI styling. Users can proofread, rewrite, summarize, and perform custom text operations on any selected text across all applications using a global hotkey (default: Ctrl+Space).

## Development Commands

### Running from Source
```bash
# Install dependencies
pip install -r Windows/requirements.txt

# Run application
cd Windows && python main.py
```

### Building Executable
```bash
# Build with PyInstaller spec file (from Windows directory)
cd Windows && python pyinstaller-build-script.py
```

The spec file creates a single-file executable with optimized exclusions and proper resource bundling.


## Architecture Overview

### Core Application Structure
- **Entry Point**: `Windows/main.py` - Simple launcher that starts the Qt application
- **Main Application**: `Windows/WritingToolApp.py` - QApplication-based system tray app with global hotkey listener
- **AI Provider System**: `Windows/aiprovider.py` - Simple Gemini AI provider implementation

### UI Architecture
The UI is modular with separate window classes in `Windows/ui/`:
- `CustomPopupWindow.py` - Main command selection popup (appears on hotkey when text is selected)
- `ResponseWindow.py` - Enhanced chat-style window (900x700px) with model/thinking controls, markdown rendering, user message styling, and save functionality. Opens directly when no text is selected.
- `SettingsWindow.py` - Provider configuration with separate chat and text operation model settings
- `OnboardingWindow.py` - Simplified first-time setup (hotkey configuration and Gemini API key)
- `ChatHistoryWindow.py` - Window for viewing, opening, and managing saved chat conversations
- `ChatManager.py` - Data management for saving and loading chat histories to JSON storage
- `UIUtils.py` - Common styling utilities and simple background rendering

### Data Flow
1. **Global hotkey detection** (pynput) → **Text capture** (clipboard) → **UI display** → **AI processing** → **Text replacement**
2. **Direct chat mode**: When no text is selected, hotkey opens ResponseWindow directly for AI conversations
3. **Threading model** ensures non-blocking AI operations using Qt signals/slots
4. **System tray** provides persistent access to settings, chat history, and controls
5. **Chat persistence** enables saving conversations with automatic title generation and JSON storage

### Chat History System
- **ChatManager** handles all chat persistence operations (save, load, delete)
- **Chat Storage**: `saved_chats.json` stores all conversations with metadata (title, timestamp, chat history)
- **Auto-title Generation**: Creates meaningful titles from conversation content
- **Conversation Continuity**: Saved chats can be reopened and continued seamlessly

## Configuration System

### Writing Operations Configuration
- `Windows/options.json` - Defines all writing operations, their prompts, icons, and behavior
- Each operation has: `prefix`, `instruction`, `icon`, and `open_in_window` properties
- `open_in_window: false` operations replace text directly
- `open_in_window: true` operations show results in ResponseWindow with chat capability

### User Settings & Data Storage
- `config.json` (created at runtime) - Stores Gemini API key, separate model settings (chat vs text operations), hotkey settings, and UI preferences
- `saved_chats.json` (created at runtime) - Persistent storage for all chat conversations with full history
- Settings are managed through the SettingsWindow UI with separate model selection for different operation types
- Chat management through ChatHistoryWindow with save/load/delete operations

## Key Components

### AI Provider Interface
```python
class AIProvider(ABC):
    @abstractmethod
    def get_response(self, system_instruction: str, prompt: str, return_response: bool = False, 
                    model: str = None, thinking_budget: int = None) -> str
    
    @abstractmethod  
    def get_settings_ui(self, parent) -> QWidget
    
    @abstractmethod
    def save_settings(self, widget: QWidget)
```

Implementation:
- `GeminiProvider` - Google's Gemini API integration using the new `genai.Client()` approach with thinking functionality (supports Gemini 2.5 Flash and 2.5 Flash Lite models)

### Text Processing Pipeline
1. **Text Selection**: Captured via clipboard operations for universal compatibility
2. **Command Selection**: CustomPopupWindow displays available operations (if text selected) or opens chat directly (if no text)
3. **AI Processing**: Threaded execution prevents UI freezing via Gemini API with automatic model selection
4. **Result Handling**: Direct replacement or ResponseWindow display based on operation type

### AI Model & Thinking System
- **Separate Model Configuration**: Chat operations use chat model (default: Gemini 2.5 Flash), text operations use text model (default: Gemini 2.5 Flash Lite)
- **Thinking Functionality**: Chat supports dynamic thinking where the model decides when to think before responding
- **Real-time Controls**: ResponseWindow includes dropdowns for model and thinking level selection per conversation
- **Context Awareness**: AI receives current date, model name, and thinking mode in system instructions

### Resource Management
- **PyInstaller Compatibility**: Uses `get_resource_path()` function to locate bundled resources (icons, options.json)
- **Runtime Resource Access**: Handles both development (file system) and compiled (temporary extraction) scenarios
- **Icon System**: Theme-aware icon loading with `_dark.png` and `_light.png` variants

### UI Styling & User Experience
- Simple solid color backgrounds for clean, minimal appearance
- Dark mode optimized styling throughout the interface
- **Enhanced Chat UI**: User messages have blue-tinted backgrounds with borders for clear conversation distinction
- **Larger Windows**: Chat windows open at 900x700px for improved readability
- **Smooth Interactions**: Fixed input focus after AI responses, eliminated window resize jumps
- **Message Display**: Shows user's original text/questions in conversation flow
- Consistent styling through UIUtils across all windows

### System Tray Integration
- **Settings**: Access provider configuration and app preferences
- **Chat History**: View, open, and manage saved conversations
- **Exit**: Clean shutdown of application
- Dark mode menu styling for consistent appearance

## Dependencies

### Core Runtime Dependencies
- **PySide6** - Qt GUI framework (main UI toolkit)
- **pynput** - Global hotkey detection and keyboard simulation
- **pyperclip** - Clipboard operations for text capture/replacement
- **markdown2** - Markdown rendering in response windows

### AI Provider Dependencies
- **google-genai** - Modern Gemini API client with thinking support

### Build Dependencies
- **pyinstaller** - Executable creation

## Localization

This version is English-only with no localization system - all UI text is hardcoded in English for simplicity.

## Platform Considerations

### Windows
- Portable executable deployment with data files stored alongside executable
- System tray integration with enhanced menu options
- Auto-start on boot capability via Windows registry
- **Data Storage**: `config.json` and `saved_chats.json` created in executable directory for portability

