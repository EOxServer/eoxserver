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

from eoxserver.core.system import System
from eoxserver.core.registry import (
    RegisteredInterface, FactoryInterface
)
from eoxserver.core.interfaces import *
from eoxserver.core.models import (
    Resource, ClassRelation
)
from eoxserver.core.exceptions import (
    InternalError, UnknownAttribute, FactoryQueryAmbiguous
)

#-----------------------------------------------------------------------
# Interfaces
#-----------------------------------------------------------------------

class ResourceInterface(RegisteredInterface):
    """
    This is the interface for resource wrappers. Resource wrappers add
    application logic to database models based on
    :class:`eoxserver.core.models.Resource`.
    
    :class:`ResourceInterface` expects two additional, mandatory
    parameters in ``REGISTRY_CONF``:
    
    * ``model_class``: the model class for the resources wrapped by the
      implementation
    * ``id_field``: the name of the id field of the implementation
    
    In order to enforce the relation model defined in
    :mod:`eoxserver.core.models` :class:`ResourceInterface`
    implementations shall have two different states: if they are
    mutable, any operations modifying the underlying model are allowed;
    if they are immutable only non-modifying operations are enabled.
    
    .. method:: setModel(model)
       
       This method shall be used to set the resource model, which
       is expected to be an instance of
       :class:`~eoxserver.core.models.Resource` or one of its
       subclasses. An :exc:`~.InternalError` shall be raised if the
       model class does not match the one defined in the ``model_class``
       registry setting.
       
    .. method:: getModel
    
       This method shall return the resource model. In case the resource
       is not mutable :exc:`~.InternalError` shall be raised.
    
    .. method:: createModel(params)
    
       This method shall create a database model with the data given in
       parameter dictionary ``params``. The keys the method understands
       may vary from implementation to implementation; they are the same
       as for :meth:`updateModel`. In case the resource is not mutable
       :exc:`~.InternalError` shall be raised.
    
    .. method:: updateModel(params)
    
       This method shall update the database model with the data given
       in parameter dictionary ``params``. The keys the method
       understands may vary from implementation to implementation; they
       are the same as for :meth:`createModel`. Note that the new data
       is not saved immediately but only when :meth:`saveModel` is
       called. In case the resource is not mutable
       :exc:`~.InternalError` shall be raised.
    
    .. method:: saveModel
    
       This method shall save the model to the database. In case the
       resource is not mutable :exc:`~.InternalError` shall be raised.
    
    .. method:: deleteModel
    
       This method shall delete the model from the database. In case the
       resource is not mutable :exc:`~.InternalError` shall be raised.
    
    .. method:: setMutable(mutable)
    
       This method shall set the mutability status of the resource. The
       optional boolean argument ``mutable`` defaults to ``True``. The
       implementation shall make sure the mutability status cannot be
       overridden once it has been set. In case of an attempt to set it
       a second time :exc:`~.InternalError` shall be raised.
    
    .. method:: getId
    
       This method shall return the ID of the resource, i.e. the
       content of the resource's ``id_field`` field.
       
    .. method:: getAttrNames
    
       This method shall return a list of attribute names for the
       resource. For each attribute name, a call to :meth:`getAttrField`
       reveals the corresponding model field and a call to
       :meth:`getAttrValue` returns the attribute value for the
       resource.
    
    .. method:: getAttrField(attr_name)
    
       This method shall return a the field name for a given attribute
       name.
    
    .. method:: getAttrValue(attr_name)
    
       This method shall return the attribute value for a given
       attribute name.
    
    .. method:: setAttrValue(attr_name, value)
    
       This method shall set the attribute with the given name to the
       given value. In case the resource is not mutable
       :exc:`~.InternalError` shall be raised.
    """
    
    REGISTRY_CONF = {
        "name": "Registered Resource Interface",
        "intf_id": "core.resources.ResourceInterface",
        "binding_method": "factory"
    }
    
    @classmethod
    def _getClassDict(InterfaceCls, ImplementationCls, bases):
        class_dict = super(ResourceInterface, InterfaceCls)._getClassDict(ImplementationCls, bases)

        if hasattr(ImplementationCls, "REGISTRY_CONF"):
            conf = ImplementationCls.REGISTRY_CONF
        else:
            raise InternalError("Missing 'REGISTRY_CONF' configuration dictionary in implementing class.")

        model_class = conf["model_class"]
        id_field = conf["id_field"]
        
        class_dict.update({
            '__get_model_class__': classmethod(lambda cls: model_class),
            '__get_id_field__': classmethod(lambda cls: id_field)
        })
        
        return class_dict
    
    @classmethod
    def _validateImplementationConf(InterfaceCls, conf):
        super(ResourceInterface, InterfaceCls)._validateImplementationConf(conf)
        
        if "model_class" not in conf:
            raise InternalError("Missing 'model_class' parameter in implementation configuration dictionary")
        
        if "id_field" not in conf:
            raise InternalError("Missing 'id_field' parameter in implementation configuration dictionary")
    
    #-------------------------------------------------------------------
    # Interface declaration
    #-------------------------------------------------------------------

    # the implementation should check if the model belongs to the
    # correct ResourceClass
    setModel = Method(
        ObjectArg("model", arg_class=Resource)
    )
    
    getModel = Method(
        returns=ObjectArg("@return", arg_class=Resource, default=None)
    )
    
    createModel = Method(
        DictArg("params")
    )
    
    updateModel = Method(
        DictArg("link_kwargs"),
        DictArg("unlink_kwargs"),
        DictArg("set_kwargs")
    )
    
    saveModel = Method()

    deleteModel = Method()
    
    setMutable = Method(
        BoolArg("mutable", default=True)
    )
    
    getId = Method(
        returns=StringArg("@return")
    )
    
    getAttrNames = Method(
        returns=ListArg("@return", arg_class=str)
    )
    
    getAttrField = Method(
        StringArg("attr_name"),
        returns = StringArg("@return")
    )
    
    getAttrValue = Method(
        StringArg("attr_name"),
        returns=Arg("@return")
    )
    
    setAttrValue = Method(
        StringArg("attr_name"),
        Arg("value")
    )

