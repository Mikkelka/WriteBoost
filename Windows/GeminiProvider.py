"""
Gemini AI Provider Implementation
--------------------------------

This module contains the GeminiProvider class that implements the AIProvider interface
for Google's Gemini API using the new genai.Client approach.
"""

from datetime import datetime
import logging
import webbrowser

# External libraries
from google import genai
from google.genai import types
from PySide6.QtWidgets import QVBoxLayout

from ProviderInterfaces import AIProvider
from ProviderUI import TextSetting, DropdownSetting


class GeminiProvider(AIProvider):
    """
    Provider for Google's Gemini API using the new genai.Client approach.
    """

    def __init__(self, app):
        self.close_requested = False
        self.client = None

        settings = [
            TextSetting(name="api_key", display_name="API Key", description="Paste your Gemini API key here"),
            DropdownSetting(
                name="chat_model_name",
                display_name="Chat Model",
                default_value="gemini-2.5-flash",
                description="Model for chat conversations and follow-up questions",
                options=[
                    ("Gemini 2.5 Flash (most intelligent | fast | 10 uses/min)", "gemini-2.5-flash"),
                    (
                        "Gemini 2.5 Flash Lite (faster | lightweight | 15 uses/min)",
                        "gemini-2.5-flash-lite",
                    ),
                ],
            ),
            DropdownSetting(
                name="text_model_name",
                display_name="Text Operations Model",
                default_value="gemini-2.5-flash-lite",
                description="Model for text operations (Proofread, Rewrite, etc.)",
                options=[
                    ("Gemini 2.5 Flash (most intelligent | fast | 10 uses/min)", "gemini-2.5-flash"),
                    (
                        "Gemini 2.5 Flash Lite (faster | lightweight | 15 uses/min)",
                        "gemini-2.5-flash-lite",
                    ),
                ],
            ),
            TextSetting(
                name="chat_system_instruction",
                display_name="Chat System Instruction",
                default_value="You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable.",
                description="System instruction for custom chat and follow-up questions (does not affect text operations like Proofread, Rewrite, etc.)",
            ),
        ]
        super().__init__(
            app,
            "Gemini",
            settings,
            "• Google's Gemini is a powerful AI model available for free!\n"
            "• An API key is required to connect to Gemini on your behalf.\n"
            "• Click the button below to get your API key.",
            "gemini",
            "Get API Key",
            lambda: webbrowser.open("https://aistudio.google.com/app/apikey"),
        )

    def get_response(
        self,
        system_instruction: str,
        prompt: str,
        return_response: bool = False,
        model: str = None,
        thinking_budget: int = None,
    ) -> str:
        """
        Generate content using Gemini with the new genai.Client approach.

        Much simpler than the previous HTTP implementation.
        Returns the full response text if return_response is True,
        otherwise emits the text via the output_ready_signal.

        Args:
            model: Override the default model (e.g., "gemini-2.5-flash")
            thinking_budget: Override the default thinking budget (0=no thinking, -1=dynamic, >0=specific amount)
        """
        logging.debug(f"Getting response - API key available: {hasattr(self, 'api_key') and bool(self.api_key)}")

        self.close_requested = False

        try:
            # Determine which model to use based on operation type
            if model:
                # Explicit model override
                use_model = model
            elif return_response:
                # Chat operations (return_response=True) use chat model
                use_model = getattr(self, "chat_model_name", "gemini-2.5-flash")
            else:
                # Text operations (return_response=False) use text model
                use_model = getattr(self, "text_model_name", "gemini-2.5-flash-lite")

            # Use provided thinking budget or fall back to default (0 = no thinking)
            use_thinking = thinking_budget if thinking_budget is not None else 0

            # Debug logging
            logging.debug(f"Making API call with model: {use_model}")
            logging.debug(f"Using thinking budget: {use_thinking}")
            logging.debug(f"System instruction length: {len(system_instruction)}")
            logging.debug(f"Prompt length: {len(prompt)}")

            # Add current date, model info, and thinking mode to system instruction
            current_date = datetime.now().strftime("%Y-%m-%d")
            thinking_mode = (
                "no thinking"
                if use_thinking == 0
                else ("dynamic thinking" if use_thinking == -1 else f"thinking budget: {use_thinking}")
            )
            enhanced_system_instruction = f"Today's date is {current_date}. You are running on {use_model} with {thinking_mode}. {system_instruction}"

            # Combine system instruction and prompt
            full_prompt = f"{enhanced_system_instruction}\n\n{prompt}"

            # Generate content using the new genai.Client approach
            response = self.client.models.generate_content(
                model=use_model,
                contents=full_prompt,
                config=types.GenerateContentConfig(thinking_config=types.ThinkingConfig(thinking_budget=use_thinking)),
            )

            response_text = response.text.rstrip("\n")
            logging.debug("API call completed successfully")

            if not return_response:
                # For direct text replacement operations, call replace_text directly
                self.app.text_operations_manager.replace_text(response_text)
                return ""
            return response_text

        except Exception as e:
            # Handle various error types
            logging.error(f"Gemini API exception: {type(e).__name__}: {str(e)}")

            error_str = str(e)
            if "timeout" in error_str.lower() or "time out" in error_str.lower():
                error_msg = "Request timed out. Please try again."
            elif "safety" in error_str.lower() or "blocked" in error_str.lower():
                error_msg = "Content was blocked by safety filters. Try rephrasing your request."
            elif "not found" in error_str.lower() or "invalid" in error_str.lower():
                error_msg = f"Model error: {error_str}"
            elif (
                "authentication" in error_str.lower()
                or "api key" in error_str.lower()
                or "unauthorized" in error_str.lower()
            ):
                error_msg = "Authentication failed. Please check your API key in settings."
            elif "service unavailable" in error_str.lower() or "server error" in error_str.lower():
                error_msg = "Gemini service temporarily unavailable. Please try again in a moment."
            else:
                error_msg = f"Gemini API Error: {error_str}"

            logging.error(f"Processed error message: {error_msg}")
            # For errors, show message via signal
            self.app.show_message_signal.emit("Error", error_msg)
        finally:
            self.close_requested = False

        return ""

    def after_load(self):
        """
        Initialize the genai.Client after configuration is loaded.
        """
        logging.debug(
            f"Configuring Gemini with API key: {'***' + str(getattr(self, 'api_key', 'NOT SET'))[-4:] if hasattr(self, 'api_key') and self.api_key else 'NOT SET'}"
        )

        if not hasattr(self, "api_key") or not self.api_key:
            logging.error("No API key found in Gemini provider")
            return

        # Create the genai.Client with the API key
        self.client = genai.Client(api_key=self.api_key)
        logging.debug("Gemini provider configured with genai.Client")

    def before_load(self):
        """
        Clean up client before reloading configuration.
        """
        self.client = None

    def cancel(self):
        self.close_requested = True

    def get_settings_ui(self, parent) -> QVBoxLayout:
        """
        Return a layout containing the provider's settings UI.
        """
        layout = QVBoxLayout()
        for setting in self.settings:
            setting.render_to_layout(layout)
        return layout

    def save_settings(self, layout: QVBoxLayout):
        """
        Save settings from the UI back to the provider configuration.
        """
        # Settings are automatically saved via the get_value() method
        # when the configuration is saved by the settings window
        pass