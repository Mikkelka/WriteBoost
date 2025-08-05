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

from ui.UIUtils import ThemeBackground, colorMode

_ = lambda x: x


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(sys.argv[0])
    return os.path.join(base_path, relative_path)


################################################################################
# Default `options.json` content to restore when the user presses "Reset"
################################################################################
DEFAULT_OPTIONS_JSON = r"""{
  "Proofread": {
    "prefix": "Proofread this:\n\n",
    "instruction": "You are a grammar proofreading assistant.\nOutput ONLY the corrected text without any additional comments.\nMaintain the original text structure and writing style.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with this (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/magnifying-glass",
    "open_in_window": false
  },
  "Rewrite": {
    "prefix": "Rewrite this:\n\n",
    "instruction": "You are a writing assistant.\nRewrite the text provided by the user to improve phrasing.\nOutput ONLY the rewritten text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with proofreading (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/rewrite",
    "open_in_window": false
  },
  "Friendly": {
    "prefix": "Make this more friendly:\n\n",
    "instruction": "You are a writing assistant.\nRewrite the text provided by the user to be more friendly.\nOutput ONLY the friendly text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/smiley-face",
    "open_in_window": false
  },
  "Professional": {
    "prefix": "Make this more professional:\n\n",
    "instruction": "You are a writing assistant.\nRewrite the text provided by the user to be more professional. Output ONLY the professional text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/briefcase",
    "open_in_window": false
  },
  "Concise": {
    "prefix": "Make this more concise:\n\n",
    "instruction": "You are a writing assistant.\nRewrite the text provided by the user to be more concise.\nOutput ONLY the concise text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with rewriting (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/concise",
    "open_in_window": false
  },
  "Table": {
    "prefix": "Convert this into a table:\n\n",
    "instruction": "You are an assistant that converts text provided by the user into a Markdown table.\nOutput ONLY the table without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is completely incompatible with this with conversion, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/table",
    "open_in_window": true
  },
  "Key Points": {
    "prefix": "Extract key points from this:\n\n",
    "instruction": "You are an assistant that extracts key points from text provided by the user. Output ONLY the key points without additional comments.\n\nYou should use Markdown formatting (lists, bold, italics, codeblocks, etc.) as appropriate to make it quite legible and readable.\n\nDon't be repetitive or too verbose.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with extracting key points (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/keypoints",
    "open_in_window": true
  },
  "Summary": {
    "prefix": "Summarize this:\n\n",
    "instruction": "You are a summarization assistant.\nProvide a succinct summary of the text provided by the user.\nThe summary should be succinct yet encompass all the key insightful points.\n\nTo make it quite legible and readable, you should use Markdown formatting (bold, italics, codeblocks...) as appropriate.\nYou should also add a little line spacing between your paragraphs as appropriate.\nAnd only if appropriate, you could also use headings (only the very small ones), lists, tables, etc.\n\nDon't be repetitive or too verbose.\nOutput ONLY the summary without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with summarisation (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/summary",
    "open_in_window": true
  },
  "Custom": {
    "prefix": "Make this change to the following text:\n\n",
    "instruction": "You are a writing and coding assistant. You MUST make the user\\'s described change to the text or code provided by the user. Output ONLY the appropriately modified text or code without additional comments. Respond in the same language as the input (e.g., English US, French). Do not answer or respond to the user\\'s text content. If the text or code is absolutely incompatible with the requested change, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/summary",
    "open_in_window": false
  }
}"""