class ResourceFactoryInterface(FactoryInterface):
    """
    This is the interface for resource factories. It extends
    :class:`~.FactoryInterface` considerably by adding functionality
    to create, update and delete resources.
    
    .. method:: create(**kwargs)
    
       This method shall create a resource according to the given
       parameters and returns it to the caller. The range of applicable
       parameters is defined by each implementation.
    
    .. method:: update(**kwargs)
    
       This method shall update a resource or a set of resources
       according to the given parameters and return the updated
       resources to the caller. The range of applicable parameters is
       defined by each implementation.
       
    .. method:: delete(**kwargs)
    
       This method shall delete a resource or a set of resources
       according to the given parameters. The range of applicable
       parameters is defined by each implementation.
       
    .. method:: getIds(**kwargs)
    
       This method shall return a list of resource IDs (i.e. the
       contents of the resource model's ``id_field`` field, see
       :class:`ResourceInterface`) for the resources given by the
       
    .. method:: getAttrValues(**kwargs)
    
       This method shall return the values of a given attribute for a
       selection of resources.
    
    .. method:: exists(**kwargs)
    
       This method shall return ``True`` if there are resources matching
       the given search criteria, ``False`` otherwise.
    """
    REGISTRY_CONF = {
        "name": "Resource factory interface",
        "intf_id": "core.resources.ResourceFactoryInterface"
    }
    
    create = Method(
        KwArgs("kwargs"),
        returns=Arg("@return")
    )
    
    update = Method(
        KwArgs("kwargs"),
        returns=ListArg("@return")
    )
    
    delete = Method(
        KwArgs("kwargs")
    )
    
    getIds = Method(
        KwArgs("kwargs"),
        returns=ListArg("@return")
    )
    
    getAttrValues = Method(
        KwArgs("kwargs"),
        returns=ListArg("@return")
    )
    
    exists = Method(
        KwArgs("kwargs"),
        returns=BoolArg("@return")    
    )

#-----------------------------------------------------------------------
# Implementations
#-----------------------------------------------------------------------

