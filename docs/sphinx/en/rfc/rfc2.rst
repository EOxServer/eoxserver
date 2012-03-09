.. RFC 2: Extension Mechanisms for EOxServer
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 EOX IT Services GmbH
  #
  # Permission is hereby granted, free of charge, to any person obtaining a copy
  # of this software and associated documentation files (the "Software"), to
  # deal in the Software without restriction, including without limitation the
  # rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
  # sell copies of the Software, and to permit persons to whom the Software is
  # furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies of this Software or works derived from this Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
  # IN THE SOFTWARE.
  #-----------------------------------------------------------------------------

.. _rfc_2:

RFC 2: Extension Mechanism for EOxServer
========================================

:Author: Stephan Krause
:Created: 2011-02-20
:Last Edit: 2011-09-15
:Status: ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc2

This RFC proposes an extension mechanism that allows to integrate
extension modules and plugins dynamically into the EOxServer
distribution and instances.

Introduction
------------

:doc:`rfc1` proposes an extensible architecture for EOxServer in order
to ensure

* modularity
* extensibility
* flexibility

of the design. It establishes the need for an extension mechanism which
acts as a sort of "glue" between different parts of the architecture
and enables dynamic binding to these components.

This RFC discusses the extension mechanism in further detail and
identifies the architectural principles and components needed to
implement it.

The constituent components of the extension mechanism design are
interface declarations, the respective implementations and a central
registry that contains metadata about interfaces and implementations
and enables dynamic binding to the latter ones.

Requirements
------------

:doc:`rfc1` proposes an extension mechanism for EOxServer. It shall
assure extensibility by additional modules and plugins and provide
functionality to enable dynamic binding to extending modules.

In the layered architecture of RFC 1 the :ref:`rfc1_core` shall be the
place where the central logic that enables the dynamic extension of
system functionality resides. The layers shall provide interface
definitions based on the extension model of the Core that can be
implemented by extending modules and plugins.

Now which extensions are needed and which requirements do they impose on
the extension mechansims? Digging deeper we have a look at the four
architectural layers of EOxServer and analyze the interfaces and
implementations needed by each of them.

The :ref:`rfc1_svc_lyr` defines a structured approach to OGC Web Service
(OWS) request handling that discerns different levels:

* services
* service versions
* service extensions
* service operations

For all of these levels interfaces are defined that are implemented by
extending modules for specific OWS and their different versions and
extensions.

The :ref:`rfc1_proc_lyr` defines interfaces for processes and processing
chains (see :doc:`rfc5`). Some of these are used internally and
integrated into the distribution, most will be provided by plugins.
While the process interface needs to be generic in order to make the
implementation of many different processes possible, it must be concise
enough to allow binding between processes in a processing chain. So,
this must be sustained by the extension mechanism as well.

The :ref:`rfc1_dint_lyr` shall provide an abstraction layer for
different data formats, metadata formats and data packaging formats.
This shall be achieved using common interfaces for coverage data, vector
data and metadata respectively.

Data and packaging formats are often not known by the system before
ingesting a dataset. Thus, some kind of autodetection of formats is
necessary. This is provided partly by the underlying
libraries such as `GDAL <http://www.gdal.org>`_, but shall also be
considered for the design of the extension mechanism: it must be
possible to dynamically bind to the right data, metadata and data
packaging format based on evaluations of the data. These tests should be
implemented by format extensions and supported by the extension 
mechansim.

The :ref:`rfc1_dacc_lyr` is built around the interface definitions of
backends and data sources stored by them. 

In addition to modularity and extensibility RFC 1 states that the
system shall be

  flexible in the sense that it must be possible to select different
  combinations of modules to deploy and activate
  
Modules can be combined to build a specific application. From a user
perspective it is essential to be able to activate and deactivate
services, service versions and service extensions globally 
and/or separately for each resource or process. The same applies for
other extensible parts of the system such as backends.

The O3S Use Case 2 for instance requires a server setup that consists of:

* local and WCS backends in the Data Access Layer
* a specific combination of coverage, vector data, metadata and
  packaging formats in the Data Integration Layer
* a feature detection process in the Processing Layer
* WPS and WFS implementations in the Service Layer

All other backends, services and processes shall be disabled.

Summarizing the requirements the extension mechanism shall support:

* extensibility by additional modules and plugins 
* dynamic binding
* interface definitions for extensions
* implementations that can be enabled or disabled

  * globally
  * per resource or per process

* modules that can be configured dynamically to build an application
* autodetection of data, metadata and data packaging formats

Extension Mechanism
-------------------

The basic questions for the design of the extension mechanism are:

* how to declare extensible interfaces
* how to design implementations of these interfaces
* how to advertise them
* how to bind to them

Unlike Java or C++, Python does not have a built-in mechanism to
declare interfaces. A method definition always comes with an
implementation. With Python 2.6 support for abstract base classes and
abstract methods was added, but at the moment it is not an option to use
this framework as this would break support for earlier Python versions.

