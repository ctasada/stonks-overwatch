import os

from django.conf import settings
from django.http import FileResponse, Http404
from django.views import View


class RootStaticFileView(View):
    def get(self, request, filename):
        file_path = os.path.join(settings.STATIC_ROOT, filename)
        if not os.path.exists(file_path):
            raise Http404(f"{filename} not found.")
        return FileResponse(open(file_path, "rb"))
