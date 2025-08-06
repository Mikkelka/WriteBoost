import markdown2
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea

from ui.MarkdownDisplay import MarkdownTextBrowser


class ChatContentScrollArea(QScrollArea):
    """Improved scrollable container for chat messages with dynamic sizing and proper spacing"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.content_widget = None
        self.layout = None
        self.setup_ui()

    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Main container widget with explicit size policy
        self.content_widget = QtWidgets.QWidget()
        self.content_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.MinimumExpanding
        )
        self.setWidget(self.content_widget)

        # Main layout with improved spacing
        self.layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.layout.setSpacing(8)  # Reduced spacing between messages
        self.layout.setContentsMargins(15, 15, 15, 15)  # Adjusted margins
        self.layout.addStretch()

        # Enhanced scroll area styling
        self.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(128, 128, 128, 0.5);
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

    def add_message(self, text, is_user=False):
        # Remove bottom stretch
        self.layout.takeAt(self.layout.count() - 1)

        # Create message container with improved width
        msg_container = QtWidgets.QWidget()
        msg_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)

        # Message layout with minimal margins
        msg_layout = QtWidgets.QVBoxLayout(msg_container)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(0)

        # Create text display with updated width
        text_display = MarkdownTextBrowser(is_user_message=is_user)

        # Enable tables extension in markdown2
        html = markdown2.markdown(text, extras=["tables"])
        text_display.setHtml(html)

        # Calculate proper text display size using full width
        text_display.document().setTextWidth(self.width() - 20)
        doc_size = text_display.document().size()
        text_display.setMinimumHeight(int(doc_size.height() + 16))

        msg_layout.addWidget(text_display)

        self.layout.addWidget(msg_container)
        self.layout.addStretch()

        if hasattr(self.parent(), "current_text_display"):
            self.parent().current_text_display = text_display

        QtCore.QTimer.singleShot(50, self.post_message_updates)

        return text_display

    def post_message_updates(self):
        """Handle updates after adding a message with proper timing"""
        self.scroll_to_bottom()
        if hasattr(self.parent(), '_adjust_window_height'):
            self.parent()._adjust_window_height()

    def update_content_height(self):
        """Recalculate total content height with improved spacing calculation"""
        total_height = 0

        # Calculate height of all messages
        for i in range(self.layout.count() - 1):  # Skip stretch item
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget_height = item.widget().sizeHint().height()
                total_height += widget_height

        # Add spacing between messages and margins
        total_height += self.layout.spacing() * (self.layout.count() - 2)  # Message spacing
        total_height += self.layout.contentsMargins().top() + self.layout.contentsMargins().bottom()

        # Set minimum height with some padding
        self.content_widget.setMinimumHeight(total_height + 10)

        # Update window height if needed
        if hasattr(self.parent(), '_adjust_window_height'):
            self.parent()._adjust_window_height()

    def scroll_to_bottom(self):
        """Smooth scroll to bottom of content"""
        vsb = self.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def resizeEvent(self, event):
        """Handle resize events with improved width calculations"""
        super().resizeEvent(event)

        # Update width for all message displays
        available_width = self.width() - 40  # Account for margins
        for i in range(self.layout.count() - 1):  # Skip stretch item
            item = self.layout.itemAt(i)
            if item and item.widget():
                container = item.widget()
                text_display = container.layout().itemAt(0).widget()
                if isinstance(text_display, MarkdownTextBrowser):
                    # Recalculate text width and height
                    text_display.document().setTextWidth(available_width)
                    doc_size = text_display.document().size()
                    text_display.setMinimumHeight(int(doc_size.height() + 20))  # Reduced padding