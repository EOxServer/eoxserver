#-----------------------------------------------------------------------
# $Id$
# 
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import imp
import os.path
from ConfigParser import ConfigParser

from django.conf import settings

class Config(object):
    def __init__(self):
        self.__eoxs_path = None
        self.__default_conf = None
        self.__instance_conf = None

        eoxs_path = self.getEOxSPath()
        
        default_conf_path = os.path.join(eoxs_path, "conf", "default.conf")
        
        if os.path.exists(default_conf_path):
            self.__default_conf = ConfigFile(default_conf_path)
        else:
            raise InternalError("Improperly installed: could not find default configuration file.")
        
        instance_conf_path = os.path.join(settings.PROJECT_DIR, "conf", "eoxserver.conf")
        
        if os.path.exists(instance_conf_path):
            self.__instance_conf = ConfigFile(instance_conf_path)
        else:
            raise InternalError("Improperly configured: could not find instance configuration file.")
    
    def getConfigValue(self, section, key):
        inst_value = self.getInstanceConfigValue(section, key)
        if inst_value is None:
            return self.getDefaultConfigValue(section, key)
        else:
            return inst_value
    
    def getDefaultConfigValue(self, section, key):
        return self.__default_conf.get(section, key)
        
    def getInstanceConfigValue(self, section, key):
        return self.__instance_conf.get(section, key)
    
    def getConcurringConfigValues(self, section, key):
        concurring_values = {}
        
        def_value = self.getDefaultConfigValue(section, key)
        if def_value is not None:
            concurring_values["default"] = def_value
        
        instance_value = self.getInstanceConfigValue(section, key)
        if instance_value is not None:
            concurring_values["instance"] = instance_value
        
        return concurring_values
    
    def getEOxSPath(self):
        if self.__eoxs_path is None:
            try:
                f, eoxs_path, desc = imp.find_module("eoxserver")
            except ImportError:
                raise InternalError("Something very strange is happening: cannot find 'eoxserver' module.")
            self.__eoxs_path = eoxs_path
        
        return self.__eoxs_path

class ConfigFile(object):
    def __init__(self, config_filename):
        self.config_filename = config_filename

        self._parser = ConfigParser()
        self._parser.read(config_filename)

    def get(self, section, key):
        if self._parser.has_option(section, key):
            return self._parser.get(section, key)
        else:
            return None
