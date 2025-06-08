"""
AI Provider Architecture for Writing Tools
--------------------------------------------

This module handles the Gemini AI provider and manages its interaction with the main application.
It uses an abstract base class pattern for provider implementations.

Key Components:
1. AIProviderSetting – Base class for provider settings (e.g. API keys, model names)
    • TextSetting      – A simple text input for settings
    • DropdownSetting  – A dropdown selection setting

2. AIProvider – Abstract base class that all providers implement.
   It defines the interface for:
      • Getting a response from the AI model
      • Loading and saving configuration settings
      • Cancelling an ongoing request

3. Provider Implementation:
    • GeminiProvider – Uses Google’s Generative AI API (Gemini) to generate content.

Response Flow:
   • The main app calls get_response() with a system instruction and a prompt.
   • The provider formats and sends the request to the Gemini API.
   • For operations that require a window (e.g. Summary, Key Points), the provider returns the full text.
   • For direct text replacement, the provider emits the full text via the output_ready_signal.
   • Conversation history (for follow-up questions) is maintained by the main app.

Note: Streaming has been fully removed throughout the code.
"""

import logging
import webbrowser
from abc import ABC, abstractmethod
from typing import List

# External libraries
from google import genai
from PySide6 import QtWidgets
from PySide6.QtWidgets import QVBoxLayout
from ui.UIUtils import colorMode


class AIProviderSetting(ABC):
    """
    Abstract base class for a provider setting (e.g., API key, model selection).
    """
    def __init__(self, name: str, display_name: str = None, default_value: str = None, description: str = None):
        self.name = name
        self.display_name = display_name if display_name else name
        self.default_value = default_value if default_value else ""
        self.description = description if description else ""

    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout):
        """Render the setting widget(s) into the provided layout."""
        pass

    @abstractmethod
    def set_value(self, value):
        """Set the internal value from configuration."""
        pass

    @abstractmethod
    def get_value(self):
        """Return the current value from the widget."""
        pass


