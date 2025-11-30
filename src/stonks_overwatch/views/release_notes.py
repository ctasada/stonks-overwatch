import os

import markdown
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View


class ReleaseNotesView(View):
    def get(self, request) -> HttpResponse:
        """
        Handle GET request for release notes.

        Reads the CHANGELOG.md file, converts it from Markdown to HTML, and returns
        either a full HTML page or an HTML fragment depending on the request type.

        Args:
            request: Django HTTP request object

        Returns:
            HttpResponse: Rendered HTML response
                - HTML fragment template for XHR requests (modal)
                - Full release notes page template for regular browser requests
        """
        is_xhr_request = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        changelog_path = os.path.join(settings.STATIC_ROOT, "CHANGELOG.md")

        # Read and convert
        with open(changelog_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Replace CHANGELOG starting lines with "Release Notes" header
        start_idx = next((i for i, line in enumerate(lines) if line.strip().startswith("##")), 0)
        markdown_content = "# Release Notes\n" + "".join(lines[start_idx:])

        html_fragment = markdown.markdown(
            markdown_content,
            extensions=[
                "fenced_code",
            ],
            output_format="html",
        )

        dark_mode_param = request.GET.get("dark_mode", "0")
        is_dark_mode = dark_mode_param in ["1", "true", "True"]

        if is_dark_mode:
            bg_color = "#3B3B3B"
            text_color = "#FFFFFF"
            code_bg = "#696969"
            blockquote_bg = "#101010"
        else:
            bg_color = "#FFFFFF"
            text_color = "#000000"
            code_bg = "#F5F5F5"
            blockquote_bg = "#F0F0F0"

        context = {
            "html_fragment": html_fragment,
            "bg_color": bg_color,
            "text_color": text_color,
            "code_bg": code_bg,
            "blockquote_bg": blockquote_bg,
        }

        # Return HTML fragment for XHR requests (modal)
        if is_xhr_request:
            return render(request, "components/release_notes_content.html", context)

        return render(request, "release_notes.html", context)
