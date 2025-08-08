import asyncio
import datetime
import os

import pyotp
import toga
import toga.platform
from toga.style import Pack
from toga.style.pack import COLUMN, END, ROW, START

from stonks_overwatch.utils.core.logger import StonksLogger


class PreferencesDialog(toga.Window):
    # Constants for magic values
    SIDEBAR_WIDTH = 120
    MAIN_BOX_MARGIN = 20
    ICON_SIZE_HEADER = 24
    ICON_SIZE_ITEM = 8
    LABEL_MARGIN_RIGHT = 10
    LABEL_WIDTH = 100
    UPDATE_FREQ_LABEL_WIDTH = 150
    UPDATE_FREQ_INPUT_WIDTH = 50
    UPDATE_FREQ_UNIT_WIDTH = 50
    UPDATE_FREQ_MIN = 1
    UPDATE_FREQ_MAX = 60
    UPDATE_FREQ_STEP = 1
    VERIFICATION_TIMER_MAX = 30

    def __init__(self, title: str = "Preferences", app: toga.App | None = None) -> None:
        """
        Initialize the PreferencesDialog window.

        Args:
            title (str): The window title.
            app (toga.App | None): The Toga application instance.
        """
        super().__init__(
            title=title,
            minimizable=False,
            resizable=False,
            closable=True,
            size=(600, 400),
        )
        self.logger = StonksLogger.get_logger("stonks_overwatch.app", "[PREFERENCES]")

        from stonks_overwatch.services.brokers.models import BrokersConfiguration, BrokersConfigurationRepository

        self.brokers_configuration_repository = BrokersConfigurationRepository()
        # Database configuration will be loaded in async_init()
        self.degiro_configuration: BrokersConfiguration | None = None

        self._app = app
        self._main_window = app.main_window

        # Main horizontal container
        self.main_box = toga.Box(style=Pack(direction=COLUMN, margin=20))

        # Content area: sidebar + main section
        self.content_box = toga.Box(style=Pack(direction=ROW, flex=1))

        # Sidebar (placeholder)
        self.content_box.add(self._create_sidebar())
        # Main section (placeholder)
        self.main_section = toga.Box(style=Pack(direction=COLUMN, flex=1))
        # UI will be created in async_init() after data is loaded
        self.content_box.add(self.main_section)

        # Buttons at the bottom
        self.button_box = toga.Box(style=Pack(direction=ROW, align_items=START, justify_content=START))
        self.ok_button = toga.Button("OK", on_press=self.on_ok, style=Pack(width=100, margin_right=10))
        self.cancel_button = toga.Button("Cancel", on_press=self.on_cancel, style=Pack(width=100, margin_right=10))
        platform = toga.platform.current_platform
        # FIXME: This is hack to force the buttons to the right-side. There should be a better approach
        self.button_box.add(toga.Box(style=Pack(direction=ROW, flex=1.0, align_items=START, justify_content=START)))
        if platform == "macOS":
            # macOS: Cancel (left), OK (right), right-aligned
            self.button_box.add(self.cancel_button)
            self.button_box.add(self.ok_button)
        else:
            # Windows/Linux: OK (left), Cancel (right), right-aligned
            self.button_box.add(self.ok_button)
            self.button_box.add(self.cancel_button)

        self.main_box.add(self.content_box)
        self.main_box.add(self.button_box)

        self.content = self.main_box

    async def async_init(self):
        """Initialize the dialog with async database calls."""
        self.degiro_configuration = await self.brokers_configuration_repository.get_broker_by_name_async("degiro")
        self.logger.debug("Brokers configuration loaded")
        if self.degiro_configuration:
            # Ensure credentials is a dictionary (initialize if None)
            if self.degiro_configuration.credentials is None:
                self.degiro_configuration.credentials = {}
        else:
            self.logger.warning("No DEGIRO configuration found in database")
        # Now create the UI with the loaded data
        self._create_degiro()

    def _create_sidebar(self) -> toga.Box:
        sidebar = toga.Box(style=Pack(direction=COLUMN, width=self.SIDEBAR_WIDTH, margin_right=self.MAIN_BOX_MARGIN))
        sidebar.add(toga.Label("Brokers", style=Pack(margin_bottom=10, font_weight="bold")))
        sidebar.add(toga.Divider(style=Pack(margin_bottom=10)))

        # Add DEGIRO as a sidebar item
        sidebar.add(self._get_broker_entry("DEGIRO", "degiro"))

        # Add more sidebar items here
        return sidebar

    def _get_broker_entry(self, broker_name: str, icon_name: str, is_header: bool = False) -> toga.Box:
        if is_header:
            icon_style = Pack(width=self.ICON_SIZE_HEADER, height=self.ICON_SIZE_HEADER, margin_right=8)
            label_style = Pack(font_weight="bold", font_size=16)
        else:
            icon_style = Pack(width=self.ICON_SIZE_ITEM, height=self.ICON_SIZE_ITEM, margin_right=4)
            label_style = Pack(margin_bottom=10)

        entry = toga.Box(style=Pack(direction=ROW, align_items=START, margin_bottom=10))
        entry.add(toga.ImageView(self._get_broker_logo(icon_name), style=icon_style))
        entry.add(toga.Label(broker_name, style=label_style))

        return entry

    def _get_broker_logo(self, broker_name: str) -> toga.Image:
        """Get the logo for a given broker."""
        logo_path = os.path.join(self._app.paths.app, "..", "static", "brokers", f"{broker_name}.png")
        if os.path.exists(logo_path):
            return toga.Image(logo_path)
        else:
            self.logger.warning(f"Logo not found for broker: {broker_name}")
            return toga.Image()

    def _add_degiro_credentials_fields(self, fields_box: toga.Box) -> toga.TextInput:
        def on_degiro_username_change(widget):
            if self.degiro_configuration:
                if self.degiro_configuration.credentials is None:
                    self.degiro_configuration.credentials = {}
                self.degiro_configuration.credentials["username"] = widget.value

        def on_degiro_password_change(widget):
            if self.degiro_configuration:
                if self.degiro_configuration.credentials is None:
                    self.degiro_configuration.credentials = {}
                self.degiro_configuration.credentials["password"] = widget.value

        def on_degiro_topt_change(widget):
            if self.degiro_configuration:
                if self.degiro_configuration.credentials is None:
                    self.degiro_configuration.credentials = {}
                self.degiro_configuration.credentials["totp_secret_key"] = widget.value

        credentials = self.degiro_configuration.credentials if self.degiro_configuration else {}
        existing_username = credentials.get("username", "")
        existing_password = credentials.get("password", "")
        existing_totp_key = credentials.get("totp_secret_key", "")

        username_row = toga.Box(style=Pack(direction=ROW, margin_bottom=10, align_items=START))
        username_label = toga.Label(
            "Username", style=Pack(width=self.LABEL_WIDTH, margin_right=self.LABEL_MARGIN_RIGHT, align_items=END)
        )
        username_input = toga.TextInput(
            value=existing_username, style=Pack(flex=1), on_change=on_degiro_username_change
        )
        username_row.add(username_label)
        username_row.add(username_input)
        fields_box.add(username_row)

        password_row = toga.Box(style=Pack(direction=ROW, margin_bottom=10, align_items=START))
        password_label = toga.Label(
            "Password", style=Pack(width=self.LABEL_WIDTH, margin_right=self.LABEL_MARGIN_RIGHT, align_items=END)
        )
        password_input = toga.PasswordInput(
            value=existing_password, style=Pack(flex=1), on_change=on_degiro_password_change
        )
        password_row.add(password_label)
        password_row.add(password_input)
        fields_box.add(password_row)

        totp_key_row = toga.Box(style=Pack(direction=ROW, margin_bottom=10, align_items=START))
        totp_key_label = toga.Label(
            "TOTP Secret Key", style=Pack(width=self.LABEL_WIDTH, margin_right=self.LABEL_MARGIN_RIGHT, align_items=END)
        )
        totp_key = toga.TextInput(value=existing_totp_key, style=Pack(flex=1), on_change=on_degiro_topt_change)
        totp_key_row.add(totp_key_label)
        totp_key_row.add(totp_key)
        fields_box.add(totp_key_row)

        return totp_key

    def _add_degiro_verification_row(self, fields_box: toga.Box, totp_key: toga.TextInput) -> None:
        verification_row = toga.Box(style=Pack(direction=ROW, margin_bottom=10, align_items=START))
        verification_label = toga.Label(
            "Verification Code",
            style=Pack(width=self.LABEL_WIDTH, margin_right=self.LABEL_MARGIN_RIGHT, align_items=END),
        )
        verification_code = toga.Label("")
        verification_timer = toga.ProgressBar(max=self.VERIFICATION_TIMER_MAX, value=0)
        verification_row.add(verification_label)
        verification_row.add(verification_code)
        verification_row.add(verification_timer)
        fields_box.add(verification_row)
        self._update_verification_code(totp_key, verification_label, verification_code, verification_timer)

    def _update_verification_code(
        self,
        totp_key: toga.TextInput,
        verification_label: toga.Label,
        verification_code: toga.Label,
        verification_timer: toga.ProgressBar,
    ) -> None:
        def refresh_code():
            if totp_key.value != "":
                try:
                    totp = pyotp.TOTP(totp_key.value)
                    verification_code.text = totp.now()
                    verification_timer.value = datetime.datetime.now().second % 30
                except Exception:
                    verification_code.text = "Invalid TOTP Key"
                verification_label.style.visibility = "visible"
                verification_code.style.visibility = "visible"
                verification_timer.style.visibility = "visible"
            else:
                verification_code.text = ""
                verification_label.style.visibility = "hidden"
                verification_code.style.visibility = "hidden"
                verification_timer.style.visibility = "hidden"
            self._app.loop.call_later(1, refresh_code)

        refresh_code()

    def _add_degiro_update_frequency_row(self, fields_box: toga.Box) -> None:
        update_frequency = self.degiro_configuration.update_frequency
        update_frequency_row = toga.Box(style=Pack(direction=ROW, margin_bottom=10, align_items=START))
        update_frequency_label = toga.Label(
            "Update Frequency",
            style=Pack(width=self.UPDATE_FREQ_LABEL_WIDTH, margin_right=self.LABEL_MARGIN_RIGHT, align_items=END),
        )

        def on_degiro_update_change(widget):
            if self.degiro_configuration and widget.value:
                self.degiro_configuration.update_frequency = widget.value

        update_frequency_input = toga.NumberInput(
            value=update_frequency,
            style=Pack(width=self.UPDATE_FREQ_INPUT_WIDTH),
            min=self.UPDATE_FREQ_MIN,
            max=self.UPDATE_FREQ_MAX,
            step=self.UPDATE_FREQ_STEP,
            on_change=on_degiro_update_change,
        )
        update_frequency_unit = toga.Label(
            "minutes",
            style=Pack(width=self.UPDATE_FREQ_UNIT_WIDTH, margin_left=self.LABEL_MARGIN_RIGHT, align_items=END),
        )
        update_frequency_row.add(update_frequency_label)
        update_frequency_row.add(update_frequency_input)
        update_frequency_row.add(update_frequency_unit)
        fields_box.add(update_frequency_row)

    def _create_degiro(self) -> None:
        self.main_section.children.clear()
        # Add icon and label in a horizontal box
        self.main_section.add(self._get_broker_entry("DEGIRO", "degiro", is_header=True))

        fields_box = toga.Box(style=Pack(direction=COLUMN, flex=1, margin_bottom=self.MAIN_BOX_MARGIN))
        enabled_value = self.degiro_configuration.enabled if self.degiro_configuration else False
        enabled_switch = toga.Switch(text="Enabled", value=enabled_value, enabled=False, style=Pack(margin_bottom=10))
        self.main_section.add(enabled_switch)
        self.main_section.add(toga.Label("Credentials:", style=Pack(font_weight="bold", margin_top=5, margin_bottom=5)))
        self.main_section.add(toga.Divider(style=Pack(margin_top=5, margin_bottom=10)))

        totp_key = self._add_degiro_credentials_fields(fields_box)
        self._add_degiro_verification_row(fields_box, totp_key)
        fields_box.add(toga.Divider(style=Pack(margin_top=5, margin_bottom=10)))
        self._add_degiro_update_frequency_row(fields_box)

        self.main_section.add(fields_box)

    def __set_visibility(self, widget: toga.Widget, visibility: str) -> None:
        if widget.style.visibility != visibility:
            widget.style.visibility = visibility
            if widget.parent:
                widget.parent.refresh()

    def on_ok(self, widget: toga.Widget) -> None:
        """Save the configuration and close the dialog."""
        if self.degiro_configuration:
            # Run the async save operation in a task
            asyncio.create_task(self._save_configuration())
        self.close()

    async def _save_configuration(self) -> None:
        """Async helper to save the configuration."""
        try:
            await self.brokers_configuration_repository.save_broker_configuration_async(self.degiro_configuration)
            self.logger.info("DEGIRO configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save DEGIRO configuration: {e}")
            # You might want to show an error dialog here

    def on_cancel(self, widget: toga.Widget) -> None:
        # Placeholder for Cancel action
        self.close()
