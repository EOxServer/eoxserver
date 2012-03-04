#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

"""
This module provides an implementation of a system configuration that relies
on different configuration files. It is used by :mod:`eoxserver.core.system` to
store the current system configuration.
"""

import imp
import os.path
from sys import prefix
from ConfigParser import RawConfigParser

from django.conf import settings

from eoxserver.core.exceptions import InternalError

class Config(object):
    """
    The :class:`Config` class represents a system configuration. Internally,
    it relies on two configuration files:
    
    * the default configuration file (``eoxserver/conf/default.conf``)
    * the instance configuration file (``conf/eoxserver.conf`` in the instance
      directory)
    
    Configuration values are read from these files.
    """
    
    def __init__(self):
        self.__eoxs_path = None
        self.__default_conf = None
        self.__instance_conf = None

        eoxs_path = self.getEOxSPath()
        
        default_conf_path = os.path.join(eoxs_path, "conf", "default.conf")
        default_conf_path_alt = os.path.join(prefix, "eoxserver/conf/default.conf")
        
        if os.path.exists(default_conf_path):
            self.__default_conf = ConfigFile(default_conf_path)
        elif os.path.exists(default_conf_path_alt):
            self.__default_conf = ConfigFile(default_conf_path_alt)
        else:
            raise InternalError("Improperly installed: could not find default configuration file.")
        
        instance_conf_path = os.path.join(settings.PROJECT_DIR, "conf", "eoxserver.conf")
        
        if os.path.exists(instance_conf_path):
            self.__instance_conf = ConfigFile(instance_conf_path)
        else:
            raise InternalError("Improperly configured: could not find instance configuration file.")
    
    def getConfigValue(self, section, key):
        """
        Returns a configuration parameter value. The ``section`` and ``key``
        arguments denote the parameter to be looked up. The value is searched
        for first in the instance configuration file; if it is not found there
        the value is read from the default configuration file.
        """
        
        inst_value = self.getInstanceConfigValue(section, key)
        if inst_value is None:
            return self.getDefaultConfigValue(section, key)
        else:
            return inst_value
    
    def getDefaultConfigValue(self, section, key):
        """
        Returns a configuration parameter default value (read from the default
        configuration file). The ``section`` and ``key`` arguments denote the
        parameter to be looked up.
        """
        
        return self.__default_conf.get(section, key)
        
    def getInstanceConfigValue(self, section, key):
        """
        Returns a configuration parameter value as defined in the instance
        configuration file, or ``None`` if it is not found there. The
        ``section`` and ``key`` arguments denote the parameter to be looked up.
        """
        
        return self.__instance_conf.get(section, key)
    
    def getConcurringConfigValues(self, section, key):
        """
        Returns a dictionary od concurring configuration parameter values. It
        may have two entries
        
        * ``default``: the default configuration parameter value
        * ``instance``: the instance configuration value
        
        If there is no configuration parameter value defined in the respective
        configuration file, the entry is omitted.
        
        The ``section`` and ``key`` arguments denote the parameter to be looked
        up.
        """
        
        concurring_values = {}
        
        def_value = self.getDefaultConfigValue(section, key)
        if def_value is not None:
            concurring_values["default"] = def_value
        
        instance_value = self.getInstanceConfigValue(section, key)
        if instance_value is not None:
            concurring_values["instance"] = instance_value
        
        return concurring_values
    
    def getEOxSPath(self):
        """
        Returns the path to the EOxServer installation (not to the instance).
        """
        
        if self.__eoxs_path is None:
            try:
                _, eoxs_path, _ = imp.find_module("eoxserver")
            except ImportError:
                raise InternalError("Something very strange is happening: cannot find 'eoxserver' module.")
            self.__eoxs_path = eoxs_path
        
        return self.__eoxs_path

class ConfigFile(object):
    """
    This is a wrapper for a configuration file. It is based on the Python
    builtin :mod:`ConfigParser` module.
    """
    
    def __init__(self, config_filename):
        self.config_filename = config_filename

        self._parser = RawConfigParser()
        self._parser.read(config_filename)

    def get(self, section, key):
        """
        Return the configuration parameter value, or ``None`` if it is not
        defined.
        
        The ``section`` argument denotes the section of the configuration file
        where to look for the parameter named ``key``. See the
        :mod:`ConfigParser` module documentation for details on the config file
        syntax.
        """
        
        if self._parser.has_option(section, key):
            return self._parser.get(section, key)
        else:
            return None
