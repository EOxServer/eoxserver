.. Webclient Interface
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Fabian Schindler <fabian.schindler@eox.at>
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

.. _webclient:

The Webclient Interface
=======================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

The webclient interface is an application running in the browser and provides a
preview of all Datasets in a specified Dataset Series. It uses an
`OpenLayers <http://openlayers.org/>`_ display to show a WMS view of the
datasets within a map context. The background map tiles are provided by
`OSGeo <http://www.osgeo.org/>`_.

It can further be used to provide a download mechanism for registered datasets.


Enable the Webclient Interface
------------------------------

To enable the webclient interface, several adjustments have to be made to the
instances `settings.py` and `urls.py`.

First off, the `eoxserver.webclient` has to be inserted in the `INSTALLED_APPS`
option of your `settings.py`. As the interface also requires several static
files like style-sheets and script files, the option `STATIC_URL` has to be set
to a path the webserver is able to serve, for example `/static/`. The static
media files are located under `path/to/eoxserver/webclient/static`.

To finally enable the webclient, a proper URL scheme has to be set up in
`urls.py`. The following lines would enable the index and the webclient view
on the URL `www.yourdomain.com/client`.
::

    urlpatterns = patterns('',
        ...
        (r'^client/$', 'eoxserver.webclient.views.index'),
        (r'^client/(.*)', 'eoxserver.webclient.views.webclient'),
        ...
    )

.. _configuration-options-label:

Available configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Optionally some configuration settings can be set in the "eoxserver.conf"
config file. These settings have to be put into the "webclient" section:
::

    preview_service=...
    outline_service=...
    preview_url=...
    outline_url=...

The `preview_...` settings defined the settings for the preview layer, showing
an actual RGB representation of the registered datasets, whereas the
`outline_...` settings are used for displaying the footprint of all registered
datasets.

The `..._service` parameter is used to define the service type used to retrieve
the image tiles displayed on the map. Currently, "wms" and "wmts" are supported
and "wms" is the default.

The `..._url` parameter defines the URL of the service providing the image
tiles. This configuration defaults to the configuration given for the
"http_service_url" setting in the "services.owscommon" section.

Using the webclient interface
-----------------------------

The webclient interface can accessed via the given URL in `urls.py` as described
in the above instructions, whereas the URL `www.yourdomain.com/client` would
open an index view, displaying links to the webclient for every dataset series
registered in the system. To view the webclient for a specific dataset series,
use this URL: `www.yourdomain.com/client/<EOID>` where `<EOID>` is the EO-ID of
the dataset series you want to inspect.

.. _fig_webclient_autotest:
.. figure:: images/webclient_autotest.png
   :align: center

   *The webclient showing the contents of the autotest instance.*

The map can be panned with via mouse dragging or the map-moving buttons in the
upper left of the screen. Alternatively, the arrow keys can be used. The
zoomlevel can be adjusted with the mouse scrolling wheel or the zoom-level
buttons located directly below the pan control buttons.

A click on the small "+" sign on the upper right of the screen reveals the
layer switcher control, where the preview and outline layers of the dataset
series can be switched on or off. By default, the preview layer is switched
off and only the outlines layer is visible.

In the upper center the EOxServer panel can be seen. It is used to select
temporal and spatial subsets for the dataset series.

The slider in the middle is used to select the spatial subset for datasets. The
left slider handle determines the minimum date boundary and the right one the
maximum date boundary for datasets to be displayed.

While moving, the value of the minimum and maximum date can be viewed in the
first tab, "Date/Time". There, it can also be adjusted manually, either as a
text input or via a date-picker widget. For extra fine-grained queries, the
minimum and maximum time values can be adjusted.

Once the date/time has changed from either the slider or the input fields, the
map is updated with the new parameters. The results varies, depending on the
background map viewing service used, as WMTS services simply ignore the time
parameter. If WMS services are configured, only datasets should be visible that
are within the given date/time slice. Please refer to
:ref:`configuration-options-label` for detailed information.

Hidden under the second tab are controls for configuring the bounding box. The
bounding box can either be entered manually with the input fields or drawn on
the map once the "Draw BBOX" function is activated. The bouning box marker and
the input values are tied together, a change on one affects the other.

Unlike the date/time selection, the bounding box has no affect on the preview
or the outlines visible. It is only used for the offering of coverages at the
final Download of data.

The "Download" dialog is shown after the "Download" button in the EOxServer
panel is clicked. It displays a list of all datasets matching the give spatial
and temporal subsets. If no datasets with the given parameters were found, an
error message is shown.

Each coverage can be (de)selected using the checkbox. Only checked datasets
will be downloaded when the "Start Download" button is clicked.

The meaning of the size input fields depends on the actual type of the dataset.
Rectified datasets can be scaled to the given size after all subsets are
applied. Referencable datasets cannot be scaled, and so the size input fields
only hint the overall (not subsetted) size of the raster data.

The multi-select box on the right displays the bands of the range type of the
dataset. Here, the single bands can be (de)selected.

Once the "Start Download" Button is clicked, all selected coverages with the
given spatial and temporal subsets and all given parameters are downloaded. The
actual behavior depends on the used browser, commonly a save file dialog
is displayed.
