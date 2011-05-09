#-----------------------------------------------------------------------
# $Id$
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

import os.path
from threading import RLock
import logging

from eoxserver.core.config import Config
from eoxserver.core.exceptions import (InternalError,
    ImplementationNotFound, ImplementationAmbiguous,
    ImplementationDisabled, BindingMethodError
)
from eoxserver.core.interfaces import *
from eoxserver.core.util.filetools import findFiles, pathToModuleName

class Registry(object):
    def __init__(self, config):
        self.config = config

        self.__intf_index = {}
        self.__impl_index = {}
        self.__kvp_index = {}
        self.__res_index = {}
    
    def bind(self, impl_id, include_disabled=False):
        if impl_id in self.__impl_index:
            if self.__impl_index[impl_id]["enabled"]:
                return self.__impl_index[impl_id]["cls"]()
            else:
                raise ImplementationDisabled("")
        else:
            raise ImplementationNotFound("")
    
    def getResource(self, factory_id, params):
        factory = self.bind(factory_id)
        
        return factory.get(**params)
    
    def findAndBind(self, intf_id, params, include_disabled=False):
        if intf_id in self.__intf_index:
            InterfaceCls = self.__intf_index[intf_id]["intf"]
            if InterfaceCls.getBindingMethod() == "kvp":
                ImplementationCls = self.__find_by_values(
                    InterfaceCls, params, include_disabled
                )
            elif InterfaceCls.getBindingMethod() == "testing":
                ImplementationCls = self.__find_by_test(
                    self.__intf_index[intf_id]["impls"],
                    params,
                    include_disabled
                )
            elif InterfaceCls.getBindingMethod() == "factory":
                raise BindingMethodError("Cannot bind directly to '%s' implementations. Use getResource() instead.")
            
            return ImplementationCls()
        else:
            raise InternalError("Unknown interface ID '%s'" % intf_id)

    def findImplementations(self, intf_id, params=None, include_disabled=False):
        if intf_id in self.__intf_index:
            InterfaceCls = self.__intf_index[intf_id]["intf"]
            if params is not None:
                _params = params
            else:
                _params = {}
            
            if InterfaceCls.getBindingMethod() == "kvp":
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
        impls = self.findImplementations(intf_id, params, include_disabled)
        
        return [impl.__get_impl_id__() for impl in impls]
    
    def getRegistryValues(self, intf_id, registry_key, include_disabled=False):
        if intf_id in self.__intf_index:
            InterfaceCls = self.__intf_index[intf_id]["intf"]
            if InterfaceCls.getBindingMethod() == "kvp":
                if registry_key not in InterfaceCls.getRegistryKeys():
                    raise InternalError("Interface '%s' has no registry key '%s'" % (
                        intf_id, registry_key
                    ))
                    
                else:
                    entries = self.__intf_index[intf_id]["impls"]
                    
                    if not include_disabled:
                        entries = filter(lambda entry: entry["enabled"], entries)
                    
                    return [entry["cls"].__get_kvps__()[registry_key] for entry in entries]
            else:
                raise InternalError("Binding method of interface '%s' is '%s', not 'kvp'." % (
                    intf_id,
                    InterfaceCls.getBindingMethod()
                ))
        else:
            raise InternalError("Unknown interface ID '%s'" % intf_id)

    def load(cls):
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
            modules.extend(cls.__find_modules(module_dir))
        
        # load modules; implementations will auto-register
        for module_name in system_modules:
            cls.__load_module(module_name, strict=True)
        
        for module_name in modules:
            cls.__load_module(module_name)
            
        self.__synchronize()
        
        self.validate()
    
    def validate(self):
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
        self.validate()

        self.__save_to_db()
    
    def getImplementationStatus(self, impl_id):
        if impl_id in self.__impl_index:
            return self.__impl_index[impl_id]["enabled"]
        else:
            raise InternalError("Unknown implementation ID '%s'" % impl_id)
    
    def enableImplementation(self, impl_id):
        if impl_id in self.__impl_index:
            self.__impl_index[impl_id]["enabled"] = True
        else:
            raise InternalError("Unknown implementation ID '%s'" % impl_id)

    def disableImplementation(self, impl_id):
        if impl_id in self.__impl_index:
            self.__impl_index[impl_id]["enabled"] = False
        else:
            raise InternalError("Unknown implementation ID '%s'" % impl_id)
    
    def clone(self):
        registry = Registry(self.config)
        
        registry.__impl_index = self.__impl_index
        registry.__intf_index = self.__intf_index
        registry.__kvp_index = self.__kvp_index
        
        return registry

    def __synchronize(self):
        qs = self.__get_from_db()
        
        self.__save_diff_to_db(qs)
    
    def __get_from_db(self):
        qs = Component.objects.all()
        
        for comp in qs:
            if comp.impl_id in self.__impl_index:
                self.__impl_index[comp.impl_id]["enabled"] = comp.enabled
        
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
            db_impl_ids = qs.values("impl_id")
        else:
            db_impl_ids = Component.objects.all().values("impl_id")
        
        for impl_id in self.__impl_index.keys():
            if impl_id not db_impl_ids:
                Component.objects.create(
                    impl_id=impl_id,
                    intf_id=self.__impl_index[impl_id]["cls"].__get_intf_id__(),
                    enabled=self.__impl_index[impl_id]["enabled"]
                )

    def __find_by_values(self, InterfaceCls, kvp_dict, include_disabled=False):
        key = self.__make_kvp_index_key(
            InterfaceCls.getInterfaceId(),
            InterfaceCls.getRegistryKeys(),
            params
        )
        entry = cls.__kvp_index.get(key)
        
        if entry:
            if entry["enabled"] or include_disabled:
                return entry["cls"]
            else:
                raise ImplementationDisabled("Implementation '%s' is disabled"n % entry["impl_id"])
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
            raise ImplementationNotFound
        elif len(impls) == 1:
            return impls[0]
        else:
            raise ImplementationAmbiguous
    
    def __find_all_by_test(self, entries, test_params, include_disabled=False):
        impls = []
        
        for entry in entries:
            if entry["enabled"] or include_disabled:
                if entry["cls"].test(test_params):
                    impls.append(entry["cls"])
        
        return impls

    def __register(self, ImplementationCls):
        # update interface index
        self.__add_to_intf_index(ImplementationCls)
        
        # update implementation index
        self.__add_to_impl_index(ImplementationCls)
        
        # update KVP index
        self.__add_to_kvp_index(ImplementationCls)

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
                    self.__impl_index[impl_id].__module__,
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
                        self.__kvp_index[key].__get_impl_id__(),
                        self.__kvp_index[key].__module__
                    ))
                    
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
            #module = __import__(module_name, globals(), locals(), [])
            f, path, desc = imp.find_module(module_name)
            module = imp.load_module(module_name, f, path, desc)
            
        except:
            if strict:
                raise InternalError("Could not load required module '%s'." % module_name)
            else:
                # NOTE: a check for consistency will be applied later
                # on; if an enabled component is missing, an exception
                # will be raised by the final validation routine
                logging.warning("Could not load module '%s'" % module_name)
                return
        finally:
            if f:
                f.close()
        
        for attr in module.__dict__.values():
            if hasattr(attr, "__ifclass__") and\
               hasattr(attr, "__rconf__") and\
               hasattr(attr, "__get_intf_id__") and\
               hasattr(attr, "__get_impl_id__") and\
               hasattr(attr, "__get_kvps__"):
                self.__register(attr)

