import sys

from app import app
import models
import views

if __name__ == '__main__':
  if 'createdb' in sys.argv:
    models.db.create_all()
  else:
    app.run(host='0.0.0.0', debug=True, port=app.config['PORT'])
