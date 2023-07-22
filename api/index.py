from http.server import BaseHTTPRequestHandler
from incidents import main


class handler(BaseHTTPRequestHandler):

    def do_GET(self):

        main()

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Success!'.encode('utf-8'))
        return
