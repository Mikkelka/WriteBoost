import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets

colorMode = "dark"  # Always dark mode


# Reusable styling functions to reduce code duplication
def get_label_style(bold=False, color_type="normal", font_size=None):
    """
    Get label styling with colorMode support.
    color_type: 'normal', 'muted', 'white'
    """
    if color_type == "normal":
        color = "#fff" if colorMode == "dark" else "#333"
    elif color_type == "muted":
        color = "#aaa" if colorMode == "dark" else "#666"
    elif color_type == "white":
        color = "#fff" if colorMode == "dark" else "#000"
    else:
        color = "#fff" if colorMode == "dark" else "#333"
    
    style = f"color: {color};"
    if bold:
        style += " font-weight: bold;"
    if font_size:
        style += f" font-size: {font_size}px;"
    
    return style


def get_input_style():
    """Get input field styling (QLineEdit, QPlainTextEdit) with colorMode support."""
    return f"""
        padding: 8px;
        border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
        border-radius: 8px;
        background-color: {"#333" if colorMode == "dark" else "white"};
        color: {"#fff" if colorMode == "dark" else "#000"};
    """


def get_button_style(variant="default"):
    """
    Get button styling with colorMode support.
    variant: 'default', 'green', 'red'
    """
    if variant == "green":
        bg_color = "#2e7d32" if colorMode == "dark" else "#4CAF50"
        hover_color = "#1b5e20" if colorMode == "dark" else "#45a049"
        text_color = "white"
    elif variant == "red":
        bg_color = "#d32f2f" if colorMode == "dark" else "#f44336"
        hover_color = "#b71c1c" if colorMode == "dark" else "#d32f2f"
        text_color = "white"
    else:  # default
        bg_color = "#444" if colorMode == "dark" else "white"
        hover_color = "#555" if colorMode == "dark" else "#f0f0f0"
        text_color = "#fff" if colorMode == "dark" else "#000"
    
    return f"""
        QPushButton {{
            padding: 8px 16px;
            border: 1px solid {"#777" if colorMode == "dark" else "#ccc"};
            border-radius: 8px;
            background-color: {bg_color};
            color: {text_color};
            font-size: 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
    """


def get_title_style(font_size=18):
    """Get title/header styling with colorMode support."""
    return f"""
        color: {"#fff" if colorMode == "dark" else "#333"};
        font-size: {font_size}px;
        font-weight: bold;
        margin-bottom: 10px;
    """


def get_dialog_style():
    """Get dialog background styling with colorMode support."""
    return f"""
        QDialog {{
            background-color: {"#2b2b2b" if colorMode == "dark" else "#f0f0f0"};
        }}
    """


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(sys.argv[0])
    return os.path.join(base_path, relative_path)


class UIUtils:
    @classmethod
    def clear_layout(cls, layout):
        """
        Clear the layout of all widgets.
        """
        while (child := layout.takeAt(0)) != None:
            # If the child is a layout, delete it
            if child.layout():
                cls.clear_layout(child.layout())
                child.layout().deleteLater()
            else:
                child.widget().deleteLater()


    @classmethod
    def setup_window_and_layout(cls, base: QtWidgets.QWidget):
        # Set the window icon
        icon_path = get_resource_path(os.path.join("icons", "app_icon.png"))
        if os.path.exists(icon_path):
            base.setWindowIcon(QtGui.QIcon(icon_path))
        main_layout = QtWidgets.QVBoxLayout(base)
        main_layout.setContentsMargins(0, 0, 0, 0)
        base.background = ThemeBackground(base)
        main_layout.addWidget(base.background)


class ThemeBackground(QtWidgets.QWidget):
    """
    A custom widget that creates a simple solid color background for the application.
    """

    def __init__(self, parent=None, border_radius=0):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.border_radius = border_radius

    def paintEvent(self, event):
        """
        Override the paint event to draw a solid color background.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        
        # Use solid color backgrounds only
        if colorMode == "dark":
            color = QtGui.QColor(35, 35, 35)  # Dark mode color
        else:
            color = QtGui.QColor(222, 222, 222)  # Light mode color
        
        brush = QtGui.QBrush(color)
        painter.setBrush(brush)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawRoundedRect(
            QtCore.QRect(0, 0, self.width(), self.height()), self.border_radius, self.border_radius
        )
