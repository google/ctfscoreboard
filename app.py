import flask
import logging

app = flask.Flask(__name__)
app.config.from_object('config')  # Load from config.py

# Main logger
if not app.debug:
  handler = logging.FileHandler(
      app.config.get('LOGFILE') or '/tmp/scoreboard.wsgi.log')
  handler.setLevel(logging.INFO)
  handler.setFormatter(
      '%(asctime)s %(levelname)8s [%(filename)s:%(lineno)d] %(message)s')
  app.logger.addHandler(handler)

# Challenge logger
handler = logging.FileHandler(
    app.config.get('CHALLENGELOG') or '/tmp/scoreboard.challenge.log')
handler.setLevel(logging.INFO)
handler.setFormatter('%(asctime)s %(message)s')
logger = logging.getLogger('scoreboard')
logger.addHandler(handler)
app.challenge_log = logger
