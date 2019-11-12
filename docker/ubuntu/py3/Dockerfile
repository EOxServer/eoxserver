FROM ubuntu:19.10

ARG DJANGO=2.2

# install OS dependency packages
RUN apt-get update \
  && apt-get install -y \
    python3 \
    python3-pip \
    libpq-dev \
    python3-gdal \
    python3-mapscript \
    gdal-bin \
  && apt-get autoremove -y \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/partial/* /tmp/* /var/tmp/*

# install EOxServer
RUN mkdir /opt/eoxserver/

ADD eoxserver /opt/eoxserver/eoxserver
ADD tools /opt/eoxserver/tools
ADD setup.cfg setup.py MANIFEST.in README.rst requirements.txt /opt/eoxserver/

# install EOxServer and its dependencies
WORKDIR /opt/eoxserver

RUN pip3 install -r requirements.txt \
  && pip3 install "django==$DJANGO" \
  && pip3 install .

# Create an EOxServer instance
RUN mkdir /opt/instance && \
  eoxserver-instance.py instance /opt/instance

WORKDIR /opt/instance

EXPOSE 8000

CMD ["gunicorn", "--chdir", "/opt/instance", "--bind", ":8000", "instance.wsgi:application", "--workers", "10",  "--worker-class", "eventlet", "--timeout", "600"]
