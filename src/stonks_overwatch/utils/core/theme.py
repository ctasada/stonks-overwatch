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
        Dict[str, str]: Dictionary with keys 'bg_color', 'text_color', 'code_bg', 'blockquote_bg'.
    """
    if is_dark_mode:
        return {
            "bg_color": "#3B3B3B",
            "text_color": "#FFFFFF",
            "code_bg": "#696969",
            "blockquote_bg": "#101010",
        }
    return {
        "bg_color": "#FFFFFF",
        "text_color": "#000000",
        "code_bg": "#F5F5F5",
        "blockquote_bg": "#F0F0F0",
    }
