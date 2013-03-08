#!/bin/sh -xe

# Activate the virtual environment
cd $WORKSPACE
source .venv/bin/activate

cd autotest/autotest
export XML_CATALOG_FILES="$WORKSPACE/schemas/catalog.xml"
echo "**> running tests ..."
python ../manage.py test services -v2
#TODO: Enable testing of all apps
#python manage.py test core services coverages -v2

# Run command line tests
echo "**> running command line tests ..."
python manage.py syncdb --noinput
python manage.py loaddata auth_data.json initial_rangetypes.json
#TODO: Expand this tests:
#eoxs_add_dataset_series
#eoxs_register_dataset
#eoxs_insert_into_series
#eoxs_check_id
#eoxs_list_ids
#eoxs_load_rangetypes
#eoxs_list_rangetypes
#eoxs_synchronize
#eoxs_remove_from_series
#eoxs_deregister_dataset
#compare with expected
