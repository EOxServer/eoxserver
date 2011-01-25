#-----------------------------------------------------------------------
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

from django.conf import settings

from eoxserver.lib.handlers import EOxSServiceHandler, EOxSVersionHandler, EOxSOperationHandler
from eoxserver.lib.config import EOxSConfig
from eoxserver.lib.exceptions import (EOxSInvalidRequestException, )

import os
import os.path
from fnmatch import fnmatch

class EOxSRegistry(object):
    _registered = False
    modules = {}
    service_handlers = []
    version_handlers = []
    operation_handlers = []
    
    @classmethod
    def register(cls, module):
        cls.modules[module.__name__] = module
        for name in dir(module):
            attr = module.__getattribute__(name)
            try:
                if type(attr) == type(object):
                    if issubclass(attr, EOxSServiceHandler):
                        if not attr.ABSTRACT:
                            cls.service_handlers.append(attr)
                    elif issubclass(attr, EOxSVersionHandler):
                        if not attr.ABSTRACT:
                            cls.version_handlers.append(attr)
                    elif issubclass(attr, EOxSOperationHandler):
                        if not attr.ABSTRACT:
                            cls.operation_handlers.append(attr)
            except:
                pass

    @classmethod
    def registerAll(cls):
        if not cls._registered:
            for filename in os.listdir(os.path.join(settings.PROJECT_DIR, "modules")):
                if filename != "__init__.py" and fnmatch(filename, "*.py"):
                    module_name = filename[:-3]
                    module = __import__("eoxserver.modules.%s" % module_name).modules.__getattribute__(module_name)
                    EOxSRegistry.register(module)
            cls._registered = True
    
    @classmethod
    def serviceSupported(cls, service):
        for HandlerClass in cls.service_handlers:
            if HandlerClass.SERVICE.upper() == service.upper():
                return True
        
        return False
    
    @classmethod
    def versionSupported(cls, service, version):
        for HandlerClass in cls.version_handlers:
            if HandlerClass.SERVICE.upper() == service.upper() and \
               version in HandlerClass.VERSIONS:
                return True
        
        return False
    
    @classmethod
    def operationSupported(cls, service, version, operation):
        for HandlerClass in cls.operation_handlers:
            if HandlerClass.SERVICE.upper() == service.upper() and \
               version in HandlerClass.VERSIONS and \
               operation.lower() in HandlerClass.OPERATIONS:
                return True
        
        else:
            return False
    
    @classmethod
    def _convertVersionNumber(cls, version):
        version_list = [int(i) for i in version.split(".")]
        version_value = 0
        for i in range(0, min(3, len(version_list))):
            version_value = version_value + version_list[i] * (100**(2-i))
            
        return version_value
    
    @classmethod
    def _versionLt(cls, version_1, version_2):
        version_1_value = cls._convertVersionNumber(version_1)
        version_2_value = cls._convertVersionNumber(version_2)

        return version_1_value < version_2_value

    @classmethod
    def getHighestVersion(cls, service, lower_than=None):
        highest_version = None
        
        for HandlerClass in cls.version_handlers:
            if HandlerClass.SERVICE.upper() == service.upper():
                for version in HandlerClass.VERSIONS:
                    if highest_version is None:
                        if lower_than is None or cls._versionLt(version, lower_than):
                            highest_version = version
                    else:
                        if cls._versionLt(highest_version, version) and (lower_than is None or cls._versionLt(version, lower_than)):
                            highest_version = version
        
        return highest_version
    
    @classmethod
    def getLowestVersion(cls, service):
        lowest_version = None
        
        for HandlerClass in cls.version_handlers:
            if HandlerClass.SERVICE.upper() == service.upper():
                for version in HandlerClass.VERSIONS:
                    if lowest_version is None:
                        lowest_version = version
                    else:
                        if cls._versionLt(version, lowest_version):
                            lowest_version = version
        
        return lowest_version

    @classmethod
    def getHandler(cls, handlers, filter_expr):
        MatchingClass = None
        for HandlerClass in handlers:
            if filter_expr(HandlerClass):
                MatchingClass = HandlerClass
                break

        if MatchingClass is None:
            return None
        else:
            return MatchingClass(EOxSConfig.getConfig(os.path.join(settings.PROJECT_DIR, "conf", "eoxserver.conf"))) # TODO: Hack -> make config singleton

    @classmethod
    def getServiceHandler(cls, service):
        handler = cls.getHandler(
            handlers=cls.service_handlers,
            filter_expr = lambda HandlerClass:
                HandlerClass.SERVICE.upper() == service.upper()
        )
        
        return handler
    
    @classmethod
    def getVersionHandler(cls, service, version):
        handler = cls.getHandler(
            handlers=cls.version_handlers,
            filter_expr = lambda HandlerClass:
                HandlerClass.SERVICE.upper() == service.upper() and \
                version in HandlerClass.VERSIONS
        )
        
        return handler

    @classmethod
    def getOperationHandler(cls, service, version, operation):
        handler = cls.getHandler(
            handlers=cls.operation_handlers,
            filter_expr=lambda HandlerClass:
                HandlerClass.SERVICE.upper() == service.upper() and \
                version in HandlerClass.VERSIONS and \
                operation.lower() in HandlerClass.OPERATIONS
        )

        return handler
