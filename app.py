import flask

app = flask.Flask(__name__)
app.config.from_object('config')  # Load from config.py
