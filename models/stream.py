import io
import picamera
import logging
import socketserver
from threading import Thread
from threading import Condition
from http import server
from .system import System
import os
from http import server
from bs4 import BeautifulSoup

PAGE= None

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

output = StreamingOutput()

class Stream(Thread):
    def __init__(self, camera):

        system = System()
        json_loads = system.json_loads()

        self._width = json_loads["record"]["width"]

        Thread.__init__(self, name='stream_thread')
        # self.config = config
        # self.logger = \
        #     Log(
        #         __name__,
        #         json_loads["log"]["level"],
        #         json_loads["log"]["log_path"],
        #         json_loads["log"]["log_name"]
        #     )
        # self.resources = resources
        self._camera = camera
        self.address = \
            (
                json_loads["stream"]["ip"],
                json_loads["stream"]["host_port"],
            )

        # Definir a resolução do stream na página.
        # base_resource_directory = "/etc/sectrans/capture"
        # stream_path = "www/stream.html"
        # stream_page = os.path.join(base_resource_directory, stream_path)
        stream_page = "www/stream.html"


        try:
            with open(stream_page, 'r') as f:
                stream_page = BeautifulSoup(f, 'html.parser')
                img_tag = stream_page.img
                img_tag['width'] = json_loads["stream"]["width"]
                img_tag['height'] = json_loads["stream"]["height"]
                global PAGE
                PAGE = stream_page

            self.server = StreamingServer(self.address, StreamingHandler)

        except Exception as e:
            # self.logger.write_log(
            #     'error', 'Pagina HTML de stream nao encontrada!')
            print(e)

    def run(self):

        system = System()
        json_loads = system.json_loads()

        if PAGE:
            try:
                self._camera.start_recording(
                    output,
                    format='mjpeg', 
                    splitter_port=json_loads["stream"]["stream_port"]
                )

                self.server.serve_forever()
            finally:
                self._camera.stop_recording(
                    splitter_port=json_loads["stream"]["stream_port"])
