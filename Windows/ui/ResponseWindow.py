import logging
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Slot

from ui.UIUtils import UIUtils, colorMode, get_resource_path
from ui.MarkdownDisplay import MarkdownTextBrowser
from ui.ChatScrollArea import ChatContentScrollArea
from ui.ChatMessageManager import ChatMessageManager

_ = lambda x: x



class ResponseWindow(QtWidgets.QWidget):
    """Enhanced response window with improved sizing and zoom handling"""

    def __init__(self, app, title=_("Response"), parent=None):
        super().__init__(parent)
        self.app = app
        self.original_title = title
        self.setWindowTitle(title)
        self.option = title.replace(" Result", "")
        self.selected_text = None
        self.input_field = None
        self.loading_label = None
        self.loading_container = None
        self.chat_area = None
        self.message_manager = ChatMessageManager([])

        # Setup thinking animation with full range of dots
        self.thinking_timer = QtCore.QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_dots)
        self.thinking_dots_state = 0
        self.thinking_dots = ["", ".", "..", "..."]  # Now properly includes all states
        self.thinking_timer.setInterval(300)

        self.init_ui()
        logging.debug("Connecting response signals")
        self.app.conversation_manager.followup_response_signal.connect(self.handle_followup_response)
        logging.debug("Response signals connected")

        # Set initial size to match final size to prevent resize jump
        initial_width = 900
        initial_height = 700
        self.resize(initial_width, initial_height)

        # Center the window on screen immediately
        screen = QtWidgets.QApplication.primaryScreen()
        frame_geometry = self.frameGeometry()
        screen_center = screen.geometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def init_ui(self):
        # Window setup with enhanced flags
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setMinimumSize(800, 600)

        # Main layout setup
        UIUtils.setup_window_and_layout(self)
        content_layout = QtWidgets.QVBoxLayout(self.background)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        # Top bar with zoom controls
        top_bar = QtWidgets.QHBoxLayout()

        # Use appropriate title - "Chat" for direct mode, operation name for text operations
        display_title = "Chat" if not self.message_manager.has_messages() else self.option
        title_label = QtWidgets.QLabel(display_title)
        title_label.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {'#ffffff' if colorMode == 'dark' else '#333333'};"
        )
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        # Zoom label with matched size
        zoom_label = QtWidgets.QLabel("Zoom:")
        zoom_label.setStyleSheet(f"""
            color: {"#aaaaaa" if colorMode == "dark" else "#666666"};
            font-size: 14px;
            margin-right: 5px;
        """)
        top_bar.addWidget(zoom_label)

        # Enhanced zoom controls with swapped order
        zoom_controls = [
            ("plus", "Zoom In", lambda: self.zoom_all_messages("in")),
            ("minus", "Zoom Out", lambda: self.zoom_all_messages("out")),
            ("reset", "Reset Zoom", lambda: self.zoom_all_messages("reset")),
        ]

        for icon, tooltip, action in zoom_controls:
            btn = QtWidgets.QPushButton()
            btn.setIcon(
                QtGui.QIcon(
                    get_resource_path(
                        os.path.join("icons", icon + ("_dark" if colorMode == "dark" else "_light") + ".png")
                    )
                )
            )
            btn.setStyleSheet(self.get_button_style())
            btn.setToolTip(tooltip)
            btn.clicked.connect(action)
            btn.setFixedSize(30, 30)
            top_bar.addWidget(btn)

        content_layout.addLayout(top_bar)

        # Copy controls with matching text size
        copy_bar = QtWidgets.QHBoxLayout()
        copy_hint = QtWidgets.QLabel(_("Select to copy with formatting"))
        copy_hint.setStyleSheet(f"color: {'#aaaaaa' if colorMode == 'dark' else '#666666'}; font-size: 14px;")
        copy_bar.addWidget(copy_hint)
        copy_bar.addStretch()

        save_chat_btn = QtWidgets.QPushButton(_("Save Chat"))
        save_chat_btn.setStyleSheet(self.get_button_style())
        save_chat_btn.clicked.connect(self.save_chat)
        copy_bar.addWidget(save_chat_btn)

        copy_md_btn = QtWidgets.QPushButton(_("Copy as Markdown"))
        copy_md_btn.setStyleSheet(self.get_button_style())
        copy_md_btn.clicked.connect(self.copy_first_response)  # Updated to only copy first response
        copy_bar.addWidget(copy_md_btn)
        content_layout.addLayout(copy_bar)

        # Loading indicator
        loading_container = QtWidgets.QWidget()
        loading_layout = QtWidgets.QHBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)

        self.loading_label = QtWidgets.QLabel(_("Thinking"))
        self.loading_label.setStyleSheet(f"""
            QLabel {{
                color: {"#ffffff" if colorMode == "dark" else "#333333"};
                font-size: 18px;
                padding: 20px;
            }}
        """)
        self.loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        loading_inner_container = QtWidgets.QWidget()
        loading_inner_container.setFixedWidth(180)
        loading_inner_layout = QtWidgets.QHBoxLayout(loading_inner_container)
        loading_inner_layout.setContentsMargins(0, 0, 0, 0)
        loading_inner_layout.addWidget(self.loading_label)

        loading_layout.addStretch()
        loading_layout.addWidget(loading_inner_container)
        loading_layout.addStretch()

        content_layout.addWidget(loading_container)
        self.loading_container = loading_container

        # Only start thinking animation if we have initial content to process
        if self.message_manager.has_messages():
            self.start_thinking_animation(initial=True)
        else:
            # Hide loading container for direct chat mode
            self.loading_container.hide()

        # Enhanced chat area with full width
        self.chat_area = ChatContentScrollArea()
        content_layout.addWidget(self.chat_area)

        # Model and thinking controls
        controls_bar = QtWidgets.QHBoxLayout()

        # Model selection
        model_label = QtWidgets.QLabel("Model:")
        model_label.setStyleSheet(
            f"color: {'#ffffff' if colorMode == 'dark' else '#333333'}; font-size: 14px; font-weight: bold;"
        )
        controls_bar.addWidget(model_label)

        self.model_dropdown = QtWidgets.QComboBox()
        self.model_dropdown.addItem("Gemini 2.5 Flash", "gemini-2.5-flash")
        self.model_dropdown.addItem("Gemini 2.5 Flash Lite", "gemini-2.5-flash-lite")
        # Set default to current configured chat model
        current_model = getattr(self.app.current_provider, "chat_model_name", "gemini-2.5-flash")
        model_index = self.model_dropdown.findData(current_model)
        if model_index >= 0:
            self.model_dropdown.setCurrentIndex(model_index)
        self.model_dropdown.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 6px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                font-size: 14px;
                min-width: 160px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                selection-background-color: {"#0078d7" if colorMode == "dark" else "#0078d7"};
            }}
        """)
        controls_bar.addWidget(self.model_dropdown)

        controls_bar.addSpacing(20)

        # Thinking level selection
        thinking_label = QtWidgets.QLabel("Thinking:")
        thinking_label.setStyleSheet(
            f"color: {'#ffffff' if colorMode == 'dark' else '#333333'}; font-size: 14px; font-weight: bold;"
        )
        controls_bar.addWidget(thinking_label)

        self.thinking_dropdown = QtWidgets.QComboBox()
        self.thinking_dropdown.addItem("No Thinking", 0)
        self.thinking_dropdown.addItem("Dynamic", -1)
        self.thinking_dropdown.addItem("Light (512)", 512)
        self.thinking_dropdown.addItem("Medium (2048)", 2048)
        self.thinking_dropdown.addItem("Heavy (8192)", 8192)
        self.thinking_dropdown.setCurrentIndex(1)  # Default to "Dynamic"
        self.thinking_dropdown.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 6px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                font-size: 14px;
                min-width: 140px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                selection-background-color: {"#0078d7" if colorMode == "dark" else "#0078d7"};
            }}
        """)
        controls_bar.addWidget(self.thinking_dropdown)

        controls_bar.addStretch()
        content_layout.addLayout(controls_bar)

        # Input area with enhanced styling
        bottom_bar = QtWidgets.QHBoxLayout()

        self.input_field = QtWidgets.QLineEdit()
        # Set appropriate placeholder based on whether we have initial content
        if self.message_manager.has_messages():
            self.input_field.setPlaceholderText(_("Ask a follow-up question") + "...")
        else:
            self.input_field.setPlaceholderText(_("Ask me anything") + "...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                font-size: 14px;
            }}
        """)
        self.input_field.returnPressed.connect(self.send_message)
        bottom_bar.addWidget(self.input_field)

        send_button = QtWidgets.QPushButton()
        send_button.setIcon(
            QtGui.QIcon(
                get_resource_path(
                    os.path.join("icons", "send" + ("_dark" if colorMode == "dark" else "_light") + ".png")
                )
            )
        )
        send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#2e7d32" if colorMode == "dark" else "#4CAF50"};
                border: none;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {"#1b5e20" if colorMode == "dark" else "#45a049"};
            }}
        """)
        send_button.setFixedSize(self.input_field.sizeHint().height(), self.input_field.sizeHint().height())
        send_button.clicked.connect(self.send_message)
        bottom_bar.addWidget(send_button)

        content_layout.addLayout(bottom_bar)

    # Method to get first response text

    def copy_first_response(self):
        """Copy only the first model response as Markdown"""
        response_text = self.get_first_response_text()
        if response_text:
            QtWidgets.QApplication.clipboard().setText(response_text)

    def get_button_style(self):
        return f"""
            QPushButton {{
                background-color: {"#444" if colorMode == "dark" else "#f0f0f0"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                border: 1px solid {"#666" if colorMode == "dark" else "#ccc"};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {"#555" if colorMode == "dark" else "#e0e0e0"};
            }}
        """

    def update_thinking_dots(self):
        """Update the thinking animation dots with proper cycling"""
        self.thinking_dots_state = (self.thinking_dots_state + 1) % len(self.thinking_dots)
        dots = self.thinking_dots[self.thinking_dots_state]

        if self.loading_label.isVisible():
            self.loading_label.setText(_("Thinking") + f"{dots}")
        else:
            self.input_field.setPlaceholderText(_("Thinking") + f"{dots}")

    def start_thinking_animation(self, initial=False):
        """Start the thinking animation for either initial load or follow-up questions"""
        self.thinking_dots_state = 0

        if initial:
            self.loading_label.setText(_("Thinking"))
            self.loading_label.setVisible(True)
            self.loading_container.setVisible(True)
        else:
            self.input_field.setPlaceholderText(_("Thinking"))
            self.loading_container.setVisible(False)

        self.thinking_timer.start()

    def stop_thinking_animation(self):
        """Stop the thinking animation"""
        self.thinking_timer.stop()
        self.loading_container.hide()
        self.loading_label.hide()
        self.input_field.setPlaceholderText(_("Ask a follow-up question"))
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        # Force layout update
        if self.layout():
            self.layout().invalidate()
            self.layout().activate()

    def zoom_all_messages(self, action="in"):
        """Apply zoom action to all messages in the chat"""
        for i in range(self.chat_area.layout.count() - 1):  # Skip stretch item
            item = self.chat_area.layout.itemAt(i)
            if item and item.widget():
                text_display = item.widget().layout().itemAt(0).widget()
                if isinstance(text_display, MarkdownTextBrowser):
                    if action == "in":
                        text_display.zoom_in()
                    elif action == "out":
                        text_display.zoom_out()
                    else:  # reset
                        text_display.reset_zoom()

        # Update layout after zooming
        self.chat_area.update_content_height()

    def _adjust_window_height(self):
        """Calculate and set the ideal window height"""
        # Skip adjustment if window already has a size
        if hasattr(self, "_size_initialized"):
            return

        try:
            # Get content widget height
            content_height = self.chat_area.content_widget.sizeHint().height()

            # Calculate other UI elements height
            ui_elements_height = (
                self.layout().contentsMargins().top()
                + self.layout().contentsMargins().bottom()
                + self.input_field.height()
                + self.layout().spacing() * 5
                + 200  # Increased from 185 for taller default height
            )

            # Get screen constraints
            screen = QtWidgets.QApplication.screenAt(self.pos())
            if not screen:
                screen = QtWidgets.QApplication.primaryScreen()

            # Calculate maximum available height (85% of screen)
            max_height = int(screen.geometry().height() * 0.85)

            # Calculate desired height to show more content initially
            desired_content_height = int(content_height * 0.85)  # Show 85% of content
            desired_total_height = min(desired_content_height + ui_elements_height, max_height)

            # Set reasonable minimum height - increased for better viewing
            final_height = max(700, desired_total_height)  # Increased from 600

            # Set width to 900px for better readability
            final_width = 900

            # Update both width and height
            self.resize(final_width, final_height)

            # Center on screen
            frame_geometry = self.frameGeometry()
            screen_center = screen.geometry().center()
            frame_geometry.moveCenter(screen_center)
            self.move(frame_geometry.topLeft())

            # Mark size as initialized
            self._size_initialized = True

        except Exception as e:
            logging.error(f"Error adjusting window height: {e}")
            self.resize(900, 700)  # Updated fallback size
            self._size_initialized = True

    @Slot(str)
    def set_text(self, text):
        """Set initial response text with enhanced handling"""
        if not text.strip():
            return

        # Add the assistant response
        self.message_manager.add_assistant_message(text)

        self.stop_thinking_animation()

        # Show the user's initial message first (if it exists)
        chat_history = self.message_manager.get_chat_history()
        if len(chat_history) >= 2:  # Should have user message + assistant response
            user_message = chat_history[0]["content"]
            display_text = self.message_manager.extract_user_display_text(user_message)
            
            if display_text:
                user_display = self.chat_area.add_message(display_text, is_user=True)
                if hasattr(self.app.config, "response_window_zoom"):
                    user_display.zoom_factor = self.app.config["response_window_zoom"]
                    user_display._apply_zoom()

        # Then show the AI response
        text_display = self.chat_area.add_message(text)

        # Update zoom state
        if hasattr(self.app.config, "response_window_zoom"):
            text_display.zoom_factor = self.app.config["response_window_zoom"]
            text_display._apply_zoom()

        QtCore.QTimer.singleShot(100, self._adjust_window_height)

    @Slot(str)
    def handle_followup_response(self, response_text):
        """Handle the follow-up response from the AI with improved layout handling"""
        if response_text:
            self.loading_label.setVisible(False)
            text_display = self.chat_area.add_message(response_text)

            # Maintain consistent zoom level
            if hasattr(self, "current_text_display"):
                text_display.zoom_factor = self.current_text_display.zoom_factor
                text_display._apply_zoom()

            chat_history = self.message_manager.get_chat_history()
            if len(chat_history) > 0 and chat_history[-1]["role"] != "assistant":
                self.message_manager.add_assistant_message(response_text)

        self.stop_thinking_animation()
        self.input_field.setEnabled(True)
        self.input_field.setFocus()

        # Update window height
        QtCore.QTimer.singleShot(100, self._adjust_window_height)

    def send_message(self):
        """Send a new message/question"""
        message = self.input_field.text().strip()
        if not message:
            return

        self.input_field.setEnabled(False)
        self.input_field.clear()

        # Get selected model and thinking level
        selected_model = self.model_dropdown.currentData()
        selected_thinking = self.thinking_dropdown.currentData()

        # Add user message and maintain zoom level
        text_display = self.chat_area.add_message(message, is_user=True)
        if hasattr(self, "current_text_display"):
            text_display.zoom_factor = self.current_text_display.zoom_factor
            text_display._apply_zoom()

        # Don't add to message history here - it's done in process_followup_question
        self.start_thinking_animation()
        self.app.process_followup_question(self, message, selected_model, selected_thinking)

    def copy_as_markdown(self):
        """Copy conversation as Markdown"""
        markdown = ""
        self.message_manager.copy_conversation_as_markdown()

    def save_chat(self):
        """Save the current chat"""
        if not self.message_manager.has_messages():
            QtWidgets.QMessageBox.information(self, "No Chat", "There's no conversation to save yet.")
            return

        try:
            from ui.ChatManager import ChatManager

            chat_manager = ChatManager()

            # Generate title from chat history
            title = chat_manager.generate_chat_title(self.message_manager.get_chat_history())

            # Show input dialog for custom title
            text, ok = QtWidgets.QInputDialog.getText(
                self, "Save Chat", "Enter a title for this chat:", QtWidgets.QLineEdit.EchoMode.Normal, title
            )

            if ok and text.strip():
                # Save or update chat
                chat_id = getattr(self, "saved_chat_id", None)
                saved_id = chat_manager.save_chat(text.strip(), self.message_manager.get_chat_history(), chat_id)

                # Store the ID for future updates
                self.saved_chat_id = saved_id

                QtWidgets.QMessageBox.information(self, "Chat Saved", f"Chat saved as: {text.strip()}")

        except Exception as e:
            logging.error(f"Error saving chat: {e}")
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save chat: {e}")

    def closeEvent(self, event):
        """Handle window close event"""
        # Save zoom factor to main config
        if hasattr(self, "current_text_display"):
            self.app.config["response_window_zoom"] = self.current_text_display.zoom_factor
            self.app.save_config(self.app.config)

        self.message_manager.set_chat_history([])

        if hasattr(self.app, "current_response_window"):
            delattr(self.app, "current_response_window")

        super().closeEvent(event)
