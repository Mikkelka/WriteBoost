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
import os
import webbrowser
import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List

# External libraries
from google import genai
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QVBoxLayout
from ui.UIUtils import colorMode, get_resource_path


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
        
        # Dropdown container
        dropdown_container = QtWidgets.QWidget()
        dropdown_layout = QtWidgets.QHBoxLayout(dropdown_container)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 8px;
                padding-right: 25px;
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
                selection-background-color: #0078d7;
            }
        """)
        
        # Arrow label
        arrow_label = QtWidgets.QLabel("▼")
        arrow_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """)
        arrow_label.setFixedSize(20, 20)
        arrow_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        
        dropdown_layout.addWidget(self.dropdown)
        dropdown_layout.addWidget(arrow_label)
        dropdown_layout.setSpacing(-20)  # Overlap the arrow on the dropdown
        for option, value in self.options:
            self.dropdown.addItem(option, value)
        index = self.dropdown.findData(self.internal_value)
        if index != -1:
            self.dropdown.setCurrentIndex(index)
        layout.addWidget(dropdown_container)

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
    
    Uses direct HTTP calls to the Gemini REST API with connection pooling for optimal performance.
    """
    def __init__(self, app):
        self.close_requested = False
        self.session = None

        settings = [
            TextSetting(name="api_key", display_name="API Key", description="Paste your Gemini API key here"),
            DropdownSetting(
                name="model_name",
                display_name="Model",
                default_value="gemini-2.5-flash-preview-05-20",
                description="Select Gemini model to use",
                options=[
                    ("Gemini 2.0 Flash (very intelligent | fast | 15 uses/min)", "gemini-2.0-flash"),
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

    async def _get_session(self):
        """Get or create an aiohttp session with connection pooling"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=10,  # Connection pool size
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(connector=connector)
        return self.session

    def get_response(self, system_instruction: str, prompt: str, return_response: bool = False) -> str:
        """
        Generate content using Gemini with connection pooling optimization.
        
        Always performs a single-shot request with streaming disabled.
        Returns the full response text if return_response is True,
        otherwise emits the text via the output_ready_signal.
        """
        import concurrent.futures
        import threading
        
        def run_async_in_thread():
            """Run async code in a separate thread with its own event loop"""
            loop = None
            try:
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the async function
                result = loop.run_until_complete(self._get_response_async(system_instruction, prompt, return_response))
                
                # Ensure session is properly closed before loop cleanup
                if self.session and not self.session.closed:
                    loop.run_until_complete(self.session.close())
                    self.session = None
                
                return result
            except Exception as e:
                # Clean up session on error
                if self.session and not self.session.closed:
                    try:
                        if loop and not loop.is_closed():
                            loop.run_until_complete(self.session.close())
                        self.session = None
                    except:
                        pass
                raise e
            finally:
                # Clean up event loop only after everything else is done
                if loop and not loop.is_closed():
                    try:
                        # Give loop time to finish cleanup
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.close()
                    except:
                        pass
        
        # Execute async code in a separate thread to avoid Qt event loop conflicts
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_async_in_thread)
            try:
                # Wait for result with timeout
                result = future.result(timeout=30)  # 30 second timeout
                return result
            except concurrent.futures.TimeoutError:
                logging.error("Request timed out after 30 seconds")
                self.app.output_ready_signal.emit("Request timed out. Please try again.")
                return ""
            except Exception as e:
                logging.error(f"Thread execution error: {e}")
                raise e

    async def _get_response_async(self, system_instruction: str, prompt: str, return_response: bool = False) -> str:
        """
        Async implementation of get_response with connection pooling.
        """
        logging.debug(f"Getting response - API key available: {hasattr(self, 'api_key') and bool(self.api_key)}")
        
        self.close_requested = False

        try:
            # Ensure we have a connection pool session
            session = await self._get_session()
            logging.debug(f"Connection pooling: Session active with {session.connector.limit} max connections")
            
            # Debug logging
            logging.debug(f"Making API call with model: {self.model_name}")
            logging.debug(f"System instruction length: {len(system_instruction)}")
            logging.debug(f"Prompt length: {len(prompt)}")
            
            # Direct HTTP call to Gemini REST API using connection pooling
            # Use v1beta for newer models like Gemini 2.5
            api_version = "v1beta" if "2.5" in self.model_name or "2.0" in self.model_name else "v1"
            url = f"https://generativelanguage.googleapis.com/{api_version}/models/{self.model_name}:generateContent"
            
            # Request payload following Gemini API format
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_instruction}\n\n{prompt}"}
                        ]
                    }
                ]
            }
            
            # HTTP headers
            headers = {
                "Content-Type": "application/json"
            }
            
            # API call using connection pooled session with timeout
            timeout = aiohttp.ClientTimeout(total=25)  # 25 second HTTP timeout
            async with session.post(
                url, 
                json=payload, 
                headers=headers,
                params={"key": self.api_key},
                timeout=timeout
            ) as http_response:
                if http_response.status == 200:
                    response_data = await http_response.json()
                    response_text = response_data["candidates"][0]["content"]["parts"][0]["text"].rstrip('\n')
                    logging.debug("API call completed successfully")
                    
                    if not return_response and not hasattr(self.app, 'current_response_window'):
                        self.app.output_ready_signal.emit(response_text)
                        self.app.replace_text(True)
                        return ""
                    return response_text
                else:
                    # Handle HTTP error status codes
                    error_data = await http_response.json()
                    error_message = error_data.get("error", {}).get("message", f"HTTP {http_response.status}")
                    raise Exception(error_message)
        except (asyncio.TimeoutError, aiohttp.ServerTimeoutError) as e:
            # Handle timeout errors from aiohttp and asyncio
            logging.error(f"HTTP timeout error: {type(e).__name__}: {str(e)}")
            error_msg = "Request timed out. The AI service is taking too long to respond. Please try again."
            logging.error(f"Processed error message: {error_msg}")
            self.app.output_ready_signal.emit(error_msg)
        except aiohttp.ClientError as e:
            # Handle aiohttp connection errors
            logging.error(f"HTTP connection error: {type(e).__name__}: {str(e)}")
            error_msg = "Connection error. Please check your internet connection and try again."
            logging.error(f"Processed error message: {error_msg}")
            self.app.output_ready_signal.emit(error_msg)
            # Reset session on connection errors
            if self.session:
                try:
                    await self.session.close()
                except:
                    pass
                self.session = None
        except Exception as e:
            # Log the full error for debugging
            logging.error(f"Full Gemini API exception: {type(e).__name__}: {str(e)}")
            
            # Check for common error types and provide helpful messages
            error_str = str(e)
            if "timeout" in error_str.lower() or "time out" in error_str.lower():
                error_msg = "Request timed out. Please try again."
            elif "safety" in error_str.lower() or "blocked" in error_str.lower():
                error_msg = "Content was blocked by safety filters. Try rephrasing your request."
            elif "not found" in error_str.lower() or "invalid" in error_str.lower() or "400" in error_str:
                error_msg = f"Model error: {error_str}"
            elif "authentication" in error_str.lower() or "api key" in error_str.lower() or "401" in error_str or "403" in error_str:
                error_msg = "Authentication failed. Please check your API key in settings."
            elif "HTTP 5" in error_str:
                error_msg = "Gemini service temporarily unavailable. Please try again in a moment."
            else:
                # Show the actual error instead of hiding it behind generic messages
                error_msg = f"Gemini API Error: {error_str}"
            
            logging.error(f"Processed error message: {error_msg}")
            self.app.output_ready_signal.emit(error_msg)
        finally:
            self.close_requested = False

        return ""

    def after_load(self):
        """
        Validate configuration for direct HTTP API calls.
        """
        logging.debug(f"Configuring Gemini with API key: {'***' + str(getattr(self, 'api_key', 'NOT SET'))[-4:] if hasattr(self, 'api_key') and self.api_key else 'NOT SET'}")
        
        if not hasattr(self, 'api_key') or not self.api_key:
            logging.error("No API key found in Gemini provider")
            return
            
        logging.debug("Gemini provider configured for connection pooled HTTP requests")

    def before_load(self):
        """
        Clean up aiohttp session before reloading configuration.
        """
        if self.session:
            # Close the aiohttp session properly
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.session.close())
            except RuntimeError:
                pass
            self.session = None

    def cancel(self):
        self.close_requested = True

