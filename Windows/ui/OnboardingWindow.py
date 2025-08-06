import logging

from PySide6 import QtCore, QtWidgets

from ui.UIUtils import UIUtils, colorMode

_ = lambda x: x


class OnboardingWindow(QtWidgets.QWidget):
    # Closing signal
    close_signal = QtCore.Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.shortcut = "ctrl+space"
        self.content_layout = None
        self.shortcut_input = None
        self.init_ui()
        self.self_close = False

    def init_ui(self):
        logging.debug("Initializing onboarding UI")
        self.setWindowTitle(_("Welcome to Writing Tools"))
        self.resize(600, 500)

        UIUtils.setup_window_and_layout(self)

        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        self.background.setLayout(self.content_layout)

        self.show_welcome_screen()

    def show_welcome_screen(self):
        UIUtils.clear_layout(self.content_layout)

        title_label = QtWidgets.QLabel(_("Welcome to Writing Tools") + "!")
        title_label.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {'#ffffff' if colorMode == 'dark' else '#333333'};"
        )
        self.content_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        features_text = f"""
        • {_('Instantly optimize your writing with AI by selecting your text and invoking Writing Tools with "ctrl+space", anywhere.')} 

        • {_('Get a summary you can chat with of articles, YouTube videos, or documents by select all text with "ctrl+a"')}
          {_("(or select the YouTube transcript from its description), invoking Writing Tools, and choosing Summary.")}

        • {_("Chat with AI anytime by invoking Writing Tools without selecting any text.")}

        • {_("Powered by Google Gemini AI")}
        """
        features_label = QtWidgets.QLabel(features_text)
        features_label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};")
        features_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        self.content_layout.addWidget(features_label)

        shortcut_label = QtWidgets.QLabel('Customize your shortcut key (default: "ctrl+space"):')
        shortcut_label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};")
        self.content_layout.addWidget(shortcut_label)

        self.shortcut_input = QtWidgets.QLineEdit(self.shortcut)
        self.shortcut_input.setStyleSheet(f"""
            font-size: 16px;
            padding: 5px;
            background-color: {"#444" if colorMode == "dark" else "white"};
            color: {"#ffffff" if colorMode == "dark" else "#000000"};
            border: 1px solid {"#666" if colorMode == "dark" else "#ccc"};
        """)
        self.content_layout.addWidget(self.shortcut_input)

        next_button = QtWidgets.QPushButton(_("Next"))
        next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        next_button.clicked.connect(self.on_next_clicked)
        self.content_layout.addWidget(next_button)

    def on_next_clicked(self):
        try:
            self.shortcut = self.shortcut_input.text()
            logging.debug(f"User selected shortcut: {self.shortcut}")
            # Initialize config with shortcut and save it
            self.app.config = {"shortcut": self.shortcut}
            logging.debug("About to save config...")
            self.app.save_config(self.app.config)
            logging.debug("Config saved, showing API key input...")
            self.show_api_key_input()
        except Exception as e:
            logging.error(f"Error in on_next_clicked: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            # Continue anyway
            self.show_api_key_input()

    def show_api_key_input(self):
        self.app.show_settings(providers_only=True)
        self.self_close = True
        self.close()

    def closeEvent(self, event):
        # Emit the close signal
        if not self.self_close:
            self.close_signal.emit()
        super().closeEvent(event)