class RegisteredInterfaceMetaClass(InterfaceMetaClass):    
    def __new__(mcls, name, bases, class_dict):
        if "REGISTRY_CONF" in class_dict:
            local_conf = class_dict["REGISTRY_CONF"]
        else:
            raise InternalError("Every interface needs a 'REGISTRY_CONF' dictionary.")
        
        mcls._validateLocalRegistryConf(local_conf)
        
        conf = mcls._mergeConfs(local_conf, bases, "__rconf__")
        
        mcls._validateRegistryconf(conf)
        
        class_dict["__rconf__"] = conf

        return InterfaceMetaClass.__new__(mcls, name, bases, class_dict)
    
    @classmethod
    def _validateLocalRegistryConf(mcls, local_conf):
        if "name" not in local_conf:
            raise InternalError("Missing 'name' parameter in interface configuration dictionary.")
        
        if "intf_id" not in local_conf:
            raise InternalError("Missing 'intf_id' parameter in interface configuration dictionary."
            
    
    @classmethod
    def _validateRegistryConf(mcls, conf):
        pass

class RegisteredInterface(Interface):
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
            raise InternalError("Missing 'REGISTRY_CONF' configuration dictionary in implementing class.")
        
        InterfaceCls._validateImplementationConf(conf)

        intf_id = InterfaceCls.getInterfaceId()
        impl_id = conf["impl_id"]
        kvps = conf.get("registry_values")

        class_dict.update({
            "__rconf__": conf,
            "__get_intf_id__": classmethod(lambda cls: intf_id),
            "__get_impl_id__": classmethod(lambda cls: impl_id),
            "__get_kvps__": classmethod(lambda cls: kvps)
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
            
            if set(conf["registry_values"].keys()) != set(InterfaceCls.getRegistryKeys()):
                raise InternalError("Registry keys in implementation configuration dictionary do not match interface definition")

    @classmethod
    def getInterfaceId(cls):
        return cls.__rconf__["intf_id"]
    
    @classmethod
    def getBindingMethod(cls):
        return cls.__rconf__["binding_method"]
    
    @classmethod
    def getRegistryKeys(cls):
        return cls.__rconf__.get("registry_keys")

class TestingInterface(RegisteredInterface):
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
    REGISTRY_CONF = {
        "name": "Registered Factory Interface",
        "intf_id": "core.registry.Factory"
    }

    get = Method(
        PosArgs("args"),
        KwArgs("kwargs"),
        returns=Arg("@return")
    )
    
    find = Method(
        PosArgs("args"),
        KwArgs("kwargs"),
        returns=ListArg("@return")
    )
    
class ComponentManagerInterface(RegisteredInterface):
    REGISTRY_CONF = {
        "name": "Component Manager Interface",
        "intf_id": "core.registry.ComponentManager"
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

class RegistryConfigReader(object):
    def __init__(self, config):
        self.config = config
        
    def validate(self):
        pass

    def getSystemModules(self):
        sys_mod_str = self.config.getDefaultConfigValue("core.registry", "system_modules")
        
        return [name.strip() for name in sys_mod_str.split(",")]
    
    @classmethod
    def getModuleDirectories(self):
        mod_dir_str = self.config.getConfigValue("core.registry", "module_dirs")
        
        return [dir.strip() for dir in mod_dir_str.split(",")]
    
    @classmethod
    def getModules(self):
        mod_str = self.config.getConfigValue("core.registry", "modules")
        
        return [name.strip() for name in mod_str.split(",")]
        