class ButtonEditDialog(QDialog):
    """
    Dialog for editing or creating a button's properties
    (name/title, system instruction, open_in_window, etc.).
    """

    def __init__(self, parent=None, button_data=None, title="Edit Button"):
        super().__init__(parent)
        self.button_data = (
            button_data
            if button_data
            else {
                "prefix": "Make this change to the following text:\n\n",
                "instruction": "",
                "icon": "icons/magnifying-glass",
                "open_in_window": False,
            }
        )
        self.setWindowTitle(title)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name
        name_label = QLabel("Button Name:")
        name_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
        """)
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Instruction (changed to a multiline QPlainTextEdit)
        instruction_label = QLabel("What should your AI do with your selected text? (System Instruction)")
        instruction_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(f"""
            QPlainTextEdit {{
                padding: 8px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
        """)
        self.instruction_input.setPlainText(self.button_data.get("instruction", ""))
        self.instruction_input.setMinimumHeight(100)
        self.instruction_input.setPlaceholderText("""Examples:
    - Fix / improve / explain this code.
    - Make it funny.
    - Add emojis!
    - Roast this!
    - Translate to English.
    - Make the text title case.
    - If it's all caps, make it all small, and vice-versa.
    - Write a reply to this.
    - Analyse potential biases in this news article.""")
        layout.addWidget(instruction_label)
        layout.addWidget(self.instruction_input)

        # open_in_window
        display_label = QLabel("How should your AI response be shown?")
        display_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        layout.addWidget(display_label)

        radio_layout = QHBoxLayout()
        self.replace_radio = QRadioButton("Replace the selected text")
        self.window_radio = QRadioButton("In a pop-up window (with follow-up support)")
        for r in (self.replace_radio, self.window_radio):
            r.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'};")

        self.replace_radio.setChecked(not self.button_data.get("open_in_window", False))
        self.window_radio.setChecked(self.button_data.get("open_in_window", False))

        radio_layout.addWidget(self.replace_radio)
        radio_layout.addWidget(self.window_radio)
        layout.addLayout(radio_layout)

        # OK & Cancel
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        for btn in (ok_button, cancel_button):
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#444" if colorMode == "dark" else "#f0f0f0"};
                    color: {"#fff" if colorMode == "dark" else "#000"};
                    border: 1px solid {"#666" if colorMode == "dark" else "#ccc"};
                    border-radius: 5px;
                    padding: 8px;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: {"#555" if colorMode == "dark" else "#e0e0e0"};
                }}
            """)
        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)
        layout.addLayout(btn_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {"#222" if colorMode == "dark" else "#f5f5f5"};
                border-radius: 10px;
            }}
        """)

    def get_button_data(self):
        return {
            "name": self.name_input.text(),
            "prefix": "Make this change to the following text:\n\n",
            # Retrieve multiline text
            "instruction": self.instruction_input.toPlainText(),
            "icon": "icons/custom",
            "open_in_window": self.window_radio.isChecked(),
        }


class DraggableButton(QtWidgets.QPushButton):
    def __init__(self, parent_window, key, text):
        super().__init__(text, parent_window)
        self.window = parent_window
        self.key = key
        self.drag_start_position = None
        self.setAcceptDrops(True)
        self.icon_container = None

        # Enable mouse tracking and hover events, and styled background
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        # Use a dynamic property "hover" (default False)
        self.setProperty("hover", False)

        # Set fixed size (adjust as needed)
        self.setFixedSize(120, 40)

        # Define base style using the dynamic property instead of the :hover pseudo-class
        self.base_style = f"""
            QPushButton {{
                background-color: {"#444" if colorMode == "dark" else "white"};
                border: 1px solid {"#666" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {"#555" if colorMode == "dark" else "#f0f0f0"};
            }}
        """
        self.setStyleSheet(self.base_style)
        logging.debug("DraggableButton initialized")

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

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_start_position = event.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton) or not self.drag_start_position:
            return

        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QtWidgets.QApplication.startDragDistance():
            return

        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()
        idx = self.window.button_widgets.index(self)
        mime_data.setData("application/x-button-index", str(idx).encode())
        drag.setMimeData(mime_data)

        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())

        self.drag_start_position = None
        drop_action = drag.exec_(QtCore.Qt.MoveAction)
        logging.debug(f"Drag completed with action: {drop_action}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-button-index"):
            event.acceptProposedAction()
            self.setStyleSheet(
                self.base_style
                + """
                QPushButton {
                    border: 2px dashed #666;
                }
            """
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.base_style)
        event.accept()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat("application/x-button-index"):
            event.ignore()
            return

        source_idx = int(event.mimeData().data("application/x-button-index").data().decode())
        target_idx = self.window.button_widgets.index(self)

        if source_idx != target_idx:
            bw = self.window.button_widgets
            bw[source_idx], bw[target_idx] = bw[target_idx], bw[source_idx]
            self.window.rebuild_grid_layout()
            self.window.update_json_from_grid()

        self.setStyleSheet(self.base_style)
        event.setDropAction(QtCore.Qt.MoveAction)
        event.acceptProposedAction()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.icon_container:
            self.icon_container.setGeometry(0, 0, self.width(), self.height())


class ButtonEditWindow(QtWidgets.QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.button_widgets = []
        logging.debug("Initializing ButtonEditWindow")
        self.init_ui()

    def init_ui(self):
        logging.debug("Setting up ButtonEditWindow UI")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Edit Writing Tools Buttons")
        self.setFixedSize(500, 600)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        self.background = ThemeBackground(self, "simple", is_popup=False, border_radius=10)
        main_layout.addWidget(self.background)

        content_layout = QtWidgets.QVBoxLayout(self.background)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Title
        title_label = QLabel("Edit Writing Tools Buttons")
        title_label.setStyleSheet(f"""
            color: {"#fff" if colorMode == "dark" else "#333"};
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        # Instructions
        instruction_label = QLabel("Drag to rearrange • Click edit/delete icons to modify buttons")
        instruction_label.setStyleSheet(f"""
            color: {"#aaa" if colorMode == "dark" else "#666"};
            font-size: 12px;
            margin-bottom: 15px;
        """)
        instruction_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(instruction_label)

        # Build buttons
        self.build_buttons_list()
        self.rebuild_grid_layout(content_layout)

        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Add New button
        add_btn = QPushButton("+ Add New")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#2e7d32" if colorMode == "dark" else "#4CAF50"};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {"#1b5e20" if colorMode == "dark" else "#45a049"};
            }}
        """)
        add_btn.clicked.connect(self.add_new_button_clicked)
        button_layout.addWidget(add_btn)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#d32f2f" if colorMode == "dark" else "#f44336"};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {"#b71c1c" if colorMode == "dark" else "#d32f2f"};
            }}
        """)
        reset_btn.clicked.connect(self.on_reset_clicked)
        button_layout.addWidget(reset_btn)

        content_layout.addLayout(button_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#444" if colorMode == "dark" else "#f0f0f0"};
                color: {"#fff" if colorMode == "dark" else "#000"};
                border: 1px solid {"#666" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                margin-top: 10px;
            }}
            QPushButton:hover {{
                background-color: {"#555" if colorMode == "dark" else "#e0e0e0"};
            }}
        """)
        close_btn.clicked.connect(self.close)
        content_layout.addWidget(close_btn)

        logging.debug("ButtonEditWindow UI setup complete")

    @staticmethod
    def load_options():
        options_path = get_resource_path("options.json")
        if os.path.exists(options_path):
            with open(options_path) as f:
                data = json.load(f)
                logging.debug("Options loaded successfully")
        else:
            logging.debug("Options file not found")
            data = {}
        return data

    @staticmethod
    def save_options(options):
        options_path = get_resource_path("options.json")
        with open(options_path, "w") as f:
            json.dump(options, f, indent=2)

    def build_buttons_list(self):
        """
        Reads options.json, creates DraggableButton for each (except "Custom"),
        storing them in self.button_widgets in the same order as the JSON file.
        """
        self.button_widgets.clear()
        data = self.load_options()

        for k, v in data.items():
            if k == "Custom":
                continue
            b = DraggableButton(self, k, k)
            icon_path = get_resource_path(v["icon"] + ("_dark" if colorMode == "dark" else "_light") + ".png")
            if os.path.exists(icon_path):
                b.setIcon(QtGui.QIcon(icon_path))

            self.add_edit_delete_icons(b)
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
        grid.setColumnMinimumWidth(2, 120)

        # Add buttons to grid (3 columns)
        row = 0
        col = 0
        for b in self.button_widgets:
            grid.addWidget(b, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        # Insert grid at the correct position (after title and instructions)
        parent_layout.insertLayout(2, grid)

    def add_edit_delete_icons(self, btn):
        """Add edit/delete icons as overlays with proper spacing."""
        if hasattr(btn, "icon_container") and btn.icon_container:
            btn.icon_container.deleteLater()

        btn.icon_container = QtWidgets.QWidget(btn)
        btn.icon_container.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        btn.icon_container.setGeometry(0, 0, btn.width(), btn.height())

        circle_style = f"""
            QPushButton {{
                background-color: {"#666" if colorMode == "dark" else "#999"};
                border-radius: 10px;
                min-width: 16px;
                min-height: 16px;
                max-width: 16px;
                max-height: 16px;
                padding: 1px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {"#888" if colorMode == "dark" else "#bbb"};
            }}
        """

        # Create edit icon (top-left)
        edit_btn = QPushButton(btn.icon_container)
        edit_btn.setGeometry(3, 3, 16, 16)
        pencil_icon = get_resource_path(
            os.path.join("icons", "pencil" + ("_dark" if colorMode == "dark" else "_light") + ".png")
        )
        if os.path.exists(pencil_icon):
            edit_btn.setIcon(QtGui.QIcon(pencil_icon))
        edit_btn.setStyleSheet(circle_style)
        edit_btn.clicked.connect(partial(self.edit_button_clicked, btn))
        edit_btn.show()

        # Create delete icon (top-right)
        delete_btn = QPushButton(btn.icon_container)
        delete_btn.setGeometry(btn.width() - 23, 3, 16, 16)
        del_icon = get_resource_path(
            os.path.join("icons", "cross" + ("_dark" if colorMode == "dark" else "_light") + ".png")
        )
        if os.path.exists(del_icon):
            delete_btn.setIcon(QtGui.QIcon(del_icon))
        delete_btn.setStyleSheet(circle_style)
        delete_btn.clicked.connect(partial(self.delete_button_clicked, btn))
        delete_btn.show()

        btn.icon_container.raise_()
        btn.icon_container.show()

    def add_new_button_clicked(self):
        dialog = ButtonEditDialog(self, title="Add New Button")
        if dialog.exec_():
            bd = dialog.get_button_data()
            data = self.load_options()
            data[bd["name"]] = {
                "prefix": bd["prefix"],
                "instruction": bd["instruction"],
                "icon": bd["icon"],  # uses 'icons/custom'
                "open_in_window": bd["open_in_window"],
            }
            self.save_options(data)

            self.build_buttons_list()
            self.rebuild_grid_layout()

            QtWidgets.QMessageBox.information(
                self,
                "Button Added",
                f"'{bd['name']}' button has been added successfully!\nRestart Writing Tools to see the new button in action.",
            )

            # Reload app options
            self.app.load_options()

    def edit_button_clicked(self, btn):
        """User clicked the small pencil icon over a button."""
        key = btn.key
        data = self.load_options()
        bd = data[key]
        bd["name"] = key

        dialog = ButtonEditDialog(self, bd)
        if dialog.exec_():
            new_data = dialog.get_button_data()
            data = self.load_options()
            if new_data["name"] != key:
                del data[key]
            data[new_data["name"]] = {
                "prefix": new_data["prefix"],
                "instruction": new_data["instruction"],
                "icon": new_data["icon"],
                "open_in_window": new_data["open_in_window"],
            }
            self.save_options(data)

            self.build_buttons_list()
            self.rebuild_grid_layout()

            QtWidgets.QMessageBox.information(
                self,
                "Button Updated",
                f"'{new_data['name']}' button has been updated successfully!\nRestart Writing Tools to see the changes in action.",
            )

            # Reload app options
            self.app.load_options()

    def delete_button_clicked(self, btn):
        """Handle deletion of a button."""
        key = btn.key
        confirm = QtWidgets.QMessageBox()
        confirm.setWindowTitle("Confirm Delete")
        confirm.setText(f"Are you sure you want to delete the '{key}' button?")
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm.setDefaultButton(QtWidgets.QMessageBox.No)

        if confirm.exec_() == QtWidgets.QMessageBox.Yes:
            try:
                data = self.load_options()
                del data[key]
                self.save_options(data)

                # Clean up UI elements
                for btn_ in self.button_widgets[:]:
                    if btn_.key == key:
                        if hasattr(btn_, "icon_container") and btn_.icon_container:
                            btn_.icon_container.deleteLater()
                        btn_.deleteLater()
                        self.button_widgets.remove(btn_)

                self.rebuild_grid_layout()

                QtWidgets.QMessageBox.information(
                    self,
                    "Button Deleted",
                    f"'{key}' button has been deleted successfully!\nRestart Writing Tools to see the changes in action.",
                )

                # Reload app options
                self.app.load_options()

            except Exception as e:
                logging.error(f"Error deleting button: {e}")
                error_msg = QtWidgets.QMessageBox()
                error_msg.setWindowTitle("Error")
                error_msg.setText(f"An error occurred while deleting the button: {str(e)}")
                error_msg.exec_()

    def on_reset_clicked(self):
        """
        Reset `options.json` to the DEFAULT_OPTIONS_JSON.
        """
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setWindowTitle("Confirm Reset to Defaults")
        confirm_box.setText("Are you sure you want to reset all buttons to their original configuration?\nThis will delete any custom buttons you've created.")
        confirm_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm_box.setDefaultButton(QtWidgets.QMessageBox.No)

        if confirm_box.exec_() == QtWidgets.QMessageBox.Yes:
            try:
                logging.debug("Resetting to default options.json")
                default_data = json.loads(DEFAULT_OPTIONS_JSON)
                self.save_options(default_data)

                self.build_buttons_list()
                self.rebuild_grid_layout()

                QtWidgets.QMessageBox.information(
                    self,
                    "Reset Complete",
                    "All buttons have been reset to their original configuration!\nRestart Writing Tools to see the changes in action.",
                )

                # Reload app options
                self.app.load_options()

            except Exception as e:
                logging.error(f"Error resetting options.json: {e}")
                error_msg = QtWidgets.QMessageBox()
                error_msg.setWindowTitle("Error")
                error_msg.setText(f"An error occurred while resetting: {str(e)}")
                error_msg.exec_()

    def update_json_from_grid(self):
        """
        Called after a drop reorder. Reflect the new order in options.json,
        so that user's custom arrangement persists.
        """
        data = self.load_options()
        new_data = {"Custom": data["Custom"]} if "Custom" in data else {}
        for b in self.button_widgets:
            new_data[b.key] = data[b.key]
        self.save_options(new_data)
        
        # Reload app options
        self.app.load_options()