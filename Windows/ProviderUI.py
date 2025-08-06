"""
Provider UI Components for Writing Tools
---------------------------------------

This module contains UI components for provider settings like TextSetting and DropdownSetting.
"""

from PySide6 import QtWidgets
from PySide6.QtWidgets import QVBoxLayout

from ProviderInterfaces import AIProviderSetting


class TextSetting(AIProviderSetting):
    """
    A text-based setting (for API keys, URLs, etc.).
    """

    def __init__(self, name: str, display_name: str = None, default_value: str = None, description: str = None):
        super().__init__(name, display_name, default_value, description)
        self.internal_value = default_value
        self.input = None

    def render_to_layout(self, layout: QVBoxLayout):
        # Label
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet("font-size: 14px; color: #ffffff; margin-bottom: 4px;")
        layout.addWidget(label)

        # Input field
        self.input = QtWidgets.QLineEdit(self.internal_value)
        self.input.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #606060;
            border-radius: 4px;
            margin-bottom: 10px;
        """)
        layout.addWidget(self.input)

        # Description
        if self.description:
            desc_label = QtWidgets.QLabel(self.description)
            desc_label.setStyleSheet("font-size: 12px; color: #bbbbbb; margin-bottom: 15px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

    def set_value(self, value):
        self.internal_value = str(value) if value is not None else ""
        if self.input:
            self.input.setText(self.internal_value)

    def get_value(self):
        if self.input:
            return self.input.text()
        return self.internal_value


class DropdownSetting(AIProviderSetting):
    """
    A dropdown/combobox setting for selecting from predefined options.
    """

    def __init__(
        self,
        name: str,
        display_name: str = None,
        default_value: str = None,
        description: str = None,
        options: list = None,
    ):
        super().__init__(name, display_name, default_value, description)
        self.options = options if options else []  # List of (display_text, value) tuples
        self.internal_value = default_value
        self.dropdown = None

    def render_to_layout(self, layout: QVBoxLayout):
        # Label
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet("font-size: 14px; color: #ffffff; margin-bottom: 4px;")
        layout.addWidget(label)

        # Dropdown
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #606060;
            border-radius: 4px;
            margin-bottom: 10px;
        """)

        # Populate options
        for display_text, value in self.options:
            self.dropdown.addItem(display_text, value)

        # Set current value
        if self.internal_value:
            index = self.dropdown.findData(self.internal_value)
            if index >= 0:
                self.dropdown.setCurrentIndex(index)

        layout.addWidget(self.dropdown)

        # Description
        if self.description:
            desc_label = QtWidgets.QLabel(self.description)
            desc_label.setStyleSheet("font-size: 12px; color: #bbbbbb; margin-bottom: 15px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

    def set_value(self, value):
        self.internal_value = str(value) if value is not None else ""
        if self.dropdown:
            index = self.dropdown.findData(self.internal_value)
            if index >= 0:
                self.dropdown.setCurrentIndex(index)

    def get_value(self):
        if self.dropdown:
            return self.dropdown.currentData()
        return self.internal_value