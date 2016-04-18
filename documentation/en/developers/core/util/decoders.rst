.. Module eoxserver.core.util.decoders
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

.. _module_core_util_decoders:

Module eoxserver.core.util.decoders
===================================

.. automodule:: eoxserver.core.util.decoders

The module documentation starts with a bit on type definitions in the
schemas used by :class:`~.KVPDecoder` and :class:`~.XMLDecoder`.

Schemas
-------

EOxServer parameter decoders use schemas to define how to obtain the
values for given parameter names or keys; these schemas are defined as
Python dictionaries which follow certain rules. The basic structure of
a schema is as follows::

    PARAM_SCHEMA = {
        "<parameter_name>": {
            "<location_parameter>": "<location>",
            "<type_parameter>": "<type_definition>",
            ["<optional_parameter>": <optional_value>, ...]
        }
    }

where

* ``parameter_name`` denotes the name that can be used to retrieve the
  parameter value in calls to :meth:`~.Decoder.getValue` or 
  :meth:`~.Decoder.getValueStrict`,
* ``location_parameter`` denotes the name defined by the concrete
  decoder implementation for the location parameter, e.g. ``kvp_key``
  for KVP Decoders,
* ``location`` denotes the location string which must be provided by the
  developer in a format defined by the decoder implementation, e.g.
  an XPath expression for XML Decoders,
* ``type_parameter`` denotes the name defined by the concrete decoder
  implementation for the type parameter, e.g. ``kvp_type`` for KVP
  decoders
* ``type_definition`` denotes a type definition string formed according
  to the rules below to be provided by the developer,
* optional parameters may be defined by the decoder implementations.

Type definition strings have a common format. They consist of a basetype
definition followed by an optional occurrence definition. The most
straightforward way is to simply define a parameter which is expected
to occur exactly once::

    "<base_type_name>"

The type of the return value is determined by the
``base_type_name`` you choose. Now that was easy.

For validation purposes you might want to add an occurrence definition.
This means you specify minimum and/or maximum expected occurrence for
the parameters. The call to :meth:`~.Decoder.getValue` and
"~.Decoder.getValueStrict` will fail if the actual occurrence of the
parameter is outside the bounds defined in the schema. A list will be
returned in case the defined maximum occurrence exceeds 1.

The occurrences are declared in square brackets following the
``base_type_name``::

    "<base_type_name>[<min_occ>:<max_occ>]"

The parameters ``min_occ`` and ``max_occ`` must be castable to integers
and will be translated to the expected minimum and maximum occurrences
respectively. This is the strictest form of occurrence definitions, but
there are shortcuts.

Omitting ``min_occ`` is allowed; minimum occurrence is then set to 0.
Omitting ``max_occ`` is allowed, meaning the occurrence is unbounded.
The occurrence definition may contain only a single occurrence value,
meaning the parameter is expected exactly ``occ`` times::

    "<base_type_name>[<occ>]"

And finally empty brackets mean arbitrary occurrence::

    "<base_type_name>[]"
    
.. important:: Occurrence definitions always refer to the occurrence of
   the parameter itself, and never to its content. For ``intlist``
   and similar base types they do not refer to the length of the
   parameter list! So ``intlist[2]`` does not denote a list of two
   integer values, but a list containing two lists of integer values
   each with arbitrary length.

Interfaces
----------

.. autoclass:: eoxserver.core.util.decoders.DecoderInterface
   :members:

Implementations
---------------

.. autoclass:: eoxserver.core.util.decoders.Decoder
   :members:
