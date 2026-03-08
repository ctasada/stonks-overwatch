from urllib.parse import urlencode


class IbkrLogoIntegration:
    """Logo integration that resolves asset icons via Interactive Brokers' internal Benzinga proxy.

    This uses an undocumented IBKR endpoint — it is not part of any public API contract
    and may change or be removed without notice. The lookup key is the IBKR contract ID
    (``conid``), which is only available for assets held in an IBKR account.
    """

    # Undocumented IBKR proxy that forwards requests to Benzinga's icon CDN.
    # Only available for authenticated IBKR sessions; used here for browser-side hotlinking.
    BASE_URL = "https://www.interactivebrokers.ie/tws.proxy/public/icons/benzinga"

    def get_logo_url(self, conid: str, theme: str = "light") -> str:
        """Build the Benzinga proxy URL for the given contract ID.

        The browser is redirected directly to this URL; missing icons are handled gracefully
        by the ``onerror`` handler in the template (``this.style.display='none'``).

        Args:
            conid: IBKR contract ID. Must be a non-empty digit string; returns ``""`` otherwise.
            theme: Display theme — ``"dark"`` selects a dark-background icon variant.
                   Defaults to ``"light"``; any value other than ``"dark"`` produces a light icon.

        Returns:
            A fully qualified URL string, or ``""`` if conid is absent or not a digit string.
        """
        if not conid or not conid.isdigit():
            return ""

        icon_type = "mark_dark" if (theme or "light").lower() == "dark" else "mark_light"
        query = urlencode(
            {
                "conid": conid,
                "type": icon_type,
                "composite_radius": 0,
                "scale": "200x200",
                "composite_auto": "false",
            }
        )
        return f"{self.BASE_URL}?{query}"
