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

from eoxserver.core.registry import (
    Registry, RegisteredInterface, RegisteredInterfaceMetaClass,
    FactoryInterface
)
from eoxserver.core.models import *

class ResourceInterface(RegisteredInterface):
    REGISTRY_CONF = {
        "name": "Registered Resource Interface",
        "intf_id": "core.registry.Resource",
        "binding_method": "factory"
    }
    
    @classmethod
    def _getClassDict(InterfaceCls, ImplementationCls, bases):
        class_dict = super(ResourceInterface, InterfaceCls)._getClassDict(ImplementationCls, bases)
        
        model_class = conf["model_class"]
        id_field = conf["id_field"]
        
        class_dict.update({
            '__get_model_class__': classmethod(lambda cls: model_class),
            '__get_id_field__': classmethod(lambda cls: id_field)
        })
    
    @classmethod
    def _validateImplementationConf(InterfaceCls, conf):
        super(ResourceInterface, InterfaceCls)._validateImplementationConf()
        
        if "model_class" not in conf:
            raise InternalError("Missing 'model_class' parameter in implementation configuration dictionary")
        
        if "id_field" not in conf:
            raise InternalError("Missing 'id_field' parameter in implementation configuration dictionary")

    # the implementation should check if the model belongs to the
    # correct ResourceClass
    setModel = Method(
        ObjectArg("model", arg_class=Resource)
    )
    
    getId = Method(
        returns=StringArg("@return")
    )
    
    save = Method()

    delete = Method()

class ResourceFactoryInterface(FactoryInterface):
    REGISTRY_CONF = {
        "name": "Resource factory interface",
        "intf_id": "core.resources.ResourceFactoryInterface"
    }
    
    getIds = Method(
        PosArgs("args"),
        KwArgs("kwargs"),
        returns=ListArg("@return")
    )

class CreatingResourceFactoryInterface(ResourceFactoryInterface):
    REGISTRY_CONF = {
        "name": "Resource factory interface also for creating new resources",
        "intf_id": "core.resources.CreatingResourceFactoryInterface"
    }
    
    create = Method(
        PosArgs("args"),
        KwArgs("kwargs"),
        returns=Arg("@return")
    )

