#!/bin/sh -e

# PostgreSQL/PostGIS database
DB_NAME="eoxserver_testing"
DB_USER="eoxserver"
DB_PASSWORD="eoxserver"
PG_DATA_DIR="/var/lib/pgsql/data"

# # Permanently start PostgreSQL
# chkconfig postgresql on
# # Init PostgreSQL
# if [ ! -f "/var/lib/pgsql/data/PG_VERSION" ] ; then
#     service postgresql initdb
# fi
# # Allow DB_USER to access DB_NAME and test_DB_NAME with password
# if ! grep -Fxq "local   $DB_NAME $DB_USER               md5" /var/lib/pgsql/data/pg_hba.conf ; then
#     sed -e "s/^# \"local\" is for Unix domain socket connections only$/&\nlocal   $DB_NAME $DB_USER               md5\nlocal   test_$DB_NAME $DB_USER          md5/" \
#         -i /var/lib/pgsql/data/pg_hba.conf
# fi
# # Reload PostgreSQL
# service postgresql force-reload

# # Configure PostgreSQL/PostGIS database

# ## Write database configuration script
# TMPFILE=`mktemp`
# cat << EOF > "$TMPFILE"
# #!/bin/sh -e
# # cd to a "safe" location
# cd /tmp
# if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='template_postgis'")" != 1 ] ; then
#     echo "Creating template database."
#     createdb -E UTF8 template_postgis
#     createlang plpgsql -d template_postgis
#     psql postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
#     if [ -f /usr/share/pgsql/contrib/postgis-64.sql ] ; then
#         psql -d template_postgis -f /usr/share/pgsql/contrib/postgis-64.sql
#     else
#         psql -d template_postgis -f /usr/share/pgsql/contrib/postgis.sql
#     fi
#     psql -d template_postgis -f /usr/share/pgsql/contrib/spatial_ref_sys.sql
#     psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
#     psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
#     psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
# fi
# if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'")" != 1 ] ; then
#     echo "Creating EOxServer database user."
#     psql postgres -tAc "CREATE USER $DB_USER NOSUPERUSER CREATEDB NOCREATEROLE ENCRYPTED PASSWORD '$DB_PASSWORD'"
# fi
# if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")" == 1 ] ; then
#     echo "Deleting EOxServer database"
#     dropdb $DB_NAME
# fi
# echo "Creating EOxServer database."
# createdb -O $DB_USER -T template_postgis $DB_NAME
# EOF
# ## End of database configuration script

# if [ -f $TMPFILE ] ; then
#     chgrp postgres $TMPFILE
#     chmod g+rx $TMPFILE
#     su postgres -c "$TMPFILE"
#     rm "$TMPFILE"
# else
#     echo "Script to configure DB not found."
# fi

if [ -n "`systemctl | grep postgresql.service`" ]
then
    info "Stopping running PostgreSQL server ..."
    systemctl stop postgresql.service
fi

[ ! -d "$PG_DATA_DIR_DEFAULT" ] || rm -fR "$PG_DATA_DIR_DEFAULT"
[ ! -d "$PG_DATA_DIR" ] || rm -fR "$PG_DATA_DIR"

cat >/etc/systemd/system/postgresql.service <<END
.include /lib/systemd/system/postgresql.service
[Service]
Environment=PGDATA=$PG_DATA_DIR
END
systemctl daemon-reload


postgresql-setup initdb
systemctl disable postgresql.service # DO NOT REMOVE!
systemctl enable postgresql.service
systemctl start postgresql.service
systemctl status postgresql.service

# STEP 5: SETUP POSTGIS DATABASE TEMPLATE
if [ -z "`sudo -u postgres psql --list | grep template_postgis`" ]
then
    sudo -u postgres createdb template_postgis
    #sudo -u postgres createlang plpgsql template_postgis

    PG_SHARE=/usr/share/pgsql
    POSTGIS_SQL="postgis-64.sql"
    [ -f "$PG_SHARE/contrib/$POSTGIS_SQL" ] || POSTGIS_SQL="postgis.sql"
    sudo -u postgres psql -q -d template_postgis -f "$PG_SHARE/contrib/$POSTGIS_SQL"
    sudo -u postgres psql -q -d template_postgis -f "$PG_SHARE/contrib/spatial_ref_sys.sql"
    sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    sudo -u postgres psql -q -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
fi


if [ -z `sudo -u postgres psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'"` ] ; then
    echo "Creating EOxServer database user."
    sudo -u postgres psql postgres -tAc "CREATE USER $DB_USER NOSUPERUSER CREATEDB NOCREATEROLE ENCRYPTED PASSWORD '$DB_PASSWORD'"
fi

if [ ! -z `sudo -u postgres psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'"` ] ; then
    echo "Deleting EOxServer database"
    sudo -u postgres dropdb $DB_NAME
fi

echo "Creating EOxServer database."
sudo -u postgres createdb -O $DB_USER -T template_postgis $DB_NAME
