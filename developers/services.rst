.. Services
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

.. _Services:

Services
========

This section deals with the creation of new Hervices handlers that allow to process OGC web service requests and are easily exposed via the :func:`ows 
<eoxserver.services.views.ows>` view.

Service Handlers are :class:`Components <eoxserver.core.component.Component>`
that at least implement the :class:`ServiceHandlerInterface
<eoxserver.services.ows.interfaces.ServiceHandlerInterface>`. For a Service
Handler to be fully accessible it is also necessary to implement either or both
of :class:`GetServiceHandlerInterface 
<eoxserver.services.ows.interfaces.GetServiceHandlerInterface>` and 
:class:`PostServiceHandlerInterface 
<eoxserver.services.ows.interfaces.PostServiceHandlerInterface>`.
For general information about Plugins/Components please refer to the 
:ref:`Plugins` documentation.


Initial Setup
-------------

Each service handler must provide the following:

  - The ``service`` the handler will contribute to
  - The ``versions`` of the ``service`` the handler is capable of responding to
  - The ``request`` of the ``service`` the handler is able to respond
  - a ``handle`` method that takes a :class:`django.http.HttpRequest` as 
    parameter

A service handler *can* provide an ``index``, which allows the sorting of
the handlers in a "GetCapabilities" response.

The following is an example handler for the "GetCapabilities" handler of the
fictional ``WES`` (Web Example Service):
::

    from eoxserver.core import Component, implements, ExtensionPoint
    from eoxserver.services.ows.interfaces import (
        ServiceHandlerInterface, GetServiceHandlerInterface,
        PostServiceHandlerInterface
    )

    class WESGetCapabilitiesHandler(Component):
        implements(ServiceHandlerInterface)
        implements(GetServiceHandlerInterface)
        implements(PostServiceHandlerInterface)

        service = "WES"
        request = "GetCapabilities"
        versions = ["1.0"]

        def handle(self, request):
            ...

.. note:: A word about versions: in EOxServer they are represented by the
   :class:`Version <eoxserver.services.version.Version>` class. It follows OGC
   conventions on treating versions. So for example the versions "1.0" and 
   "1.0.1" are considered equal. For our example this means that our handler
   will be able to respond to any request with a version "1.0.x".

