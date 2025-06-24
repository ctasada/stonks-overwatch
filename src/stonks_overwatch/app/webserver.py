import os
import socketserver
from mimetypes import guess_type
from urllib.parse import unquote
from wsgiref.simple_server import WSGIServer
from wsgiref.util import FileWrapper


# Middleware to serve static files from the staticfiles directory.
# For some reason, the static files cannot be served directly when using Toga. This class provides a solution
class StaticFilesMiddleware:
    def __init__(self, app, static_url="/static/", static_root="staticfiles"):
        self.app = app
        self.static_url = static_url
        self.static_root = static_root

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path.startswith(self.static_url):
            rel_path = unquote(path[len(self.static_url) :].lstrip("/"))
            file_path = os.path.join(self.static_root, rel_path)

            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = guess_type(file_path)[0] or "application/octet-stream"
                start_response("200 OK", [("Content-Type", content_type)])
                return FileWrapper(open(file_path, "rb"))

            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"Static file not found"]

        return self.app(environ, start_response)


class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    pass
