.. EOxServer Developers' Guide
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

.. _EOxServer Developers' Guide:

EOxServer Developers' Guide
===========================

The Developers' Guide is intended for people who want to use EOxServer
as a development framework for geospatial services, or do have to
extend EOxServer's functionality to implement specific data and metadata
formats for instance.

Users of the EOxServer software stack please refer to the 
:ref:`EOxServer Users' Guide`. Users range from administrators installing and 
configuring the software stack and operators registering the available *EO 
Data* on the *Provider* side to end users consuming the registered *EO Data* 
on the *User* side.

.. figure:: ../users/images/Global_Use_Case.png
   :align: center

.. toctree::
   :maxdepth: 3
   
   basics
   core
   data_model
   plugins
   services
   data_formats
   metadata_formats
   autotest
   soap_proxy
   handling_coverages
   modules
   testing

.. TODO
   processes
