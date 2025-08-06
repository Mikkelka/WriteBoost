import logging
import time
import threading

import pyperclip
from pynput import keyboard as pykeyboard
from PySide6 import QtCore
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QMessageBox


class TextOperationsManager(QtCore.QObject):
    """Handles text capture, processing, and replacement operations"""
    
    show_message_signal = Signal(str, str)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.output_queue = ""
        
        # Connect signals
        self.show_message_signal.connect(self.show_message_box)

    def get_selected_text(self, max_retries=2):
        """
        Get the currently selected text from any application with optimized timing.
        Args:
            max_retries (int): Maximum number of attempts to capture text
        """
        clipboard_backup = pyperclip.paste()
        
        for attempt in range(max_retries):
            logging.debug(f"Text capture attempt {attempt + 1}/{max_retries}")
            
            # Clear the clipboard
            self.clear_clipboard()

            # Simulate Ctrl+C
            logging.debug("Simulating Ctrl+C")
            kbrd = pykeyboard.Controller()

            def press_ctrl_c():
                kbrd.press(pykeyboard.Key.ctrl.value)
                kbrd.press("c")
                kbrd.release("c")
                kbrd.release(pykeyboard.Key.ctrl.value)

            press_ctrl_c()

            # Progressive delay: 0.1s first attempt, then 0.3s
            delay = 0.1 if attempt == 0 else 0.3
            time.sleep(delay)
            logging.debug(f"Waited {delay}s for clipboard")

            # Get the selected text
            selected_text = pyperclip.paste()
            logging.debug(f"Clipboard content after Ctrl+C: '{selected_text}'")
            logging.debug(f"Original clipboard backup: '{clipboard_backup}'")
            
            # Check if we got meaningful text
            if selected_text and selected_text.strip():
                # We got some text, assume it's selected text
                logging.debug(f"Got text from clipboard: '{selected_text}'")
                # Restore the clipboard and return success
                pyperclip.copy(clipboard_backup)
                return selected_text
            elif selected_text != clipboard_backup:
                # We got different text (even if empty), could be valid selection
                logging.debug(f"Got different text from clipboard: '{selected_text}'")
                # Restore the clipboard and return success
                pyperclip.copy(clipboard_backup)
                return selected_text
                
            # If last attempt failed, break to avoid unnecessary waiting
            if attempt == max_retries - 1:
                logging.warning("Failed to capture selected text after all attempts")

        # Restore the clipboard before returning empty result
        pyperclip.copy(clipboard_backup)
        return ""

    @staticmethod
    def clear_clipboard():
        """
        Clear the system clipboard.
        """
        try:
            pyperclip.copy("")
        except Exception as e:
            logging.error(f"Error clearing clipboard: {e}")

    def process_option(self, option, selected_text, custom_change=None):
        """
        Process the selected writing option in a separate thread.
        """
        logging.debug(f"Processing option: {option}")

        # For Summary, Key Points, Table, and empty text custom prompts, create response window
        if (option == "Custom" and not selected_text.strip()) or self.app.options[option]["open_in_window"]:
            window_title = "Chat" if (option == "Custom" and not selected_text.strip()) else option
            self.app.current_response_window = self.app.show_response_window(window_title, selected_text)

            # Initialize chat history with text/prompt
            if option == "Custom" and not selected_text.strip():
                # For direct AI queries, don't include empty text
                self.app.current_response_window.message_manager.set_chat_history([])
            else:
                # For other options, include the original text
                self.app.current_response_window.message_manager.set_chat_history([
                    {"role": "user", "content": f"Original text to {option.lower()}:\n\n{selected_text}"}
                ])
        else:
            # Clear any existing response window reference for non-window options
            if hasattr(self.app, "current_response_window"):
                delattr(self.app, "current_response_window")

        threading.Thread(
            target=self.process_option_thread, args=(option, selected_text, custom_change), daemon=True
        ).start()

    def process_option_thread(self, option, selected_text, custom_change=None):
        """
        Thread function to process the selected writing option using the AI model.
        """
        logging.debug(f"Starting processing thread for option: {option}")
        try:
            if selected_text.strip() == "":
                # No selected text
                if option == "Custom":
                    prompt = custom_change
                    system_instruction = getattr(
                        self.app.current_provider,
                        "chat_system_instruction",
                        "You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable.",
                    )
                else:
                    self.show_message_signal.emit("Error", "Please select text to use this option.")
                    return
            else:
                selected_prompt = self.app.options.get(option, ("", ""))
                prompt_prefix = selected_prompt["prefix"]
                system_instruction = selected_prompt["instruction"]
                if option == "Custom":
                    prompt = f"{prompt_prefix}Described change: {custom_change}\n\nText: {selected_text}"
                else:
                    prompt = f"{prompt_prefix}{selected_text}"

            self.output_queue = ""

            logging.debug(f"Getting response from provider for option: {option}")

            if (option == "Custom" and not selected_text.strip()) or self.app.options[option]["open_in_window"]:
                logging.debug("Getting response for window display")
                response = self.app.current_provider.get_response(system_instruction, prompt, return_response=True)
                logging.debug(f"Got response of length: {len(response) if response else 0}")

                # For custom prompts with no text, add question to chat history
                if option == "Custom" and not selected_text.strip():
                    self.app.current_response_window.message_manager.add_user_message(custom_change)

                # Set initial response using QMetaObject.invokeMethod to ensure thread safety
                if hasattr(self.app, "current_response_window"):
                    # noinspection PyTypeChecker
                    QtCore.QMetaObject.invokeMethod(
                        self.app.current_response_window,
                        "set_text",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, response),
                    )
                    logging.debug("Invoked set_text on response window")
            else:
                logging.debug("Getting response for direct replacement")
                self.app.current_provider.get_response(system_instruction, prompt)
                logging.debug("Response processed")

        except Exception as e:
            logging.error(f"An error occurred: {e}", exc_info=True)

            if "Resource has been exhausted" in str(e):
                self.show_message_signal.emit(
                    "Error - Rate Limit Hit",
                    "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
                )
            else:
                self.show_message_signal.emit("Error", f"An error occurred: {e}")

    @Slot(str, str)
    def show_message_box(self, title, message):
        """
        Show a message box with the given title and message.
        """
        QMessageBox.warning(None, title, message)

    @Slot(str)
    def replace_text(self, new_text):
        """
        Replaces the text by pasting in the LLM generated text. With "Key Points" and "Summary", invokes a window with the output instead.
        """
        error_message = "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST"

        # Confirm new_text exists and is a string
        if new_text and isinstance(new_text, str):
            self.output_queue += new_text
            current_output = self.output_queue.strip()  # Strip whitespace for comparison

            # If the new text is the error message, show a message box
            if current_output == error_message:
                self.show_message_signal.emit("Error", "The text is incompatible with the requested change.")
                return

            # Check if we're building up to the error message (to prevent partial pasting)
            if len(current_output) <= len(error_message):
                clean_current = "".join(current_output.split())
                clean_error = "".join(error_message.split())
                if clean_current == clean_error[: len(clean_current)]:
                    return

            logging.debug("Processing output text")
            try:
                # For Summary and Key Points, show in response window
                if hasattr(self.app, "current_response_window"):
                    # Use set_text for initial content, not append_text
                    self.app.current_response_window.set_text(self.output_queue.rstrip("\n"))
                else:
                    # For other options, use the original clipboard-based replacement
                    clipboard_backup = pyperclip.paste()
                    cleaned_text = self.output_queue.rstrip("\n")
                    pyperclip.copy(cleaned_text)

                    kbrd = pykeyboard.Controller()

                    def press_ctrl_v():
                        kbrd.press(pykeyboard.Key.ctrl.value)
                        kbrd.press("v")
                        kbrd.release("v")
                        kbrd.release(pykeyboard.Key.ctrl.value)

                    press_ctrl_v()
                    time.sleep(0.2)
                    pyperclip.copy(clipboard_backup)

                if not hasattr(self.app, "current_response_window"):
                    self.output_queue = ""

            except Exception as e:
                logging.error(f"Error processing output: {e}")
        else:
            logging.debug("No new text to process")