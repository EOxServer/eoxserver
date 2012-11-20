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
This module contains the implementation of the registry as well as associated
interface declarations. The registry is the core component of EOxServer that
links different parts of the system together. The registry allows for
components to bind to implementations of registered interfaces. It supports
modularity, extensibility and flexibility of EOxServer.
"""

import imp
import os.path
from inspect import isclass

from django.conf import settings

from eoxserver.core.models import Component
from eoxserver.core.exceptions import (InternalError, ConfigError,
    ImplementationNotFound, ImplementationAmbiguous,
    ImplementationDisabled, BindingMethodError
)
from eoxserver.core.interfaces import *
from eoxserver.core.util.filetools import findFiles, pathToModuleName

class Registry(object):
    """
    The :class:`Registry` class implements the functionalities for detecting,
    registering, finding and binding to implementations of registered
    interfaces. It is instantiated by :class:`eoxserver.core.system.System`
    during the startup process.
    
    The constructor expects a :class:`~.Config` instance as input. The values
    will be validate and read using a :class:`RegistryConfigReader` instance.
    """
    
    def __init__(self, config):
        self.config = config

        self.__intf_index = {}
        self.__impl_index = {}
        self.__kvp_index = {}
        self.__fact_index = {}
    
    def bind(self, impl_id):
        """
        Bind to the implementation with ID ``impl_id``. This method returns
        a new instance of the requested implementation if it is enabled.
        
        If the implementation is disabled :exc:`~.ImplementationDisabled` will
        be raised. If the ID ``impl_id`` is not known to the registry
        :exc:`ImplementationNotFound` will be raised.
        """
        
        if impl_id in self.__impl_index:
            if self.__impl_index[impl_id]["enabled"]:
                return self.__impl_index[impl_id]["cls"]()
            else:
                raise ImplementationDisabled(
                    "Implementation '%s' is disabled." % impl_id
                )
        else:
            raise ImplementationNotFound(impl_id)
    
    def getFromFactory(self, factory_id, params):
        """
        Get an implementation instance from the factory with ID ``factory_id``
        using the parameter dictionary ``params``. This is a shortcut which
        binds to the factory and calls its :meth:`~FactoryInterface.get` method
        then.
        
        :exc:`~.InternalError` will be raised if required arguments are missing
        in the ``params`` dictionary. :exc:`~.ImplementationDisabled` will be
        raised if either the factory or the appropriate implementation are
        disabled. :exc:`~.ImplementationNotFound` will be raised if either
        the factory or the appropriate implementation are unknown to the
        registry.
        """
        
        factory = self.bind(factory_id)
        
        return factory.get(**params)
    
    def findAndBind(self, intf_id, params):
        """
        This method finds implementations based of a registered interface
        with ID ``intf_id`` using the parameter dictionary ``params`` and
        returns an instance of the matching implementation. This
        works only for the ``kvp`` and ``testing`` binding methods, in other
        cases :exc:`~.BindingMethodError` will be raised.
        
        If the binding method of the interface is ``kvp`` the ``params``
        dictionary must map the registry keys defined in the interface
        declaration to values. The KVP combination will be compared with the
        values given in the respective implementations. If a matching
        implementation is found an instance will be returned, otherwise
        :exc:`~.ImplementationNotFound` is raised. If the class found is
        disabled :exc:`~.ImplementationDisabled` is raised.
        
        If the binding method of the interface is ``testing`` the ``params``
        dictionary will be passed to the :meth:`~TestingInterface.test` method
        of the respective implementations. If no implementation matches
        :exc:`~.ImplementationNotFound` will be raised. If more than one are
        found :exc:`~.ImplementationAmbiguous` will be raised.
        """
        
        if intf_id in self.__intf_index:
            InterfaceCls = self.__intf_index[intf_id]["intf"]
            if InterfaceCls.getBindingMethod() == "direct":
                raise BindingMethodError("You have to bind directly to implementations of '%s'" % intf_id)
            elif InterfaceCls.getBindingMethod() == "kvp":
                ImplementationCls = self.__find_by_values(
                    InterfaceCls, params
                )
            elif InterfaceCls.getBindingMethod() == "testing":
                ImplementationCls = self.__find_by_test(
                    self.__intf_index[intf_id]["impls"],
                    params
                )
            elif InterfaceCls.getBindingMethod() == "factory":
                raise BindingMethodError("The registry cannot generate '%s' implementations. Use getFromFactory() instead." % intf_id)
            
            return ImplementationCls()
        else:
            raise InternalError("Unknown interface ID '%s'" % intf_id)

    def findImplementations(self, intf_id, params=None, include_disabled=False):
        """
        This method returns a list of implementations of a given interface.
        It requires the interface ID as a parameter.
        
        Furthermore, a parameter dictionary can be passed to the method. The
        results will then be filtered according to these parameters. The
        dictionary does not have to contain all the parameters defined by the
        interface; in case some parameters are omitted, the result list may
        contain several different implementations.
        
        Third is an optional ``include_disabled`` parameter with defaults to
        ``False``. If ``True``, disabled implementations will be reported as
        well.
        
        An :exc:`~.InternalError` is raised if parameters are passed to the
        method that are not defined in the interface declaration or not
        recognized by the interface :meth:`test` method.
        """
        
        if intf_id in self.__intf_index:
            InterfaceCls = self.__intf_index[intf_id]["intf"]
            if params is not None:
                _params = params
            else:
                _params = {}
            
            if InterfaceCls.getBindingMethod() == "direct" or \
               InterfaceCls.getBindingMethod() == "factory":
                impls = self.__find_all_impls(
                    self.__intf_index[intf_id]["impls"],
                    include_disabled
                )
            elif InterfaceCls.getBindingMethod() == "kvp":
                impls = self.__find_all_by_values(
                    self.__intf_index[intf_id]["impls"],
                    _params,
                    include_disabled
                )
            elif InterfaceCls.getBindingMethod() == "testing":
                impls = self.__find_all_by_test(
                    self.__intf_index[intf_id]["impls"],
                    _params,
                    include_disabled
                )
            
            return impls
        else:
            raise InternalError("Unknown interface ID '%s'" % intf_id)

    def getImplementationIds(self, intf_id, params=None, include_disabled=False):
        """
        This method returns a list of implementation IDs for a given interface.
        It requires the interface ID as a parameter.
        
        Furthermore, a parameter dictionary can be passed to the method. The
        results will then be filtered according to these parameters. The
        dictionary does not have to contain all the parameters defined by the
        interface; in case some parameters are omitted, the result list may
        contain several different implementations.
        
        Third is an optional ``include_disabled`` parameter with defaults to
        ``False``. If ``True``, disabled implementations will be reported as
        well.
        
        An :exc:`~.InternalError` is raised if parameters are passed to the
        method that are not defined in the interface declaration or not
        recognized by the interface :meth:`test` method.
        """
        impls = self.findImplementations(intf_id, params, include_disabled)
        
        return [impl.__get_impl_id__() for impl in impls]
    
    def getRegistryValues(self, intf_id, registry_key, filter=None, include_disabled=False):
        """
        This method returns a list of registry values of implementations 
        of an interface with ``interface_id`` and a registry key
        ``registry_key`` defined in the interface declaration.
        
        With the ``filter`` argument you can impose certain restrictions on the
        implementations (registry values) to be returned. It is expected to
        contain a dictionary of registry keys and values that the implementation
        must expose to be included.
        
        Using the ``include_disabled`` argument you can determine whether.
        
        This method raises :exc:`~.InternalError` if the interface ID is
        unknown.
        """
        if intf_id in self.__intf_index:
            InterfaceCls = self.__intf_index[intf_id]["intf"]
            
            if InterfaceCls.getBindingMethod() == "kvp":
                if registry_key not in InterfaceCls.getRegistryKeys():
                    raise InternalError("Interface '%s' has no registry key '%s'" % (
                        intf_id, registry_key
                    ))
                    
                else:
                    if filter:
                        _filter = filter
                    else:
                        _filter = {}
                    
                    impls = self.__find_all_by_values(
                        self.__intf_index[intf_id]["impls"],
                        _filter
                    )
                    
                    return [impl.__get_kvps__()[registry_key] for impl in impls]
            else:
                raise InternalError("Binding method of interface '%s' is '%s', not 'kvp'." % (
                    intf_id,
                    InterfaceCls.getBindingMethod()
                ))
        else:
            raise InternalError("Unknown interface ID '%s'" % intf_id)
        
    def getFactoryImplementations(self, factory):
        """
        Returns a list of implementations for a given factory.
        
        Raises :exc:`~.InternalError` if the factory is not found in the
        registry.
        """
        factory_id = factory.__get_impl_id__()
        
        if factory_id in self.__fact_index:
            return [entry["cls"] for entry in self.__fact_index[factory_id]]
        else:
            raise InternalError("Unknown Factory ID '%s'." % factory_id)

    def load(self):
        """
        This method loads the registry, i.e. it scans the modules specified
        in the configuration for interfaces and implementations. It is
        invoked by the ``~.System`` class upon initialization.

        You should *never* invoke this method directly. Always use
        :meth:`~.System.init` to initialize and :meth:`~.System.getRegistry` to
        access the registry.
        
        There are three configuration settings taken into account.
        
        First, the ``system_modules`` setting in ``default.conf``. These
        modules are always loaded and cannot be left aside in individual
        instances.
        
        Second, the ``module_dirs`` setting in the local configuration of the
        instance (``eoxserver.conf``) is taken into account. This expected to
        be a comma-separated list of directories. These directories and all
        the directory trees underneath them are searched for Python modules.
        
        Third, the ``modules`` setting in ``eoxserver.conf``. This is
        expecte to be a comma-separated list of module names which shall be
        loaded.
        
        All modules specified or detected by scanning directories will be
        loaded and searched for interfaces descending from
        :class:`RegisteredInterface` as well as their implementations. These
        will be automatically included in the registry and accessible using
        the different binding methods provided.
        
        As a last step, the registry is synchronized with the database. This
        means that the implementation looks up the entries for the different
        implementations in the database and determines whether they are
        enabled or not. If it finds an implementation which has not yet been
        registered it will be saved to the database but disabled by default.
        """
        # get module directories from config
        reader = RegistryConfigReader(self.config)
        reader.validate()
        
        system_modules = reader.getSystemModules()
        module_dirs = reader.getModuleDirectories()
        modules = reader.getModules()
        
        # find modules
        for module_dir in module_dirs:
            # find .py files
            # and append them to the modules list
            modules.extend(self.__find_modules(module_dir))
        
        # load modules
        for module_name in system_modules:
            self.__load_module(module_name, strict=True)
        
        for module_name in modules:
            self.__load_module(module_name)
            
        self.__synchronize()
        
        self.validate()
    
    def validate(self):
        """
        This method is intended to validate the component configuration.
        
        It looks up all implementations of :class:`ComponentManagerInterface`
        and calls their respective :meth:`~ComponentManagerInterface.validate`
        methods.
        
        At the moment, no component managers are implemented, so this
        method does not have any effects.
        """
        msgs = []
        
        Managers = self.findImplementations("core.registry.ComponentManager")

        for Manager in Managers:
            manager = Manager()
            try:
                manager.validate(self)
            except ConfigError, e:
                msgs.append(str(e))
        
        if len(msgs) > 0:
            raise ConfigError("\n".join(msgs))
    
    def save(self):
        """
        This saves the registry configuration to the database. This means
        the status of the enabled / disabled flag for each implementation
        will be saved overriding any previous settings stored.
        """
        self.validate()

        self.__save_to_db()
    
    def getImplementationStatus(self, impl_id):
        """
        Returns the implementation status (``True`` for enabled, ``False`` for
        disabled) for the given implementation ID ``impl_id``.
        
        Raises :exc:`~.InternalError` if the implementation ID is
        unknown.
        """
        if impl_id in self.__impl_index:
            return self.__impl_index[impl_id]["enabled"]
        else:
            raise InternalError("Unknown implementation ID '%s'" % impl_id)
    
    def enableImplementation(self, impl_id):
        """
        Changes the implementation status to enabled for implementation ID
        ``impl_id``. Note that this change is not automatically stored to
        the database (you have to call :meth:`save` to do that).
        
        Raises :exc:`~.InternalError` if the implementation ID is unknown.
        """
        if impl_id in self.__impl_index:
            self.__impl_index[impl_id]["enabled"] = True
        else:
            raise InternalError("Unknown implementation ID '%s'" % impl_id)

    def disableImplementation(self, impl_id):
        """
        Changed the implementation status to disable for implementation ID
        ``impl_id``. Note that this change is not automatically stored to
        the database (you have to call :meth:`save` to do that).
        
        Raises :exc:`~.InternalError` if the implementation ID is unknown.
        """
        if impl_id in self.__impl_index:
            self.__impl_index[impl_id]["enabled"] = False
        else:
            raise InternalError("Unknown implementation ID '%s'" % impl_id)
    
    def clone(self):
        """
        Returns an exact copy of the registry.
        """
        
        registry = Registry(self.config)
        
        registry.__impl_index = self.__impl_index
        registry.__intf_index = self.__intf_index
        registry.__kvp_index = self.__kvp_index
        registry.__fact_index = self.__fact_index
        
        return registry

    def __synchronize(self):
        qs = self.__get_from_db()
        
        for impl_id, entry in self.__impl_index.items():
            if entry["enabled"]:
                logging.debug("%s: enabled" % impl_id)
            else:
                logging.debug("%s: disabled" % impl_id)
        
        self.__save_diff_to_db(qs)
    
    def __get_from_db(self):
        qs = Component.objects.all()
        
        for comp in qs:
            if comp.impl_id in self.__impl_index:
                
                # TODO: at the moment, the 'enabled' property is stored
                # in each index seperately. Make the indices point to
                # the same entry, so 'enabled' does not need to be set
                # three times (once for each index)
                self.__impl_index[comp.impl_id]["enabled"] = comp.enabled
                
                intf_id = self.__impl_index[comp.impl_id]["cls"].__get_intf_id__()
                entries = self.__intf_index[intf_id]["impls"]
                for entry in entries:
                    if entry["impl_id"] == comp.impl_id:
                        entry["enabled"] = comp.enabled
                
                if self.__intf_index[intf_id]["intf"].getBindingMethod() == "kvp":
                    key = self.__make_kvp_index_key(
                        intf_id,
                        self.__intf_index[intf_id]["intf"].getRegistryKeys(),
                        self.__impl_index[comp.impl_id]["cls"].__get_kvps__()
                    )
                    self.__kvp_index[key]["enabled"] = comp.enabled
        
        return qs
    
    def __save_to_db(self, qs=None):
        if qs:
            _qs = qs
        else:
            _qs = Component.objects.all()
        
        for comp in qs:
            if comp.impl_id in self.__impl_index and\
               comp.enabled != self.__impl_index[comp.impl_id]["enabled"]:
                comp.enabled = self.__impl_index[comp.impl_id]["enabled"]
                comp.save()
        
        self.__save_diff_to_db(_qs)
    
    def __save_diff_to_db(self, qs=None):
        if qs is not None:
            db_impl_ids = qs.values_list("impl_id", flat=True)
        else:
            db_impl_ids = Component.objects.all().values_list("impl_id", flat=True)
        
        for impl_id in self.__impl_index.keys():
            if impl_id not in db_impl_ids:
                Component.objects.create(
                    impl_id=impl_id,
                    intf_id=self.__impl_index[impl_id]["cls"].__get_intf_id__(),
                    enabled=self.__impl_index[impl_id]["enabled"]
                )

    def __find_all_impls(self, entries, include_disabled=False):
        if include_disabled:
            return [entry["cls"] for entry in entries]
        else:
            return [entry["cls"] for entry in filter(
                lambda entry: entry["enabled"], entries
            )]

    def __find_by_values(self, InterfaceCls, kvp_dict, include_disabled=False):
        key = self.__make_kvp_index_key(
            InterfaceCls.getInterfaceId(),
            InterfaceCls.getRegistryKeys(),
            kvp_dict
        )
        entry = self.__kvp_index.get(key)
        
        if entry:
            if entry["enabled"] or include_disabled:
                return entry["cls"]
            else:
                raise ImplementationDisabled("Implementation '%s' is disabled." % entry["impl_id"])
        else:
            raise ImplementationNotFound(
                "No implementation found for interface '%s' and parameters: '%s'" % (
                    InterfaceCls.getInterfaceId(),
                    str(kvp_dict)
                ))
    
    def __find_all_by_values(self, entries, kvp_dict, include_disabled=False):
        impls = []
        
        for entry in entries:
            if entry["enabled"] or include_disabled:
                impl_dict = entry["cls"].__get_kvps__()
                matches = True
                
                for key, value in kvp_dict.items():
                    if key in impl_dict:
                        if value != impl_dict[key]:
                            matches = False
                            break
                    else:
                        raise InternalError("Key '%s' not found in registry values of implementation '%s'" % (
                            key, entry["impl_id"]
                        ))
                
                if matches:
                    impls.append(entry["cls"])
        
        return impls
    
    def __find_by_test(self, entries, test_params, include_disabled=False):
        impls = self.__find_all_by_test(entries, test_params, include_disabled)
        
        if len(impls) == 0:
            raise ImplementationNotFound("")
        elif len(impls) == 1:
            return impls[0]
        else:
            raise ImplementationAmbiguous("")
    
    def __find_all_by_test(self, entries, test_params, include_disabled=False):
        impls = []
        
        for entry in entries:
            if entry["enabled"] or include_disabled:
                if entry["cls"]().test(test_params):
                    impls.append(entry["cls"])
        
        return impls

    def __register_implementation(self, ImplementationCls):
        # update interface index
        self.__add_to_intf_index(ImplementationCls)
        
        # update implementation index
        self.__add_to_impl_index(ImplementationCls)
        
        # update KVP index
        self.__add_to_kvp_index(ImplementationCls)
        
        # update factory index
        self.__add_to_fact_index(ImplementationCls)
    
    def __register_interface(self, InterfaceCls):
        logging.debug("Registry.__register_interface(): intf_id: %s" % InterfaceCls.getInterfaceId())
        
        intf_id = InterfaceCls.getInterfaceId()
        
        if intf_id in self.__intf_index:
            if InterfaceCls is not self.__intf_index[intf_id]["intf"]:
                raise InternalError("Duplicate interface ID '%s' for '%s' in module '%s' and '%s' in module '%s'" % (
                    intf_id,
                    InterfaceCls.__name__,
                    InterfaceCls.__module__,
                    self.__intf_index[intf_id]["intf"].__name__,
                    self.__intf_index[intf_id]["intf"].__module__
                ))
        else:
            self.__intf_index[intf_id] = {
                "intf": InterfaceCls,
                "impls": []
            }

    def __add_to_intf_index(self, ImplementationCls):
        intf_id = ImplementationCls.__get_intf_id__()
        impl_id = ImplementationCls.__get_impl_id__()
        
        if intf_id in self.__intf_index:
            if self.__intf_index[intf_id]["intf"] is ImplementationCls.__ifclass__:
                self.__intf_index[intf_id]["impls"].append(
                    self.__get_index_entry(ImplementationCls)
                )
            else:
                raise InternalError("Duplicate Interface ID '%s' for '%s' in '%s' and '%s' in '%s'." % (
                    intf_id,
                    ImplementationCls.__ifclass__.__name__,
                    ImplementationCls.__ifclass__.__module__,
                    self.__intf_index[intf_id]["intf"].__name__,
                    self.__intf_index[intf_id]["intf"].__module__
                ))
        else:
            self.__intf_index[intf_id] =  {
                "intf": ImplementationCls.__ifclass__,
                "impls": [self.__get_index_entry(ImplementationCls)]
            }

    def __add_to_impl_index(self, ImplementationCls):
        intf_id = ImplementationCls.__get_intf_id__()
        impl_id = ImplementationCls.__get_impl_id__()
        
        if impl_id in self.__impl_index:
            if self.__impl_index[impl_id] is not ImplementationCls:
                raise InternalError("Duplicate implementation id '%s' defined in modules '%s' and '%s'" % (
                    impl_id,
                    self.__impl_index[impl_id]["cls"].__module__,
                    ImplementationCls.__module__
                ))
        else:
            self.__impl_index[impl_id] = self.__get_index_entry(ImplementationCls)
    
    def __add_to_kvp_index(self, ImplementationCls):

        intf_id = ImplementationCls.__get_intf_id__()
        impl_id = ImplementationCls.__get_impl_id__()
        
        if ImplementationCls.__ifclass__.getBindingMethod() == "kvp":
            key = self.__make_kvp_index_key(
                intf_id,
                ImplementationCls.__ifclass__.getRegistryKeys(),
                ImplementationCls.__get_kvps__()
            )
            if key not in self.__kvp_index:
                self.__kvp_index[key] = self.__get_index_entry(ImplementationCls)
            else:
                if self.__kvp_index[key] is not ImplementationCls:
                    # TODO: conflict resolution mechanisms
                    raise InternalError("Conflicting implementations for Interface '%s': Same KVP values for '%s' in '%s' and '%s' in '%s'" % (
                        intf_id,
                        impl_id,
                        ImplementationCls.__module__,
                        self.__kvp_index[key]["cls"].__get_impl_id__(),
                        self.__kvp_index[key]["cls"].__module__
                    ))
    
    def __add_to_fact_index(self, ImplementationCls):
        if ImplementationCls.__ifclass__.getBindingMethod() == "factory":

            
            for factory_id in ImplementationCls.__get_factory_ids__():
                logging.debug("Registry.__add_to_fact_index(): adding '%s' to '%s'" % (
                    ImplementationCls.__get_impl_id__(),
                    factory_id
                ))
                
                if factory_id in self.__fact_index:
                    self.__fact_index[factory_id].append(
                        self.__get_index_entry(ImplementationCls)
                    )
                else:
                    self.__fact_index[factory_id] = [
                        self.__get_index_entry(ImplementationCls)
                    ]
    
    def __get_index_entry(self, ImplementationCls, enabled=False):
        return {
            "cls": ImplementationCls,
            "impl_id": ImplementationCls.__get_impl_id__(),
            "enabled": enabled
        }

    def __make_kvp_index_key(self, intf_id, registry_keys, kvp_dict):
        key_list = [intf_id]
        
        if registry_keys is None:
            raise InternalError("Interface '%s' has no registry keys." % intf_id)
        
        for registry_key in registry_keys:
            if registry_key in kvp_dict:
                key_list.append((kvp_dict[registry_key], registry_key))
            else:
                raise InternalError("Missing registry key '%s'." % registry_key)
        
        return tuple(key_list)
        
    def __find_modules(self, dir):
        # check if dir is a subdirectory of the eoxserver or instance
        # directory
        abs_path = os.path.abspath(dir)
        
        if abs_path.startswith(settings.PROJECT_DIR) or \
           abs_path.startswith(self.config.getEOxSPath()):
            module_files = findFiles(abs_path, "*.py")
            
            try:
                return [pathToModuleName(module_file) for module_file in module_files]
            except InternalError, e:
                raise ConfigError(str(e))
        else:
            raise ConfigError("Can search for extending modules and plugins in subdirecories of EOxServer distribution and instance dir only.")
    
    def __load_module(self, module_name, strict=False):
        try:
            # TODO: use imp module here (it reloads modules, which is more close to what we want)
            module = __import__(module_name, globals(), locals(), [])
            
            for sub_module_name in module_name.split(".")[1:]:
                module = getattr(module, sub_module_name)
            #f, path, desc = imp.find_module(module_name)
            #module = imp.load_module(module_name, f, path, desc)
            
        except Exception, e:
            if strict:
                raise InternalError("Could not load required module '%s'. Error was: %s" % (
                    module_name, str(e)
                ))
            else:
                # NOTE: a check for consistency will be applied later
                # on; if an enabled component is missing, an exception
                # will be raised by the final validation routine
                logging.warning("Could not load module '%s'. Error was: %s" % (
                    module_name, str(e)
                ))
                return
                
        for attr in module.__dict__.values():
            if isclass(attr) and issubclass(attr, RegisteredInterface):
                self.__register_interface(attr)
            elif hasattr(attr, "__ifclass__") and\
               hasattr(attr, "__rconf__") and\
               hasattr(attr, "__get_intf_id__") and\
               hasattr(attr, "__get_impl_id__") and\
               hasattr(attr, "__get_kvps__"):
                self.__register_implementation(attr)

class RegisteredInterfaceMetaClass(InterfaceMetaClass):    
    def __new__(cls, name, bases, class_dict):
        if "REGISTRY_CONF" in class_dict:
            local_conf = class_dict["REGISTRY_CONF"]
        else:
            raise InternalError("Every interface needs a 'REGISTRY_CONF' dictionary.")
        
        cls._validateLocalRegistryConf(local_conf)
        
        conf = cls._mergeConfs(local_conf, bases, "__rconf__")
        
        cls._validateRegistryConf(conf)
        
        class_dict["__rconf__"] = conf

        return InterfaceMetaClass.__new__(cls, name, bases, class_dict)
    
    @classmethod
    def _validateLocalRegistryConf(mcls, local_conf):
        if "name" not in local_conf:
            raise InternalError("Missing 'name' parameter in interface configuration dictionary.")
        
        if "intf_id" not in local_conf:
            raise InternalError("Missing 'intf_id' parameter in interface configuration dictionary.")
            
    
    @classmethod
    def _validateRegistryConf(mcls, conf):
        pass

class RegisteredInterface(Interface):
    """
    This class is the base class for all interfaces to be registered in the
    registry. All interfaces whose implementations shall be registered must
    be derived from :class:`RegisteredInterface`.
    
    All interfaces derived from :class:`RegisteredInterface` must contain a
    ``REGISTRY_CONF`` dictionary. See the introduction for details.
    """
    
    __metaclass__ = RegisteredInterfaceMetaClass

    REGISTRY_CONF = {
        "name": "Abstract Registered Interface base class",
        "intf_id": "core.registy.Registered",
        "binding_method": "kvp"
    }
    
    @classmethod
    def _getClassDict(InterfaceCls, ImplementationCls, bases):
        class_dict = super(RegisteredInterface, InterfaceCls)._getClassDict(ImplementationCls, bases)
        
        if hasattr(ImplementationCls, "REGISTRY_CONF"):
            conf = ImplementationCls.REGISTRY_CONF
        else:
            raise InternalError("Missing 'REGISTRY_CONF' configuration dictionary in implementing class '%s'." % ImplementationCls.__name__)
        
        InterfaceCls._validateImplementationConf(conf)

        intf_id = InterfaceCls.getInterfaceId()
        impl_id = conf["impl_id"]
        kvps = conf.get("registry_values")
        factory_ids = conf.get("factory_ids", ())

        class_dict.update({
            "__rconf__": conf,
            "__get_intf_id__": classmethod(lambda cls: intf_id),
            "__get_impl_id__": classmethod(lambda cls: impl_id),
            "__get_kvps__": classmethod(lambda cls: kvps),
            "__get_factory_ids__": classmethod(lambda cls: factory_ids)
        })
        
        return class_dict
    
    @classmethod
    def _validateImplementationConf(InterfaceCls, conf):
        if "name" not in conf:
            raise InternalError("Missing 'name' parameter in implementation configuration dictionary.")
        
        if "impl_id" not in conf:
            raise InternalError("Missing 'impl_id' parameter in implementation configuration dictionary.")
        
        if InterfaceCls.getBindingMethod() == "kvp":
            if "registry_values" not in conf:
                raise InternalError("Missing 'registry_values' parameter in implementation configuration dictionary.")
            
            if not InterfaceCls._keysMatch(conf["registry_values"].keys(), InterfaceCls.getRegistryKeys()):
                raise InternalError("Registry keys in implementation configuration dictionary for '%s' do not match interface definition" % conf["impl_id"])
    
    @classmethod
    def _keysMatch(InterfaceCls, impl_keys, intf_keys):
        return (len(impl_keys) == 0 and len(intf_keys) == 0) or\
               (all(map(lambda key: key in intf_keys, impl_keys)) and \
                all(map(lambda key: key in impl_keys, intf_keys)))

    @classmethod
    def getInterfaceId(cls):
        return cls.__rconf__["intf_id"]
    
    @classmethod
    def getBindingMethod(cls):
        return cls.__rconf__["binding_method"]
    
    @classmethod
    def getRegistryKeys(cls):
        if "registry_keys" in cls.__rconf__:
            return cls.__rconf__["registry_keys"]
        else:
            return []

class TestingInterface(RegisteredInterface):
    """
    This class is a descendant of :class:`RegisteredInterface` that adds
    a single method. It is used for binding by test, which enables binding
    decisions that cannot easily be implemented by key-value-pair comparisons.
    
    .. method:: test(params)
    
       This method is invoked by the registry when determining which
       implementation to bind to. Based on the parameter dictionary ``params``
       the method shall decide whether the implementation is applicable and
       return ``True``. If it is not applicable the method shall return
       ``False``.
    """
    REGISTRY_CONF = {
        "name": "Registered Testing Interface",
        "intf_id": "core.registry.Testing",
        "binding_method": "testing"
    }
    
    test = Method(
        DictArg("params"),
        returns=BoolArg("@return")
    )

class FactoryInterface(RegisteredInterface):
    """
    This is the basic interface for factories. It is a descendant of
    :class:`RegisteredInterface`.
    
    .. method:: get(**kwargs)

       This method shall return an instance of an implementation that matches
       the parameters given as keyword arguments. The set of arguments
       understood depends on the individual factory and can be found in the
       respective documentation.
       
       The method shall raise an exception if no matching implementation or
       instance thereof can be found, or if the choice is ambiguous.
    
    .. method:: find(**kwargs)
    
       This method shall return a list of implementation instances that
       matches the parameters given as keyword arguments. The set of arguments
       understood depends on the individual factory and can be found in the
       respective documentation.
    """
    
    REGISTRY_CONF = {
        "name": "Registered Factory Interface",
        "intf_id": "core.registry.Factory",
        "binding_method": "direct"
    }

    get = Method(
        KwArgs("kwargs"),
        returns=Arg("@return")
    )
    
    find = Method(
        KwArgs("kwargs"),
        returns=ListArg("@return")
    )
    
class ComponentManagerInterface(RegisteredInterface):
    """
    This interface is not in use at the moment. It was intended to provide
    an API for controlling the status of a larger set of implementations and
    their dependencies, though the concept has never been elaborated.
    """
    REGISTRY_CONF = {
        "name": "Component Manager Interface",
        "intf_id": "core.registry.ComponentManager",
        "binding_method": "direct"
    }
    
    getName = Method(
        returns=StringArg("@returns")
    )
    
    getId = Method(
        returns=StringArg("@returns")
    )
    
    enable = Method(
        ObjectArg("registry", arg_class=Registry),
        BoolArg("cascade", default=False)
    )
    
    disable = Method(
        ObjectArg("registry", arg_class=Registry),
        BoolArg("cascade", default=False)
    )
    
    createRelations = Method()
    
    enableRelation = Method(
        StringArg("obj_id")
    )
    
    disableRelation = Method(
        StringArg("obj_id")
    )
    
    notify = Method(
        ObjectArg("resource"),
        StringArg("event")
    )

class RegistryConfigReader(object):
    """
    This class provides some functions for reading configuration settings used
    by the :class:`Registry`. 
    """
    def __init__(self, config):
        self.config = config
        
    def validate(self):
        """
        Validates the configuration; a no-op at the moment.
        """
        pass

    def getSystemModules(self):
        """
        This method returns a list of dotted names of system modules. The
        values are read from ``system_modules`` setting in the
        ``[core.registry]`` section of the ``default.conf`` configuration file.
        
        The format of the setting is expected to be a comma-separated list of
        the module names.
        """
        sys_mod_str = self.config.getDefaultConfigValue("core.registry", "system_modules")
        
        if sys_mod_str:
            return [name.strip() for name in sys_mod_str.split(",")]
        else:
            return []
    
    def getModuleDirectories(self):
        """
        This method returns a list of directory paths where to look for
        modules to load (see also :meth:`Registry.load`). The values are read
        from the ``module_dirs`` setting in the ``[core.registry]`` section of
        the instance specific ``eoxserver.conf`` configuration file.
        
        The format of the setting is expected to be a comma-separated list of
        paths.
        """
        mod_dir_str = self.config.getConfigValue("core.registry", "module_dirs")
        
        if mod_dir_str:
            return [dir.strip() for dir in mod_dir_str.split(",")]
        else:
            return []

    def getModules(self):
        """
        This method returs a list of dotted names of modules to be loaded (see
        also :meth:`Registry.load`). The values are read from the ``modules``
        setting in the ``[core.registry]`` section of the instance specific
        ``eoxserver.conf`` configuration file.
        
        The format of the setting is expected to be a comma-separated list of
        dotted module names.
        """
        mod_str = self.config.getConfigValue("core.registry", "modules")
        
        if mod_str:
            return [name.strip() for name in mod_str.split(",")]
        else:
            return []
        
