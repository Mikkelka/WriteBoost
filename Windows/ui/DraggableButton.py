import logging

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt

from ui.UIUtils import colorMode


class DraggableButton(QtWidgets.QPushButton):
    def __init__(self, parent_window, key, text, is_chat_operation=False):
        super().__init__(text, parent_window)
        self.window = parent_window
        self.key = key
        self.is_chat_operation = is_chat_operation
        self.drag_start_position = None
        self.setAcceptDrops(True)
        self.icon_container = None

        # Enable mouse tracking and hover events, and styled background
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        # Use a dynamic property "hover" (default False)
        self.setProperty("hover", False)

        # Set fixed size (adjust as needed) - wider to match Add New/Reset buttons
        self.setFixedSize(200, 50)

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
                padding: 12px 50px 12px 15px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if colorMode == "dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {hover_color};
            }}
        """
        self.setStyleSheet(self.base_style)
        logging.debug(f"DraggableButton initialized - is_chat: {is_chat_operation}")

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
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        if not self.drag_start_position:
            return

        if (event.pos() - self.drag_start_position).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return

        drag = QtGui.QDrag(self)
        mimeData = QtCore.QMimeData()
        mimeData.setText(self.key)
        drag.setMimeData(mimeData)

        dropAction = drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            source_key = event.mimeData().text()
            target_key = self.key

            if source_key != target_key:
                self.window.swap_buttons(source_key, target_key)

            event.accept()
        else:
            event.ignore()

    def contextMenuEvent(self, event):
        context_menu = QtWidgets.QMenu(self)

        edit_action = context_menu.addAction("Edit")
        delete_action = context_menu.addAction("Delete")

        action = context_menu.exec(event.globalPos())
        if action == edit_action:
            self.window.edit_button(self.key)
        elif action == delete_action:
            self.window.delete_button(self.key)