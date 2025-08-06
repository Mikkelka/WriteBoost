import logging
import os

from pynput import keyboard as pykeyboard
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Signal, Slot, QObject

import ui.CustomPopupWindow
import ui.ResponseWindow
from ui.UIUtils import get_resource_path




class HotkeyManager(QObject):
    """Handles global hotkey registration and detection"""
    
    hotkey_triggered_signal = Signal()

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.hotkey_listener = None
        self.registered_hotkey = None
        self.popup_window = None
        
        # Connect signals
        self.hotkey_triggered_signal.connect(self.on_hotkey_pressed)

    def start_hotkey_listener(self):
        """
        Create listener for global hotkeys.
        """
        orig_shortcut = self.app.config.get("shortcut", "ctrl+space")
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

    @Slot()
    def on_hotkey_pressed(self):
        """
        Handle the hotkey press event.
        """
        logging.debug("Hotkey pressed")

        # Check for spam triggers
        if self.app.check_trigger_spam():
            logging.warning("Hotkey spam detected - quitting application")
            self.app.exit_app()
            return

        # Original hotkey handling continues...
        if self.app.current_provider:
            logging.debug("Cancelling current provider's request")
            self.app.current_provider.cancel()
            self.app.text_operations_manager.output_queue = ""

        # noinspection PyTypeChecker
        QtCore.QMetaObject.invokeMethod(self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection)

    @Slot()
    def _show_popup(self):
        """
        Show the popup window when the hotkey is pressed.
        """
        logging.debug("Showing popup window")
        # First attempt with default sleep
        selected_text = self.app.text_operations_manager.get_selected_text()

        # Retry with more attempts if no text captured
        if not selected_text:
            logging.debug("No text captured, retrying with more attempts")
            selected_text = self.app.text_operations_manager.get_selected_text(max_retries=3)

        logging.debug(f'Selected text: "{selected_text}"')
        try:
            # Check if we have any meaningful text
            if not selected_text.strip():
                logging.debug("No text selected, opening chat window directly")
                # Open ResponseWindow directly for chat
                response_window = ui.ResponseWindow.ResponseWindow(self.app, "Chat", None)
                response_window.show()
                return

            if self.popup_window is not None:
                logging.debug("Existing popup window found")
                if self.popup_window.isVisible():
                    logging.debug("Closing existing visible popup window")
                    self.popup_window.close()
                self.popup_window = None
            logging.debug("Creating new popup window")
            self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(self.app, selected_text)

            # Set the window icon
            icon_path = get_resource_path(os.path.join("icons", "app_icon.png"))
            if os.path.exists(icon_path):
                self.app.setWindowIcon(QtGui.QIcon(icon_path))

            # Position the popup window centered on the cursor
            cursor_pos = QtGui.QCursor.pos()
            frame_geometry = self.popup_window.frameGeometry()
            frame_geometry.moveCenter(cursor_pos)
            self.popup_window.move(frame_geometry.topLeft())

            logging.debug("Displaying popup window")
            self.popup_window.show()
            self.popup_window.activateWindow()
            self.popup_window.raise_()

        except Exception as e:
            logging.error(f"Error showing popup: {e}")

    def stop_hotkey_listener(self):
        """Stop the hotkey listener"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None