from functools import partial
import json
import logging
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ui.UIUtils import ThemeBackground, colorMode, get_resource_path

_ = lambda x: x








class SimpleButton(QtWidgets.QPushButton):
    def __init__(self, parent_popup, key, text, is_chat_operation=False):
        super().__init__(text, parent_popup)
        self.popup = parent_popup
        self.key = key
        self.is_chat_operation = is_chat_operation

        # Enable hover events and styled background
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        # Use a dynamic property "hover" (default False)
        self.setProperty("hover", False)

        # Set fixed size (adjust as needed)
        self.setFixedSize(120, 40)

        # Different styling for chat operations vs direct replacement
        if is_chat_operation:
            # Blue-tinted styling for chat operations
            bg_color = "#2e4057" if colorMode == "dark" else "#e3f2fd"
            border_color = "#3f5c7a" if colorMode == "dark" else "#90caf9"
            hover_color = "#3f5c7a" if colorMode == "dark" else "#bbdefb"
        else:
            # Default gray styling for direct replacement
            bg_color = "#444" if colorMode == "dark" else "white"
            border_color = "#666" if colorMode == "dark" else "#ccc"
            hover_color = "#555" if colorMode == "dark" else "#f0f0f0"

        # Define base style using the dynamic property instead of the :hover pseudo-class
        self.base_style = f"""
            QPushButton {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {hover_color};
            }}
        """
        self.setStyleSheet(self.base_style)
        logging.debug(f"SimpleButton initialized - is_chat: {is_chat_operation}")

    def enterEvent(self, event):
        self.setProperty("hover", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)


class CustomPopupWindow(QtWidgets.QWidget):
    def __init__(self, app, selected_text):
        super().__init__()
        self.app = app
        self.selected_text = selected_text
        self.has_text = bool(selected_text.strip())

        self.custom_input = None
        self.input_area = None

        self.button_widgets = []

        logging.debug("Initializing CustomPopupWindow")
        self.init_ui()

    def init_ui(self):
        logging.debug("Setting up CustomPopupWindow UI")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowTitle("Writing Tools")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background = ThemeBackground(self, border_radius=10)
        main_layout.addWidget(self.background)

        content_layout = QtWidgets.QVBoxLayout(self.background)
        # Margin Control
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # TOP BAR LAYOUT & STYLE
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(0)

        content_layout.addLayout(top_bar)

        # Input area (hidden in edit mode)
        self.input_area = QWidget()
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText(_("Describe your change...") if self.has_text else _("Ask your AI..."))
        self.custom_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
        """)
        self.custom_input.returnPressed.connect(self.on_custom_change)
        input_layout.addWidget(self.custom_input)

        send_btn = QPushButton()
        send_icon = get_resource_path(
            os.path.join("icons", "send" + ("_dark" if colorMode == "dark" else "_light") + ".png")
        )
        if os.path.exists(send_icon):
            send_btn.setIcon(QtGui.QIcon(send_icon))
        send_btn.setStyleSheet(f"""
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
        send_btn.setFixedSize(self.custom_input.sizeHint().height(), self.custom_input.sizeHint().height())
        send_btn.clicked.connect(self.on_custom_change)
        input_layout.addWidget(send_btn)

        content_layout.addWidget(self.input_area)

        if self.has_text:
            self.build_buttons_list()
            self.rebuild_grid_layout(content_layout)
        else:
            self.custom_input.setMinimumWidth(300)

        # show update notice if applicable
        if self.app.config.get("update_available", False):
            update_label = QLabel()
            update_label.setOpenExternalLinks(True)
            update_label.setText(
                '<a href="https://github.com/theJayTea/WritingTools/releases" style="color:rgb(255, 0, 0); text-decoration: underline; font-weight: bold;">There\'s an update! :D Download now.</a>'
            )
            update_label.setStyleSheet("margin-top: 10px;")
            content_layout.addWidget(update_label, alignment=QtCore.Qt.AlignCenter)

        logging.debug("CustomPopupWindow UI setup complete")
        self.installEventFilter(self)
        QtCore.QTimer.singleShot(250, lambda: self.custom_input.setFocus())

    @staticmethod
    def load_options():
        options_path = get_resource_path("options.json")
        if os.path.exists(options_path):
            with open(options_path) as f:
                data = json.load(f)
                logging.debug("Options loaded successfully")
        else:
            logging.debug("Options file not found")

        return data

    @staticmethod
    def save_options(options):
        options_path = get_resource_path("options.json")
        with open(options_path, "w") as f:
            json.dump(options, f, indent=2)

    def build_buttons_list(self):
        """
        Reads options.json, creates SimpleButton for each (except "Custom"),
        storing them in self.button_widgets in the same order as the JSON file.
        """
        self.button_widgets.clear()
        data = self.load_options()

        for k, v in data.items():
            if k == "Custom":
                continue
            
            # Check if this operation opens in a chat window
            is_chat_operation = v.get("open_in_window", False)
            
            b = SimpleButton(self, k, k, is_chat_operation=is_chat_operation)

            b.clicked.connect(partial(self.on_generic_instruction, k))
            self.button_widgets.append(b)

    def rebuild_grid_layout(self, parent_layout=None):
        """Rebuild grid layout with consistent sizing."""
        if not parent_layout:
            parent_layout = self.background.layout()

        # Remove existing grid
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            if isinstance(item, QtWidgets.QGridLayout):
                grid = item
                for j in reversed(range(grid.count())):
                    w = grid.itemAt(j).widget()
                    if w:
                        grid.removeWidget(w)
                parent_layout.removeItem(grid)
                break

        # Create new grid with fixed column width
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 120)
        grid.setColumnMinimumWidth(1, 120)

        # Add buttons to grid
        row = 0
        col = 0
        for b in self.button_widgets:
            grid.addWidget(b, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        parent_layout.addLayout(grid)








    def on_custom_change(self):
        txt = self.custom_input.text().strip()
        if txt:
            self.app.process_option("Custom", self.selected_text, txt)
            self.close()

    def on_generic_instruction(self, instruction):
        self.app.process_option(instruction, self.selected_text)
        self.close()

    def eventFilter(self, obj, event):
        # Hide on deactivate
        if event.type() == QtCore.QEvent.WindowDeactivate:
            self.hide()
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
