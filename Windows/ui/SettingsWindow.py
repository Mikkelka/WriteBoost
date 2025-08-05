from aiprovider import AIProvider
from PySide6 import QtCore, QtWidgets

from ui.UIUtils import UIUtils


class SettingsWindow(QtWidgets.QWidget):
    """
    The settings window for the application.
    Now with scrolling support for better usability on smaller screens.
    """

    close_signal = QtCore.Signal()

    def __init__(self, app, providers_only=False):
        super().__init__()
        self.app = app
        self.current_provider_layout = None
        self.providers_only = providers_only
        self.gradient_radio = None
        self.plain_radio = None
        self.provider_container = None
        self.autostart_checkbox = None
        self.shortcut_input = None
        self.init_ui()
        self.retranslate_ui()

    def retranslate_ui(self):
        self.setWindowTitle("Settings")

    def init_provider_ui(self, provider: AIProvider, layout):
        """
        Initialize the user interface for the provider with compact dark styling.
        """
        if self.current_provider_layout:
            self.current_provider_layout.setParent(None)
            UIUtils.clear_layout(self.current_provider_layout)
            self.current_provider_layout.deleteLater()

        self.current_provider_layout = QtWidgets.QVBoxLayout()
        self.current_provider_layout.setSpacing(8)

        # Simple API key button
        if provider.button_text:
            button = QtWidgets.QPushButton(provider.button_text)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d7;
                    color: white;
                    padding: 8px 16px;
                    font-size: 12px;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
            button.clicked.connect(provider.button_action)
            self.current_provider_layout.addWidget(button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Initialize config if needed
        if "providers" not in self.app.config:
            self.app.config["providers"] = {}
        if provider.provider_name not in self.app.config["providers"]:
            self.app.config["providers"][provider.provider_name] = {}

        # Add provider settings
        for setting in provider.settings:
            setting.set_value(
                self.app.config["providers"][provider.provider_name].get(setting.name, setting.default_value)
            )
            setting.render_to_layout(self.current_provider_layout)

        layout.addLayout(self.current_provider_layout)

    def init_ui(self):
        """
        Initialize the user interface for the settings window.
        Compact dark design focused on essentials.
        """
        self.setWindowTitle("Settings")
        # Smaller, more compact window
        self.setMinimumWidth(450)
        self.setFixedWidth(450)

        # Dark background
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
        """)

        # Set up the main layout without UIUtils background
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        if not self.providers_only:
            title_label = QtWidgets.QLabel("Settings")
            title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 10px;")
            main_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

            # Add shortcut key input
            shortcut_label = QtWidgets.QLabel("Shortcut Key:")
            shortcut_label.setStyleSheet("font-size: 14px; color: #ffffff; margin-top: 10px;")
            main_layout.addWidget(shortcut_label)

            self.shortcut_input = QtWidgets.QLineEdit(self.app.config.get("shortcut", "ctrl+space"))
            self.shortcut_input.setStyleSheet("""
                font-size: 14px;
                padding: 8px;
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #606060;
                border-radius: 4px;
            """)
            main_layout.addWidget(self.shortcut_input)

        # Separator line
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setStyleSheet("color: #505050;")
        main_layout.addWidget(separator)

        # AI Provider section
        provider_label = QtWidgets.QLabel("Gemini AI")
        provider_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; margin-top: 10px;")
        main_layout.addWidget(provider_label)

        # Create container for provider UI
        self.provider_container = QtWidgets.QVBoxLayout()
        main_layout.addLayout(self.provider_container)

        # Initialize Gemini provider UI
        provider_instance = self.app.providers[0]  # Only Gemini provider
        self.init_provider_ui(provider_instance, self.provider_container)

        # Save button
        save_button = QtWidgets.QPushButton("Finish AI Setup" if self.providers_only else "Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_button.clicked.connect(self.save_settings)
        main_layout.addWidget(save_button)

        if not self.providers_only:
            restart_notice = QtWidgets.QLabel("Restart required for changes to take effect")
            restart_notice.setStyleSheet("font-size: 12px; color: #999999; margin-top: 8px;")
            restart_notice.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(restart_notice)

        # Compact window size
        self.resize(450, 380)

    def save_settings(self):
        """Save the current settings."""
        self.app.config["locale"] = "en"

        if not self.providers_only:
            self.app.config["shortcut"] = self.shortcut_input.text()
            self.app.config["theme"] = "plain"  # Force dark theme
        else:
            self.app.create_tray_icon()

        self.app.config["streaming"] = False
        self.app.config["provider"] = "Gemini"

        self.app.providers[0].save_config()  # Only Gemini provider

        self.app.current_provider = self.app.providers[0]  # Only Gemini provider

        self.app.current_provider.load_config(self.app.config.get("providers", {}).get("Gemini", {}))

        self.app.register_hotkey()
        self.providers_only = False
        self.close()

    def closeEvent(self, event):
        """Handle window close event."""
        if self.providers_only:
            self.close_signal.emit()
        super().closeEvent(event)
