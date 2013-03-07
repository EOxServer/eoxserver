#!/bin/sh -xe

# Activate the virtual environment
cd $WORKSPACE
source .venv/bin/activate

cd autotest
export XML_CATALOG_FILES="$WORKSPACE/schemas/catalog.xml"
echo "**> running tests ..."
python manage.py test services -v2
#python manage.py test core services coverages -v2

# Run command line tests
echo "**> running command line tests ..."
python manage.py syncdb --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json
