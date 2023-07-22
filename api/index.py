import datetime
from http.server import BaseHTTPRequestHandler
from flask import Flask


NAME_OPTIONS = [
    "Tired Michael",
]


app = Flask(__name__)


@app.route('/')
def home():
    return 'Hello, World!'


@app.route('/about')
def about():
    return 'About'


@app.route('/username')
def username():
    # todo: generate auth header

    print(f"Cron has been invoked at {datetime.datetime.now()}")
    return 'Success'


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # todo: generate auth header

        print(f"Cron has been invoked at {datetime.datetime.now()}")

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return
