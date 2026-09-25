FROM ubuntu:26.04 AS base

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
RUN apt-get -y update \
  && apt-get -y install \
    python3 \
    libpython3.14 \
    libsqlite3-mod-spatialite \
    libmapserver2t64 \
    gdal-bin \
  && apt-get -y autoremove \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/partial/* /tmp/* /var/tmp/*

RUN mkdir /opt/eoxserver/
WORKDIR /opt/eoxserver

# -----------------------------------------------------------------------------

FROM base as build

# install build OS dependency packages
RUN apt-get -y update \
  && apt-get -y install \
    python3-pip \
    python3-venv \
    libgdal-dev \
    python3-dev \
    libpq-dev \
    python3-mapscript \
  && apt-get clean

# setting up a venv to install user packages in
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# mapscript - clone global installation to venv
RUN sh -c 'PYTHON_VERSION=$(python --version | sed -e '"'s/Python \([23]\.[0-9]\+\).*/\1/'"') \
  && TARGET_PATH="$VIRTUAL_ENV/lib/python$PYTHON_VERSION/site-packages" \
  && SOURCE_PATH="/usr/lib/python3/dist-packages" \
  && cp -vlR "$SOURCE_PATH"/mapscript* "$TARGET_PATH"'

# install dependencies
RUN pip3 install --force-reinstall --no-binary :all: psycopg2
RUN pip3 install "numpy<2.6.0" # make sure NumPy is installed before GDAL
RUN pip3 install "GDAL==$(gdal-config --version)"
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------

FROM base as final

# copy files and directories from the build stage image
COPY --from=build "$VIRTUAL_ENV" "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install EOxServer
COPY . .

ENV PROMETHEUS_MULTIPROC_DIR /var/tmp/prometheus_multiproc_dir
RUN mkdir $PROMETHEUS_MULTIPROC_DIR  # make sure this is writable by webserver user

EXPOSE 8000

ENTRYPOINT ["/opt/eoxserver/entrypoint.sh"]

CMD "gunicorn" $GUNICORN_CMD_ARGS
