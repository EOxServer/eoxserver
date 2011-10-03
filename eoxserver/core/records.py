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
This module provides interfaces as well as a simple implementation for record
wrappers. The design objective for this module was to provide a more lightweight
alternative to resource wrappers based on :mod:`eoxserver.core.resources`.

Record wrappers shall couple data stored in the database with
additional application logic. They are lazy in the sense that data assigned to
the wrapper is not written to the database immediately. They are also immutable,
i.e. once they have been initialized their data cannot be changed any more. Last
but not least, they are able to cope with non-abstract model inheritance.
"""

from eoxserver.core.system import System
from eoxserver.core.interfaces import *
from eoxserver.core.registry import RegisteredInterface, FactoryInterface
from eoxserver.core.exceptions import InternalError, UniquenessViolation

#-------------------------------------------------------------------------------
# Interface declarations
#-------------------------------------------------------------------------------

class RecordWrapperInterface(RegisteredInterface):
    """
    This class defines an interface for simple lazy record wrappers which are
    used throughout EOxServer to couple data and metadata stored in the
    configuration database with additional application logic.

    Implementations of this interface shall wrap a model record and couple it
    with additional attributes and dynamic behaviour. The wrapper shall be lazy,
    i.e. any changes to the model record or to the attributes will not affect
    the database until the programmer explicitly calls :meth:`save`,
    :meth:`getRecord`.
    
    .. method:: getType
    
       This method shall return the type of record the wrapper represents. This
       method is needed especially by factories which return multiple classes
       of :class:`RecordWrapperInterface` implementations that wrap models
       inheriting from a common base model.
    
    .. method:: setRecord(record)
    
       This method shall initialize the record wrapper with an existing model
       record. It shall raise :exc:`~.InternalError` in case the record is
       of an incompatible type
    
    .. method:: setAttrs(**kwargs)
    
       This method shall initialize the record wrapper with implementation
       dependent attributes. It shall raise :exc:`~.InternalError` in case 
       there are mandatory attributes missing.
    
    .. method:: sync(fetch_existing=False)
    
       Synchronize with the database, i.e. fetch or create a record with the
       instance attributes.

       The method shall respect uniqueness constraints on the underlying model,
       i.e. return an existing record matching the instance attributes if
       possible and create a new one only if all constraints are satisfied. In
       case neither is possible :exc:`~.UniquenessViolation` shall be raised.
       
       If the optional ``fetch_existing`` argument is set to ``True``, try to
       get an existing record with the same attributes from the database even
       if no uniqueness constraints apply. If there is none, create a new one.
       
    .. method:: getRecord(fetch_existing=False)
    
       Return the record wrapped by the implementation. If none has been defined
       yet, fetch or create one with the instance attributes.
    
       The method shall respect uniqueness constraints on the underlying model,
       i.e. return an existing record matching the instance attributes if
       possible and create a new one only if all constraints are satisfied.
       In case neither is possible :exc:`~.UniquenessViolation` shall be raised.

       If the optional ``fetch_existing`` argument is set to ``True``, try to
       get an existing record with the same attributes from the database even
       if no uniqueness constraints apply. If there is none, create a new one.
    
    .. method:: delete(commit=True)
    
       Delete the model record and perform any related logic.
    
       This method accepts an optional boolean parameter ``commit`` which
       defaults to ``True``. If it is set to ``False`` do not actually delete
       the record, but do perform the additional logic. This is useful for
       bulk deletion by factories; it should be used with great care as it might
       leave the system in an inconsistent state if the database record is not
       removed afterwards.

    """
    
    REGISTRY_CONF = {
        "name": "Record Wrapper Interface",
        "intf_id": "core.records.RecordWrapperInterface",
        "binding_method": "factory"
    }

    getType = Method(
        returns = StringArg("@return")
    )
    
    setRecord = Method(
        ObjectArg("record")
    )
    
    setAttrs = Method(
        KwArgs("kwargs")
    )
    
    sync = Method(
        BoolArg("fetch_existing", default=False)
    )
    
    getRecord = Method(
        BoolArg("fetch_existing", default=False),
        returns = ObjectArg("@return")
    )
    
    delete = Method(
        BoolArg("commit", default=True)
    )

class RecordWrapperFactoryInterface(FactoryInterface):
    """
    This is the interface for factories returning record wrappers, i.e.
    implementations of :class:`RecordWrapperInterface`. It inherits from
    :class:`~.FactoryInterface`.
    
    .. method:: create(**kwargs)
    
       Create a record wrapper with the given attributes. The keyword arguments
       accepted by this method shall correlate to the attribute keyword
       arguments accepted by the underlying :class:`ResourceWrapperInterface`
       implementations.
       
       For factories that generate different types of record wrappers a
       mandatory ``type`` keyword argument shall be required that shall
       correlate to the return value of the
       :meth:`ResourceWrapperInterface.getType` method of the desired record
       wrapper type.
       
    .. method:: getOrCreate(**kwargs)
    
       Get or create a record wrapper with the given attributes. That is,
       if a database record matching all the given attributes exists, return
       a wrapper with this record, otherwise create a new record. The keyword
       arguments accepted by this method shall correlate to the attribute
       keyword arguments accepted by the underlying
       :class:`ResourceWrapperInterface` implementations.
       
       For factories that generate different types of record wrappers a
       mandatory ``type`` keyword argument shall be required that shall
       correlate to the return value of the
       :meth:`ResourceWrapperInterface.getType` method of the desired record
       wrapper type.
       
    .. method:: update(**kwargs)
    
       Update model records in bulk. Return the record wrappers for the
       updated records.
       
    .. method:: delete(**kwargs)
    
       Delete model records in bulk and apply any additional logic defined by
       the specific record wrapper implementations; see
       :meth:`RecordWrapperInterface.delete`.
    """
    
    REGISTRY_CONF = {
        "name": "Record Wrapper Factory Interface",
        "intf_id": "core.records.RecordWrapperFactoryInterface",
        "binding_method": "direct"
    }
    
    create = Method(
        KwArgs("kwargs"),
        returns = ObjectArg("@return")
    )
    
    getOrCreate = Method(
        KwArgs("kwargs"),
        returns = ObjectArg("@return")
    )
    
    update = Method(
        KwArgs("kwargs"),
        returns = ListArg("@return")
    )
    
    delete = Method(
        KwArgs("kwargs")
    )

#-------------------------------------------------------------------------------
# Record wrapper base class
#-------------------------------------------------------------------------------

class RecordWrapper(object):
    """
    This is a common base class for :class:`RecordWrapperInterface`
    implementations.
    
    Concrete implementations may derive from it overriding the respective
    methods.
    """
    
    def __init__(self):
        self.record = None
        
    def getType(self):
        """
        This method shall return the type of record the wrapper represents.
        Raises :exc:`~.InternalError` by default.
        """
        
        raise InternalError("Not implemented.")
    
    def setRecord(self, record):
        """
        Assign the model record ``record`` to the instance. This method raises
        :exc:`~.InternalError` if the record does not validate.
        """
        self._validate_record(record)
        
        self._set_record(record)
    
    def setAttrs(self, **kwargs):
        """
        Assign the attributes given as keyword arguments to the instance.
        This method raises :exc:`~.InternalError` if attributes do not validate.
        """
        self._validate_attrs(**kwargs)
        
        self._set_attrs(**kwargs)
    
    def sync(self, fetch_existing=False):
        """
        """
        if not self.record:
            unique_record = self._fetch_unique_record()
            
            if unique_record:
                self.record = unique_record
            else:
                if fetch_existing:
                    self.record = self._fetch()
                
                if not self.record:
                    self._create_record()
    
    def getRecord(self, fetch_existing=False):
        """
        Get the model record wrapped by the instance (i.e. an instance of a
        subclass of :class:`django.db.models.Model`). This method calls
        :meth:`sync` to fetch or create a record if none has been defined.
        The ``fetch_existing`` argument is parsed to :meth:`sync`.
        """
        self.sync(fetch_existing)
        
        return self.record
    
    def delete(self, commit=True):
        """
        Delete the model record wrapped by the instance from the database and
        perform any additional logic related to the deletion. Do nothing if
        there is no model record defined. See
        :meth:`ResourceWrapperInterface.delete` for a description of the
        ``commit`` parameter.
        
        """
        
        if self.record:
            self._pre_delete()
            
            if commit:
                self.record.delete()
                
                del self.record
        

    def _validate_record(self, record):
        # used internally by :meth:`setRecord` to validate record; expected to
        # raise :exc:`~.InternalError` in case the record does not validate;
        
        pass
        
    def _set_record(self, record):
        # used internally by :meth:`setRecord` to assign record to the instance
        
        self.record = record
        
    def _validate_attrs(self, **kwargs):
        # used internally to validate the attributes to be assigned to the
        # wrapper instance with :meth:`setAttrs`; expected to raise
        # :exc:`~.InternalError` in case the attributes do not validate
        
        pass

    def _set_attrs(self, **kwargs):
        # used internally by :meth:`setAttrs` to assign attributes to the
        # instance; needs to be overridden by subclasses; raises
        # :exc:`~.InternalError` by default
        
        raise InternalError("Not implemented.")

    def _fetch_unique_record(self):
        # Fetch a record from the database and check it against the uniqueness
        # constraints; returns ``None`` if there is no existing record; raise
        # :exc:`~.UniquenessViolation` if uniqueness constraints cannot be
        # satisfied
        
        raise InternalError("Not implemented.")
        
    def _fetch(self, *fields):
        # Fetch a record from the database; the positional arguments are expected
        # to be a subset of the wrapper instance attribute names; if they are
        # omitted a record matching all instance attributes is searched; if
        # there is no matching record, ``None`` shall be returned
        
        if fields:
            query = self._get_query(fields)
        else:
            query = self._get_query()

        records = self._get_query_set(query)
        
        if records.count() == 0:
            return None
        else:
            return records[0]

    def _get_query(self, fields=None):
        # return a dictionary of field lookups to be submitted to a Django
        # object managers :meth:`filter` method;
        
        raise InternalError("Not implemented.")
        
    def _get_query_set(self, query):
        # return a query set of records matching the lookup parameters
        # submitted with the ``query`` argument (see :meth:`_get_query`)
        
        raise InternalError("Not implemented.")

    def _create_record(self):
        # used internally by :meth:`sync` and :meth:`getRecord` to create
        # model record from instance attributes
        
        raise InternalError("Not Implemented.")
        
    def _pre_delete(self):
        # used internally by :meth:`delete` to perform any additional logic
        # before deleting the database record wrapped by the implementation;
        # be sure to raise an appropriate exception if this method fails and
        # record deletion shall be prevented; be sure to be able to roll back
        # changes if needed in order to keep the wrapper in a consistent state
        
        raise InternalError("Not implemented.")

#-------------------------------------------------------------------------------
# Record wrapper factory base class
#-------------------------------------------------------------------------------

class RecordWrapperFactory(object):
    """
    This factory gives access to record wrappers.
    """
    
    def __init__(self):
        self.impls = {}
        
        for Impl in System.getRegistry().getFactoryImplementations(self):
            self.impls[Impl().getType()] = Impl

    def get(self, **kwargs):
        """
        Get a record wrapper for a database model record. This method
        accepts either one of the following two keyword arguments:
        
        * ``pk``: primary key of a record
        * ``record``: a model record
        
        :exc:`~.InternalError` is raised if none of these is given. The
        data package wrapper returned will be of the right type for the given
        model record.
        """
        if "pk" in kwargs:
            pk = kwargs["pk"]
            
            record = self._get_record_by_pk(pk)
            
        elif "record" in kwargs:
            record = kwargs["record"]
            
        else:
            raise InternalError(
                "Either 'pk' or 'record' keyword arguments needed for getting a record wrapper."
            )
        
        wrapper = self._get_record_wrapper(record)
        
        wrapper.setRecord(record)
        
        return wrapper
    
    def find(self, **kwargs):
        """
        Find database model records and return the corresponding record wrappers.
        Not yet implemented.
        """
        
        pass # TODO
    
    def create(self, **kwargs):
        """
        Create a data package wrapper instance of a given type. This method
        expects a ``type`` keyword argument that indicates the data package
        type of the wrapper to be created. All other keyword arguments are
        passed on to the :meth:`~RecordWrapper.setAttrs` method of the
        respective wrapper class.
        
        :exc:`~.InternalError` is raised if the ``type`` keyword argument is
        missing or does not contain a valid type name. :exc:`~.InternalError`
        exceptions raised by :meth:`RecordWrapper.setAttrs` are passed on as
        well.
        """
        
        if "type" in kwargs:
            wrapper_type = kwargs["type"]
        else:
            raise InternalError("Missing mandatory 'type' parameter.")

        if wrapper_type not in self.impls:
            raise InternalError(
                "Unknown wrapper type '%s'." % wrapper_type
            )
        else:
            wrapper = self.impls[wrapper_type]()
            wrapper.setAttrs(**kwargs)
            
            return wrapper
            
    def getOrCreate(self, **kwargs):
        """
        Get a wrapper for an existing record with the given attributes or
        create a new one. This calls :meth:`create` and
        :meth:`RecordWrapper.sync`. The returned wrapper will always
        contain a database record (it is not lazy).
        
        :exc:`~.InternalError` is raised if there are mandatory attribute
        keyword arguments missing and :exc:`~.UniquenessViolation` if the
        record could not be created due to unqiueness constraints.
        """
        wrapper = self.create(**kwargs)
        
        wrapper.sync(fetch_existing=True)
        
        return wrapper

    def update(self, **kwargs):
        """
        Update model records in bulk. Not yet implemented.
        """
        
        pass # TODO
    
    def delete(self, **kwargs):
        """
        Delete model records in bulk. Not yet implemented.
        """
        
        pass # TODO

    def _get_record_by_pk(self, pk):
        # retrieve the model record from the respective database model (table)
        # using the given primary key ``pk``; this method may return a record
        # from a base model in case of non-abstract model inheritance; in the
        # latter case :meth:`_get_record_wrapper` must be able to read the
        # subclass type from the record
        
        raise InternalError("Not implemented.")
    
    def _get_record_wrapper(self, record):
        # return the correct wrapper for the record respecting the record type
        # in case of non-abstract model inheritanze and initialize it
        
        raise InternalError("Not implemented.")
