#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
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

from eoxserver.core.registry import Registry, RegisteredInterface
from eoxserver.core.config import Config
from eoxserver.core.interfaces import Method, ObjectArg

class StartupHandlerInterface(RegisteredInterface):
    REGISTRY_CONF = {
        "name": "Startup Handler Interface",
        "intf_id": "core.startup.StartupHandler",
        "registry_keys": (),
    }

    startup = Method(
        ObjectArg("config", arg_class=Config),
        ObjectArg("registry", arg_class=Registry),
    )
    
    reset = Method(
        ObjectArg("config", arg_class=Config),
        ObjectArg("registry", arg_class=Registry),
    )
