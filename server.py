import flask
import os
from flask import send_from_directory

app = flask.Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    pass
if __name__ == "__main__":
    app.secret_key = 'ItIsASecret'
    app.debug = True
    app.run()