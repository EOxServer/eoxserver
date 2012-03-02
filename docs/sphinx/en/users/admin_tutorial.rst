.. Administration Web Application Tutorial
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

.. index::
   single: Administration Web Application Tutorial
   single: Administration Web Application

.. _Administration Web Application Tutorial:

Administration Web Application Tutorial
=======================================

EOxServer can handle two types of datasets: (1) **Rectified Grids** and (2)
**Referenceable Grids** where (1) are having a regular spacing in projected or
geographic CRS and (2) are not rectified, but are associated with (one or more)
coordinate transformation which relate the image or engineering CRS to a
projected or geographic CRS.

Grids or datasets can be organized in **Stitched Mosaics** if they are
homogeneous or in **Dataset Series** if they are heterogeneous. In other words a
DEM being shipped in multiple files integrating seamlessly in a bigger dataset
(like the freely available SRTM dataset from NASA) can be organized in a
Stitched Mosaic. Multiple datasets with spatial and/or temporal overlappings can
be organized in a Dataset Series. Furthermore multiple Stitched Mosaics can also
be organized in Dataset Series.

In addition to register data from **Local Stores** it is also possible to
add data from an external **FTP storage** or from a **rasdaman** database.

[SCHI2011]_

Creating a custom Range Type
----------------------------

Before registering any data in EOxServer some vital information on the datasets
has to be provided. Detailed information regarding the kind of data stored can
be defined in the Range Type. A Range Type is a collection of bands which
themselves are assigned to a specifig Data Type.

A simple standard PNG for example holds 4 bands (RGB + Alpha) each of them able
to store 8 bit data. Therefore the Range Type would have to be defined with four
bands (red, green, blue, alpha) each of them having 'Byte' as Data Type.

In our example we use the reduced MERIS RGB data coming in the autotest
directory. gdalinfo provides us with the most important information:
::

    [...]
    Band 1 Block=541x5 Type=Byte, ColorInterp=Red
    Band 2 Block=541x5 Type=Byte, ColorInterp=Green
    Band 3 Block=541x5 Type=Byte, ColorInterp=Blue

First, we have to define the bands by clicking "add" next to "Bands" in the 
Admin interface. In "Name", "Identifier" and "Description" you can enter the
same content for now. The default "Definition" value for now can be
"http://www.opengis.net/def/property/OGC/0/Radiance". "UOM" stands for "unit of
measurement" which in our case is radiance defined by the value "W.m-2.Sr-1".
For displaying the data correctly it is recommended to assign the respective
value in "GDAL Interpretation". NoData values can be defined by adding a
"Nilvaluerecord". (see screenshot)

.. _fig_admin_app_01_add_band:
.. figure:: images/admin_app_01_add_band.png
   :align: center

.. _fig_admin_app_02_create_band1:
.. figure:: images/admin_app_02_create_band1.png
   :align: center

.. _fig_admin_app_03_create_band2:
.. figure:: images/admin_app_03_create_band2.png
   :align: center

After adding also the green and blue band we can proceed defining the Range
Type. After providing the new Range Type with a name you will have to assign a
Data Type of all data. In our case we select "Byte". Below we now have to add
our three Bands by clicking on the "+" icon. The important part here is to
assign each Band it's respective number ('1' for red and so on). (see
screenshot)

.. _fig_admin_app_04_add_rangetype:
.. figure:: images/admin_app_04_add_rangetype.png
   :align: center

Linking to a Local Path
-----------------------

Click "Add" on "Local paths" and paste the desired local directory where your
data is. Make sure the apache system user has read acces!

..
  # Linking to a FTP Storage
  # ------------------------
  # TBD

..
  # Linking to a rasdaman Storage
  # -----------------------------
  # TBD

Creating a Data Package
-----------------------

A **Data Package** consists of an GDAL-readable image file and a corresponding
XML metadata file using the WCS 2.0 Earth Observation Application Profile
(EO-WCS).

.. _fig_admin_app_05_data_package:
.. figure:: images/admin_app_05_data_package.png
   :align: center

..
  # Adding a single Rectified Dataset
  # ---------------------------------
  # TBD

Adding Data Sources
----------------------------

After adding a Local Path or location (pointing to a single directory, not a
specific file) you can combine this with a search pattern and create a Data
Source. A viable search pattern would be something like "*.tif" to add all TIFF
files stored in that directory. Please note that in this case, every TIFF needs
a XML file with the exact same name holding the EO-Metadata.

.. _fig_admin_app_06_add_data_source:
.. figure:: images/admin_app_06_add_data_source.png
   :align: center

.. 
  # Creating a Stitched Mosaic
  # --------------------------
  # TBD

Creating a Dataset Series
-------------------------

A Dataset Series can contain one or more Stitched Mosaics, a time series of
datasets or a collection of datasets. A Dataset Series therefor has its own
metadata entry with respect to the metadata of its containing datasets.

.. _fig_admin_app_07_add_dataset_series:
.. figure:: images/admin_app_07_add_dataset_series.png
   :align: center

.. [SCHI2011] Schiller C., S. Meissl et al., Introducing WCS 2.0, EO-WCS, and Open Source implementations (MapServer, rasdaman, and EOxServer) enabling the Online Data Access to Heterogeneous Multidimensional Satellite Data.
