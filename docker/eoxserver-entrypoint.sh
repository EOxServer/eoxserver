#!/bin/bash

# select python interpreter
PYTHON=$(which python3 || which python)
INSTANCE_DIR="/opt/${INSTANCE_NAME}"

# check if the instance dir exists. if not, this triggers the creation of a new instance
if [ ! -d "${INSTANCE_DIR}" ]; then
  eoxserver-instance.py "${INSTANCE_NAME}" "${INSTANCE_DIR}"
  cd "${INSTANCE_DIR}"

  # create the database models
  $PYTHON manage.py migrate --noinput
  $PYTHON manage.py collectstatic --noinput

  # if all credentials are passed, create a django superuser
  if [[ ! -z "$DJANGO_USER" && ! -z "$DJANGO_MAIL" && ! -z "$DJANGO_PASSWORD" ]] ; then
    $PYTHON manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('${DJANGO_USER}', '${DJANGO_MAIL}', '${DJANGO_PASSWORD}')"
  fi

  # loop over potential initialization scripts
  if [ ! -z "${INIT_SCRIPTS}" ] ; then
    for f in ${INIT_SCRIPTS} ; do
      source $f
    done
  fi
fi

cd "${INSTANCE_DIR}"

# run the initial command
eval $@
