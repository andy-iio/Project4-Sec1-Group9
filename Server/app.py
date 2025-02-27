from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return 'If you see this its working!'