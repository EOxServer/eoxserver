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
This module defines an interface for startup handlers that are called during
system startup or reset.
"""

from eoxserver.core.registry import Registry, RegisteredInterface
from eoxserver.core.config import Config
from eoxserver.core.interfaces import Method, ObjectArg

class StartupHandlerInterface(RegisteredInterface):
    """
    This is an interface for startup handlers. These handlers are called
    automatically in the startup sequence; see the :mod:`eoxserver.core.system`
    module documentation. It is intended to be implemented by modules or
    components that need additional global system setup operations.
    
    .. method:: startup(config, registry)
    
       This method is called in the startup sequence after the configuration
       has been validated and the registry has been set up. Those are passed
       as ``config`` and ``registry`` parameters respectively.
       
       It may perform any additional logic needed for the setup of the
       components concerned by the implementation.
    
    .. method:: reset(config, registry)
    
       This method is called in the reset sequence after the new configuration
       has been validated and the registry has been set up. Those are passed
       as ``config`` and ``registry`` parameters respectively.
       
       It may perform any additional logic needed by the components concerned
       by the implementation for switching to the new configuration.
    """
    
    REGISTRY_CONF = {
        "name": "Startup Handler Interface",
        "intf_id": "core.startup.StartupHandler",
        "binding_method": "direct"
    }

    startup = Method(
        ObjectArg("config", arg_class=Config),
        ObjectArg("registry", arg_class=Registry),
    )
    
    reset = Method(
        ObjectArg("config", arg_class=Config),
        ObjectArg("registry", arg_class=Registry),
    )
