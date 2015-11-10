# Pull base image.
FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -y apt-file
RUN apt-get install -y python-software-properties software-properties-common
RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update \
&&  apt-get install -y aptitude \
&&  aptitude install -y \
    gdal-bin \
    libgdal1-dev \
    libxml2 \
    python-lxml \
    python-libxml2 \
    libproj0 \
    libproj-dev \
    libgeos-dev \
    libgeos++-dev \
    cgi-mapserver \
    python-mapscript \
    python-psycopg2 \
    postgis \
    python-gdal \
    python-pip \
    wget \
    git
RUN apt-get install -y libpython-dev
RUN  wget https://pypi.python.org/packages/source/p/pysqlite/pysqlite-2.6.3.tar.gz \
&&  tar xzf pysqlite-2.6.3.tar.gz \
&&  cd pysqlite-2.6.3 \
&&  sed -i "/define=SQLITE_OMIT_LOAD_EXTENSION/c\#define=SQLITE_OMIT_LOAD_EXTENSION" setup.cfg \
&&  sudo python setup.py install
RUN cd - \
&&  pip install "django>=1.7,<1.8" \
&&  pip install twisted \
&&  django-admin.py --version
RUN git clone --recursive https://github.com/EOxServer/eoxserver
RUN cd eoxserver \
&&  python setup.py develop

# temporary fix of spatialite init
# takes very long if not set to 1
RUN cd eoxserver/eoxserver/core/commands \
&&  sed -i 's/InitSpatialMetadata()/InitSpatialMetadata(1)/g' create_instance.py

RUN cd eoxserver \
&&  eoxserver-admin.py create_instance eoxtest --init-spatialite
RUN cd eoxserver/eoxtest \
&&  python manage.py syncdb --noinput --traceback \
&&  echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin','test@eox.at','admin')" | python manage.py shell


ENTRYPOINT cd eoxserver/eoxtest \
&&  python manage.py runserver 0.0.0.0:8000
