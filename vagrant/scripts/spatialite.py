#!/usr/bin/python

from eoxserver.core.commands import create_instance

tmp = create_instance.Command()
tmp._init_spatialite("autotest","/var/eoxserver/")