class TextSetting(AIProviderSetting):
    """
    A text-based setting (for API keys, URLs, etc.).
    """
    def __init__(self, name: str, display_name: str = None, default_value: str = None, description: str = None):
        super().__init__(name, display_name, default_value, description)
        self.internal_value = default_value
        self.input = None

    def render_to_layout(self, layout: QVBoxLayout):
        # Label
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet("font-size: 14px; color: #ffffff; margin-bottom: 4px;")
        layout.addWidget(label)
        
        # Input field
        self.input = QtWidgets.QLineEdit(self.internal_value)
        self.input.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #606060;
            border-radius: 4px;
        """)
        self.input.setPlaceholderText(self.description)
        layout.addWidget(self.input)

    def set_value(self, value):
        self.internal_value = value

    def get_value(self):
        return self.input.text()


class DropdownSetting(AIProviderSetting):
    """
    A dropdown setting (e.g., for selecting a model).
    """
    def __init__(self, name: str, display_name: str = None, default_value: str = None,
                 description: str = None, options: list = None):
        super().__init__(name, display_name, default_value, description)
        self.options = options if options else []
        self.internal_value = default_value
        self.dropdown = None

    def render_to_layout(self, layout: QVBoxLayout):
        # Label
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet("font-size: 14px; color: #ffffff; margin-bottom: 4px;")
        layout.addWidget(label)
        
        # Dropdown
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 8px;
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #0078d7;
            }
        """)
        for option, value in self.options:
            self.dropdown.addItem(option, value)
        index = self.dropdown.findData(self.internal_value)
        if index != -1:
            self.dropdown.setCurrentIndex(index)
        layout.addWidget(self.dropdown)

    def set_value(self, value):
        self.internal_value = value

    def get_value(self):
        return self.dropdown.currentData()


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All providers must implement:
      • get_response(system_instruction, prompt) -> str
      • after_load() to create their client or model instance
      • before_load() to cleanup any existing client
      • cancel() to cancel an ongoing request
    """
    def __init__(self, app, provider_name: str, settings: List[AIProviderSetting],
                 description: str = "An unfinished AI provider!",
                 logo: str = "generic",
                 button_text: str = "Go to URL",
                 button_action: callable = None):
        self.provider_name = provider_name
        self.settings = settings
        self.app = app
        self.description = description if description else "An unfinished AI provider!"
        self.logo = logo
        self.button_text = button_text
        self.button_action = button_action

    @abstractmethod
    def get_response(self, system_instruction: str, prompt: str) -> str:
        """
        Send the given system instruction and prompt to the AI provider and return the full response text.
        """
        pass

    def load_config(self, config: dict):
        """
        Load configuration settings into the provider.
        """
        logging.debug(f"Loading config for provider: {config}")
        for setting in self.settings:
            if setting.name in config:
                setattr(self, setting.name, config[setting.name])
                setting.set_value(config[setting.name])
                logging.debug(f"Set {setting.name} to: {'***' + str(config[setting.name])[-4:] if setting.name == 'api_key' else config[setting.name]}")
            else:
                setattr(self, setting.name, setting.default_value)
                logging.debug(f"Set {setting.name} to default: {setting.default_value}")
        self.after_load()

    def save_config(self):
        """
        Save provider configuration settings into the main config file.
        """
        config = {}
        for setting in self.settings:
            config[setting.name] = setting.get_value()
        self.app.config["providers"][self.provider_name] = config
        self.app.save_config(self.app.config)

    @abstractmethod
    def after_load(self):
        """
        Called after configuration is loaded; create your API client here.
        """
        pass

    @abstractmethod
    def before_load(self):
        """
        Called before reloading configuration; cleanup your API client here.
        """
        pass

    @abstractmethod
    def cancel(self):
        """
        Cancel any ongoing API request.
        """
        pass


class GeminiProvider(AIProvider):
    """
    Provider for Google's Gemini API.
    
    Uses the new google.genai.Client.models.generate_content() to generate text.
    """
    def __init__(self, app):
        self.close_requested = False
        self.client = None

        settings = [
            TextSetting(name="api_key", display_name="API Key", description="Paste your Gemini API key here"),
            DropdownSetting(
                name="model_name",
                display_name="Model",
                default_value="gemini-2.5-flash-preview-05-20",
                description="Select Gemini model to use",
                options=[
                    ("Gemini 2.0 Flash Lite (intelligent | very fast | 30 uses/min)", "gemini-2.0-flash-lite-preview-02-05"),
                    ("Gemini 2.0 Flash (very intelligent | fast | 15 uses/min)", "gemini-2.0-flash"),
                    ("Gemini 2.0 Flash Thinking (most intelligent | slow | 10 uses/min)", "gemini-2.0-flash-thinking-exp-01-21"),
                    ("Gemini 2.5 Flash (most intelligent | fast | 10 uses/min)", "gemini-2.5-flash-preview-05-20"),
                ]
            )
        ]
        super().__init__(app, "Gemini", settings,
            "• Google’s Gemini is a powerful AI model available for free!\n"
            "• An API key is required to connect to Gemini on your behalf.\n"
            "• Click the button below to get your API key.",
            "gemini",
            "Get API Key",
            lambda: webbrowser.open("https://aistudio.google.com/app/apikey"))

    def get_response(self, system_instruction: str, prompt: str, return_response: bool = False) -> str:
        """
        Generate content using Gemini.
        
        Always performs a single-shot request with streaming disabled.
        Returns the full response text if return_response is True,
        otherwise emits the text via the output_ready_signal.
        """
        logging.debug(f"Getting response - API key available: {hasattr(self, 'api_key') and bool(self.api_key)}")
        logging.debug(f"Client initialized: {self.client is not None}")
        
        self.close_requested = False

        try:
            # Debug logging
            logging.debug(f"Making API call with model: {self.model_name}")
            logging.debug(f"System instruction length: {len(system_instruction)}")
            logging.debug(f"Prompt length: {len(prompt)}")
            
            # Single-shot call using new Google genai client
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=f"{system_instruction}\n\n{prompt}"
            )
            
            logging.debug("API call completed successfully")
            response_text = response.text.rstrip('\n')
            if not return_response and not hasattr(self.app, 'current_response_window'):
                self.app.output_ready_signal.emit(response_text)
                self.app.replace_text(True)
                return ""
            return response_text
        except Exception as e:
            # Log the full error for debugging
            logging.error(f"Full Gemini API exception: {type(e).__name__}: {str(e)}")
            if hasattr(e, 'response'):
                logging.error(f"Response object: {e.response}")
            
            # Check for common error types and provide helpful messages
            error_str = str(e)
            if "quota" in error_str.lower() or "rate" in error_str.lower():
                error_msg = "Rate limit exceeded. Please wait a moment and try again."
            elif "safety" in error_str.lower() or "blocked" in error_str.lower():
                error_msg = "Content was blocked by safety filters. Try rephrasing your request."
            elif "not found" in error_str.lower() or "invalid" in error_str.lower():
                error_msg = f"Model error. Please check your configuration. Details: {error_str}"
            elif "authentication" in error_str.lower() or "api key" in error_str.lower():
                error_msg = "Authentication failed. Please check your API key in settings."
            else:
                error_msg = f"Gemini API Error: {error_str}"
            
            logging.error(f"Processed error message: {error_msg}")
            self.app.output_ready_signal.emit(error_msg)
        finally:
            self.close_requested = False

        return ""

    def after_load(self):
        """
        Configure the Google genai client.
        """
        logging.debug(f"Configuring Gemini with API key: {'***' + str(getattr(self, 'api_key', 'NOT SET'))[-4:] if hasattr(self, 'api_key') and self.api_key else 'NOT SET'}")
        
        if not hasattr(self, 'api_key') or not self.api_key:
            logging.error("No API key found in Gemini provider")
            return
            
        self.client = genai.Client(api_key=self.api_key)

    def before_load(self):
        self.client = None

    def cancel(self):
        self.close_requested = True

