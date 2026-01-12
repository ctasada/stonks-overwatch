"""
Color utility functions for dark/light mode theming.
"""

from typing import Dict


def get_theme_colors(is_dark_mode: bool) -> Dict[str, str]:
    """
    Return a dictionary of theme colors based on dark mode setting.

    Args:
        is_dark_mode (bool): Whether dark mode is enabled.

    Returns:
        Dict[str, str]: Dictionary with theme colors for all UI components.
    """
    if is_dark_mode:
        return {
            # Base colors
            "bg_color": "#3B3B3B",
            "text_color": "#FFFFFF",
            "code_bg": "#696969",
            "blockquote_bg": "#101010",
            # Settings-specific colors
            "secondary_color": "#B0B0B0",
            "border_color": "#555555",
            "hover_bg": "#4a4a4a",
            "active_bg": "#4a5568",
            "form_bg": "#4a4a4a",
            "form_border": "#555555",
        }
    return {
        # Base colors
        "bg_color": "#FFFFFF",
        "text_color": "#000000",
        "code_bg": "#F5F5F5",
        "blockquote_bg": "#F0F0F0",
        # Settings-specific colors
        "secondary_color": "#6c757d",
        "border_color": "#dee2e6",
        "hover_bg": "#f8f9fa",
        "active_bg": "#D0E0FF",
        "form_bg": "#FFFFFF",
        "form_border": "#dee2e6",
    }
