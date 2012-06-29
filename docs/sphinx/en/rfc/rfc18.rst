.. RFC 18
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
.. _rfc_18:

RFC 18: Operator Interface Architecture
=======================================

:Author: Stephan Krause
:Created: 2012-05-08
:Last Edit: $Date$
:Status: IN PREPARATION
:Discussion: n/a

The new Operator Interface of EOxServer shall become the main entrance point
for operators who want to administrate an EOxServer instance. The Web UI design
shall focus on usability and support for frequent administration tasks.

The architecture of the Operator Interface shall be modular and extensible in
order to accomodate for future extension and facilitate the maintenance of the
software.

Introduction
------------

At the moment operators have two possibilities to administrate an EOxServer
instance:

* Command Line Tools
* Administration Web Client

The current Administration Client implementation is based on the
:mod:`django.contrib.admin` package and very tightly coupled with the data
model of EOxServer. Whereas this approach has made the development
considerably easier it has several severe drawbacks with respect to usability
and safety of the system:

* the EOxServer data model is fairly complicated and handling it requires a deep
  understanding of the EO-WCS standard as well as Django concepts like model
  inheritance
* certain actions trigger long-running processing tasks on the server side that
  are so far hidden from the operators
* there is no support for asynchronous requests which would be the preferred
  method
* error reporting and status monitoring is only minimal
* the current Admin Interface allows to edit database records without checks
  for consistency; the danger of breaking the system unintentionally is quite
  high

Therefore a new web-based Operator Interface shall be designed that facilitates
the administration tasks. It shall be more usable in the sense that

* the design shall focus on frequent administration tasks rather than the data
  model
* the interface shall provide guidance for operators
* safety shall be increased by checking the consistency of input data and
  organizing the operator actions in a way that precludes unintentionally
  breaking the system
* the operator shall have an overview of the processing tasks going on in the
  backend

From the software point of view, the design shall focus on

* modularity and extensibility, thus preparing for future extensions of
  EOxServer and increasing maintainability
* reusing existing administration code like Coverage Managers
* separation of model, view and controller components where model and controller
  components should be concentrated on the server side and the view on the
  client side

Requirements
------------

The Operator Interface shall support the most frequent tasks for administration.
These include:

* registering a Dataset
* handling the Range Types
* creating a Dataset Series 
* creating a Stitched Mosaic
* deleting a Dataset, Dataset Series or Stitched Mosaic
* adding a Dataset to a Dataset Series or Stitched Mosaic
* removing a Dataset from a Dataset Series or Stitched Mosaic
* creating / adding / removing a data source to/from a Dataset Series or
  Stitched Mosaic 
* viewing the logs
* enabling / disabling of components
* user management

Structure of the Operator Interface
-----------------------------------

.. _fig_opclient_uml:
.. figure:: resources/rfc18/opclient_uml.png
   :align: center

   *The Operator Interface structure expressed in a UML class diagram.*

The Operator Interface shall be organized in so called Operator Components,
which represents a grouped set of user-interactions with the server. The
components are individually accessible via an URL and usually only one
component is visible at a time. A component may have dependencies to other
components to be registered prior to its visualization.

Each component allows access to a certain set of functionalites, called
Resources and Actions. Resources are data models accessed via a REST interface,
whereas Actions are methods to be executed on the server, either instantaneous
or over time.

To visualize Resources and Actions, each Component consists of Action Views
which manage a set of Actions and Resources. An Action View is responsible to
visualize data with widgets and perform required method calls as requested by
the user.

The communication between the Action Views and the underlying Actions and
Resources is operated via certain Interfaces, namely the REST and the RPC
interface. Interfaces are provided by the server via dynamically created URLs
within the Operator Interface with the help of pythons standard library
SimpleXMLRPCServer and the Django extension library django-rest-framework. The
interfaces are consumed by the JavaScript client using the rpc.js and the
Backbone.js libraries.

Each visual representation of the Operator Interface, namely the Components and
Action View, consists of three elements:

* A Django HTML template
* A JavaScript View class
* A python class, entailing arbitrary information and "glue" between the other
  two parts

Only the third part needs to be adjusted when creating a new visual element,
for both the template and the JavaScript class defaults shall help with the
usage.

Layout of Componets
-------------------


Required Components
-------------------


Access Controll
---------------

The Operator Interface itself, its Resources and its Actions shall only be
accessible for authorized users. Also, the Interface shall distinguish between
at least two types of users: administrative users and users that only have
reading permissions and are not allowed to alter data. The permissions shall
be able to be set fine-grained, on a per-action or per-resource basis.

It is proposed to use the Django buil-in auth framework and its integrations in
other software frameworks.


Configuration and Registration of Components
--------------------------------------------

On the server side, the Operator Interface is set up similar to the Djangos
built-in Admin Interface. To enable the Operator Interface, its app identifier
has to be inserted in the `INSTALLED_APPS` list setting and its URLs have to be
included in the URLs configuration file.

Also similar to the Admin Interface, the Operator Interface provides an
`autodiscover()` function, which sweeps through all `INSTALLED_APPS`
directories in search of a `operator.py` module, which shall contain the apps
setup of Components, Action Views, Actions and Resources.




Technologies Used
-----------------








* index page: dashboard?
* organisation: component -> action
* customization: look and feel
* widgets?
  * log viewer -> internal logging framework
  * confirmations
  * model views
  * use of ModelForm? -> probably not feasible if recurring to wrappers
  * WMS viewing widget
* interactive mode? -> future extension
* HTML or JavaScript?
  * Backbone.js?
  * link between client views and server
  * link between command line tools and client views?
  * how to integrate components and additional extensions
* core & extensions vs. universal plugging mechanism
* how to refer to data models
* access to the data model through wrappers and coverage managers
* is listing records also an action?
* integration with viewing service
* review of the interface/implementation model of EOxServer w.r.t. model etc.
* use of Django templates, forms?
* adaptation to changes in data model, interfaces
  * how to keep adaptation efforts minimal?
* security issues?
* integration with IDM?
* relation to admin interface?
  * abolish (in the long term)?
  * keep (as a database editing tool only)?
* read-only access for demonstration service?

JavaScript/AJAX based option
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Backbone.js
* JSON exchange interface
* asynchronous processing
* Advantages:
  * flexibility
  * high usability
  * rich client
* Disadvantages:
  * more difficult to implement
  * difficult to maintain
  * cannot reuse much of Django's web development framework

HTML based option
~~~~~~~~~~~~~~~~~

* RESTful
* Advantages:
  * easier to implement
  * reuse of Django templating system etc.
* Disadvantage:
  * static
  * long waiting times with risk of timeouts
  * low usability for long-running tasks

Combinations
~~~~~~~~~~~~

* mainly HTML based with JavaScript/AJAX elements

Interface
~~~~~~~~~

* JSON based
* RESTful
* single URL -> routes to others (extensibility)
* presentation models?
* actions

Questions
~~~~~~~~~

* How to integrate server and client?
  * REST?
* How rich<* Which frameworks to use on the client side?
  * jQuery
  * Backbone.js?
* How to model actions and bind them to views and interfaces?
* How to use Django templating capabilities?
* How to integrate asynchronous processing?
* Architectural prerogatives on server side?
* Changes to the core? ComponentManager and others ...
* Refactoring the coverage managers?
* Layout of components?
