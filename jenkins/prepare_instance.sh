#!/bin/sh
# Create the virtual environment if it does not exist
cd $WORKSPACE
if [ -d ".venv" ]; then
  echo "**> virtualenv exists!"
else
  echo "**> creating virtualenv..."
  virtualenv --system-site-packages .venv
fi

# activate the virtual environment
source .venv/bin/activate

# Install EOxServer
echo "**> installing eoxserver..."
python setup.py develop

# Create the EOxServer instance
echo "**> creating autotest instance..."
mv autotest tmp1
eoxserver-admin.py create_instance autotest --init_spatialite
mv autotest/manage.py tmp1/
mv autotest/autotest/ tmp2
rmdir autotest/
mv tmp1 autotest
mv tmp2/settings.py autotest/
mv tmp2/conf/eoxserver.conf autotest/conf/
mv tmp2/wsgi.py autotest/
mv tmp2/data/config.sqlite autotest/data/
mv tmp2/data/init_spatialite-2.3.sql autotest/data/
rm -r tmp2
sed -e 's/\/autotest\/autotest/\/autotest/' -i autotest/settings.py
sed -e 's/\/autotest\/autotest/\/autotest/' -i autotest/conf/eoxserver.conf
sed -e 's/allowed_actions=/allowed_actions=Add,Delete/' -i autotest/conf/eoxserver.conf