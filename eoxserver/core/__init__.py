

from component import Component, ComponentManager, ExtensionPoint, implements

env = ComponentManager()


def initialize():
    from django.utils.importlib import import_module
    from django.conf import settings

    for plugin in getattr(settings, "PLUGINS", ()):
        import_module(plugin)
