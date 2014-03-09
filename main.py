import sys

from app import app
import models
import views

if __name__ == '__main__':
  if 'createdb' in sys.argv:
    models.db.create_all()
  app.run(debug=True, port=app.config['PORT'])
