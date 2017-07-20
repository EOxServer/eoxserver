#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

"""\
The eoxserver.core package provides functionality for the initialization and
re-initialization of the component system.
For convenience, the module imports the most important items from the
:mod:`eoxserver.core.component` module and instantiates a component manager
:obj:`eoxserver.core.env`.
"""


import logging
import threading

from eoxserver.core.component import (
    ComponentManager, ComponentMeta, Component,
    ExtensionPoint, UniqueExtensionPoint, implements
)
from eoxserver.core.util.importtools import easy_import, import_module


env = ComponentManager()
logger = logging.getLogger(__name__)

__init_lock = threading.RLock()
__is_initialized = False


def initialize():
    """ Initialize the EOxServer plugin system by trying to import all the
        plugins referenced by the `PLUGINS` configuration entry from the
        settings module. If a module path ends with '*' then all direct
        submodules will be imported aswell and if it ends with '**' it means
        that the import will be done recursively.
    """

    global __is_initialized

    with __init_lock:
        if __is_initialized:
            return
        __is_initialized = True

        from django.conf import settings

        logger.info("Initializing EOxServer components.")

        for plugin in getattr(settings, "COMPONENTS", ()):
            easy_import(plugin)


def reset():
    """ Reset the EOxServer plugin system.
    """

    global __is_initialized

    with __init_lock:
        if not __is_initialized:
            return
        __is_initialized = False

        logger.info("Resetting EOxServer components.")
        ComponentMeta._registry = {}
        ComponentMeta._components = []

        initialize()
