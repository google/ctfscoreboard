FROM debian:jessie

RUN apt-get update && apt-get install -y \
    nginx \
    python \
    python-pip \
    supervisor \
    uwsgi \
    uwsgi-plugin-python \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
COPY doc/nginx.conf /etc/nginx/sites-enabled/default
COPY doc/docker/supervisord.conf /etc/supervisor/conf.d/

COPY . /opt/scoreboard
WORKDIR /opt/scoreboard

RUN python main.py createdb
RUN chmod 766 /tmp/scoreboard*

CMD ["/usr/bin/supervisord"]