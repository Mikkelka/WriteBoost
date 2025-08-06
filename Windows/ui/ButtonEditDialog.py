import json
import logging
import os
import sys

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from ui.UIUtils import colorMode, get_resource_path, get_label_style, get_input_style, get_button_style, get_dialog_style

_ = lambda x: x






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
                "open_in_window": False,
            }
        )
        self.setWindowTitle(title)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name
        name_label = QLabel("Button Name:")
        name_label.setStyleSheet(get_label_style(bold=True))
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(f"QLineEdit {{ {get_input_style()} }}")
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Instruction (changed to a multiline QPlainTextEdit)
        instruction_label = QLabel("What should your AI do with your selected text? (System Instruction)")
        instruction_label.setStyleSheet(get_label_style(bold=True))
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(f"QPlainTextEdit {{ {get_input_style()} }}")
        self.instruction_input.setPlainText(self.button_data.get("instruction", ""))
        layout.addWidget(instruction_label)
        layout.addWidget(self.instruction_input)

        # Prefix
        prefix_label = QLabel("Prefix (text added before your selected text):")
        prefix_label.setStyleSheet(get_label_style(bold=True))
        self.prefix_input = QLineEdit()
        self.prefix_input.setStyleSheet(f"QLineEdit {{ {get_input_style()} }}")
        self.prefix_input.setText(self.button_data.get("prefix", ""))
        layout.addWidget(prefix_label)
        layout.addWidget(self.prefix_input)


        # Open in window
        window_label = QLabel("Display Mode:")
        window_label.setStyleSheet(get_label_style(bold=True))
        layout.addWidget(window_label)

        self.replace_radio = QRadioButton("Replace selected text directly")
        self.window_radio = QRadioButton("Open result in a new window")
        self.replace_radio.setStyleSheet(get_label_style())
        self.window_radio.setStyleSheet(get_label_style())

        # Set default selection
        if self.button_data.get("open_in_window", False):
            self.window_radio.setChecked(True)
        else:
            self.replace_radio.setChecked(True)

        layout.addWidget(self.replace_radio)
        layout.addWidget(self.window_radio)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        # Style buttons
        button_style = get_button_style()
        self.ok_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Set dialog style
        self.setStyleSheet(get_dialog_style())

    def get_button_data(self):
        """Return the button data from the dialog"""
        return {
            "name": self.name_input.text().strip(),
            "prefix": self.prefix_input.text(),
            "instruction": self.instruction_input.toPlainText(),
            "open_in_window": self.window_radio.isChecked(),
        }