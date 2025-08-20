import os
import sys
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from ui.UIUtils import colorMode, get_resource_path




class MarkdownTextBrowser(QtWidgets.QTextBrowser):
    """Enhanced text browser for displaying Markdown content with improved sizing"""

    def __init__(self, parent=None, is_user_message=False):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.zoom_factor = 1.2
        self.base_font_size = 14
        self.is_user_message = is_user_message

        # Critical: Remove scrollbars to prevent extra space
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Set size policies to prevent unwanted expansion
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)

        self._apply_zoom()

    def _apply_zoom(self):
        new_size = int(self.base_font_size * self.zoom_factor)

        # Updated stylesheet with table styling
        if self.is_user_message:
            # User message styling - blue/green tint
            bg_color = "#2a3f5f" if colorMode == "dark" else "#e3f2fd"
            border_color = "#4a6fa5" if colorMode == "dark" else "#90caf9"
        else:
            # AI message styling - neutral
            bg_color = "#333" if colorMode == "dark" else "white"
            border_color = "#555" if colorMode == "dark" else "#ccc"

        self.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {bg_color};
                color: {"#ffffff" if colorMode == "dark" else "#000000"};
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px;
                margin: 0px;
                font-size: {new_size}px;
                line-height: 1.3;
                width: 100%;
            }}

            /* Table styles */
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }}
            
            th, td {{
                border: 1px solid {"#555" if colorMode == "dark" else "#ccc"};
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: {"#444" if colorMode == "dark" else "#f5f5f5"};
                font-weight: bold;
            }}
            
            tr:nth-child(even) {{
                background-color: {"#3a3a3a" if colorMode == "dark" else "#f9f9f9"};
            }}
            
            tr:hover {{
                background-color: {"#484848" if colorMode == "dark" else "#f0f0f0"};
            }}
        """)

    def _update_size(self):
        # Calculate correct document width
        available_width = self.viewport().width() - 16  # Account for padding
        self.document().setTextWidth(available_width)

        # Get precise content height
        doc_size = self.document().size()
        content_height = doc_size.height()

        # Add minimal padding for content
        new_height = int(content_height + 16)  # Reduced total padding

        if self.minimumHeight() != new_height:
            self.setMinimumHeight(new_height)
            self.setMaximumHeight(new_height)  # Force fixed height

            # Update scroll area if needed
            scroll_area = self.get_scroll_area()
            if scroll_area:
                scroll_area.update_content_height()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            # Get the main response window
            parent = self.parent()
            while parent and not hasattr(parent, 'zoom_all_messages'):
                parent = parent.parent()

            if parent:
                if delta > 0:
                    parent.zoom_all_messages("in")
                else:
                    parent.zoom_all_messages("out")
                event.accept()
        else:
            # Pass wheel events to parent for scrolling
            if self.parent():
                self.parent().wheelEvent(event)

    def zoom_in(self):
        old_factor = self.zoom_factor
        self.zoom_factor = min(3.0, self.zoom_factor * 1.1)
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()

    def zoom_out(self):
        old_factor = self.zoom_factor
        self.zoom_factor = max(0.5, self.zoom_factor / 1.1)
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()

    def reset_zoom(self):
        old_factor = self.zoom_factor
        self.zoom_factor = 1.2  # Reset to default zoom
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()

    def get_scroll_area(self):
        """Find the parent ChatContentScrollArea"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'update_content_height'):  # Check for ChatContentScrollArea method
                return parent
            parent = parent.parent()
        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_size()