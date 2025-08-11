import webbrowser

import toga
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW


class ExpiredDialog(toga.Window):
    def __init__(self, title: str, license_info: dict, main_window: toga.Window | None = None):
        super().__init__(
            title=title,
            minimizable=False,
            resizable=False,
            closable=True,
            size=(400, 400),  # Set initial size
        )
        self.license_info = license_info
        self._main_window = main_window

        # Main container with margin
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=20, align_items=CENTER))

        # # Add application icon
        # self.logo = toga.ImageView(
        #     image=toga.Icon.APP_ICON,
        #     style=Pack(width=120, height=120, margin_bottom=20)
        # )
        # self.main_box.add(self.logo)

        # Title
        title_text = self._get_title_text()
        self.title_label = toga.Label(
            title_text,
            style=Pack(
                font_size=24,
                font_weight="bold",
                text_align="center",
                margin_bottom=10,
            ),
        )
        self.main_box.add(self.title_label)

        # Message
        message_text = self._get_message_text()
        self.message_label = toga.Label(
            message_text,
            style=Pack(
                text_align="center",
                margin_bottom=20,
                color="rgb(108, 117, 125)",  # Bootstrap text-secondary
            ),
        )
        self.main_box.add(self.message_label)

        # Info Box with light background
        self.info_box = toga.Box(
            style=Pack(
                direction=COLUMN,
                margin=20,
                background_color="rgb(248, 249, 250)",  # Bootstrap bg-light
                margin_bottom=20,
            )
        )
        self.main_box.add(self.info_box)

        # Info content with two-column layout
        info_fields = [
            ("Version:", self.license_info["version"]),
            ("Build Date:", self.license_info["build_date"].strftime("%b %d, %Y")),
            ("Expired On:", self.license_info["expiration_date"].strftime("%b %d, %Y")),
            ("Testing Period:", f"{self.license_info['expiration_days']} days"),
        ]

        for label, value in info_fields:
            row = toga.Box(style=Pack(direction=ROW, margin_bottom=10))
            row.add(toga.Label(label, style=Pack(flex=1, font_weight="bold", color="rgb(33, 37, 41)")))
            row.add(toga.Label(value, style=Pack(flex=1, color="rgb(108, 117, 125)")))
            self.info_box.add(row)

        # Button container
        button_box = toga.Box(style=Pack(direction=ROW, align_items=CENTER))
        self.request_button = toga.Button(
            "Request New Build",
            on_press=self.open_support_url,
            style=Pack(
                margin=(10, 20),
                background_color="#0d6efd",  # Bootstrap primary blue
                color="#ffffff",  # White text
                font_weight="bold",
                width=200,  # Fixed width for better appearance
            ),
        )
        button_box.add(self.request_button)
        self.main_box.add(button_box)

        # Footer text
        footer_box = toga.Box(style=Pack(direction=COLUMN, align_items=CENTER, margin_top=20))

        self.footer_text = toga.Label(
            "Thank you for participating in our testing program!",
            style=Pack(
                text_align="center",
                margin_bottom=5,
                color="rgb(108, 117, 125)",  # Bootstrap text-muted
                font_size=12,
            ),
        )
        footer_box.add(self.footer_text)

        self.footer_link = toga.Button(
            "Your feedback helps us improve the application.",
            on_press=self.open_support_url,
            style=Pack(
                margin=(10, 20),
                background_color="#0d6efd",  # Bootstrap primary blue
                color="#ffffff",  # White text
                font_weight="bold",
                width=200,  # Fixed width for better appearance
            ),
        )
        footer_box.add(self.footer_link)
        self.main_box.add(footer_box)

        # Set the content
        self.content = self.main_box

    def _get_title_text(self):
        days_remaining = self.license_info["days_remaining"]
        if days_remaining is not None:
            if days_remaining <= 0:
                return "Trial Version Expired"
            elif days_remaining < 7:
                return "Trial Version Expires Soon"
        return "Trial Version Info"

    def _get_message_text(self):
        days_remaining = self.license_info["days_remaining"]
        if days_remaining is not None:
            if days_remaining <= 0:
                return (
                    "This trial version of the application has expired.\n"
                    "To continue testing, please contact your developer for a new testing build."
                )
            elif days_remaining < 7:
                return (
                    f"Your trial version will expire in {days_remaining} days.\n"
                    "Please contact your developer to get a new build."
                )
            else:
                return f"Your trial version is active and will expire in {days_remaining} days."
        return "Trial version information is not available."

    def open_support_url(self, widget):
        webbrowser.open_new_tab(self.license_info["support_url"])

    def show(self):
        if self._main_window and self._main_window.position and self._main_window.size:
            # Center the dialog relative to the main window
            main_x, main_y = self._main_window.position
            main_width, main_height = self._main_window.size
            dialog_width, dialog_height = self.size

            # Calculate center position
            x = main_x + (main_width - dialog_width) // 2
            y = main_y + (main_height - dialog_height) // 2

            self.position = (x, y)

        # Show the window which will bring it to the front
        super().show()
