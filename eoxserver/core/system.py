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

import os
import re
from threading import RLock, Condition, local
import logging

from django.conf import settings

from eoxserver.core.config import Config
from eoxserver.core.registry import Registry, RegistryConfigReader
from eoxserver.core.interfaces import RUNTIME_VALIDATION_LEVEL, IntfConfigReader

class Environment(local):
    def __init__(self, config, registry):
        self.config = config
        self.registry = registry

class System(object):
    UNCONFIGURED = 0
    STARTING = 10
    RESETTING = 20
    CONFIGURED = 30
    ERROR = 40
    
    __lock = RLock()
    
    __state_cond = Condition()
    __state = UNCONFIGURED
    
    __thread_env = None
    __registry = None
    __config = None
    
    @classmethod
    def startRequest(cls):
        cls.__state_cond.acquire()
        
        try:
            if cls.__state == cls.UNCONFIGURED:
                cls.__state = cls.STARTING
                cls.__state_cond.notifyAll()
                cls.__state_cond.release()
                try:
                    config, registry = cls.__load()
                    cls.__state_cond.acquire()
                    cls.__state = cls.CONFIGURED
                    cls.__config = config
                    cls.__registry = registry
                    cls.__thread_env = Environment(config, registry)
                except:
                    cls.__state_cond.acquire()
                    cls.__state = cls.ERROR
                    raise
            elif cls.__state == cls.STARTING or cls.__state == cls.RESETTING:
                while not (cls.__state == cls.CONFIGURED or cls.__state == cls.ERROR):
                    cls.__state_cond.wait()
                
                if cls.__state == cls.CONFIGURED:
                    cls.__thread_env.config = cls.__config
                    cls.__thread_env.registry = cls.__registry
                else:
                    raise InternalError("Could not load system config.")
            elif cls.__state == cls.ERROR:
                cls.__state = cls.RESETTING
                cls.__state_cond.notifyAll()
                cls.__state_cond.release()
                
                try:
                    config, registry = cls.__load(reset=True)
                    cls.__state_cond.acquire()
                    cls.__state = cls.CONFIGURED
                    cls.__config = config
                    cls.__registry = registry
                    cls.__thread_env.config = config
                    cls.__thread_env.registry = registry
                except:
                    cls.__state_cond.acquire()
                    cls.__state = cls.ERROR
                    raise
        finally:
            # try to release the state condition lock; if it has not
            # been acquired, ignore the resulting RuntimeError
            try:
                cls.__state_cond.notifyAll()
                cls.__state_cond.release()
            except RuntimeError: 
                pass
    
    @classmethod
    def reset(cls):
        cls.__state_cond.acquire()
        
        try:
            if cls.__state == cls.UNCONFIGURED:
                cls.__state = cls.STARTING
                cls.__state_cond.notifyAll()
                cls.__state_cond.release()
                try:
                    config, registry = cls.__load()
                    cls.__state_cond.acquire()
                    cls.__state = cls.CONFIGURED
                    cls.__config = config
                    cls.__registry = registry
                    cls.__thread_env = Environment(cls.__config, cls.__registry)
                except:
                    cls.__state_cond.acquire()
                    cls.__state = cls.ERROR
                    raise
            else:
                while cls.__state == cls.STARTING or cls.__state == cls.RESETTING:
                    cls.__state_cond.wait()
                
                prev_state = cls.__state
                
                cls.__state = cls.RESETTING
                cls.__state_cond.notifyAll()
                cls.__state_cond.release()
                
                try:
                    config, registry = cls.__load(reset=True)
                    cls.__state_cond.acquire()
                    cls.__state = cls.CONFIGURED
                    cls.__config = config
                    cls.__registry = registry
                    cls.__thread_env.config = config
                    cls.__thread_env.registry = registry
                except:
                    cls.__state_cond.acquire()
                    cls.__state = prev_state
                    raise

        finally:
            # try to release the state condition lock; if it has not
            # been acquired, ignore the resulting RuntimeError
            try:
                cls.__state_cond.notifyAll()
                cls.__state_cond.release()
            except RuntimeError:
                pass
        
    @classmethod
    def getRegistry(cls):
        if cls.__thread_env:
            return cls.__thread_env.registry
        else:
            raise InternalError("Could not access thread environment. System is in error state.")
    
    @classmethod
    def getConfig(cls):
        if cls.__thread_env:
            return cls.__thread_env.config
        else:
            raise InternalError("Could not access thread environment. System is in error state")
    
    @classmethod
    def __load(cls, reset=False):
        try:
            # first load the config
            config = Config()
            
            # validate the system configuration
            system_reader = SystemConfigReader(config)
            system_reader.validate()
            
            # configure the logging module
            logging.basicConfig(
                filename=system_reader.getLoggingFilename(),
                format=system_reader.getLoggingFormat(),
                level=system_reader.getLoggingLevel()
            )
            
            # TODO: integrate IPC
            
            # set up interfaces
            cls.__setup_interfaces(config)
            
            # set up registry
            registry = cls.__setup_registry(config)
            
            # invoke extending configuration validators
            cls.__validate_ext(config, registry)
            
            # invoke extending startup handlers
            if reset:
                cls.__reset_ext(config, registry)
            else:
                cls.__startup_ext(config, registry)
            
            return (config, registry)
            
        except Exception, e:
            logging.error("Could not start up system due to exception: %s" % str(e))
            
            raise
            
    @classmethod
    def __setup_interfaces(cls, config):
        # validate interface configuration
        intf_reader = IntfConfigReader(config)
        intf_reader.validate()
        
        # set runtime validation level
        level = intf_reader.getRuntimeValidationLevel()
        if level:
            RUNTIME_VALIDATION_LEVEL = level
    
    @classmethod
    def __setup_registry(cls, config):
        # validate registry configuration
        registry_reader = RegistryConfigReader(config)
        registry_reader.validate()
        
        # load registry
        registry = Registry(config)
        registry.load()
        
        return registry

    @classmethod
    def __validate_ext(cls, config, registry):
        Readers = registry.findImplementations(intf_id="core.readers.ConfigReader")
        
        for Reader in Readers:
            Reader().validate(config)

    @classmethod
    def __startup_ext(cls, config, registry):
        Handlers = registry.findImplementations(intf_id="core.startup.StartupHandler")
        
        for Handler in Handlers:
            Handler().startup(config, registry)
    
    @classmethod
    def __reset_ext(cls, config, registry):
        Handlers = registry.findImplementations(intf_id="core.startup.StartupHandler")
        
        for Handler in Handlers:
            Handler().reset(config, registry)

class SystemConfigReader(object):
    def __init__(self, config):
        self.config = config
    
    def validate(self):
        instance_id = self.getInstanceID()
        if not instance_id: 
            raise ConfigError("Missing mandatory 'instance_id' parameter")
        elif not re.match("[A-Za-z_][A-Za-z0-9_.-]*", instance_id):
            raise ConfigError("'instance_id' parameter must be NCName")
        
        if not self.getLoggingFilename():
            raise ConfigError("Missing mandatory 'logging_filename' parameter")

    def getInstanceID(self):
        return self.config.getInstanceConfigValue("core.system", "instance_id")

    def getLoggingFilename(self):
        return self.config.getInstanceConfigValue("core.system", "logging_filename")
    
    def getLoggingFormat(self):
        return self.config.getConfigValue("core.system", "logging_format")
    
    def getLoggingLevel(self):
        LEVELS = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        level_name = self.config.getInstanceConfigValue("core.system", "logging_level")
        
        if not level_name or level_name.upper() not in LEVELS:
            level_name = self.config.getDefaultConfigValue("core.system", "logging_level")
        
        return LEVELS[level_name.upper()]
