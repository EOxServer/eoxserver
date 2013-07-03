.. Module eoxserver.core.interfaces
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
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

.. _module_core_interfaces:

Module eoxserver.core.interfaces
================================

.. automodule:: eoxserver.core.interfaces

Introduction
------------

Interfaces play a key role in the extension mechanism of EOxServer which is
described in :doc:`/en/rfc/rfc1` and :doc:`/en/rfc/rfc2`. Extensibility is one
of the main features of the EOxServer architecture. Based on its generic core,
the different EOxServer layers shall be able to dynamically integrate additional
behaviour by defining interfaces that can be implemented by different modules
and plugins.

The module :mod:`eoxserver.core.registry` implements the actual extension
mechanism based on the capabilities of this module.

:mod:`eoxserver.core.interfaces` is completely independent from the EOxServer
extension mechanism on the other hand. Actually, due its generic nature, it is
completely independent from the EOxServer project itself and can be used in any
other situation where interface declaration and validation might be of interest.

How does it work?
~~~~~~~~~~~~~~~~~

An interface is an ordinary Python class deriving from the :class:`Interface`
class or one of its descendants. Interfaces contain method declarations. As
there is no way to declare method signatures without implementing the method in
Python an alternative solution has been chosen: declarations are made using
class variables that contain instances of the :class:`Method` class provided
by this module.

Interfaces inherit declarations from their parents. They even support multiple
inheritance. This allows to extend and combine existing interfaces in a
straightforward way comparable to the way interfaces are declared in Java
for instance.

The :class:`Method` constructor accepts an arbitrary number of input argument
declarations as well as an optional output declaration. Similar to method
declarations, argument declarations are made using instances of special classes
derived from the :class:`Arg` base class.

Implementations can be derived from new-style classes which we will call
*implementing class* in this document. Each interface has an
:meth:`~Interface.implement` method that accepts an implementing class and
returns an implementation (which is a Python class deriving from the
implementing class). An exception will be raised when calling
:meth:`~Interface.implement` with an implementing class that does not validate,
e.g. because methods do not match the declarations made in the interface.

As a development tool, :mod:`eoxserver.core.interfaces` supports runtime
validation of interfaces. This allows to check for consistency of the
argument types sent by a calling object to an implementation instance with the
argument type declaration in the interface.

.. _module_core_interfaces_intf_decl:

Interface Declaration
---------------------

As mentioned in the introduction, interfaces are ordinary Python classes
deriving from :class:`Interface` or one of its descendants. Method declarations
are made using the :class:`Method` class.

The :class:`Method` constructor accepts an arbitrary number of argument
declarations as positional arguments as well as an optional output declaration
stated with the ``returns`` keyword argument. Argument and output declarations
are made using instances of the :class:`Arg` class and its descendants.

All argument types take a name as input. For an implementation to validate, this
must be a valid Python argument name (except for output declarations).
Furthermore, all argument types accept a ``default`` keyword argument that
defines a default value for the argument and marks it as optional.

Let's see an example::

    from eoxserver.core.interfaces import *

    class SomeInterface(Interface):
    
        f = Method(
            IntArg("x"),
            returns = IntArg("@return")
        )
    
    class AnotherInterface(Interface):
    
        g = Method(
            FloatArg("x", default=0.0),
            returns = FloatArg("@return")
        )
    
    class SomeDerivedInterface(SomeInterface, AnotherInterface):
    
        pass

In this short code snippet, we declare three interfaces. Implementations of
:class:`SomeInterface` shall have a method :meth:`f` that takes an integer
``x`` as an argument and returns an integer value. Implementations of
:class:`AnotherInterface` shall have a method :meth:`g` that takes a float
``x`` as an argument and returns a float value. :class:`SomeDerivedInterface`
inherits from both, so implementations of that interface must exhibit
:meth:`f` and :meth:`g` methods that work in the way described above.

Interfaces can have an interface configuration, i.e. a class variable called
``INTERFACE_CONF`` which contains a dictionary of configuration values. So far, 
only ``runtime_validation_level`` is supported, see
:ref:`module_core_interfaces_validation`.

.. _module_core_interfaces_impls:

Implementations
---------------

Implementations will be constructed from implementing classes using the
:meth:`~Interface.implement` method of the interface. This method will
validate the implementating class and return an implementation class that
inherits from the input class.

The implementation exhibits exactly the  behaviour of the implementing class.
Internally, the implementation may differ considerably from the implementing
class, especially if you use runtime validation capabilities, see under
:ref:`module_core_interfaces_descriptors` below.

Note that you can define any number of additional public or private methods
in an implementing class which will be present in the implementation as well.
You cannot omit any method or argument declared in the interface, though, as
the implementing class would not validate then.

Now for an example of implementations of the interface defined above in
section :ref:`module_core_interfaces_intf_decl`::

    class SomeImplementingClass(object):
    
        def f(self, x):
            return int(x)
    
    class AnotherImplementingClass(object):
    
        def g(self, x=0.0):
            return float(x)
    
    class AThirdImplementingClass(SomeImplementingClass):
    
        def g(self, x=0.0):
            return 2.0 * float(x)
            
    SomeImplementation = SomeInterface.implement(SomeImplementingClass)
    AnotherImplementation = AnotherInterface.implement(AnotherImplementingClass)
    AThirdImplementation = SomeDerivedInterface.implement(AThirdImplementingClass)
    
