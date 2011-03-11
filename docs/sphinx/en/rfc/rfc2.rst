.. RFC 2: Extension Mechanisms for EOxServer

.. _rfc_2:

RFC 2: Extension Mechanism for EOxServer
========================================

:Author: Stephan Krause
:Created: 2011-02-20
:Last Edit: 2011-03-11
:Status: IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc2

This RFC proposes an extension mechanism that allows to integrate
extension modules and plugins dynamically into the EOxServer
distribution and instances.

Introduction
------------

* motivation
* addressed problems
* proposed solution

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

Other than Java or C++, Python does not have a built-in mechanism to
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
resources they may operate on. See section :ref:`rfc2_config` for
further details.

Implementations of interfaces are not isolated objects. They depend on
libraries, functionality provided by the EOxServer core and layers and,
last but not least, on other interface implementations. In order to
assure that the dynamically configurable system is in a consistent
state, the interdependencies between implementations need to be
properly advertised and stored in the configuration data model.

Another issue that arises when designing a dynamic extension mechanism
is the possibility of conflicts between extending modules. Conflicts
are more natural and frequent than one may assume at first. Take for
example service extensions like EO-WCS that in certain cases need to
override the implementation of the base service (WCS 2.0 in this case).
Without further information the central registry cannot decide which
implementation to bind to. This calls for a conflict resolution
mechanism and for further metadata to be stored in the configuration
data model.

For more information see section :ref:`rfc2_dep_confl` below. For
further details on service extensions please refer to :doc:`rfc3`.

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
  implementations by a special mechanism using metaclasses

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
more challenging for developers. Using Python metaclasses allows to
customize class generation and inheritance enabling validation at
"compile time" (i.e. when classes are created) and runtime (i.e. when
instance methods are invoked) as well as separation of interface
definition from implementation.

How can this be achieved? The proposed mechanism relies on an
interface base class called ``Interface`` that concrete interface
declarations can derive from, implementing code contained in a
conventional Python class and a function called ``implement()`` that
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

Actually, starting with Python 2.6 you can even be more
concise using the class decorator syntax::

    from eoxserver.services.owscommon import ServiceInterface
    
    @ServiceInterface.implement
    class WxSServiceImplementation(object):
        
        def handle(self, req):
            
            # ...
            
            return response

The call to ``implement()`` ensures validation of the interface and
produces an implementation class that inherits all the code of the
implementing class and contains information about the
interface. This is only the basic functionality of the interface
implementation process: more is to be revealed in the following
sections.

.. _rfc2_impl_val:

Validation of Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _rfc2_registry:

Registry and Dynamic Binding
----------------------------
* hooks
* extension names
* keys, values
* naming conventions

::

    from eoxserver.core.registry import Registry
    
    def dispatch(service_name, req):
    
        service = Registry.bind(
            hook = "services.owscommon.ServiceInterface",
            registry_values = {
                "services.owscommon.service": service_name
            }
        )
        
        response = service.handle(req)
        
        return response

* checks directories for classes derived from ExtensibleInterface base
  class
  
    * layer root directory
    * layer directories for implementations
    * plugins directory of distribution
    * plugins directory of instance

* registers implementations

    * only valid implementations, i.e.:

      * all key-value-pairs provided
      * valid values for all configuration parameters

* enables search for implementations using:

  * the interface hook
  * the registry key-value-pairs stored with the request
  * a test() function that returns if the implementation is applicable,
    e.g. for data, metadata and packaging formats

* tries to resolve conflicts

  * based on subclass and superclass settings

* settings for conflict resolution
* settings for enabling / disabling


.. _rfc2_dep_confl:

Dependencies and Conflicts
--------------------------

* dependencies

  * service extensions may depend on the service implementation and
    other service extensions, see :doc:`rfc3`

* conflict:

  * more than one implementation for the same hook and
    key-value-combination
  * more than one implementation is applicable for testing
    implementations
  * default, recessive, dominant, levels
  * more than on service extension may be applicable see :doc:`rfc3`

* conflict resolution

.. _rfc2_config:

Configuration Data Model and Admin Client Actions
-------------------------------------------------

* enabling and disabling using the admin

  * global settings
  * settings on a per-resource basis

Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
