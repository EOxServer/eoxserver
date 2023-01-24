# EOxServer

EOxServer is a Python application and library for presenting Earth
Observation (EO) data and metadata.

![build](https://github.com/EOxServer/eoxserver/actions/workflows/ci.yml/badge.svg)
[![PyPi](https://badge.fury.io/py/EOxServer.svg)](https://pypi.org/project/EOxServer/)
[![ReadTheDocs](https://readthedocs.org/projects/eoxserver/badge/?version=master)](http://docs.eoxserver.org/en/master)

EOxServer implements the [OGC](http://www.opengeospatial.org)
Implementation Specifications EO-WCS and EO-WMS on top of
[MapServer's](http://mapserver.org) [WCS](http://www.opengeospatial.org/standards/wcs) and
[WMS](http://www.opengeospatial.org/standards/wms) implementations.
EOxServer is released under the
[EOxServer Open License](https://docs.eoxserver.org/en/stable/copyright.html) an MIT-style
license and written in python and entirely based on open source software including:

- [MapServer](http://mapserver.org)
- [Django/GeoDjango](https://www.djangoproject.com)
- [GDAL](http://www.gdal.org>)
- [SpatiaLite](http://www.gaia-gis.it/spatialite)
- [PostGIS](http://postgis.refractions.net/>)
- [PROJ.4](http://trac.osgeo.org/proj/>)

More information is available at [https://eoxserver.org](https://eoxserver.org). Documentation
is available at [readthedocs](https://docs.eoxserver.org/en/stable/)

## Docker

To run with SpatiaLite database simply run:

```sh
docker run -it --rm -p 8080:8000 eoxa/eoxserver
```

EOxServer is now accessible at [http://localhost:8080/](http://localhost:8080/).
And you can login to the `Admin Client` using:

- username: admin
- password: admin

The following environment variables control configuration:

- `DB`: Specify the used database type. either `spatialite` or `postgis`
- `DB_PW`, `DB_NAME`, `DB_HOST`, `DB_USER`: these credentials will be used to establish a
    connection to the postgres database when DB is set to `postgis` in order to wait
    for it to come online
- `INSTANCE_NAME`: the name of the instance passed to `eoxserver-instance.py` - defaults
    to `instance`
- `INSTANCE_DIR`: the directory of the instance. Defaults to `/opt/instance`
- `DJANGO_USER`, `DJANGO_MAIL`, `DJANGO_PASSWORD`: when set, these credentials will be
    used to create a superuser to be used for the Django Admin. By default, no user is
    created
- `COLLECT_STATIC`: if set to "true" (the default), static files will be collected
    upon initialization
- `PREINIT_SCRIPTS`: the list of commands that will be executed before
    the instance is initialized
- `INIT_SCRIPTS`: the list of commands that will be executed once
    when the instance is initialized
- `STARTUP_SCRIPTS`: the list of commands that will be executed before
    the command is run
- `GUNICORN_CMD_ARGS`: gunicorn command arguments. Defaults to
    `--config /opt/eoxserver/gunicorn.conf.py ${INSTANCE_NAME}.wsgi:application`

## Development

The autotest instance can be used for development and testing.
More information in `./autotest/README.md`