So, two basic design options remain:

* using conventional Python classes and inheritance mechanisms for
  interfaces and implementations
* customize the interface declaration and implementation creation using
  Python metaclasses

Whereas the first approach is easier, the second one can provide more
control and a clear differentiation between interface declaration
and implementation. Both design options are discussed in further detail
in the :ref:`rfc2_ifs_impls` section below.

The second major topic is how to find and bind to implementations of an
interface if not all implementations are known to the system a priori,
as is the case with plugins. Some "glue" is needed that holds the
system together and allows for dynamic binding. In the case of EOxServer
this is implemented by a central registry that keeps track of
implementations by automatically scanning Python modules in certain
directories that are supposed to contain EOxServer extending modules or
plugins. For more details on the basics of :ref:`rfc2_registry` see
below.

In most cases an instance of EOxServer will not need all the
functionality provided by the distribution or plugins installed on the
system. Dynamic binding allows for enabling and disabling certain
services, processes, formats, backends and plugins in an interactive
way using the administration client. In order to assure this required
functionality a configuration data model is needed that allows to store
information about what parts of the system are activated and what
resources they may operate on. See the section :ref:`rfc2_model` for
further details.

Implementations of interfaces are not isolated objects. They depend on
libraries, functionality provided by the EOxServer core and layers and,
last but not least, on other interface implementations. In order to
assure that the dynamically configurable system is in a consistent
state, the interdependencies between implementations need to be
properly advertised and stored in the configuration data model.

After this short overview, we will go more in depth in the following
sections.

.. _rfc2_ifs_impls:

Interfaces and Implementations
------------------------------

As already discussed before there are two design options for interfaces
and implementations:

* interfaces and implementations as conventional Python classes that
  are linked through inheritance
* interfaces as special Python classes that are linked to
  implementations by a custom mechanism.

Whereas the first approach is straightforward and easy to implement and
handle it has also some serious drawbacks. Most importantly it does
not allow for a clear separation between interface declaration and 
implementation. A method declared in the interface always must contain
an implementation, and an implementation may change the signature of the
methods it implements in any possible way.

What's more, as the implementation inherits (mostly generic) method
code from the interface there is no way to validate if it actually
defines concrete methods to override the "abstract" ones the interface
class provides.

So, there are also good reasons for the second approach although it is
more challenging for developers. The approach proposed here allows to
customize class generation and inheritance enabling validation at
"compile time" (i.e. when classes are created) and runtime (i.e. when
instance methods are invoked) as well as separation of interface
definition from implementation.

How can this be achieved? The proposed mechanism relies on an
interface base class called ``Interface`` that concrete interface
declarations can derive from, implementing code contained in a
conventional Python class and a method called ``implement()`` that
generates a special  implementation class from the interface declaration
and the class containing the implementing code.

Interface Declaration
~~~~~~~~~~~~~~~~~~~~~

It has already been said that interface declarations shall derive from
a common base class called ``Interface``. But that is not the end of the
story - one big question remains: how to declare actual methods without
implementation? The proposed approach is not to declare methods as such
at all, but use classes representing them instead.

For this end three classes are to be defined alongside the ``Interface``
base class.

* instances of the ``Constant`` class represent constants defined by
  the interface
* instances of the ``Method`` class represent methods
* instances of the ``Arg`` class represent method arguments; subclasses
  of ``Arg`` allow for type validation, e.g. instances of ``IntArg``
  represent integer arguments

Let's have a look at a quick example::

    from eoxserver.core.interfaces import Interface, Method, Arg

    class ServiceInterface(Interface):
        handle = Method(
            Arg("req")
        )

.. note::

  Code examples in this RFC are merely informational. The actual
  implementation may deviate a little bit from them. A reference
  documentation will be prepared for the definitive extension
  mechanism.

This snippet of Python code represents a simple and complete interface
declaration. The ``ServiceInterface`` class will be used in further
examples as well. It shows a method definition that declares the
following: the method ``handle`` shall take one argument of arbitrary
type named ``req`` that stands for an OWS request.

As you can see the declaration is a class variable containing an
instance of the ``Method`` class. It is not a method (it does not even
have to be callable). It serves two purposes:

* documentation of the interface
* validation of the implementation

Thinking of these two goals, the writer of the code could have been more
rigorous and declare an argument like this::

    handle = Method(
        ObjectArg("req", arg_class=OWSRequest)
    )

That way it is documented what kind of argument is expected. When
defining the implementation it is enforced that it have a method
``handle`` which takes exactly one argument besides ``self``, otherwise
an exception will be raised. When invoking an interface of the
implementation it can be validated that the argument is of the right
type. More on this later under :ref:`rfc2_impl_val`. Now let's have a
look at implementations.

Implementations
~~~~~~~~~~~~~~~

The proposed design of interface implementation intends to hide all the
complexity of this process from the developers of implementations. They
just have to write an implementing class which is a normal new-style
Python class, and wrap it with the ``implement()`` method of the
interface, such as in the following example::

    from eoxserver.services.owscommon import ServiceInterface

    class WxSService(object):
        
        def handle(self, req):
            
            # ...
            
            return response
    
    WxSServiceImplementation = ServiceInterface.implement(WxSService)

