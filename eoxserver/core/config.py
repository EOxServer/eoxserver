#-------------------------------------------------------------------------------
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
on different configuration files.
"""

import imp
from os.path import join, getmtime
from sys import prefix
import threading
import logging
from time import time

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser


from django.conf import settings


config_lock = threading.RLock()
logger = logging.getLogger(__name__)

# configuration singleton
_cached_config = None
_last_access_time = None


def get_eoxserver_config():
    """ Returns the EOxServer config as a :class:`ConfigParser.RawConfigParser`
    """
    with config_lock:
        if not _cached_config or \
                getmtime(get_instance_config_path()) > _last_access_time:
            reload_eoxserver_config()

    return _cached_config


def reload_eoxserver_config():
    """ Triggers the loading or reloading of the EOxServer config as a
        :class:`ConfigParser.RawConfigParser`.
    """
    global _cached_config, _last_access_time
    _, eoxs_path, _ = imp.find_module("eoxserver")
    paths = [
        join(eoxs_path, "conf", "default.conf"),
        join(prefix, "eoxserver/conf/default.conf"),
        get_instance_config_path()
    ]

    logger.info(
        "%soading the EOxServer configuration. Using paths: %s."
        % ("Rel" if _cached_config else "L", ", ".join(paths))
    )

    with config_lock:
        _cached_config = RawConfigParser()
        _cached_config.read(paths)
        _last_access_time = time()


def get_instance_config_path():
    """ Convenience function to get the path to the instance config.
    """
    return join(settings.PROJECT_DIR, "conf", "eoxserver.conf")
