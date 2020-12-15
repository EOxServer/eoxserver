FROM centos:7

ARG DJANGO=1.11.26

# install OS dependency packages
RUN rpm -Uvh http://yum.packages.eox.at/el/eox-release-7-0.noarch.rpm \
  && yum update -y \
  && yum install -y epel-release \
  && yum install -y \
    python \
    postgresql \
    postgis \
    python-psycopg2 \
    gdal \
    gdal-python \
    mapserver \
    mapserver-python \
    libxml2 \
    libxml2-python \
    python-lxml \
    python-pip \
  && yum clean all

# install EOxServer
RUN mkdir /opt/eoxserver/

ADD eoxserver /opt/eoxserver/eoxserver
ADD tools /opt/eoxserver/tools
ADD setup.cfg setup.py MANIFEST.in README.rst requirements.txt /opt/eoxserver/

# install EOxServer and its dependencies
WORKDIR /opt/eoxserver

RUN pip install -r requirements.txt \
  && pip install -U "django==$DJANGO" \
  && pip install -U "gunicorn<19" \
  && pip install .

# Create an EOxServer instance
RUN mkdir /opt/instance \
  && eoxserver-instance.py instance /opt/instance

WORKDIR /opt/instance

EXPOSE 8000

CMD ["gunicorn", "--chdir", "/opt/instance", "--bind", ":8000", "instance.wsgi:application", "--workers", "10",  "--worker-class", "eventlet", "--timeout", "600"]