The call to ``implement()`` ensures validation of the interface and
produces an implementation class that inherits all the code of the
implementing class and contains information about the interface. This is
only the basic functionality of the interface implementation process:
more is to be revealed in the following sections.

.. _rfc2_impl_val:

Validation of Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The validation of implementations is performed in two ways:

* at class creation time
* at instance method invocation time

Validation at class creation time checks:

* if all methods declared by the interface are implemented
* if the method arguments of the interface and implementation match

Class creation time validation is performed unconditionally.

Instance method invocation time ("runtime") validation is optional. It
can be triggered by the ``runtime_validation_level`` setting. There are
three possible values for this option:

* ``trust``: no runtime validation
* ``warn``: argument types are checked against interface declaration;
  in case of mismatch a warning is written to the log file
* ``fail``: argument types are checked against interface declaration;
  in case of mismatch an exception is raised
  
The ``runtime_validation_level`` option can be set

    * globally (in configuration file)
    * per interface
    * per implementation

where stricter settings override weaker ones.

.. note::

  The ``warn`` and ``fail`` levels are intended for use
  throughout the development process. In a production setting ``trust``
  should be used.

.. _rfc2_registry:

Registry
--------

The Registry is the core component for managing the extension mechanism
of EOxServer. It is the central entry point for:

* automated detection of registered interfaces and implementations
* dynamical binding to the implementations
* configuration of components and relations between them

Its functionality shall be discussed in further detail in the following
subsections: 

* :ref:`rfc2_model`
* :ref:`rfc2_detect`
* :ref:`rfc2_binding`

.. _rfc2_model:

Data Model
~~~~~~~~~~

The data model for the Extension Mechanism including dynamic binding is
implemented primarily by the :ref:`rfc2_registry`; for persistent
information it relies on the configuration files and the database.

As you'd expect, the Registry data model relies on interfaces and
implementations. However, not all of them are registered, but only 
descendants of :class:`RegisteredInterface` and their respective
implementations. :class:`RegisteredInterface` extends the configuration
model for interfaces with information relevant to the registration and
dynamic binding processes. This is an example for a valid
configuration::
    
    from eoxserver.core.registry import RegisteredInterface
    
    class SomeInterface(RegisteredInterface):
    
        REGISTRY_CONF = {
            "name": "Some Interface",
            "intf_id": "somemodule.SomeInterface",
            "binding_method": "direct"
        }

The most important parts are the interface ID ``intf_id`` and the
``binding_method`` settings which will be used by the registry to find
implementations of the interface and to determine how to bind to them.
For more information see the :ref:`rfc2_binding` section below.

The registry model is accompanied by a database model that allows to
store persistently which parts of the system (services, plugins, etc.)
are enabled and which resources they have access to.

.. figure:: resources/rfc2/model_core.png
   :align: center
   
   *Database Model for the Registry*

For every registered implementation an :class:`Implementation` instance
and database record are created. Implementations are subdivided into
components and resource classes, each with their respective model
deriving from :class:`Implementation`. Components stand for the active
parts of the system like Service Handlers. They can be enabled or
disabled. Resource classes relate to a specific resource wrapper which
in turn relate to some specific model derived from :class:`Resource`.

Furthermore, there is the possibility to create, enable and disable
relations between components and  specific resource instances or
resource classes. These relations are used to determine whether a given
component has access to a given resource or resource class. They allow
to configure the behaviour e.g. of certain services and protect parts
of an EOxServer instance from unwanted access.

As the number of registered components is quite large and as there are
many interdependencies between them and to resource classes specific
Component Managers shall be introduced in order to:

* group them to larger entities which are more easy to handle
* validate the configuration with respect to these interdependencies
* facilitate relation management
* automatically create the needed relations

These managers shall implement the common
:class:`ComponentManagerInterface`.

.. _rfc2_detect:

Detection
~~~~~~~~~

The first step in the dynamic binding process provided by the registry
is the detection of interfaces and implementations to be registered.
For this end the registry loads the modules defined in the configuration
files and searches them for descendants of :class:`RegisteredInterface`
and their implementations. The metadata of the detected interfaces and
implementations (the contents of``REGISTRY_CONF``) is ingested into the
registry. This metadata is used for binding to the implementations,
see the following subsection :ref:`rfc2_binding` for details.

The main EOxServer configuration file ``eoxserver.conf`` contains
options for determining which modules shall be scanned during the
detection phase. The user can define single modules and whole
directories to be searched for modules there.

.. _rfc2_binding:

Binding
~~~~~~~

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

Voting History
--------------

:Motion: To accept RFC 2
:Voting Start: 2011-07-25
:Voting End: 2011-09-15
:Result: +6 for ACCEPTED

Traceability
------------

:Requirements: N/A
:Tickets: N/A
