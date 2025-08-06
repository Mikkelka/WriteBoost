import logging
from PySide6 import QtWidgets


class ChatMessageManager:
    """Handles chat message logic and operations"""

    def __init__(self, chat_history=None):
        self.chat_history = chat_history or []

    def get_first_response_text(self):
        """Get the first model response text from chat history"""
        try:
            # Check chat history exists
            if not self.chat_history:
                return None

            # Find first assistant message
            for msg in self.chat_history:
                if msg["role"] == "assistant":
                    return msg["content"]

            return None
        except Exception as e:
            logging.error(f"Error getting first response: {e}")
            return None

    def copy_first_response_to_clipboard(self):
        """Copy only the first model response as Markdown"""
        response_text = self.get_first_response_text()
        if response_text:
            QtWidgets.QApplication.clipboard().setText(response_text)
            return True
        return False

    def copy_conversation_as_markdown(self):
        """Copy entire conversation as Markdown"""
        markdown = ""
        for msg in self.chat_history:
            if msg["role"] == "user":
                markdown += f"**User**: {msg['content']}\n\n"
            else:
                markdown += f"**Assistant**: {msg['content']}\n\n"

        if markdown:
            QtWidgets.QApplication.clipboard().setText(markdown)
            return True
        return False

    def add_user_message(self, message):
        """Add a user message to chat history"""
        self.chat_history.append({"role": "user", "content": message})

    def add_assistant_message(self, message):
        """Add an assistant message to chat history"""
        self.chat_history.append({"role": "assistant", "content": message})

    def has_messages(self):
        """Check if there are any messages in chat history"""
        return len(self.chat_history) > 0

    def get_chat_history(self):
        """Get the complete chat history"""
        return self.chat_history

    def set_chat_history(self, history):
        """Set the chat history"""
        self.chat_history = history or []

    def extract_user_display_text(self, user_message):
        """Extract appropriate display text from user message"""
        # For operations like Summary/Key Points, extract and show just the selected text
        if user_message.startswith("Original text to"):
            # Extract the actual text after "Original text to X:\n\n"
            if ":\n\n" in user_message:
                actual_text = user_message.split(":\n\n", 1)[1]
                if actual_text.strip():  # Only return if there's actual content
                    return actual_text
        
        # For custom prompts without selected text, show the actual user question
        return user_message