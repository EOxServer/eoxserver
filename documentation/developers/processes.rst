.. Processes
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

.. _Processes:

Processes
=========

This section deals with the creation of new Processes to be exposed via the WPS
interface.

Processes are simply :class:`Components <eoxserver.core.component.Component>`
that implement the :class:`ProcessInterface
<eoxserver.services.ows.wps.interfaces.ProcessInterface>`. For general
information about Plugins/Components please refer to the :ref:`Plugins`
documentation.

Creating a new Process
----------------------

As we already mentioned, Processes are :class:`Components
<eoxserver.core.component.Component>`:
::

    from eoxserver.core import Component, implements
    from eoxserver.services.ows.wps.interfaces import ProcessInterface

    class ExampleProcess(Component):
        implements(ProcessInterface)
        ...

Apart from some optional metadata and a mandatory identifier, each Process has
specific input parameters and output items. Those can be of various formats and
complexity. Each input and output must be declared in the processes section.
Let's start with a simple example, using `LiteralData
<eoxserver.services.ows.wps.parameters.LiteralData>`_ inputs and outputs:
::

    from eoxserver.services.ows.wps.parameters import LiteralData

    class ExampleProcess(Component):
        implements(ProcessInterface)

        identifier = "ExampleProcess"
        title = "Example Title."
        metadata = {"example-metadata": "http://www.metadata.com/example-metadata"}
        profiles = ["example_profile"]

        inputs = [
            ("example_input", LiteralData(
                'example_input', str, optional=True,
                abstract="Example string input.",
            ))
        ]

        outputs = [
            ("example_output", LiteralData(
                'example_output', str,
                abstract="Example string output.", default="n/a"
            )),
        ]

        ...

:class:`LiteralData <eoxserver.services.ows.wps.parameters.LiteralData>`
inputs will always try to parse the input to the defined type. E.g: if you
defined your input type to ``float``, an error will be raised if the supplied
parameters could not be passed. On the other hand, all your outputs will be
properly encoded and even translated to a specific unit if requested. Your
execute function will not need to hassle with type conversions of any kind for
your inputs/outputs.

Now that we have defined a Process with metadata, inputs and outputs we can
start writing the ``execute`` method of our Process. Each input parsed before it
is passed to our ``execute`` method where it is mapped to a named parameter

Our ``execute`` method is expected to return either a normal Python object if
we only declared a single output, or a :class:`dict` of outputs where the
``keys`` are the names of our declared outputs:
::

    class ExampleProcess(Component):
        implements(ProcessInterface)

        ...

        inputs = [
            ("example_input", LiteralData(
                'example_input', str, optional=True,
                abstract="Example string input.",
            ))
        ]

        outputs = [
            ("example_output", LiteralData(
                'example_output', str,
                abstract="Example string output.", default="n/a"
            )),
        ]

        def execute(self, **inputs):
            outputs = {}
            outputs["example_output"] = "Echo '%s'" % inputs["example_input"]
            return outputs


Another often used type for Processes are :class:`BoundingBoxes
<eoxserver.services.ows.wps.parameters.BoundingBox>`. They are declared as
follows:
::

    from eoxserver.core import Component, implements
    from eoxserver.services.ows.wps.interfaces import ProcessInterface
    from eoxserver.services.ows.wps.parameters import (
        BoundingBoxData, BoundingBox
    )

    class ExampleProcess(Component):
        implements(ProcessInterface)

        ...

        inputs = [
            ("example_bbox_input", BoundingBoxData(
                "example_bbox_input", crss=(4326, 3857),
                default=BoundingBox([[-90, -180], [+90, +180]]),
            )),
        ]
        outputs = [
            ("example_bbox_output", BoundingBoxData(
                "example_bbox_output", crss=(4326, 0)
            )),
        ]
        ...

The third kind of input and output is :class:`ComplexData
<eoxserver.services.ows.wps.parameters>` which can come in various formats,
binary or textual representation and either raw or base64 encoding.