class ResourceFactory(object):
    IMPL_CLASSES = []
    
    def get(self, subj_id, *args, **kwargs):
        model = None
        ImplementationCls = None
        
        for Cls in self.IMPL_CLASSES:
            ModelClass = Cls.__get_model_class__()
            
            try:
                new_model = ModelClass.objects.get(*args, **kwargs)
                if model is None:
                    model = new_model
                    ImplementationCls = Cls
                else:
                    if isinstance(new_model, model.__class__):
                        model = new_model
                        ImplementationCls = Cls
                    elif isinstance(model, new_model.__class__):
                        pass
                    else:
                        raise FactoryQueryAmbiguous("")
                        
            except model_class.MultipleObjectsReturned:
                raise FactoryQueryAmbiguous("")
            except:
                pass
        
        if model is not None:
            try:
                rel = model.relations.get(rel_class="rel_get", subj__impl_id=subj_id)
            except Relation.DoesNotExist:
                try:
                    rel = ClassRelation.objects.get(rel_class="rel_get", subj__impl_id=subj_id, obj__impl_id=ImplementationCls.__get_impl_id__())
                except ClassRelation.DoesNotExist:
                    return None
            
            if rel.enabled:
                return self._getResourceImplementation(ImplementationCls, model)
        else:
            return None

    
    def getIds(self, subj_id, *args, **kwargs):
        ids = set()
        
        filter_args = self._getFilterArgs(kwargs)
        
        for ImplementationCls in self._getImplementationClasses(*args, **kwargs):
            models = self._filterModels(subj_id, ImplementationCls, filter_args)
            
            ids.union(set(models.values(ImplementationCls.__get_id_field__())))

        return list(ids)
    
    def find(self, subj_id, *args, **kwargs):
        impl_and_models = []
        
        filter_args = self._getFilterArgs(kwargs)
        
        for ImplementationCls in self._getImplementationClasses(*args, **kwargs):
            models = self._filterModels(subj_id, ImplementationCls, filter_args)
            
            for AnotherImplementationCls, other_models in impl_and_models:
                if issubclass(ImplementationCls.__get_model_class__(), AnotherImplementationCls.__get_model_class__()) and\
                   ImplementationCls.__get_id_field__() == AnotherImplementationCls.__get_id_field__():
                    other_models = other_models.exclude(
                        **{"%s__in" % AnotherImplementationCls.__get_id_field__(): models.values(ImplementationCls.__get_id_field__())}
                    )
                elif issubclass(AnotherImplementationCls.__get_model_class__(), ImplementationCls.__get_model_class__()) and\
                     ImplementationCls.__get_id_field__() == AnotherImplementationCls.__get_id_field__():
                    models = models.exclude(
                        **{"%s__in" % ImplementationCls.__get_id_field__(): other_models.values(AnotherImplementationCls.__get_id_field__())}
                    )
            
            impl_and_models.append((ImplementationCls, models))
        
        resources = []
        
        for ImplementationCls, models in impl_and_models:
            resources.extend(
                [self._getResourceImplementation(ImplementationCls, model) for model in models]
            )
        
        return resources
    
    def _getResourceImplementation(self, ImplementationCls, model):
        res = ImplementationCls()
        res.setModel(model)
        
        return res
    
    def _getImplementationClass(self, *args, **kwargs):
        if len(args) > 0:
            impl_id = args[0]
        elif "impl_id" in kwargs:
            impl_id = kwargs["impl_id"]
        else:
            impl_id = None
        
        if impl_id:
            matching_classes = filter(lambda impl_class : impl_class.__get_impl_id__() == impl_id, self.IMPL_CLASSES)
            if len(matching_classes) == 0:
                raise InternalError("Unknown or incompatible resource class '%s'" % res_class_id)
            elif len(matching_classes) > 1:
                raise InternalError("Ambiguous implementation id '%s'" % res_class_id)
            else:
                return matching_classes[0]
        elif len(self.IMPL_CLASSES) == 1:
            return self.IMPL_CLASSES[0]
        else:
            raise InternalError("Missing 'impl_id' parameter")
    
    def _getImplementationClasses(self, *args, **kwargs):
        if len(args) > 0:
            arg_value = args[0]
        elif "impl_id" in kwargs:
            arg_value = kwargs["impl_id"]
        else:
            return self.IMPL_CLASSES
        
        if isinstance(arg_value, str):
            impl_ids = [arg_value]
        elif isinstance(arg_value, list) or isinstance(arg_value, tuple):
            impl_ids = arg_value
        else:
            raise InternalError("Invalid value for 'impl_id': must be string, list or tuple")

        return filter(lambda Cls: Cls.__get_impl_id__() in impl_ids, self.IMPL_CLASSES)


    
    def _getFilterArgs(self, kwargs):
        filter_args = kwargs.copy()
        
        if "impl_id" in filter_args:
            del filter_args["impl_id"]
        
        return filter_args
    
    def _filterModels(self, subj_id, ImplementationCls, filter_args):
        model_class = ImplementationCls.__get_model_class__()
        models = model_class.objects.filter(**filter_args)
        
        if subj_id != "core.views.Admin":
            try:
                class_rel = ClassRelation.objects.get(
                    rel_class="rel_get",
                    subj__impl_id=subj_id,
                    obj__impl_id=ImplementationCls.__get_impl_id__()
                )
                
                class_enabled = class_rel.enabled
            except ClassRelation.DoesNotExist:
                class_enabled = False
            
            if class_enabled:
                models = models.exclude(
                    relations__subj__impl_id=subj_id,
                    relations__enabled=False
                )
            else:
                models = models.filter(
                     relations__subj__impl_id=subj_id,
                     relations__enabled=True
                )

        return models

class CreatingResourceFactory(ResourceFactory):
    def create(self, subj_id, *args, **kwargs):
        ImplementationCls = self._getImplementationClass(*args, **kwargs)
        
        try:
            rel = ClassRelation.objects.get(
                rel_class="rel_create",
                subj__impl_id=subj_id,
                obj__impl_id=ImplementationCls.__get_impl_id__()
            )
            
            if rel.enabled:
                return self._createResourceImplementation(ImplementationCls, *args, **kwargs)
                
        except ClassRelation.DoesNotExist:
            return None

    def _createResourceImplementation(self, subj_id, ImplementationCls, *args, **kwargs):
        model = ImplementationCls.__get_model_class__().objects.create(
            *args, **kwargs
        )
        
        self._addRelations(subj_id, model)
        
        return self._getResourceImplementation(ImplementationCls, model)

    def _addRelations(self, subj_id, ImplementationCls, model):
        SubjectClass() = Registry.findImplementation(impl_id=subj_id)
        
        if SubjectClass.__has_cap__("cap_get", ImplementationCls.__get_impl_id__())
            model.relations.add(
                rel_class = "rel_get",
                subj = Component.objects.get(impl_id=subj_id)
            )
