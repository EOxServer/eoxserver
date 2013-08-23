import logging
import traceback
import pkgutil

from django.utils.importlib import import_module

from component import Component, ComponentManager, ExtensionPoint, implements

env = ComponentManager()
logger = logging.getLogger(__name__)


def initialize():
    """ Initialize the EOxServer plugin system by trying to import all the 
        plugins referenced by the `PLUGINS` configuration entry from the 
        settings module. If a module path ends with '*' then all direct 
        submodules will be imported aswell and if it ends with '**' it means 
        that the import will be done recursively.
    """

    from django.conf import settings

    for plugin in getattr(settings, "PLUGINS", ()):

        parts = plugin.split(".")
        if parts[-1] == "*":
            import_modules(".".join(parts[:-1]))
        elif parts[-1] == "**":
            import_recursive(".".join(parts[:-1]))
        else:
            try:
                import_module(plugin)
                logger.debug("Imported plugin '%s'." % plugin)
            except ImportError:
                logger.error("Failed to import plugin '%s'." % plugin)
                logger.debug(traceback.format_exc())


def import_modules(base_module_path):
    """ Helper function to import all direct submodules within a package. This 
        function is not recursive.
    """

    path = import_module(base_module_path).__path__
    for loader, module_name, is_pkg in pkgutil.iter_modules(path):
        full_path = "%s.%s" % (base_module_path, module_name)
        try:
            loader.find_module(module_name).load_module(module_name)
            logger.debug("Imported plugin '%s'." % full_path)
        except ImportError:
            logger.error("Failed to import plugin '%s'." % full_path)
            logger.debug(traceback.format_exc())


def import_recursive(base_module_path):
    """  Helper function to recursively import all submodules and packages.
    """

    path = import_module(base_module_path).__path__
    for loader, module_name, is_pkg in pkgutil.walk_packages(path):
        full_path = "%s.%s" % (base_module_path, module_name)
        try:
            loader.find_module(module_name).load_module(module_name)
            logger.debug("Imported plugin '%s'." % full_path)
        except ImportError:
            logger.error("Failed to import plugin '%s'." % full_path)
            logger.debug(traceback.format_exc())
