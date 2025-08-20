from datetime import datetime
import json
import logging
import os
import sys
from typing import Dict, List, Optional




class ChatManager:
    """Manages saving and loading of chat histories"""

    def __init__(self):
        self.chats_file = os.path.join(os.path.dirname(sys.argv[0]), "saved_chats.json")

    def save_chat(self, title: str, chat_history: List[Dict], chat_id: Optional[str] = None) -> str:
        """
        Save a chat with the given title and history.
        Returns the chat ID.
        """
        try:
            # Load existing chats
            chats = self.load_all_chats()

            # Generate ID if not provided
            if not chat_id:
                chat_id = f"chat_{int(datetime.now().timestamp())}"

            # Create chat data
            chat_data = {
                "id": chat_id,
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "chat_history": chat_history,
            }

            # Add or update chat
            existing_index = next((i for i, chat in enumerate(chats) if chat["id"] == chat_id), None)
            if existing_index is not None:
                chats[existing_index] = chat_data
            else:
                chats.append(chat_data)

            # Save to file
            self._save_chats(chats)
            logging.debug(f"Chat saved with ID: {chat_id}")
            return chat_id

        except Exception as e:
            logging.error(f"Error saving chat: {e}")
            raise

    def load_all_chats(self) -> List[Dict]:
        """Load all saved chats"""
        try:
            if os.path.exists(self.chats_file):
                with open(self.chats_file, encoding="utf-8") as f:
                    chats = json.load(f)
                    # Sort by timestamp, newest first
                    return sorted(chats, key=lambda x: x["timestamp"], reverse=True)
            return []
        except Exception as e:
            logging.error(f"Error loading chats: {e}")
            return []

    def load_chat(self, chat_id: str) -> Optional[Dict]:
        """Load a specific chat by ID"""
        chats = self.load_all_chats()
        return next((chat for chat in chats if chat["id"] == chat_id), None)

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat by ID"""
        try:
            chats = self.load_all_chats()
            chats = [chat for chat in chats if chat["id"] != chat_id]
            self._save_chats(chats)
            logging.debug(f"Chat deleted: {chat_id}")
            return True
        except Exception as e:
            logging.error(f"Error deleting chat: {e}")
            return False

    def _save_chats(self, chats: List[Dict]):
        """Save chats to file"""
        with open(self.chats_file, "w", encoding="utf-8") as f:
            json.dump(chats, f, indent=2, ensure_ascii=False)

    def generate_chat_title(self, chat_history: List[Dict]) -> str:
        """Generate a title for a chat based on its content"""
        if not chat_history:
            return f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Get first user message content
        first_message = next((msg["content"] for msg in chat_history if msg["role"] == "user"), "")

        # Clean up the message for title
        if first_message:
            # Remove "Original text to X:" prefix if present
            if "Original text to" in first_message and ":\n\n" in first_message:
                first_message = first_message.split(":\n\n", 1)[1]

            # Truncate and clean
            title = first_message.strip()[:50]
            if len(first_message) > 50:
                title += "..."
            return title

        return f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
