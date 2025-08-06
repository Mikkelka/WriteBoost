"""
Provider Interface Definitions for Writing Tools
----------------------------------------------

This module contains the abstract base classes and interfaces for AI providers.
It defines the contract that all providers must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import List

from PySide6.QtWidgets import QVBoxLayout


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


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All providers must implement:
      • get_response(system_instruction, prompt) -> str
      • after_load() to create their client or model instance
      • before_load() to cleanup any existing client
      • cancel() to cancel an ongoing request
    """

    def __init__(
        self,
        app,
        provider_name: str,
        settings: List[AIProviderSetting],
        description: str = "An unfinished AI provider!",
        logo: str = "generic",
        button_text: str = "Go to URL",
        button_action: callable = None,
    ):
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
                logging.debug(
                    f"Set {setting.name} to: {'***' + str(config[setting.name])[-4:] if setting.name == 'api_key' else config[setting.name]}"
                )
            else:
                setattr(self, setting.name, setting.default_value)

        self.after_load()

    def save_config(self):
        """
        Save provider configuration settings into the main config file.
        """
        try:
            logging.debug(f"=== Provider {self.provider_name} save_config starting ===")
            
            config = {}
            for setting in self.settings:
                try:
                    value = setting.get_value()
                    config[setting.name] = value
                    logging.debug(f"Setting {setting.name} = {value}")
                except Exception as e:
                    logging.error(f"Error getting value for setting {setting.name}: {e}")
                    raise
            
            logging.debug(f"Provider config collected: {config}")
            
            # Ensure providers section exists in app config
            if self.app.config is None:
                logging.warning("App config was None, initializing...")
                self.app.config = {}
            
            if "providers" not in self.app.config:
                logging.debug("Creating providers section in app config")
                self.app.config["providers"] = {}
                
            self.app.config["providers"][self.provider_name] = config
            logging.debug(f"Added provider config to app config: {self.app.config}")
            
            logging.debug("About to call app.save_config...")
            self.app.save_config(self.app.config)
            logging.debug("=== Provider save_config completed successfully ===")
            
        except Exception as e:
            logging.error(f"ERROR in provider save_config: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    @abstractmethod
    def after_load(self):
        """
        Called after configuration has been loaded.
        Providers should use this to initialize their client/model.
        """
        pass

    @abstractmethod
    def before_load(self):
        """
        Called before configuration is loaded.
        Providers should use this to cleanup existing clients.
        """
        pass

    @abstractmethod
    def get_settings_ui(self, parent) -> QVBoxLayout:
        """
        Return a layout containing the provider's settings UI.
        """
        pass

    @abstractmethod
    def save_settings(self, layout: QVBoxLayout):
        """
        Save settings from the UI back to the provider configuration.
        """
        pass

    @abstractmethod
    def cancel(self):
        """
        Cancel any ongoing requests.
        """
        pass