.. Plugins
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

.. _Plugins:

Plugins
=======

EOxServer uses a plugin framework to extend or alter the built-in
functionality. The plugin system is based on `trac's Component Architecture
<http://trac.edgewall.org/wiki/TracDev/ComponentArchitecture>`_. We copied the
relevant file as :mod:`eoxserver.core.component` to not add the full trac
framework as a dependency.

EOxServer plugins are classes that inherit from
:class:`eoxserver.core.component.Component`. Each component can implement any
number of interfaces, which are usually skeleton classes to provide
documentation of what methods and fields each implementation shall provide.
In this architecture, interfaces are just informative and allow the runtime
binding via :class:`eoxserver.core.component.ExtensionPoint`.

All plugins are self-registering, which means the module containing the
component just needs to be imported through any kind of import mechanism and,
voilà, the component is registered and ready for use.


Important
---------

Components should not be created manually, but only be retrieved via an
:class:`eoxserver.core.component.ExtensionPoint`. This further implies that
the :meth:`__init__` method shall not take any arguments, as instance creation
is out of the reach.

Additionally, :class:`Component` instances are never destroyed and shared
among different threads, so it is highly advised to not store any data in the
:class:`Component` itself.

Loading modules
---------------

EOxServer provides mechanisms to conveniently load modules and thus
registering all entailed plugins. This is done via the :obj:`COMPONENTS` setting in your instances :file:`settings.py`.

This setting must be an iterable of strings which follow the dotted python
module path notation, with two exceptions:

 - Module paths ending with ".*" will import all modules of a package.
 - Paths ending with ".**" will do the same, with the exception of doing so
   recursively.

E.g: :obj:`"eoxserver.services.ows.**"` will load all subpackages and modules of the :mod:`eoxserver.services.ows` package. (This is an easy way to enable
all OWS services, by the way).

To only enable WMS in version 1.3 you could use the following import line:
:obj:`"eoxserver.services.ows.wms.v13.*"`. If you only want to only enable
specific requests (for whatever reason) you'd have to list their modules
seperately.

The EOxServer instance :file:`settings.py` template is already preconfigured
with the most common components modules.


Example
-------

The following demonstrates the use of the component architecture in a
simplified manner:

In :mod:`myapp/interfaces.py`:
::

    class DataReaderInterface(object):
        "Interface for reading data from a file."
        def read_data(self, filename, n):
            "Read 'n' bytes from the file 'filename'."

In :mod:`myapp/components.py`:
::

    from eoxserver.core.component import Component, implements
    from myapp.interfaces import DataReaderInterface

    class BasicDataReader(Component):
        "Reads data from the file with the built-in Python functionality."

        implements(DataReaderInterface)

        def read_data(self, filename, n):
            with open(filename) as f:
                return f.read(n)

We can now use this component the following way in :mod:`myapp/main.py`:
::

    from myapp.interfaces import DataReaderInterface

    class App(object):
        data_readers = ExtensionPoint(DataReaderInterface)

        def run(self, filename):
            if not self.data_readers:
                raise Exception("No data reader implementation found.")

            print(data_readers[0].read_data(filename))

In the "myapp/interfaces.py" we declare an interface for "data readers". The
only method implementations of this interface shall provide is the
:meth:`read_data` method. In the "myapp/components.py" we provide a simple
implementation of this interface that uses built-in functionality to open a
file and read a data. Please not the `implements(DataReaderInterface)` which
declares that this component implements a specific interface.

In the "myapp/main.py" we declare a class that actually tries to find an
implementation of the :class:`DataReaderInterface` and invoke its
:meth:`read_data` method. In this case we only use the first available
implementation of the interface, in other cases it might make sense to loop
over all, or search for a specific one that satisfies a condition.
