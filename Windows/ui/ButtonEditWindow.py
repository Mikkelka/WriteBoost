from functools import partial
import json
import logging
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ui.UIUtils import ThemeBackground, colorMode, get_resource_path, get_title_style, get_label_style, get_button_style
from ui.ButtonEditDialog import ButtonEditDialog
from ui.DraggableButton import DraggableButton

_ = lambda x: x




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

        self.background = ThemeBackground(self, border_radius=10)
        main_layout.addWidget(self.background)

        content_layout = QtWidgets.QVBoxLayout(self.background)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # Title
        title_label = QLabel("Edit Writing Tools Buttons")
        title_label.setStyleSheet(get_title_style())
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)

        # Instructions
        instruction_label = QLabel("Drag to rearrange • Click edit/delete icons to modify buttons")
        instruction_label.setStyleSheet(get_label_style(color_type="muted", font_size=12) + " margin-bottom: 15px;")
        instruction_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(instruction_label)

        # Build buttons
        self.build_buttons_list()
        self.rebuild_grid_layout(content_layout)

        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Add New button
        add_btn = QPushButton("+ Add New")
        add_btn.setStyleSheet(get_button_style("green"))
        add_btn.clicked.connect(self.add_new_button_clicked)
        button_layout.addWidget(add_btn)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet(get_button_style("red"))
        reset_btn.clicked.connect(self.on_reset_clicked)
        button_layout.addWidget(reset_btn)

        content_layout.addLayout(button_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(get_button_style() + " margin-top: 10px;")
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
    def load_default_options():
        """
        Load the original default options. This replaces the need for DEFAULT_OPTIONS_JSON.
        """
        return {
            "Proofread": {
                "prefix": "Proofread this:\n\n",
                "instruction": "You are a grammar proofreading assistant.\nOutput ONLY the corrected text without any additional comments.\nMaintain the original text structure and writing style.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with this (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
                "open_in_window": False
            },
            "Rewrite": {
                "prefix": "Rewrite this:\n\n",
                "instruction": "You are a writing assistant.\nRewrite the text provided by the user to improve phrasing.\nOutput ONLY the rewritten text without additional comments.\nRespond in the same language as the input (e.g., English US, French).\nDo not answer or respond to the user's text content.\nIf the text is absolutely incompatible with proofreading (e.g., totally random gibberish), output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
                "open_in_window": False
            },
            "Summary": {
                "prefix": "Original text to summarize:\n\n",
                "instruction": "You are an expert text summarizer.\nProvide a comprehensive summary of the given text that captures the main points, key details, and overall message.\nUse Markdown formatting with appropriate headers, bullet points, and emphasis where helpful.\nMaintain the tone and style appropriate to the source material.\nEnsure the summary is concise yet complete, typically 20-30% of the original length.",
                "open_in_window": True
            },
            "Key Points": {
                "prefix": "Original text to extract key points:\n\n",
                "instruction": "You are an expert at extracting key information.\nAnalyze the given text and extract the most important key points.\nPresent the key points as a well-organized list using Markdown formatting.\nUse bullet points or numbered lists as appropriate.\nHighlight the most critical information using **bold** text.\nEnsure each point is clear, concise, and captures essential information.",
                "open_in_window": True
            },
            "Friendly": {
                "prefix": "Make this sound more friendly:\n\n",
                "instruction": "You are a writing assistant focused on tone adjustment.\nRewrite the text to sound more friendly, warm, and approachable while maintaining the core message.\nOutput ONLY the rewritten text without additional comments.\nKeep the same language as the input.\nMaintain professionalism while adding warmth.\nIf the text is incompatible with this request, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
                "open_in_window": False
            },
            "Professional": {
                "prefix": "Make this sound more professional:\n\n",
                "instruction": "You are a writing assistant focused on professional tone.\nRewrite the text to sound more professional, formal, and business-appropriate while maintaining the core message.\nOutput ONLY the rewritten text without additional comments.\nKeep the same language as the input.\nUse appropriate professional vocabulary and structure.\nIf the text is incompatible with this request, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
                "open_in_window": False
            },
            "Concise": {
                "prefix": "Make this more concise:\n\n",
                "instruction": "You are a writing assistant focused on brevity.\nRewrite the text to be more concise and to-the-point while preserving all essential information and meaning.\nOutput ONLY the rewritten text without additional comments.\nKeep the same language as the input.\nEliminate redundancy, filler words, and unnecessary elaboration.\nIf the text is incompatible with this request, output \"ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST\".",
                "open_in_window": False
            },
            "Custom": {
                "prefix": "",
                "instruction": "You are a helpful writing assistant. Follow the user's instructions precisely and provide clear, accurate assistance with their text.",
                "open_in_window": False
            }
        }

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
            
            # Check if this operation opens in a chat window
            is_chat_operation = v.get("open_in_window", False)
            
            b = DraggableButton(self, k, k, is_chat_operation=is_chat_operation)

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

        # Create new grid with fixed column width (2 columns for wider buttons)
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.setColumnMinimumWidth(0, 200)
        grid.setColumnMinimumWidth(1, 200)

        # Add buttons to grid (2 columns)
        row = 0
        col = 0
        for b in self.button_widgets:
            grid.addWidget(b, row, col)
            col += 1
            if col > 1:
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

        # Calculate vertical center for icon positioning
        center_y = (btn.height() - 16) // 2
        
        # Create edit icon (center-right, first position)
        edit_btn = QPushButton(btn.icon_container)
        edit_btn.setGeometry(btn.width() - 45, center_y, 16, 16)
        pencil_icon = get_resource_path(
            os.path.join("icons", "pencil" + ("_dark" if colorMode == "dark" else "_light") + ".png")
        )
        if os.path.exists(pencil_icon):
            edit_btn.setIcon(QtGui.QIcon(pencil_icon))
        edit_btn.setStyleSheet(circle_style)
        edit_btn.clicked.connect(partial(self.edit_button_clicked, btn))
        edit_btn.show()

        # Create delete icon (center-right, second position)
        delete_btn = QPushButton(btn.icon_container)
        delete_btn.setGeometry(btn.width() - 23, center_y, 16, 16)
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
            
            # Create new ordered data with existing buttons first
            new_data = {}
            
            # Add existing buttons first
            for key, value in data.items():
                if key != "Custom":  # Skip Custom section for now
                    new_data[key] = value
            
            # Add new button at the end
            new_data[bd["name"]] = {
                "prefix": bd["prefix"],
                "instruction": bd["instruction"],
                "open_in_window": bd["open_in_window"],
            }
                    
            # Add Custom section at the end if it exists
            if "Custom" in data:
                new_data["Custom"] = data["Custom"]
                
            self.save_options(new_data)

            self.build_buttons_list()
            self.rebuild_grid_layout()

            QtWidgets.QMessageBox.information(
                self,
                "Button Added",
                f"'{bd['name']}' button has been added successfully!\nRestart Writing Tools to see the new button in action.",
            )

            # Reload app options
            self.app.config_manager.load_options()
            self.app.options = self.app.config_manager.options

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
            self.app.config_manager.load_options()
            self.app.options = self.app.config_manager.options

    def delete_button_clicked(self, btn):
        """Handle deletion of a button."""
        key = btn.key
        
        # Confirmation dialog - set parent to None to ensure it stays on top
        confirm = QtWidgets.QMessageBox(None)
        confirm.setWindowTitle("Confirm Delete")
        confirm.setText(f"Are you sure you want to delete the '{key}' button?")
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm.setWindowFlags(confirm.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        
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
                self.app.config_manager.load_options()
                self.app.options = self.app.config_manager.options

            except Exception as e:
                logging.error(f"Error deleting button: {e}")
                error_msg = QtWidgets.QMessageBox()
                error_msg.setWindowTitle("Error")
                error_msg.setText(f"An error occurred while deleting the button: {str(e)}")
                error_msg.exec_()

    def on_reset_clicked(self):
        """
        Reset `options.json` to the default options.
        """
        try:
            logging.debug("Resetting to default options.json")
            default_data = self.load_default_options()
            self.save_options(default_data)

            self.build_buttons_list()
            self.rebuild_grid_layout()

            QtWidgets.QMessageBox.information(
                self,
                "Reset Complete",
                "All buttons have been reset to their original configuration!\nRestart Writing Tools to see the changes in action.",
            )

            # Reload app options
            self.app.config_manager.load_options()
            self.app.options = self.app.config_manager.options

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
        new_data = {}
        
        # Add buttons in their current UI order
        for b in self.button_widgets:
            new_data[b.key] = data[b.key]
            
        # Add Custom section at the end if it exists
        if "Custom" in data:
            new_data["Custom"] = data["Custom"]
            
        self.save_options(new_data)
        
        # Reload app options
        self.app.config_manager.load_options()
        self.app.options = self.app.config_manager.options

    def swap_buttons(self, source_key, target_key):
        """Swap two buttons in the grid and update JSON order"""
        # Find the buttons in our list
        source_idx = target_idx = -1
        for i, btn in enumerate(self.button_widgets):
            if btn.key == source_key:
                source_idx = i
            elif btn.key == target_key:
                target_idx = i

        if source_idx != -1 and target_idx != -1:
            # Swap in our list
            self.button_widgets[source_idx], self.button_widgets[target_idx] = (
                self.button_widgets[target_idx], 
                self.button_widgets[source_idx]
            )
            
            # Rebuild the UI and update JSON
            self.rebuild_grid_layout()
            self.update_json_from_grid()

    def edit_button(self, key):
        """Edit button - called from DraggableButton context menu"""
        # Find the button
        for btn in self.button_widgets:
            if btn.key == key:
                self.edit_button_clicked(btn)
                break

    def delete_button(self, key):
        """Delete button - called from DraggableButton context menu"""
        # Find the button
        for btn in self.button_widgets:
            if btn.key == key:
                self.delete_button_clicked(btn)
                break