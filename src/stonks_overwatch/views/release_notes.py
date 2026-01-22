import os

import markdown
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from stonks_overwatch.config.config import Config


class ReleaseNotesView(View):
    def get(self, request) -> HttpResponse:
        """
        Handle GET request for release notes.

        Reads the CHANGELOG.md file, converts it from Markdown to HTML, and returns
        a self-contained template that renders as either a full HTML page or an HTML
        fragment depending on the request type (AJAX vs regular).

        Args:
            request: Django HTTP request object

        Returns:
            HttpResponse: Rendered HTML response from release_notes_content.html
                - HTML fragment for AJAX requests (modal in base.html)
                - Full HTML page for regular requests (native app WebView)
        """
        is_ajax_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        changelog_path = os.path.join(settings.STATIC_ROOT, "CHANGELOG.md")

        # Read and convert
        with open(changelog_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Extract changelog content starting from first version heading
        start_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("##")), 0)
        markdown_content = "".join(lines[start_idx:])

        html_fragment = markdown.markdown(
            markdown_content,
            extensions=[
                "fenced_code",
            ],
            output_format="html",
        )

        # Get global appearance setting
        config = Config.get_global()
        appearance = config.appearance

        context = {
            "html_fragment": html_fragment,
            "is_standalone": not is_ajax_request,  # Wrap in HTML structure for non-AJAX requests
            "APPEARANCE": appearance,
        }

        # Always return the content component (it handles standalone vs fragment internally)
        return render(request, "components/release_notes_content.html", context)
