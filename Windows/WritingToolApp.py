import json
import logging
import os
import signal
import sys
import time

from aiprovider import GeminiProvider
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QMessageBox
import ui.CustomPopupWindow
import ui.OnboardingWindow
import ui.ResponseWindow
import ui.SettingsWindow
import ui.ButtonEditWindow
import ui.ChatHistoryWindow

from TextOperationsManager import TextOperationsManager
from HotkeyManager import HotkeyManager
from ConfigManager import ConfigManager
from ConversationManager import ConversationManager
from ui.UIUtils import get_resource_path




class WritingToolApp(QtWidgets.QApplication):
    """
    The main application class for Writing Tools.
    """

    show_message_signal = Signal(str, str)  # a signal for showing message boxes

    def __init__(self, argv):
        super().__init__(argv)
        self.current_response_window = None
        logging.debug("Initializing WritingToolApp")
        self.show_message_signal.connect(self.show_message_box)
        
        # Initialize managers
        self.config_manager = ConfigManager(self)
        self.text_operations_manager = TextOperationsManager(self)
        self.hotkey_manager = HotkeyManager(self)
        self.conversation_manager = ConversationManager(self)
        
        # Connect signals between managers
        self.conversation_manager.followup_response_signal.connect(self.handle_followup_response)
        self.conversation_manager.show_message_signal.connect(self.show_message_box)
        
        # Load configuration and options using manager
        self.config_manager.load_config()
        self.config_manager.load_options()
        
        # Set references for backward compatibility
        self.config = self.config_manager.config
        self.options = self.config_manager.options
        self.config_path = self.config_manager.config_path
        self.options_path = self.config_manager.options_path
        self.onboarding_window = None
        self.tray_icon = None
        self.tray_menu = None
        self.settings_window = None
        self.button_edit_window = None
        self.last_replace = 0

        # Initialize the ctrl+c hotkey listener
        self.ctrl_c_timer = None
        self.setup_ctrl_c_listener()

        # Setup available AI providers
        self.providers = [GeminiProvider(self)]

        if not self.config:
            logging.debug("No config found, showing onboarding")
            self.onboarding_window = self.config_manager.show_onboarding()
        else:
            logging.debug("Config found, setting up hotkey and tray icon")

            # Initialize the current provider, defaulting to Gemini
            provider_name = self.config.get("provider", "Gemini")
            logging.debug(f"Provider name from config: {provider_name}")

            self.current_provider = next(
                (provider for provider in self.providers if provider.provider_name == provider_name), None
            )
            if not self.current_provider:
                logging.warning(f"Provider {provider_name} not found. Using default provider.")
                self.current_provider = self.providers[0]

            provider_config = self.config.get("providers", {}).get(provider_name, {})
            logging.debug(f"Loading provider config: {provider_config}")
            self.current_provider.load_config(provider_config)

            self.create_tray_icon()
            self.hotkey_manager.register_hotkey()

        self.recent_triggers = []  # Track recent hotkey triggers
        self.TRIGGER_WINDOW = 1.5  # Time window in seconds
        self.MAX_TRIGGERS = 3  # Max allowed triggers in window

    def check_trigger_spam(self):
        """
        Check if hotkey is being triggered too frequently (3+ times in 1.5 seconds).
        Returns True if spam is detected.
        """
        current_time = time.time()

        # Add current trigger
        self.recent_triggers.append(current_time)

        # Remove old triggers outside the window
        self.recent_triggers = [t for t in self.recent_triggers if current_time - t <= self.TRIGGER_WINDOW]

        # Check if we have too many triggers in the window
        return len(self.recent_triggers) >= self.MAX_TRIGGERS

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
        try:
            # Ensure config_path is set
            if not hasattr(self, 'config_path') or not self.config_path:
                self.config_path = os.path.join(os.path.dirname(sys.argv[0]), "config.json")
                logging.debug(f"Set config_path to: {self.config_path}")
                
            logging.debug(f"Saving config to: {self.config_path}")
            logging.debug(f"Config content: {config}")
            
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
                logging.debug("Config saved successfully")
            self.config = config
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            raise

    def show_onboarding(self):
        """
        Show the onboarding window for first-time users.
        """
        logging.debug("Showing onboarding window")
        self.onboarding_window = ui.OnboardingWindow.OnboardingWindow(self)
        self.onboarding_window.close_signal.connect(self.exit_app)
        self.onboarding_window.show()

    def start_hotkey_listener(self):
        """
        Create listener for global hotkeys.
        """
        orig_shortcut = self.config.get("shortcut", "ctrl+space")
        # Parse the shortcut string, for example ctrl+alt+h -> <ctrl>+<alt>+h
        shortcut = "+".join([f"{t}" if len(t) <= 1 else f"<{t}>" for t in orig_shortcut.split("+")])
        logging.debug(f"Registering global hotkey for shortcut: {shortcut}")
        try:
            if self.hotkey_listener is not None:
                self.hotkey_listener.stop()

            def on_activate():
                logging.debug("triggered hotkey")
                self.hotkey_triggered_signal.emit()  # Emit the signal when hotkey is pressed

            # Define the hotkey combination
            hotkey = pykeyboard.HotKey(pykeyboard.HotKey.parse(shortcut), on_activate)
            self.registered_hotkey = orig_shortcut

            # Helper function to standardize key event
            def for_canonical(f):
                return lambda k: f(self.hotkey_listener.canonical(k))

            # Create a listener and store it as an attribute to stop it later
            self.hotkey_listener = pykeyboard.Listener(
                on_press=for_canonical(hotkey.press), on_release=for_canonical(hotkey.release)
            )

            # Start the listener
            self.hotkey_listener.start()
        except Exception as e:
            logging.error(f"Failed to register hotkey: {e}")

    def register_hotkey(self):
        """
        Register the global hotkey for activating Writing Tools.
        """
        logging.debug("Registering hotkey")
        self.start_hotkey_listener()
        logging.debug("Hotkey registered")

    def on_hotkey_pressed(self):
        """
        Handle the hotkey press event.
        """
        logging.debug("Hotkey pressed")

        # Check for spam triggers
        if self.check_trigger_spam():
            logging.warning("Hotkey spam detected - quitting application")
            self.exit_app()
            return

        # Original hotkey handling continues...
        if self.current_provider:
            logging.debug("Cancelling current provider's request")
            self.current_provider.cancel()
            self.output_queue = ""

        # noinspection PyTypeChecker
        QtCore.QMetaObject.invokeMethod(self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection)

    @Slot()
    def _show_popup(self):
        """
        Show the popup window when the hotkey is pressed.
        """
        logging.debug("Showing popup window")
        # First attempt with default sleep
        selected_text = self.text_operations_manager.get_selected_text()

        # Retry with more attempts if no text captured
        if not selected_text:
            logging.debug("No text captured, retrying with more attempts")
            selected_text = self.text_operations_manager.get_selected_text(max_retries=3)

        logging.debug(f'Selected text: "{selected_text}"')
        try:
            # Check if we have any meaningful text
            if not selected_text.strip():
                logging.debug("No text selected, opening chat window directly")
                # Open ResponseWindow directly for chat
                response_window = ui.ResponseWindow.ResponseWindow(self, "Chat", None)
                response_window.show()
                return

            if self.popup_window is not None:
                logging.debug("Existing popup window found")
                if self.popup_window.isVisible():
                    logging.debug("Closing existing visible popup window")
                    self.popup_window.close()
                self.popup_window = None
            logging.debug("Creating new popup window")
            self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(self, selected_text)

            # Set the window icon
            icon_path = get_resource_path(os.path.join("icons", "app_icon.png"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
            # Get the screen containing the cursor
            cursor_pos = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor_pos)
            if screen is None:
                screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.geometry()
            logging.debug(f"Cursor is on screen: {screen.name()}")
            logging.debug(f"Screen geometry: {screen_geometry}")
            # Show the popup to get its size
            self.popup_window.show()
            self.popup_window.adjustSize()
            # Ensure the popup it's focused, even on lower-end machines
            self.popup_window.activateWindow()
            QtCore.QTimer.singleShot(100, self.popup_window.custom_input.setFocus)

            popup_width = self.popup_window.width()
            popup_height = self.popup_window.height()
            # Calculate position
            x = cursor_pos.x()
            y = cursor_pos.y() + 20  # 20 pixels below cursor
            # Adjust if the popup would go off the right edge of the screen
            if x + popup_width > screen_geometry.right():
                x = screen_geometry.right() - popup_width
            # Adjust if the popup would go off the bottom edge of the screen
            if y + popup_height > screen_geometry.bottom():
                y = cursor_pos.y() - popup_height - 10  # 10 pixels above cursor
            self.popup_window.move(x, y)
            logging.debug(f"Popup window moved to position: ({x}, {y})")
        except Exception as e:
            logging.error(f"Error showing popup window: {e}", exc_info=True)

    def process_option(self, option, selected_text, custom_change=None):
        """
        Process the selected writing option in a separate thread.
        """
        self.text_operations_manager.process_option(option, selected_text, custom_change)


    @Slot(str, str)
    def show_message_box(self, title, message):
        """
        Show a message box with the given title and message.
        """
        QMessageBox.warning(None, title, message)

    def show_response_window(self, option, text):
        """
        Show the response in a new window instead of pasting it.
        """
        response_window = ui.ResponseWindow.ResponseWindow(self, f"{option} Result")
        response_window.selected_text = text  # Store the text for regeneration
        response_window.show()
        return response_window


    def create_tray_icon(self):
        """
        Create the system tray icon for the application.
        """
        if self.tray_icon:
            logging.debug("Tray icon already exists")
            return

        logging.debug("Creating system tray icon")
        icon_path = get_resource_path(os.path.join("icons", "app_icon.png"))
        if not os.path.exists(icon_path):
            logging.warning(f"Tray icon not found at {icon_path}")
            # Use a default icon if not found
            self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        else:
            self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(icon_path), self)
        # Set the tooltip (hover name) for the tray icon
        self.tray_icon.setToolTip("WritingTools")
        self.tray_menu = QtWidgets.QMenu()
        self.tray_icon.setContextMenu(self.tray_menu)

        self.update_tray_menu()
        self.tray_icon.show()
        logging.debug("Tray icon displayed")

    def update_tray_menu(self):
        """
        Update the tray menu with all menu items, including pause functionality
        and proper translations.
        """
        self.tray_menu.clear()

        # Apply dark mode styles using darkdetect
        self.apply_dark_mode_styles(self.tray_menu)

        # Settings menu item
        settings_action = self.tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)

        # Chat History menu item
        chat_history_action = self.tray_menu.addAction("Chat History")
        chat_history_action.triggered.connect(self.show_chat_history)

        # Edit Buttons menu item
        edit_buttons_action = self.tray_menu.addAction("Edit Buttons")
        edit_buttons_action.triggered.connect(self.show_button_edit)

        # Exit menu item
        exit_action = self.tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.exit_app)

    @staticmethod
    def apply_dark_mode_styles(menu):
        """
        Apply dark styles to the tray menu.
        """
        palette = menu.palette()
        # Always use dark mode
        palette.setColor(QtGui.QPalette.Window, QtGui.QColor("#2d2d2d"))  # Dark background
        palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("#ffffff"))  # White text
        menu.setPalette(palette)

    """
    The function below (process_followup_question) processes follow-up questions in the chat interface for Summary, Key Points, and Table operations.

    This method handles the complex interaction between the UI, chat history, and AI providers:

    1. Chat History Management:
    - Maintains a list of all messages (original text, summary, follow-ups)
    - Properly formats roles (user/assistant) for each message
    - Preserves conversation context across multiple questions (until the Window is closed)

    2. Provider-Specific Handling:
    a) Gemini:
        - Converts internal roles to Gemini's user/model format
        - Uses chat sessions with proper history formatting
        - Maintains context through chat.send_message()
    
    b) OpenAI-compatible:
        - Uses standard OpenAI message array format
        - Includes system instruction and full conversation history
        - Properly maps internal roles to OpenAI roles

    3. Flow:
    a) User asks follow-up question
    b) Question is added to chat history
    c) Full history is formatted for the current provider
    d) Response is generated while maintaining context
    e) Response is displayed in chat UI
    f) New response is added to history for future context

    4. Threading:
    - Runs in a separate thread to prevent UI freezing
    - Uses signals to safely update UI from background thread
    - Handles errors too

    Args:
        response_window: The ResponseWindow instance managing the chat UI
        question: The follow-up question from the user

    This implementation manages chat history & model roles for the Gemini provider.
    """

    def process_followup_question(self, response_window, question, model=None, thinking_budget=None):
        """
        Process a follow-up question in the chat window.
        """
        self.conversation_manager.process_followup_question(response_window, question, model, thinking_budget)
    
    @Slot(str)
    def handle_followup_response(self, response_text):
        """Handle followup response from conversation manager"""
        if hasattr(self, 'current_response_window') and self.current_response_window:
            self.current_response_window.handle_followup_response(response_text)

    def show_settings(self, providers_only=False):
        """
        Show the settings window.
        """
        logging.debug("Showing settings window")
        # Always create a new settings window to handle providers_only correctly
        self.settings_window = ui.SettingsWindow.SettingsWindow(self, providers_only=providers_only)
        self.settings_window.close_signal.connect(self.exit_app)
        self.settings_window.retranslate_ui()
        self.settings_window.show()

    def show_chat_history(self):
        """
        Show the chat history window.
        """
        logging.debug("Showing chat history window")
        try:
            import ui.ChatHistoryWindow

            self.chat_history_window = ui.ChatHistoryWindow.ChatHistoryWindow(self)
            self.chat_history_window.close_signal.connect(lambda: setattr(self, "chat_history_window", None))
            self.chat_history_window.show()
        except Exception as e:
            logging.error(f"Error showing chat history window: {e}")
            self.show_message_signal.emit("Error", f"Failed to open chat history: {e}")

    def show_button_edit(self):
        """
        Show the button edit window.
        """
        logging.debug("Showing button edit window")
        try:
            self.button_edit_window = ui.ButtonEditWindow.ButtonEditWindow(self)
            self.button_edit_window.show()
        except Exception as e:
            logging.error(f"Error showing button edit window: {e}")
            self.show_message_signal.emit("Error", f"Failed to open button edit window: {e}")

    def setup_ctrl_c_listener(self):
        """
        Listener for Ctrl+C to exit the app.
        """
        signal.signal(signal.SIGINT, lambda signum, frame: self.handle_sigint(signum, frame))
        # This empty timer is needed to make sure that the sigint handler gets checked inside the main loop:
        # without it, the sigint handle would trigger only when an event is triggered, either by a hotkey combination
        # or by another GUI event like spawning a new window. With this we trigger it every 100ms with an empy lambda
        # so that the signal handler gets checked regularly.
        self.ctrl_c_timer = QtCore.QTimer()
        self.ctrl_c_timer.start(100)
        self.ctrl_c_timer.timeout.connect(lambda: None)

    def handle_sigint(self, signum, frame):
        """
        Handle the SIGINT signal (Ctrl+C) to exit the app gracefully.
        """
        logging.info("Received SIGINT. Exiting...")
        self.exit_app()

    def exit_app(self):
        """
        Exit the application.
        """
        logging.debug("Stopping the listener")
        self.hotkey_manager.stop_hotkey_listener()
        logging.debug("Exiting application")
        self.quit()
