FROM ubuntu:20.04

ARG DJANGO=2.2.17
ARG TZ=UTC

ENV INSTANCE_NAME=instance

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
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update \
  && apt-get install -y \
    python3 \
    python3-pip \
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

# install EOxServer
RUN mkdir /opt/eoxserver/

ADD eoxserver /opt/eoxserver/eoxserver
ADD tools /opt/eoxserver/tools
ADD setup.cfg setup.py MANIFEST.in README.rst requirements.txt /opt/eoxserver/
ADD docker/eoxserver-entrypoint.sh /opt/eoxserver/
ADD docker/gunicorn.conf.py /opt/eoxserver/

# install EOxServer and its dependencies
WORKDIR /opt/eoxserver

RUN pip3 install -r requirements.txt \
  && pip3 install "django==$DJANGO" \
  && pip3 install .

EXPOSE 8000

ENTRYPOINT ["/opt/eoxserver/eoxserver-entrypoint.sh"]

CMD ["gunicorn", "$GUNICORN_CMD_ARGS"]