As you can see, :class:`SomeImplementingClass` implements
:class:`SomeInterface`. The required method :meth:`f` is present and has the
correctly named input parameters and even enforces that the output has the
correct type, though this can only be validated using runtime validation (not
when creating the implementation).

In :class:`AnotherImplementingClass` you see an example for default value
declaration.

:class:`AThirdImplementingClass` is interesting in two ways. First, it
derives from :class:`SomeImplementingClass` inheriting its :meth:`f` method.
This way you can build hierarchies of implementing classes similar to the
way you can build hierarchies of interfaces. Second, you see that the
implementation hierarchies may deviate from the interface hierarchies; instead
of inheriting the :meth:`g` method from :class:`AnotherImplementingClass`
an alternative version of this method is implemented that again matches the
interface declaration.

If you have an implementation and want to know which interface it implements
you can use the magic ``__ifclass__`` attribute::

    >>> AThirdImplementingClass.__ifclass__.__name__
    'SomeDerivedInterface'
    
Implementing classes can define an implementation configuration, i.e. class
variable called ``IMPL_CONF`` that contains a dictionary of configuration
settings. So far, only ``runtime_validation_level`` is supported, see
:ref:`module_core_interfaces_validation`.

.. _module_core_interfaces_validation:

Validation of Implementations
-----------------------------

The validation of implementations is performed in two ways:

* at class creation time
* at instance method invocation time ("runtime")

Validation at class creation time checks:

* if all methods declared by the interface are implemented
* if the method arguments of the interface and implementation match in the
  sense that

  * all declared arguments are present
  * the names and the order of the arguments in the implementation match
    the interface declaration
  * the optional default value declarations match

Class creation time validation is performed unconditionally.

Instance method invocation time ("runtime") validation is optional. It
can be triggered by the ``runtime_validation_level`` setting. There are three
possible values for this option:

* ``trust``: no runtime validation
* ``warn``: argument types are checked against interface declaration;
  in case of mismatch a warning is written to the log file
* ``fail``: argument types are checked against interface declaration;
  in case of mismatch an exception is raised
  
The ``runtime_validation_level`` option can be set

    * globally (in the configuration file, 
      see :ref:`module_core_interfaces_reader`)
    * per interface (in the ``INTERFACE_CONF`` dictionary)
    * per implementation (in the ``IMPL_CONF`` dictionary)

where stricter settings override weaker ones. 

.. note::

  The ``warn`` and ``fail`` levels are intended for use
  throughout the development process. In a production setting ``trust``
  should be used.

Reference
---------

This documentation concentrates on the public methods of the involved classes.
Actually, there is only one public method you will need to invoke and that is
:meth:`Interface.implement`; all others are public only to
the extent that they are invoked by other objects defined in this module.
   
The implementation of :mod:`eoxserver.core.interfaces` involves some deep and
beautiful Python magic. We skip most of these details here, only in the
:ref:`module_core_interfaces_descriptors` sections you will find a reference to
some of it.

Interfaces
~~~~~~~~~~

.. autoclass:: Interface
   :members:

Methods
~~~~~~~

.. autoclass:: Method
   :members:

Arguments
~~~~~~~~~

.. autoclass:: Arg
   :members:
   
.. autoclass:: StrArg
   :members:
   
.. autoclass:: UnicodeArg
   :members:

.. autoclass:: StringArg
   :members:
   
.. autoclass:: BoolArg
   :members:
   
.. autoclass:: IntArg
   :members:
   
.. autoclass:: LongArg
   :members:
   
.. autoclass:: FloatArg
   :members:
   
.. autoclass:: RealArg
   :members:
   
.. autoclass:: ComplexArg
   :members:
   
.. autoclass:: IterableArg
   :members:
   
.. autoclass:: SubscriptableArg
   :members:
   
.. autoclass:: ListArg
   :members:
   
.. autoclass:: DictArg
   :members:

.. autoclass:: ObjectArg
   :members:

.. autoclass:: PosArgs
   :members:
   
.. autoclass:: KwArgs
   :members:

.. _module_core_interfaces_reader:

Config Reader
~~~~~~~~~~~~~

.. autoclass:: IntfConfigReader
   :members:

.. _module_core_interfaces_descriptors:

Descriptors
~~~~~~~~~~~

Descriptors are used to customize method access in Python. They are some of the
more advanced Python language features; if you want to know more about them,
please refer to the `Python Language Reference
<http://docs.python.org/reference/datamodel.html#invoking-descriptors>`_.

.. autoclass:: ValidationDescriptor
   :members:

.. autoclass:: ValidationWrapper
   :members:

.. autoclass:: WarningDescriptor
   :members:

.. autoclass:: WarningWrapper
   :members:

.. autoclass:: FailingDescriptor
   :members:

.. autoclass:: FailingWrapper
   :members:

