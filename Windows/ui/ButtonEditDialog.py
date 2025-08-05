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

from ui.UIUtils import colorMode

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
  "Summary": {
    "prefix": "Original text to summarize:\n\n",
    "instruction": "You are an expert text summarizer.\nProvide a comprehensive summary of the given text that captures the main points, key details, and overall message.\nUse Markdown formatting with appropriate headers, bullet points, and emphasis where helpful.\nMaintain the tone and style appropriate to the source material.\nEnsure the summary is concise yet complete, typically 20-30% of the original length.",
    "icon": "icons/summary",
    "open_in_window": true
  },
  "Key Points": {
    "prefix": "Original text to extract key points:\n\n",
    "instruction": "You are an expert at extracting key information.\nAnalyze the given text and extract the most important key points.\nPresent the key points as a well-organized list using Markdown formatting.\nUse bullet points or numbered lists as appropriate.\nHighlight the most critical information using **bold** text.\nEnsure each point is clear, concise, and captures essential information.",
    "icon": "icons/keypoints",
    "open_in_window": true
  },
  "Friendly": {
    "prefix": "Make this sound more friendly:\n\n",
    "instruction": "You are a writing assistant focused on tone adjustment.\nRewrite the text to sound more friendly, warm, and approachable while maintaining the core message.\nOutput ONLY the rewritten text without additional comments.\nKeep the same language as the input.\nMaintain professionalism while adding warmth.\nIf the text is incompatible with this request, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/smiley-face",
    "open_in_window": false
  },
  "Professional": {
    "prefix": "Make this sound more professional:\n\n",
    "instruction": "You are a writing assistant focused on professional tone.\nRewrite the text to sound more professional, formal, and business-appropriate while maintaining the core message.\nOutput ONLY the rewritten text without additional comments.\nKeep the same language as the input.\nUse appropriate professional vocabulary and structure.\nIf the text is incompatible with this request, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/briefcase",
    "open_in_window": false
  },
  "Concise": {
    "prefix": "Make this more concise:\n\n",
    "instruction": "You are a writing assistant focused on brevity.\nRewrite the text to be more concise and to-the-point while preserving all essential information and meaning.\nOutput ONLY the rewritten text without additional comments.\nKeep the same language as the input.\nEliminate redundancy, filler words, and unnecessary elaboration.\nIf the text is incompatible with this request, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
    "icon": "icons/concise",
    "open_in_window": false
  },
  "Custom": {
    "prefix": "",
    "instruction": "You are a helpful writing assistant. Follow the user's instructions precisely and provide clear, accurate assistance with their text.",
    "icon": "icons/custom",
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
        layout.addWidget(instruction_label)
        layout.addWidget(self.instruction_input)

        # Prefix
        prefix_label = QLabel("Prefix (text added before your selected text):")
        prefix_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        self.prefix_input = QLineEdit()
        self.prefix_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
        """)
        self.prefix_input.setText(self.button_data.get("prefix", ""))
        layout.addWidget(prefix_label)
        layout.addWidget(self.prefix_input)

        # Icon
        icon_label = QLabel("Icon (without .png/.svg, e.g., 'icons/magnifying-glass'):")
        icon_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        self.icon_input = QLineEdit()
        self.icon_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if colorMode == "dark" else "white"};
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
        """)
        self.icon_input.setText(self.button_data.get("icon", ""))
        layout.addWidget(icon_label)
        layout.addWidget(self.icon_input)

        # Open in window
        window_label = QLabel("Display Mode:")
        window_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        layout.addWidget(window_label)

        self.replace_radio = QRadioButton("Replace selected text directly")
        self.window_radio = QRadioButton("Open result in a new window")
        self.replace_radio.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'};")
        self.window_radio.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'};")

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
        button_style = f"""
            QPushButton {{
                padding: 8px 16px;
                border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#444" if colorMode == "dark" else "white"};
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
            QPushButton:hover {{
                background-color: {"#555" if colorMode == "dark" else "#f0f0f0"};
            }}
        """
        self.ok_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Set dialog style
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {"#2b2b2b" if colorMode == "dark" else "#f0f0f0"};
            }}
        """)

    def get_button_data(self):
        """Return the button data from the dialog"""
        return {
            "name": self.name_input.text().strip(),
            "prefix": self.prefix_input.text(),
            "instruction": self.instruction_input.toPlainText(),
            "icon": self.icon_input.text().strip(),
            "open_in_window": self.window_radio.isChecked(),
        }