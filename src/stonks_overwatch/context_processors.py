import os


def app_mode_processor(request):
    """Add app mode context to detect if running in Toga WebView or as webapp"""
    is_desktop_app = os.environ.get("STONKS_OVERWATCH_APP") == "1"
    return {
        "is_desktop_app": is_desktop_app,
        "is_webapp": not is_desktop_app,
    }
