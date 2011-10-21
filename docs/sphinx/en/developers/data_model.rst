.. Data Model Overview

Data Model
==========

The core resources in EOxServer are coverages, more precisely GridCoverages. 
The EOxServer data model adopts and strongly relates to the data model from 
EO-WCS (OGC 10-140) as shown below in :ref:`fig_eo-wcs_data_model`.

.. _fig_eo-wcs_data_model:
.. figure:: images/EO-WCS_Data_Model.png
   :align: center

   *EO-WCS Data Model from OGC 10-140*


EOxServer Core
--------------

:ref:`fig_model_core` below shows the data model of the EOxServer core.

.. _fig_model_core:
.. figure:: images/model_core.png
   :align: center

   *EOxServer Data Model for the Core*

Data Integration Layer
----------------------

:ref:`fig_model_coverages` below shows the data model of the coverage resources.
Note the correlation with the EO-WCS data model as shown above.

.. _fig_model_coverages:
.. figure:: images/model_coverages.png
   :align: center

   *EOxServer Data Model for Coverage Resources*

Data Access Layer
-----------------

:ref:`fig_model_backends` below shows the data model of the back-ends layer.

.. _fig_model_backends:
.. figure:: images/model_backends.png
   :align: center

   *EOxServer Data Model for Back-ends*
