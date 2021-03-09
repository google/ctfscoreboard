FROM debian:buster

RUN apt-get update && apt-get install -y \
    nginx \
    python3 \
    python3-dev \
    python3-pip \
    supervisor \
    uwsgi \
    uwsgi-plugin-python3 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
COPY doc/nginx.conf /etc/nginx/sites-enabled/default
COPY doc/docker/supervisord.conf /etc/supervisor/conf.d/

COPY . /opt/scoreboard
# Suggest you mount a config at /opt/scoreboard/config.py instead
COPY config.example.py /opt/scoreboard/config.py
WORKDIR /opt/scoreboard

RUN make

# TODO: migrate this to run at runtime
RUN python3 main.py createdb
RUN chmod 666 /tmp/scoreboard*

CMD ["/usr/bin/supervisord"]
