.. ConfigurationOptions
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2012 EOX IT Services GmbH
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


.. index::
    single: Supported Raster File Formats and Their Configuration  

.. _FormatsConfiguration:

Supported Raster File Formats and Their Configuration  
=====================================================

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

In this section, the EOxServer's handling of raster file
formats and OWS service specific format configuration is described. 

Format Registry 
---------------

Format registry is the list of raster file formats recognised by EOxServer. The
format registry holds definition of both the inputs and output formats. The each
format record defines the MIME-type (unique, primary key), library, driver, and
the default file extension. 

Currently, the EOxServer handle the raster data exclusively by the `GDAL
<http://www.gdal.org>`_ library. Thus, in principle, any raster file `format
supported by GDAL <http://www.gdal.org/formats_list.html>`_ library can be
supported by EOxServer. In particular, any raster file format readable by the
GDAL library (provided that the file structure can be decomposed to one
single-type, single- or multi-band image) can be used as the input and, vice
versa, any raster file format writeable by the GDAL library can used as the
output produced by WCS and WMS services. 

Any raster file format intended to be used by the EOxServer must be defined in
the format registry. The format registry provides unique mapping from
MIME-type to the (GDAL) format driver format. 

Format Configuration
--------------------

The format registry configuration is split in two parts (files): 

    * per-installation (mandatory) format configuration (set
      up automatically during the EOxServer installation) defining the default
      baseline set of formats
      (``<instal.path>/eoxserver/conf/default_formats.conf``). 
    * per-instance (optional) format configuration allowing customization of the
      format registry (``<instance path>/conf/formats.conf``). 

In case of conflicting format definitions, the per-instance configuration takes
the precedence. The both formats' configuration files share the same text file
format. 

The formats' configuration is a simple text file containing a simple list of
format definition. One format definition (record) per line. Each record is
then a comma separated list of following text fields:::

    <MIME-type>, <driver>, <file extension>

The mime type is used as the primary key and thus any repeated MIME-type will
rewrite the previous format definition(s) using this MIME-type.
The driver field should be in format ``GDAL/<GDAL driver name>``. To list
available drivers provided by your GDAL installation use following command:::
    
    gdalinfo --formats

The ``GDAL`` prefix is used as place-holder to allow future use of different
library back-end.  The file extension shall be written including the separating
dot ``.``.  Any leading or trailing white-characters as well as the empty lines
are ignored.  The ``#`` character is used as line-comment and any content
between this character and the end of line is ignored. 

An example format definition::: 

    image/tiff,GDAL/GTiff,.tif # GeoTIFF raster file format 

Since the list of supported drivers may vary for different installations of
the back-end (GDAL) library, the library drivers are checked by the EOxServer
ignoring any format definition requiring non-supported library driver. Any
invalid format record is reported to the EOxServer log. 
Further, the EOxServer checks automatically which of the library drivers are
'read-only', i.e., which cannot be used to produce output images, and
restricts these to be used for data input only. 

Web Coverage Service - Format Configuration 
-------------------------------------------

The list of the file formats supported by the *Web Coverage Service* (WCS) is
specified in the EOxServer's configuration (``<instance
path>/conf/eoxserver.conf``) in section ``serices.ows.wcs`` :::

    [services.ows.wcs]
    supported_formats=<MIME type>[,<MIME type>[,<MIME type> ... ]]

The supported WCS formats are specified as a comma-separated list of MIME-types.
The listed MIME-types must be defined in the format registry otherwise they will
be ignored. The read-only file formats will be ignored. 

The supported formats are announced through the WCS ``Capabilities`` and
``CoverageDescription`` (the output may vary based on the WCS version used).
The use of in invalid MIME-type (not listed among the supported formats) by the
``getCoverge()`` operation will lead to an error (OWS Exception). 

Web Coverage Service - Native Format Configuration 
--------------------------------------------------

The *native format* (as defined by `WCS 2.0.1 `[OGC 07-068r4]`_) is the default
raster file format produced by the ``getCoverage()`` operation in case of
missing explicit format specification. By default, the EOxServer sets the native
format to the format of the stored source data (source format), however, in
cases when the source format cannot be used ('read-only' source format) and/or
another default format is desired, the EOxServer allows configuration of the
WCS *native format* (``<instance path>/conf/eoxserver.conf``, section
``services.ows.wcs20``)::

    [services.ows.wcs20]
    default_native_format=<MIME-type>
    source_to_native_format_map=[<src.MIME-type,native-MIME-type>[,<src.MIME-type,native-MIME-type> ... ]]

The default *native format* option is used in cases when the source format
cannot be used (read-only) and not source to native format mapping. This option
must be always set to a valid format (GeoTIFF by default). The source to native
format mapping, as the name suggests, maps the (zero, one, or more) source
formats to a non-defaults native formats. The source formats are not restricted
to the read-only ones. This option accepts comma-separated list of MIME-type
pairs.   

Web Map Service - Format Configuration 
--------------------------------------

The list of the file formats supported by the *Web Map Service's* (WMS)
``getMap()`` operation is specified in the EOxServer's configuration
(``<instance path>/conf/eoxserver.conf``) in section ``serices.ows.wms``::

    [services.ows.wms]
    supported_formats=<MIME type>[,<MIME type>[,<MIME type> ... ]]

The supported WMS formats are specified as a comma-separated list of MIME-types.
The listed MIME-types must be defined in the format registry otherwise they will
be ignored. The read-only file formats will be ignored. 

The supported formats are announced through the WMS ``Capabilities`` (the output
may vary based on the WMS version used). 

References
----------

:[OGC 09-110r4]: http://www.opengeospatial.org/standards/wcs
