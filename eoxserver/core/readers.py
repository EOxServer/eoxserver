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
This module defines an interface for configuration readers.
"""

from eoxserver.core.interfaces import Method, ObjectArg
from eoxserver.core.config import Config
from eoxserver.core.registry import RegisteredInterface

class ConfigReaderInterface(RegisteredInterface):
    """
    This interface is intended to provide a way to validate and access the
    system configuration to modules which rely on configuration parameters. It
    defines only one mandatory :meth:`validate` method, but developers are free
    to add methods or attributes that give easy access to the underlying
    configuration values.
    
    .. method:: validate(config)
    
       This method shall validate the given system configuration ``config`` (a
       :class:`~.Config` instance). It shall raise a :exc:`~.ConfigError`
       exception in case the configuration with respect to the sections and
       parameters concerned by the implementation is invalid. It has no return
       value.
       
       The :meth:`validate` method is called automatically at system startup or
       configuration reset. If it fails system startup or reset will not
       succeed. So please be careful to raise :exc:`~.ConfigError` only in
       situations
       
       * when the components that need the parameter(s) are enabled
       * when the configuration will always lead to an error
    
       Otherwise, configuration errors of one optional module might break the
       whole system.
    """
    
    REGISTRY_CONF = {
        "name": "Config Reader Interface",
        "intf_id": "core.readers.ConfigReader",
        "binding_method": "direct"
    }
    
    validate = Method(ObjectArg("config", arg_class=Config))
