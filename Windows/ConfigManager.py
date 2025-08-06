import json
import logging
import os
import sys

import ui.OnboardingWindow
from ui.UIUtils import get_resource_path




class ConfigManager:
    """Handles configuration and options loading/saving"""

    def __init__(self, app):
        self.app = app
        self.config = None
        self.options = None
        self.config_path = None
        self.options_path = None

    def load_config(self):
        """
        Load the configuration file.
        """
        self.config_path = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
        logging.debug(f"Loading config from {self.config_path}")
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path) as f:
                    content = f.read().strip()
                    if content:
                        self.config = json.loads(content)
                        logging.debug("Config loaded successfully")
                    else:
                        logging.debug("Config file is empty")
                        self.config = None
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Config file is corrupted or unreadable: {e}")
                self.config = None
        else:
            logging.debug("Config file not found")
            self.config = None

    def load_options(self):
        """
        Load the options file.
        """
        self.options_path = get_resource_path("options.json")
        logging.debug(f"Loading options from {self.options_path}")
        if os.path.exists(self.options_path):
            with open(self.options_path) as f:
                self.options = json.load(f)
                logging.debug("Options loaded successfully")
        else:
            logging.debug("Options file not found")
            self.options = None

    def save_config(self, config):
        """
        Save the configuration file.
        """
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=4)
            logging.debug("Config saved successfully")
        self.config = config

    def show_onboarding(self):
        """
        Show the onboarding window for first-time users.
        """
        logging.debug("Showing onboarding window")
        onboarding_window = ui.OnboardingWindow.OnboardingWindow(self.app)
        onboarding_window.close_signal.connect(self.app.exit_app)
        onboarding_window.show()
        return onboarding_window