.. Module eoxserver.core.registry

.. _module_core_registry:

Module eoxserver.core.registry
==============================

.. automodule:: eoxserver.core.registry

Introduction
------------

The registry has been introduced as a core component of EOxServer with
:doc:`/en/rfc/rfc2`. The registry is the central entry point for:

* automated detection of registered interfaces and implementations
* dynamic binding to the implementations
* configuration of components and relations between them

The concept of the registry builds on interfaces and their
implementations as defined in :mod:`eoxserver.core.interfaces`.

This module defines a specialized class of interfaces called
:class:`RegisteredInterface`. This subclass of :class:`~.Interface` defines
additional metadata needed by the registry and adds some more logic to the
implementation process. In order to include implementations in the registry
the interface has to be derived from :class:`RegisteredInterface`.

Implementations of registered interfaces can be detected automatically by the
registry and are then ingested into it. The information stored in the registry
consists of:

* registered interfaces
* implementations of registered interfaces
* status of implementations (components)
* binding method and parameters

Implementations can be switched on and off. The registry will only return
instances of implementations that are enabled. This feature can be used to
fine-tune the behaviour of the system.

There are several binding methods defined that determine how to get instances
of implementations of registered interfaces. Binding can be parametrized, so
that the appropriate implemenation is chosen based on some parameters conveyed
with the request. As the parameters can be defined at runtime and as new 
implementations with other binding parameters can be added in a flexible way, we
speek of dynamic binding.

Registered Interfaces and Implementations
-----------------------------------------

* RegisteredInterface
* REGISTRY_CONF
* implement() method

The registry is a repository for interfaces and implementations. Only
interfaces derived from :class:`RegisteredInterface` and their respective
implementations will be included in the registry.

:class:`RegisteredInterface` adds some features and requirements to the
:class:`~.Interface` base class. First of all, it expects a ``REGISTRY_CONF``
dictionary class variable for the interface declaration. The following keys are
accepted or required at least:

* ``name``: The name of the interface (mandatory)
* ``intf_id``: The unique ID of the interface; by convention this should include
  the dotted module name (mandatory)
* ``binding_method``: The name of the binding method (optional, defaults to
  ``direct``)

Depending on the binding method additional parameters may be required. See the
:ref:`module_core_registry_bind` section.

Detection and Registration
--------------------------

* config settings
* loading of modules
* searching of implementations
* registration

.. _module_core_registry_bind:

Dynamic Binding
---------------

The registry provides four binding methods:

* direct binding
* KVP binding
* test binding
* factory binding

Direct binding means that the implementation to bind to is directly
referenced by the caller using its implementation ID::

    from eoxserver.core.system import System
    
    impl = System.getRegistry().bind(
        "somemodule.SomeImplementation"
    )

Direct binding is available for every implementation. You can also set
the ``binding_method`` in the ``REGISTRY_CONF`` of an interface to
``direct``, meaning that its implementations are reachable only by
this method. This is used e.g. for component managers and factories.

The easiest method for parametrized dynamic binding is key-value-pair
matching, or KVP binding. It is used if an interface defines ``kvp`` as
its ``binding_method``. The interface must then define in its
``REGISTRY_CONF`` one or more ``registry_keys``, the implementations
in turn must define ``registry_values`` for these keys. When looking
up a matching implementation, the parameters given with the request
are matched against these key-value-pairs. Finally, the registry returns
an instance of the matching implementation::

    from eoxserver.core.system import System
    
    def dispatch(service_name, req):
    
        service = System.getRegistry().findAndBind(
            intf_id = "services.interfaces.ServiceHandler",
            params = {
                "services.interfaces.service": service_name.lower()
            }
        )
        
        response = service.handle(req)
        
        return response

This binding method is used e.g. for binding to service, version
and operation handlers for OGC Web Services based on the parameters
sent with the request.

A more flexible way to determine which implementation to bind to is
the test binding method (``"binding_method": "testing"``). In this case,
the interface must be derived from :class:`TestingInterface`. The
implementation must provide a :meth:`test` method which will be invoked
by the registry in order to determine if it is suitable for a given set
of parameters. This can be used e.g. to determine which format handler
to use for a given dataset::

    from eoxserver.core.system import System
    
    format = System.getRegistry().findAndBind(
        intf_id = "resources.coverages.formats.FormatInterface",
        params = {
            "filename": filename
        }
    )
    
    ...
    
The fourth binding method is factory binding (
``"binding_method": "factory"``). In this case the registry invokes a
factory that returns an instance of the desired implementation.
Factories must be implementations of a descendant of
:class:`FactoryInterface`. Implementations and factories are linked
together only at runtime, based on the metadata collected during the
detection phase. This binding method is used e.g. for binding to
instances of a resource wrapper::

    from eoxserver.core.system import System
    
    resource = System.getRegistry().getFromFactory(
        factory_id = "resources.coverages.wrappers.SomeResourceFactory",
        obj_id = "some_resource_id"
    )

In order to access other functions of the factory you can bind to it
directly. For retrieving all resources that are accessible through a
factory you would use code like this::

    from eoxserver.core.system import System
    
    resource_factory = System.getRegistry().bind(
        "resources.coverages.wrappers.SomeResourceFactory"
    )
    
    resources = resource_factory.find()

Components
----------

Reference
---------

Registry
~~~~~~~~

.. autoclass:: Registry
   :members:

Interfaces
~~~~~~~~~~

.. autoclass:: RegisteredInterface
   :members:

.. autoclass:: TestingInterface
   :members:

.. autoclass:: FactoryInterface
   :members:

.. autoclass:: ComponentManagerInterface
   :members:
   
Config Reader
~~~~~~~~~~~~~

.. autoclass:: RegistryConfigReader
