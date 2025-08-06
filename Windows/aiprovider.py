"""
AI Provider Architecture for Writing Tools
--------------------------------------------

This module serves as the main entry point for AI providers and maintains backward compatibility.
The actual implementations have been split into separate modules for better organization.

Key Components:
1. ProviderInterfaces.py - Abstract base classes (AIProvider, AIProviderSetting)
2. ProviderUI.py - UI components (TextSetting, DropdownSetting)  
3. GeminiProvider.py - Gemini API implementation

This file imports and re-exports all components to maintain backward compatibility.
"""

# Import all components for backward compatibility
from ProviderInterfaces import AIProvider, AIProviderSetting
from ProviderUI import TextSetting, DropdownSetting
from GeminiProvider import GeminiProvider

# Re-export all classes to maintain backward compatibility
__all__ = [
    'AIProvider',
    'AIProviderSetting', 
    'TextSetting',
    'DropdownSetting',
    'GeminiProvider'
]