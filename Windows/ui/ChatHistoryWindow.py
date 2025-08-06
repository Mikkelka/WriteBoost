from datetime import datetime
import logging
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMessageBox

from ui.ChatManager import ChatManager
from ui.UIUtils import UIUtils, colorMode, get_resource_path

_ = lambda x: x




class ChatListItem(QtWidgets.QWidget):
    """A single chat item in the list"""

    open_requested = Signal(str)  # chat_id
    delete_requested = Signal(str)  # chat_id

    def __init__(self, chat_data, parent=None):
        super().__init__(parent)
        self.chat_data = chat_data
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Chat info
        info_layout = QtWidgets.QVBoxLayout()

        # Title
        title_label = QtWidgets.QLabel(self.chat_data["title"])
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        info_layout.addWidget(title_label)

        # Timestamp
        timestamp = datetime.fromisoformat(self.chat_data["timestamp"])
        time_str = timestamp.strftime("%Y-%m-%d %H:%M")
        time_label = QtWidgets.QLabel(time_str)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {"#aaaaaa" if colorMode == "dark" else "#666666"};
                font-size: 12px;
            }}
        """)
        info_layout.addWidget(time_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        # Open button
        open_btn = QtWidgets.QPushButton("Open")
        open_btn.setStyleSheet(self.get_button_style())
        open_btn.clicked.connect(lambda: self.open_requested.emit(self.chat_data["id"]))
        button_layout.addWidget(open_btn)

        # Delete button
        delete_btn = QtWidgets.QPushButton()
        delete_btn.setIcon(
            QtGui.QIcon(
                get_resource_path(
                    os.path.join("icons", "cross" + ("_dark" if colorMode == "dark" else "_light") + ".png")
                )
            )
        )
        delete_btn.setStyleSheet(self.get_delete_button_style())
        delete_btn.setToolTip("Delete Chat")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.chat_data["id"]))
        button_layout.addWidget(delete_btn)

        layout.addLayout(button_layout)

        # Item styling
        self.setStyleSheet(f"""
            ChatListItem {{
                background-color: {"#444" if colorMode == "dark" else "#f8f8f8"};
                border: 1px solid {"#666" if colorMode == "dark" else "#ddd"};
                border-radius: 8px;
                margin: 2px;
            }}
            ChatListItem:hover {{
                background-color: {"#555" if colorMode == "dark" else "#f0f0f0"};
            }}
        """)

    def get_button_style(self):
        return f"""
            QPushButton {{
                background-color: {"#2e7d32" if colorMode == "dark" else "#4CAF50"};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {"#1b5e20" if colorMode == "dark" else "#45a049"};
            }}
        """

    def get_delete_button_style(self):
        return f"""
            QPushButton {{
                background-color: {"#d32f2f" if colorMode == "dark" else "#f44336"};
                border: none;
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {"#b71c1c" if colorMode == "dark" else "#d32f2f"};
            }}
        """


class ChatHistoryWindow(QtWidgets.QWidget):
    """Window for displaying and managing saved chats"""

    close_signal = Signal()

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.chat_manager = ChatManager()
        self.setWindowTitle("Chat History")
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setMinimumSize(600, 400)
        self.resize(700, 500)

        self.setup_ui()
        self.load_chats()

        # Set window icon
        icon_path = get_resource_path(os.path.join("icons", "app_icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

    def setup_ui(self):
        # Main layout setup
        UIUtils.setup_window_and_layout(self)
        content_layout = QtWidgets.QVBoxLayout(self.background)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Header
        header_layout = QtWidgets.QHBoxLayout()

        title_label = QtWidgets.QLabel("Chat History")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {"#ffffff" if colorMode == "dark" else "#333333"};
                font-size: 24px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QtWidgets.QPushButton()
        refresh_btn.setIcon(
            QtGui.QIcon(
                get_resource_path(
                    os.path.join("icons", "regenerate" + ("_dark" if colorMode == "dark" else "_light") + ".png")
                )
            )
        )
        refresh_btn.setStyleSheet(self.get_button_style())
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.clicked.connect(self.load_chats)
        header_layout.addWidget(refresh_btn)

        content_layout.addLayout(header_layout)

        # Chat list
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        self.chat_list_widget = QtWidgets.QWidget()
        self.chat_list_layout = QtWidgets.QVBoxLayout(self.chat_list_widget)
        self.chat_list_layout.setSpacing(5)
        self.chat_list_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.chat_list_widget)
        content_layout.addWidget(self.scroll_area)

        # Empty state label
        self.empty_label = QtWidgets.QLabel("No saved chats yet.\nStart a conversation and save it to see it here.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: {"#aaaaaa" if colorMode == "dark" else "#666666"};
                font-size: 16px;
                padding: 50px;
            }}
        """)
        self.empty_label.hide()
        content_layout.addWidget(self.empty_label)

    def get_button_style(self):
        return f"""
            QPushButton {{
                background-color: {"#444" if colorMode == "dark" else "#f0f0f0"};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                border: 1px solid {"#666" if colorMode == "dark" else "#ccc"};
                border-radius: 5px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {"#555" if colorMode == "dark" else "#e0e0e0"};
            }}
        """

    def load_chats(self):
        """Load and display all saved chats"""
        try:
            # Clear existing items
            for i in reversed(range(self.chat_list_layout.count())):
                child = self.chat_list_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)

            # Load chats
            chats = self.chat_manager.load_all_chats()

            if not chats:
                self.empty_label.show()
                self.scroll_area.hide()
            else:
                self.empty_label.hide()
                self.scroll_area.show()

                # Add chat items
                for chat in chats:
                    chat_item = ChatListItem(chat)
                    chat_item.open_requested.connect(self.open_chat)
                    chat_item.delete_requested.connect(self.delete_chat)
                    self.chat_list_layout.addWidget(chat_item)

                # Add stretch to push items to top
                self.chat_list_layout.addStretch()

        except Exception as e:
            logging.error(f"Error loading chats: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load chats: {e}")

    def open_chat(self, chat_id: str):
        """Open a saved chat"""
        try:
            chat_data = self.chat_manager.load_chat(chat_id)
            if not chat_data:
                QMessageBox.warning(self, "Error", "Chat not found")
                return

            # Create new response window with chat history
            from ui.ResponseWindow import ResponseWindow

            response_window = ResponseWindow(self.app, "Saved Chat")
            response_window.chat_history = chat_data["chat_history"].copy()
            response_window.saved_chat_id = chat_id  # Store ID for updating

            # Display chat history
            for message in chat_data["chat_history"]:
                if message["role"] == "assistant":
                    response_window.chat_area.add_message(message["content"])
                elif message["role"] == "user" and not message["content"].startswith("Original text to"):
                    response_window.chat_area.add_message(message["content"], is_user=True)

            # Stop thinking animation and enable input
            response_window.stop_thinking_animation()
            response_window.show()

            # Store reference in app
            self.app.current_response_window = response_window

            # Close history window
            self.close()

        except Exception as e:
            logging.error(f"Error opening chat: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open chat: {e}")

    def delete_chat(self, chat_id: str):
        """Delete a saved chat"""
        reply = QMessageBox.question(
            self,
            "Delete Chat",
            "Are you sure you want to delete this chat?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.chat_manager.delete_chat(chat_id):
                    self.load_chats()  # Refresh the list
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete chat")
            except Exception as e:
                logging.error(f"Error deleting chat: {e}")
                QMessageBox.warning(self, "Error", f"Failed to delete chat: {e}")

    def closeEvent(self, event):
        """Handle window close"""
        self.close_signal.emit()
        super().closeEvent(event)
