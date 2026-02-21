FROM ubuntu:24.04

ENV VIRTUAL_ENV=/opt/venv
ENV INSTANCE_NAME=instance
ENV TZ=UTC
ENV PYTHONPATH='/opt/eoxserver'
ENV PYTHONUNBUFFERED="1"

# possible values are "postgis" and "spatialite"
ENV DB=spatialite
ENV DB_HOST ''
ENV DB_NAME ''
ENV DB_USER ''
ENV DB_PW ''

# set these variables to add a django user upon instance initialization
ENV DJANGO_USER ''
ENV DJANGO_MAIL ''
ENV DJANGO_PASSWORD ''

# set this to a glob or filename in order to run after initialization
ENV INIT_SCRIPTS=''

# override this or specify additional options in the config file
ENV GUNICORN_CMD_ARGS "--config /opt/eoxserver/gunicorn.conf.py ${INSTANCE_NAME}.wsgi:application"

# install OS dependency packages
RUN apt-get update \
  && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    python3-gdal \
    python3-mapscript \
    gdal-bin \
    libsqlite3-mod-spatialite \
    postgresql-client \
    python3-psycopg2 \
  && apt-get autoremove -y \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/partial/* /tmp/* /var/tmp/*

# setting up a venv to install user packages in
RUN python3 -m venv --system-site-packages $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

ENV PROMETHEUS_MULTIPROC_DIR /var/tmp/prometheus_multiproc_dir
RUN mkdir $PROMETHEUS_MULTIPROC_DIR  # make sure this is writable by webserver user

RUN mkdir /opt/eoxserver/
WORKDIR /opt/eoxserver

# install dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# install EOxServer
COPY . .

EXPOSE 8000

ENTRYPOINT ["/opt/eoxserver/entrypoint.sh"]

CMD "gunicorn" $GUNICORN_CMD_ARGS