class ResourceWrapper(object):
    """
    This is the base class for resource wrapper implementations.
    """
    
    # FIELDS = {}
    
    def __init__(self):
        self.__model = None
        self.__mutable = None
    
    def setModel(self, model):
        """
        Use this function to set the coverage model that shall be
        wrapped.
        """
        # NOTE: the class method __get_model_class__ is defined in the
        # implementation only.
        if isinstance(model, self.__class__.__get_model_class__()):
            self.__model = model
        else:
            raise InternalError("Model class mismatch. Expected '%s', got '%s'." % (
                self.__class__.__get_model_class__().__name__,
                model.__class__.__name__
            ))
    
    def getModel(self):
        """
        Returns the model wrapped by this implementation.
        """
        if self.__mutable:
            return self.__model
        else:
            raise InternalError(
                "Cannot access model for immutable resource."
            )

    def createModel(self, params):
        """
        This method shall be used to create models for the concrete
        coverage type.
        """
        
        if self.__mutable:
            create_dict = self._get_create_dict(params)
            self._create_model(create_dict)
            self._post_create(params)
            self.saveModel()
        else:
            raise InternalError(
                "Cannot create model for immutable resource."
            )
    
    def updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        if self.__mutable:
            self._updateModel(link_kwargs, unlink_kwargs, set_kwargs)
            self.saveModel()
        else:
            raise InternalError(
                "Cannot update model for immutable resource."
            )
    
    def saveModel(self):
        """
        Save the coverage model to the database.
        """
        if self.__mutable:
            self.__model.full_clean()
            self.__model.save()
        else:
            raise InternalError(
                "Cannot save model for immutable resource."
            )
        
    def deleteModel(self):
        """
        Delete the coverage model.
        """
        if self.__mutable:
            self.__model.delete()
        else:
            raise InternalError(
                "Cannot delete model for immutable resource."
            )
    
    def getId(self):
        """
        This method shall return the model ID, i.e. the content of
        its ``id_field`` field. Child classes may override it in order
        to implement more efficient data access.
        """
        return getattr(self.__model, self.__class__.__get_id_field__())
        
    def setMutable(self, mutable=True):
        """
        This method sets the mutability status of the resource. It
        accepts one optional boolean argument ``mutable`` which defaults
        to ``True``. The mutability status can be set only once for
        each resource, attempts to change it will cause an
        :exc:`~.InternalError` to be raised.
        """
        if self.__mutable is None:
            self.__mutable = bool(mutable)
        else:
            raise InternalError(
                "Cannot change mutability status of a resource."
            )
    
    def getAttrNames(self):
        """
        Returns a list of names of the accessible attributes of the
        resource.
        """
        return self.__class__.FIELDS.keys()
    
    def getAttrField(self, attr_name):
        """
        Returns the field name for the attribute named ``attr_name``. 
        An :exc:`~.UnknownAttribute` exception is raised if there is
        no attribute with the given name.
        """
        if attr_name in self.__class__.FIELDS:
            return self.__class__.FIELDS[attr_name]
        else:
            raise UnknownAttribute(
                "Unknown attribute '%s' for resource '%s'." % (
                    attr_name,
                    self.__class__.__name__
                )
            )
    
    def getAttrValue(self, attr_name):
        """
        Returns the value of the attribute named ``attr_name``. An
        :exc:`UnknownAttribute` exception is raised in case there is
        no attribute with the given name.
        """
        if attr_name in self.__class__.FIELDS:
            obj = self.__model
            for item in self.FIELDS[attr_name].split("__"):
                obj = getattr(obj, item)
            return obj
            
        else:
            raise UnknownAttribute(
                "Unknown attribute '%s' for resource '%s'." % (
                    attr_name,
                    self.__class__.__name__
                )
            )
    
    def setAttrValue(self, attr_name, value):
        """
        Sets the value of the attribute named ``attr_name`` to
        ``value``. An :exc:`~.InternalError` is raised if the resource
        is not mutable.
        """
        if self.__mutable:
            if attr_name in self.__class__.FIELDS:
                obj = self.__model
                parts = self.FIELDS[attr_name].split("__")
                for item in parts[:-1]:
                    obj = getattr(obj, item)
                setattr(obj, parts[-1], value)
                obj.save()
            
            else:
                raise UnknownAttribute(
                    "Unknown attribute '%s' for resource '%s'." % (
                        attr_name,
                        self.__class__.__name__
                    )
                )
        else:
            raise InternalError(
                "Cannot set attributes on immutable resources."
            )
    
    def _get_create_dict(self, params):
        return {}
    
    def _create_model(self, create_dict):
        raise InternalError("Not implemented.")
        
    def _post_create(self, params):
        pass
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        pass

    def _getAttrValue(self, attr_name):
        raise InternalError("Not implemented.")
        
    def _setAttrValue(self, attr_name, value):
        raise InternalError("Not implemented.")

