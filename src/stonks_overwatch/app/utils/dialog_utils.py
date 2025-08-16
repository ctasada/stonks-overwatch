from typing import Optional

import toga


def center_window_on_parent(window: toga.Window, parent_window: Optional[toga.Window]) -> None:
    """
    Center the given window on its parent window.
    """
    if parent_window and getattr(parent_window, "position", None) and getattr(parent_window, "size", None):
        main_x, main_y = parent_window.position
        main_width, main_height = parent_window.size
        dialog_width, dialog_height = window.size
        x = main_x + (main_width - dialog_width) // 2
        y = main_y + (main_height - dialog_height) // 2
        window.position = (x, y)
