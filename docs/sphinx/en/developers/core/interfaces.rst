.. Module eoxserver.core.interfaces

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

...

Interface Declaration
---------------------

Implementations
---------------

Validation of Implementations
-----------------------------

Reference
---------

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

Config Reader
~~~~~~~~~~~~~

.. autoclass:: IntfConfigReader
   :members:

Descriptors
~~~~~~~~~~~

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