class ResourceFactory(object):
    """
    This is the base class for implementations of
    :class:`ResourceFactoryInterface`.
    """
    def get(self, **kwargs):
        """
        Returns the resource instance wrapping the resource model
        defined by the input parameters. This method accepts three
        optional keyword arguments:
        
        * ``subj_id``: the id of the calling component
        * ``obj_id``: the resource ID of the resource
        * ``filter_exprs``: a list of filter expressions that define
          the resource
        
        Note that ``obj_id`` and ``filter_exprs`` are mutually
        exclusive, but exactly one of them must be provided. The
        ``subj_id`` argument will be used to check for relations to
        the resource (not yet implemented).
        """
        
        subj_id = kwargs.get("subj_id")
        obj_id = kwargs.get("obj_id")
        filter_exprs = kwargs.get("filter_exprs")
        
        if obj_id is None and filter_exprs is None:
            raise InternalError("Invalid call to ResourceFactory.get(): Either 'obj_id' or 'filter_exprs' keyword argument must be provided.")
        elif obj_id is not None and filter_exprs is not None:
            raise InternalError("Invalid call to ResourceFactory.get(): Can provide only one of 'obj_id' and 'filter_exprs'")
        
        model = None
        ImplementationCls = None
        
        for Cls in System.getRegistry().getFactoryImplementations(self):
            if obj_id is not None: # query by obj_id
                new_model = self._getById(Cls, obj_id)
            else: # query using filters
                new_model = self._getByFilters(Cls, filter_exprs)
                
            if new_model is not None:
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
        
        if model is not None:
            # TODO: implement relation management
            
            #if subj_id is not None:
                #try:
                    #rel = model.relations.get(rel_class="rel_get", subj__impl_id=subj_id)
                #except Relation.DoesNotExist:
                    #try:
                        #rel = ClassRelation.objects.get(
                            #rel_class="rel_get",
                            #subj__impl_id=subj_id,
                            #obj__impl_id=ImplementationCls.__get_impl_id__()
                        #)
                    #except ClassRelation.DoesNotExist:
                        #return None
                
                #if rel.enabled:
                    #return self._getResourceImplementation(ImplementationCls, model)
            #else:
            
            # --- END TODO
            
            return self._getResourceImplementation(ImplementationCls, model)
        else:
            return None

    
    def find(self, **kwargs):
        """
        Returns a list of resource instances matching the given search
        criteria. This method accepts three optional arguments:
        
        * ``subj_id``: the id of the calling component
        * ``impl_ids``: the implementation IDs of the resource classes
          to be taken into account
        * ``filter_exprs``: a list of filter expressions that constrain
          the resources
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        """
        subj_id = kwargs.get("subj_id")
        impl_ids = kwargs.get("impl_ids")
        filter_exprs = kwargs.get("filter_exprs", [])
        
        impl_and_models = []
        
        for ImplementationCls in self._getImplementationClasses(impl_ids):
            models = self._filter(ImplementationCls, filter_exprs)
            
            # TODO: implement relation management
            
            #if self.subj_id is not None:
                #models = self._getRelated(
                    #subj_id, ImplementationCls, models
                #)
                
            # --- END TODO
            
            for AnotherImplementationCls, other_models in impl_and_models:
                if issubclass(
                        ImplementationCls.__get_model_class__(),
                        AnotherImplementationCls.__get_model_class__()
                    ) and\
                    ImplementationCls.__get_id_field__() == \
                    AnotherImplementationCls.__get_id_field__():
                        other_models = other_models.exclude(
                            **{"%s__in" % AnotherImplementationCls.__get_id_field__(): models.values_list(ImplementationCls.__get_id_field__(), flat=True)}
                        )
                elif issubclass(
                        AnotherImplementationCls.__get_model_class__(),
                        ImplementationCls.__get_model_class__()
                    ) and\
                    ImplementationCls.__get_id_field__() == \
                    AnotherImplementationCls.__get_id_field__():
                        models = models.exclude(
                            **{"%s__in" % ImplementationCls.__get_id_field__(): other_models.values_list(AnotherImplementationCls.__get_id_field__(), flat=True)}
                        )
            
            impl_and_models.append((ImplementationCls, models))
        
        resources = []
        
        for ImplementationCls, models in impl_and_models:
            resources.extend(
                [self._getResourceImplementation(ImplementationCls, model) for model in models]
            )
        
        return resources
    
    def create(self, **kwargs):
        """
        This method creates a resource according to the given
        parameters and returns it to the caller. It accepts one
        mandatory and two optional parameters:
        
        * ``subj_id``: the id of the calling component (optional)
        * ``impl_id``: the implementation ID of the resource to be
          created (mandatory)
        * ``params``: a dictionary of parameters to initialize the
          resource with; the format of this dictionary is specific to
          the resource class
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        """
        subj_id = kwargs.get("subj_id")
        
        if "impl_id" in kwargs:
            impl_id = kwargs["impl_id"]
        else:
            raise InternalError("Missing required 'impl_id' parameter.")
        
        params = kwargs.get("params", {})
                
        ImplementationCls = self._getImplementationClass(impl_id)
        
        # TODO: implement relation management
        
        #if subj_id is not None:
            #try:
                #rel = ClassRelation.objects.get(
                    #rel_class="rel_create",
                    #subj__impl_id=subj_id,
                    #obj__impl_id=ImplementationCls.__get_impl_id__()
                #)
                
                #if rel.enabled:
                    #resource = ImplementationCls()
                    #resource.createModel(params)
                    
                    #for comp_mgr in System.getRegistry().getComponentMangagers(subj_id):
                        #comp_mgr.notify(resource, "created")
                    
                    #return resource
                #else:
                    #return None
                    
            #except ClassRelation.DoesNotExist:
                #return None
            
        # --- END TODO
        
        resource = ImplementationCls()
        resource.setMutable() # required for creating model
        
        resource.createModel(params)
        
        return resource
    
    def update(self, **kwargs):
        """
        This method runs updates on a selection of resources and
        returns the updated resources. It accepts the following
        parameters:
        
        * ``subj_id``: the id of the calling component
        * ``obj_id``: the resource ID of the resource
        * ``impl_ids``: the implementation IDs of the resource classes
          to be taken into account
        * ``filter_exprs``: a list of filter expressions that constrain
          the resources
        * ``attrs``: a dictionary of attribute names and values; the
          attribute names are specific to the resource classes
        * ``params``: a dictionary of parameters to update the
          resource with; the format of this dictionary is specific to
          the resource classes
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        
        The ``obj_id`` argument and the ``impl_ids`` and
        ``filter_exprs`` arguments on the other hand are mutually
        exclusive. The ``attrs`` and ``params`` arguments are mutually
        exclusive as well, exactly one of them has to be specified.
        :exc:`InternalError` is raised if these conditions are not
        met.
        """
        subj_id = kwargs.get("subj_id") # TODO: implement relation management
        
        obj_id = kwargs.get("obj_id")
        impl_ids = kwargs.get("impl_ids")
        filter_exprs = kwargs.get("filter_exprs", [])
        
        attrs = kwargs.get("attrs", {})
        params = kwargs.get("params", {})
        
        if obj_id is not None and \
           (impl_ids is not None or len(filter_exprs) > 0):
            raise InternalError(
                "ResourceFactory.update() accepts either 'obj_id' or 'impl_ids' and/or 'filter_exprs' as arguments."
            )
        
        if len(attrs) > 0 and len(params) > 0:
            raise InternalError(
                "ResourceFactory.update() accepts either 'attrs' or 'params' as arguments."
            )
        elif len(attrs) + len(params) == 0:
            raise InternalError(
                "ResourceFactory.update() expects either 'attrs' or 'params' as arguments."
            )
        
        if obj_id is not None:
            resource = self.get(subj_id=subj_id, obj_id=obj_id)
            
            if len(attrs) > 0:
                for attr_name, attr_value in attrs.items():
                    resource.setAttrValue(attr_name, attr_value)
                    
                resource.saveModel()
                
            else:
                resource.updateModel(params)
                
                resource.saveModel()
            
            return [resource]
        else:
            if len(attrs) > 0:
                return self._updateByAttrs(
                    impl_ids, filter_exprs, attrs
                )
                
            else:
                return self._updateByParams(
                    impl_ids, filter_exprs, params
                )
        
    def delete(self, **kwargs):
        """
        This method deletes a selection of resources. It accepts the
        following parameters:
        
        * ``subj_id``: the id of the calling component
        * ``obj_id``: the resource ID of the resource
        * ``impl_ids``: the implementation IDs of the resource classes
          to be taken into account
        * ``filter_exprs``: a list of filter expressions that constrain
          the resources
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        
        The ``obj_id`` argument and the ``impl_ids`` and
        ``filter_exprs`` arguments on the other hand are mutually
        exclusive. :exc:`InternalError` is raised if these conditions
        are not met.
        """
        subj_id = kwargs.get("subj_id") # TODO: implement relation management
        
        obj_id = kwargs.get("obj_id")
        impl_ids = kwargs.get("impl_ids")
        filter_exprs = kwargs.get("filter_exprs", [])
        
        if obj_id is not None and \
           (impl_ids is not None or len(filter_exprs) > 0):
            raise InternalError(
                "ResourceFactory.delete() accepts either 'obj_id' or 'impl_ids' and/or 'filter_exprs' as arguments."
            )
        
        if obj_id is not None:
            resource = self.get(subj_id=subj_id, obj_id=obj_id)
            
            resource.deleteModel()
        
        else:
            for ImplementationCls in self._getImplementationClasses(impl_ids):
                models = self._filter(ImplementationCls, filter_exprs)
                
                models.delete()

    def getIds(self, **kwargs):
        """
        This method returns the IDs of a selection of resources. It
        accepts the following parameters:
        
        * ``subj_id``: the id of the calling component
        * ``impl_ids``: the implementation IDs of the resource classes
          to be taken into account
        * ``filter_exprs``: a list of filter expressions that constrain
          the resources
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        """
        subj_id = kwargs.get("subj_id")
        impl_ids = kwargs.get("impl_ids")
        filter_exprs = kwargs.get("filter_exprs", [])
        
        ids = set()
        
        for ImplementationCls in self._getImplementationClasses(impl_ids):
            models = self._filter(ImplementationCls, filter_exprs)
            
            if subj_id is not None:
                models = self._getRelated(
                    subj_id, ImplementationCls, models
                )
            
            ids.union(set(models.values_list(ImplementationCls.__get_id_field__(), flat=True)))

        return list(ids)
    
    def getAttrValues(self, **kwargs):
        """
        This method returns the values of a given attribute for a
        selection of resources.
        
        * ``subj_id``: the id of the calling component
        * ``impl_ids``: the implementation IDs of the resource classes
          to be taken into account
        * ``filter_exprs``: a list of filter expressions that constrain
          the resources
        * ``attr_name``: the attribute name (mandatory)
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        
        Raises :exc:`~.InternalError` if the ``attr_name`` argument is
        missing, or :exc:`~.UnknownAttribute` if the attribute name is
        not known to a resource.
        """
        subj_id = kwargs.get("subj_id") # TODO: relation management
        
        impl_ids = kwargs.get("impl_ids")
        filter_exprs = kwargs.get("filter_exprs", [])
        
        if "attr_name" in kwargs:
            attr_name = kwargs["attr_name"]
        else:
            raise InternalError(
                "ResourceFactory.getAttrValues() requires 'attr_name' argument."
            )
        
        attr_values = []
        
        for ImplementationCls in self._getImplementationClasses(impl_ids):
            models = self._filter(ImplementationCls, filter_exprs)
            
            impl = ImplementationCls()
            
            attr_values.extend(models.values_list(
                impl.getAttrField(attr_name), flat=True
            ))
        
        return attr_values
    
    def exists(self, **kwargs):
        """
        Returns ``True`` if there are resources matching the given
        criteria, or ``False`` otherwise.
        
        * ``subj_id``: the id of the calling component
        * ``obj_id``: the id of the requested resource
        * ``impl_ids``: the implementation IDs of the resource classes
          to be taken into account
        * ``filter_exprs``: a list of filter expressions that constrain
          the resources
        
        Note that ``filter_exprs`` will not be taken into account when
        ``obj_id`` is given.
        
        The ``subj_id`` argument will be used to check for relations to
        the resources (not yet implemented).
        """
        
        subj_id = kwargs.get("subj_id") # TODO: relation management
        
        obj_id = kwargs.get("obj_id")
        impl_ids = kwargs.get("impl_ids")
        filter_exprs = kwargs.get("filter_exprs", [])
        
        if obj_id is not None:
            return any([
                self._getById(ImplementationCls, obj_id) is not None
                for ImplementationCls in self._getImplementationClasses(impl_ids)
            ])
        
        for ImplementationCls in self._getImplementationClasses(impl_ids):
            models = self._filter(ImplementationCls, filter_exprs)
            
            if models.count() > 0:
                return True
        
        return False
        
    def _getById(self, ImplementationCls, obj_id):
        ModelClass = ImplementationCls.__get_model_class__()
        
        try:
            return ModelClass.objects.get(
                **{ImplementationCls.__get_id_field__(): obj_id}
            )
        except ModelClass.DoesNotExist:
            return None
        except ModelClass.MultipleObjectsReturned:
            raise FactoryQueryAmbiguous("")
    
    def _getByFilters(self, ImplementationCls, filter_exprs):
        models = self._filter(ImplementationCls, filter_exprs)
        
        if len(models) == 0:
            return None
        elif len(models) == 1:
            return models[1]
        else:
            raise FactoryQueryAmbiguous("")
    
    def _filter(self, ImplementationCls, filter_exprs):
        ModelClass = ImplementationCls.__get_model_class__()
        
        qs = ModelClass.objects.all()
        
        for filter_expr in filter_exprs:
            filter = System.getRegistry().findAndBind(
                intf_id = "core.filters.Filter",
                params = {
                    "core.filters.res_class_id": ImplementationCls.__get_impl_id__(),
                    "core.filters.expr_class_id": filter_expr.__class__.__get_impl_id__(),
                }
            )
            
            qs = filter.applyToQuerySet(filter_expr, qs)
        
        return qs
    
    def _getResourceImplementation(self, ImplementationCls, model):
        res = ImplementationCls()
        res.setModel(model)
        res.setMutable() # TODO: see ticket
        
        return res
    
    def _getImplementationClass(self, impl_id):
        ImplClasses = System.getRegistry().getFactoryImplementations(self)
        
        if impl_id:
            matching_classes = filter(
                lambda impl_class : impl_class.__get_impl_id__() == impl_id,
                ImplClasses
            )
            if len(matching_classes) == 0:
                raise InternalError("Unknown or incompatible resource class '%s'" % impl_id)
            elif len(matching_classes) > 1:
                raise InternalError("Ambiguous implementation id '%s'" % impl_id)
            else:
                return matching_classes[0]
        elif len(ImplClasses) == 1:
            return ImplClasses[0]
        else:
            raise InternalError("Missing 'impl_id' parameter")

    def _getImplementationClasses(self, impl_ids):
        if impl_ids is None:
            return System.getRegistry().getFactoryImplementations(self)
        elif not (isinstance(impl_ids, list) or isinstance(impl_ids, tuple)):
            raise InternalError("Invalid value for 'impl_ids': must be list or tuple")

        return filter(
            lambda Cls: Cls.__get_impl_id__() in impl_ids,
            System.getRegistry().getFactoryImplementations(self)
        )
    
    def _getRelated(self, subj_id, ImplementationCls, models):
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

    def _updateByAttrs(self, impl_ids, filter_exprs, attrs):
        resources = []
        
        for ImplementationCls in self._getImplementationClasses(impl_ids):
            models = self._filter(ImplementationCls, filter_exprs)
        
            impl = ImplementationCls()
            
            update_dict = {}
            for attr_name, attr_value in attrs.items():
                try:
                    field_name = impl.getAttrField(attr_name)
                    
                    update_dict[field_name] = attr_value
                except UnknownAttribute:
                    continue
            
            if len(update_dict) > 0:
                models.update(**update_dict)
                
                resources.extend([
                    self._getResourceImplementation(
                        ImplementationCls, model
                    )
                    for model in models
                ])
                
        return resources

    def _updateByParams(self, impl_ids, filter_exprs, params):
        resources = []
        
        for ImplementationCls in self._getImplementationClasses(impl_ids):
            models = self._filter(ImplementationCls, filter_exprs)
            
            new_resources = [
                self._getResourceImplementation(
                    ImplementationCls, model
                )
                for model in models
            ]
            
            for resource in new_resources:
                resource.updateModel(params)
                resource.saveModel()
            
            resources.extend(new_resources)
            
        return resources
