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
# or
cd Windows; python pyinstaller-build-script.py
```

The spec file creates a single-file executable with optimized exclusions and proper resource bundling.


## Architecture Overview

### Core Application Structure
- **Entry Point**: `Windows/main.py` - Simple launcher that starts the Qt application
- **Main Application**: `Windows/WritingToolApp.py` - Streamlined QApplication orchestrator (506 lines, down from 752)
- **Manager Architecture**: Modular managers handle specific responsibilities:
  - `TextOperationsManager.py` - Text capture, processing, and replacement operations
  - `HotkeyManager.py` - Global hotkey registration and detection
  - `ConfigManager.py` - Configuration and options loading/saving
  - `ConversationManager.py` - Follow-up questions and chat conversations
- **AI Provider System**: Modular provider architecture:
  - `aiprovider.py` - Main entry point maintaining backward compatibility
  - `ProviderInterfaces.py` - Abstract base classes for AI providers
  - `ProviderUI.py` - UI components for provider settings
  - `GeminiProvider.py` - Google Gemini API implementation

### UI Architecture
The UI is highly modular with focused components in `Windows/ui/`:

#### Main Windows
- `CustomPopupWindow.py` - Main command selection popup (appears on hotkey when text is selected)
- `ResponseWindow.py` - Main chat window orchestrator (557 lines, down from 888)
- `SettingsWindow.py` - Provider configuration with separate chat and text operation model settings
- `OnboardingWindow.py` - Simplified first-time setup (hotkey configuration and Gemini API key)
- `ChatHistoryWindow.py` - Window for viewing, opening, and managing saved chat conversations

#### ResponseWindow Components (Refactored)
- `MarkdownDisplay.py` - Enhanced text browser for displaying Markdown with zoom controls
- `ChatScrollArea.py` - Scrollable container for chat messages with dynamic sizing
- `ChatMessageManager.py` - Message handling logic and chat history operations

#### Button Editing System (Refactored)
- `ButtonEditWindow.py` - Main button editing interface (459 lines, down from 733)
- `ButtonEditDialog.py` - Dialog for creating/editing individual buttons
- `DraggableButton.py` - Draggable button component with context menus

#### Utilities
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

### AI Provider Architecture (Refactored)
The AI provider system has been modularized for better organization:

#### Core Interfaces (`ProviderInterfaces.py`)
```python
class AIProvider(ABC):
    @abstractmethod
    def get_response(self, system_instruction: str, prompt: str, return_response: bool = False, 
                    model: str = None, thinking_budget: int = None) -> str
    
    @abstractmethod  
    def get_settings_ui(self, parent) -> QWidget
    
    @abstractmethod
    def save_settings(self, widget: QWidget)

class AIProviderSetting(ABC):
    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout)
```

#### UI Components (`ProviderUI.py`)
- `TextSetting` - Text input fields for API keys, system instructions
- `DropdownSetting` - Dropdown selections for model choices

#### Implementation (`GeminiProvider.py`)
- `GeminiProvider` - Google's Gemini API integration using the new `genai.Client()` approach with thinking functionality (supports Gemini 2.5 Flash and 2.5 Flash Lite models)

#### Backward Compatibility (`aiprovider.py`)
- Imports and re-exports all components to maintain existing code compatibility

### Text Processing Pipeline (Manager-Based)
1. **Text Selection**: `TextOperationsManager` captures text via clipboard operations for universal compatibility
2. **Hotkey Detection**: `HotkeyManager` handles global hotkey registration and triggers popup display
3. **Command Selection**: `CustomPopupWindow` displays available operations (if text selected) or opens chat directly (if no text)
4. **AI Processing**: `TextOperationsManager` handles threaded execution preventing UI freezing via Gemini API with automatic model selection
5. **Result Handling**: Direct text replacement or ResponseWindow display based on operation type
6. **Follow-up Conversations**: `ConversationManager` handles chat continuations and thinking functionality

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

## Refactoring Summary

### Code Organization Improvements
Major refactoring completed to improve maintainability and organization:

- **ResponseWindow.py**: 888 → 557 lines (-37%), split into 4 focused components
- **WritingToolApp.py**: 752 → 506 lines (-33%), extracted 4 manager classes
- **ButtonEditWindow.py**: 733 → 459 lines (-37%), split into 3 UI components
- **aiprovider.py**: 460 → 27 lines (-94%), modularized into 3 specialized files

**Total**: From 4 monolithic files (2,833 lines) to 19 focused modules with improved separation of concerns.

### Architecture Benefits
- **Manager Pattern**: Clear separation of responsibilities across TextOperations, Hotkey, Config, and Conversation managers
- **Component-Based UI**: ResponseWindow and ButtonEdit systems broken into reusable components
- **Modular Providers**: AI provider system supports extensibility while maintaining backward compatibility
- **Maintained Functionality**: All existing features preserved with improved code organization

## Platform Considerations

### Windows
- Portable executable deployment with data files stored alongside executable
- System tray integration with enhanced menu options
- Auto-start on boot capability via Windows registry
- **Data Storage**: `config.json` and `saved_chats.json` created in executable directory for portability

