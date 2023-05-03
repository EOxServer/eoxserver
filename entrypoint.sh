#!/bin/bash

# eoxserver-entrypoint.sh
# This is the docker ENTRYPOINT script (https://docs.docker.com/engine/reference/builder/#entrypoint)
# It ensures a database connection and a running instance before refering execution to the passed command

# select python interpreter
PYTHON=$(which python3 || which python)
INSTANCE_DIR=${INSTANCE_DIR:-"/opt/instance"}
COLLECT_STATIC=${COLLECT_STATIC:-"true"}

# wait for the database connection before continuing
if [ "${DB:-postgis}" = "postgis" ] ; then
  until PGPASSWORD=${DB_PW} psql "${DB_NAME}" -h "${DB_HOST}" -U "${DB_USER}" -c "\q"; do
    >&2 echo "Database is unavailable - sleeping"
    sleep 5
  done
fi

# check if the instance dir exists. if not, this triggers the creation of a new instance
if [ ! -d "${INSTANCE_DIR}" ]; then
  mkdir -p "${INSTANCE_DIR}"

  # allow to specify pre-initialization scripts
  if [ ! -z "${PREINIT_SCRIPTS}" ] ; then
    for f in ${PREINIT_SCRIPTS} ; do
      source $f
    done
  fi
  
  ./eoxserver/scripts/eoxserver-instance.py "${INSTANCE_NAME}" "${INSTANCE_DIR}"
  cd "${INSTANCE_DIR}"

  # create the database schema
  $PYTHON manage.py migrate --noinput

  # collect static files if required
  if [ "${COLLECT_STATIC}" = "true" ] ; then
    $PYTHON manage.py collectstatic --noinput
  fi

  # if all credentials are passed, create a django superuser if it does not exist yet
  if [[ ! -z "$DJANGO_USER" && ! -z "$DJANGO_MAIL" && ! -z "$DJANGO_PASSWORD" ]] ; then
    $PYTHON manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='${DJANGO_USER}').exists() or \
    User.objects.create_superuser('${DJANGO_USER}', '${DJANGO_MAIL}', '${DJANGO_PASSWORD}')"
  fi

  # loop over potential initialization scripts
  if [ ! -z "${INIT_SCRIPTS}" ] ; then
    for f in ${INIT_SCRIPTS} ; do
      source $f
    done
  fi
fi

# allow to specify startup scripts, that will be called every time in the entry point
if [ ! -z "${STARTUP_SCRIPTS}" ] ; then
  for f in ${STARTUP_SCRIPTS} ; do
    source $f
  done
fi

# run the initial command
exec "$@"
