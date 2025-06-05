#!/usr/bin/env python

import asyncio
import os
import socketserver
from mimetypes import guess_type
from threading import Thread
from urllib.parse import unquote
from wsgiref.simple_server import WSGIServer
from wsgiref.util import FileWrapper

import django
import toga
from django.core.handlers.wsgi import WSGIHandler
from django.core.management import call_command
from django.core.servers.basehttp import WSGIRequestHandler

# Middleware to serve static files from the staticfiles directory.
# For some reason, the static files cannot be served directly when using Toga. This class provides a solution
class StaticFilesMiddleware:
    def __init__(self, app, static_url='/static/', static_root='staticfiles'):
        self.app = app
        self.static_url = static_url
        self.static_root = static_root

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith(self.static_url):
            rel_path = unquote(path[len(self.static_url):].lstrip('/'))
            file_path = os.path.join(self.static_root, rel_path)

            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = guess_type(file_path)[0] or 'application/octet-stream'
                start_response('200 OK', [('Content-Type', content_type)])
                return FileWrapper(open(file_path, 'rb'))

            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return [b'Static file not found']

        return self.app(environ, start_response)

class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    pass

class StonksOverwatchApp(toga.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("INIT...")
        self.main_window = None
        self.on_exit = None
        self.server_thread = None
        self.web_view = None
        self._httpd = None
        self.server_exists = None

    def web_server(self):
        print("Configuring settings...")
        os.environ["DJANGO_SETTINGS_MODULE"] = "stonks_overwatch.settings"
        os.environ["STONKS_OVERWATCH_DATA_DIR"] = self.paths.data.as_posix()
        os.environ["STONKS_OVERWATCH_CONFIG_DIR"] = self.paths.config.as_posix()
        os.environ["STONKS_OVERWATCH_LOGS_DIR"] = self.paths.logs.as_posix()
        os.environ["STONKS_OVERWATCH_CACHE_DIR"] = self.paths.cache.as_posix()
        django.setup(set_prefix=False)

        print("Applying database migrations...")
        call_command("migrate")

        print("Starting server...")
        # Use port 0 to let the server select an available port.
        self._httpd = ThreadedWSGIServer(("127.0.0.1", 0), WSGIRequestHandler)
        self._httpd.daemon_threads = True

        wsgi_handler = WSGIHandler()

        # If the import is not done locally, the settings.py file is loaded too early,
        # ignoring the necessary configuration
        from stonks_overwatch.settings import STATIC_ROOT
        static_middleware = StaticFilesMiddleware(wsgi_handler, static_url='/static/', static_root=STATIC_ROOT)
        self._httpd.set_app(static_middleware)

        # The server is now listening, but connections will block until
        # serve_forever is run.
        self.loop.call_soon_threadsafe(self.server_exists.set_result, "ready")
        self._httpd.serve_forever()

    async def exit_handler(self, app):
        # Return True if app should close, and False if it should remain open
        if await self.dialog(
                toga.ConfirmDialog("Confirm Exit", "Are you sure you want to exit?")
        ):
            print("Shutting down...")
            self._httpd.shutdown()

            return True
        else:
            return False

    def startup(self):
        self.server_exists = asyncio.Future()

        self.web_view = toga.WebView()

        self.server_thread = Thread(target=self.web_server)
        self.server_thread.start()

        self.on_exit = self.exit_handler

        self.main_window = toga.MainWindow()
        self.main_window.size = (1024, 768)
        self.main_window.content = self.web_view

        # Remove default menu items that are not needed
        for command in self.commands:
            if command.group.text == "File" and command.text == "Close All":
                self.commands.remove(command)

    async def on_running(self):
        await self.server_exists

        host, port = self._httpd.socket.getsockname()
        print(f"Server running on {host}:{port}")
        self.web_view.url = f"http://{host}:{port}"

        self.main_window.show()

def main():
    return StonksOverwatchApp(
        'Stonks Overwatch',
        'com.caribay.investments.stonks_overwatch'
    )

