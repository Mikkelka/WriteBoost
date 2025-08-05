import logging
import threading

from PySide6.QtCore import QObject, Signal


class ConversationManager(QObject):
    """Handles follow-up questions and conversations"""
    
    followup_response_signal = Signal(str)
    show_message_signal = Signal(str, str)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app

    def process_followup_question(self, response_window, question, model=None, thinking_budget=None):
        """
        Process a follow-up question in the chat window.
        """
        logging.debug(f"Processing follow-up question: {question} with model: {model}, thinking: {thinking_budget}")

        def process_thread():
            logging.debug("Starting follow-up processing thread")
            try:
                # Get current chat history using the message manager
                chat_history = response_window.message_manager.get_chat_history()

                # Add current question to chat history
                response_window.message_manager.add_user_message(question)

                # Get updated chat history
                history = response_window.message_manager.get_chat_history().copy()

                # System instruction from user settings
                system_instruction = getattr(
                    self.app.current_provider,
                    "chat_system_instruction",
                    "You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable.",
                )

                logging.debug("Sending request to AI provider")

                # Format conversation for new Google genai client
                # Build conversation context from history
                conversation_text = system_instruction + "\n\n"

                # Only add previous conversation if there is any
                if len(history) > 1:  # More than just the current question
                    for msg in history[:-1]:  # Exclude the current question
                        if msg["role"] == "user":
                            conversation_text += f"User: {msg['content']}\n\n"
                        else:
                            conversation_text += f"Assistant: {msg['content']}\n\n"

                conversation_text += f"User: {question}\n\nAssistant:"

                # Use the provider's get_response method with return_response=True
                response_text = self.app.current_provider.get_response(
                    system_instruction="",
                    prompt=conversation_text,
                    return_response=True,
                    model=model,
                    thinking_budget=thinking_budget,
                )

                logging.debug(f"Got response of length: {len(response_text)}")

                # Add response to chat history
                response_window.message_manager.add_assistant_message(response_text)

                # Emit response via signal
                self.followup_response_signal.emit(response_text)

            except Exception as e:
                logging.error(f"Error processing follow-up question: {e}", exc_info=True)

                if "Resource has been exhausted" in str(e):
                    self.show_message_signal.emit(
                        "Error - Rate Limit Hit",
                        "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
                    )
                    self.followup_response_signal.emit("Sorry, an error occurred while processing your question.")
                else:
                    self.show_message_signal.emit("Error", f"An error occurred: {e}")
                    self.followup_response_signal.emit("Sorry, an error occurred while processing your question.")

        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()