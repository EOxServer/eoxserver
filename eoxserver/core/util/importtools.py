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

""" This module contains utilities to easily import hierarchies of packages and
modules.
"""

import logging
import traceback
import pkgutil

try:
    # Python >= 3.1
    from importlib import import_module
except:
    try:
        # Django versions >= 1.9
        from django.utils.module_loading import import_module
    except ImportError:
        # Django versions < 1.9
        from django.utils.importlib import import_module


logger = logging.getLogger(__name__)


def easy_import(module_path):
    """ Utility function to import one or more modules via a given module path.
        The last component of the module path can also be a '*' or a '**'
        character string which imports all submodules of the package either
        recursively (with '**') or not (with '*').

        :param module_path: a typical python module path in the dotted notation.
                            wildcards can be appeded at the last level.
    """

    parts = module_path.split(".")
    if parts[-1] == "*":
        import_modules(".".join(parts[:-1]))
    elif parts[-1] == "**":
        import_recursive(".".join(parts[:-1]))
    else:
        try:
            import_module(module_path)
            logger.debug("Imported module '%s'." % module_path)
        except ImportError:
            logger.error("Failed to import module '%s'." % module_path)
            logger.debug(traceback.format_exc())


def import_modules(base_module_path):
    """ Helper function to import all direct submodules within a package. This
        function is not recursive.

        :param base_module_path: the base module path in the dotted notation.
    """

    path = import_module(base_module_path).__path__
    for loader, module_name, is_pkg in pkgutil.iter_modules(path):
        full_path = "%s.%s" % (base_module_path, module_name)
        try:
            loader.find_module(module_name).load_module(module_name)
            logger.debug("Imported module '%s'." % full_path)
        except ImportError:
            logger.error("Failed to import module '%s'." % full_path)
            logger.debug(traceback.format_exc())


def import_recursive(base_module_path):
    """  Helper function to recursively import all submodules and packages.

        :param base_module_path: the base module path in the dotted notation.
    """

    path = import_module(base_module_path).__path__
    for loader, module_name, is_pkg in pkgutil.walk_packages(path):
        full_path = "%s.%s" % (base_module_path, module_name)
        try:
            loader.find_module(module_name).load_module(module_name)
            logger.debug("Imported module '%s'." % full_path)
        except ImportError:
            logger.error("Failed to import module '%s'." % full_path)
            logger.debug(traceback.format_exc())


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path)

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
        )
