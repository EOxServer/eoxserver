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

:Author: Stephan Krause, Fabian Schindler
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

Basic Concepts
--------------

.. _fig_opclient_uml:
.. figure:: resources/rfc18/opclient_uml.png
   :align: center

   *The Operator Interface structure expressed in a UML class diagram.*

The Operator Interface shall be organized in so called Operator Components.
Operator Components correspond to groups of related packages and modules of
EOxServer or its extensions. The most important components at the moment
are :mod:`eoxserver.core` and :mod:`eoxserver.resources.coverages`.

An Operator Component bundles Actions and Views related to the specific
EOxServer component in the backend.

Actions provide an interface for operators to edit the system configuration
including the data and metadata stored in the database. Most Actions are
related to resources, e.g. coverages or Dataset Series.

In order to make the functionality of these Actions available, the Operator
Interface shall include Action Views. Action Views shall group actions and
information that are closely related to each other.

Each Operator Component may contain several Action Views. They represent a UI
for access to the actions in the backend. Several Actions may be attached to a
single Action View, and Actions may appear in several Action Views.

For example, an Action View might show a list of Rectified Datasets with
basic metadata which allows to create and delete items. Creation and deletion
should each be modeled as Actions on the server side. Another Action View may
show the whole information for a single Rectified Dataset and include
forms and inputs to edit the metadata.

As far as possible, the Action Views should be composed of reusable Widgets.
Widgets consist of HTML and/or JavaScript. The aforementioned list of
Rectified Datasets, would be a typical example. It could be used also in the
Dataset Series View.

The core implementation of the Operator Interface shall provide reusable
components to build Widgets of (e.g. lists ...).

The communication between the Action Views and the underlying Actions should
be done via specific Interfaces. One REST-based interface shall be implemented
whiche shall allow to read data and metadata to be displayed, and one
RPC-based interface shall be implemented in order to trigger actions on the
server side.

Layout of the Operator Interface
--------------------------------

The entry point to the operator interface shall be a dashboard-like page. It is
envisaged to present a tab for each Operator Component; this tab shall
contain an overview of the Action Views the Operator Component exhibits.

So, on the client side, each Operator Component should provide:

* A name for the Operator Component that will be shown as caption of the
  tab
* the overview of the Operator Component, which links to the Action Views;
  as an alternative the Action Views may be contained in sub-tabs
* the Action Views
* the Widgets used in the Action Views
* a widget to be displayed on the entry page dashboard (optional)

Each visual representation of the Operator Interface, namely the entry page
dashboard, the Operator Component overview and the Action Views consist of:

* A Django HTML template
* A JavaScript View class
* A python class, entailing arbitrary information and "glue" between the other
  two parts

Only the third part needs to be adjusted when creating a new visual element,
for both the template and the JavaScript class defaults shall help with the
usage.

Implementing Components
-----------------------

To create a component, one simply shall have to subclass the abstract base
class provided by the Operator Interface API. It shall be easily adjustible
by using either a custom JavaScript view class or a different django template.

To further improve the handling of components, several default properties
within the subclass can be used, like title, name, description or others. Of
course default values shall be provided.

Components are registered by the Operator Interface API function
``register()``, which shall be sufficient to append it to the visualized
components.

Example Component definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example::

    import operatorinterface as operator

    class MyAComponent(operator.Component):
        dependencies = [SomeOtherComponent]
        name = "ComponentA"
        javascript_class = "App.Views.MyAComponentView"

    operator.site.register(MyAComponent)


Implementing Action Views
-------------------------

The implementation of action views is very much like the implementation of
components and should follow the same rules concerning JavaScript view classes
and django templates.

Additionally it shall have two fields named "Actions" and "Resources", each is 
a list of Action or Resource classes.

# TODO maybe adding widgets?

Example Action View definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example::

    class MyTestActionView(operator.ActionView):
        actions = [MyTestAction]
        name = "mytestactionview"
        javascript_class = "App.Views.MyTestActionView"


Implementing Actions
--------------------

Actions should not necessarily be accessible via RPC calls, but should be also
be used in other contexts, like CLI tools or others.

To create an Action, one simply has to subclass the abstract base class for
actions and to implement the functionality as methods for this class. Either
all public functions (as per `Python PEP 8 definition
<http://www.python.org/dev/peps/pep-0008/#method-names-and-instance-variables>`_)
are automatically registered or the method names to be exported have to be
manually declared in a class property.


Example Action definition
~~~~~~~~~~~~~~~~~~~~~~~~~

Example::

    class ProgressAction(BaseAction):
        name = "progressaction"
        permissions = [ ... ]
        
        def start(self):
            ...
        
        def status(self, obj_id):
            ...
        
        def stop(self, obj_id):
            ...

Implementing Resources
----------------------

Implementing Resources should be as easy as implementing actions. As with
Actions, Resources are implemented by subclassing the according abstract base
class and providing several options. The only mandatory arguments shall be the
Django model to be externalized, optional are the permissions required for this
resource, maybe means to limit the acces to read-/write-only (maybe coupled
to the provided permissions) and the inc-/exclusion of model fields.

Example Resource definition
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example::

    class MyResource(ModelResource):
        model = MyModel
        exclude = ( ... )
        include = ( ... )
        permissions = [ ... ]


Required Components
-------------------


# TBD



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

On the server side, the Django framework shall be used to provide the basic
functionality of the Operator Interface including specifically the URL setup,
HTML templating and request dispatching.

To help publishing RESTful resources, the django extension `Django REST
framework <http://django-rest-framework.org/>`_ can be used. It provides a
rather simple, yet customizeable access to database model. It also supports
user authorization as required in the chapter `Access Controll`_.

To provide the RPC interface, there are two possibilities. The first is a
wrapped setup of the `SimpleXMLRPCServer module
<http://docs.python.org/library/simplexmlrpcserver.html>`_, which would
represent an abstraction of the XML to the actual entailed data and the
dispatching of registered functions. As the module is already included in the
standard library of recent Python versions, this approach would not impose an
additional dependency. A drawback is the missing user authorization, which has
to be implemented manually. Also, this method is only suitable for XML-RPC,
which is more verbose than its JSON counterpart.

The second option would be to use a django extension framework, e.g
`rpc4django <http://davidfischer.name/rpc4django/>`_. This framework eases the
setup of RPC enabled functions, provides user authorization an is agnostic to
the RPC protocol used (either JSON- or XML-RPC).

On the client side, several JavaScript libraries are required. For DOM
manipulation and several utility functions `jQuery <http://jquery.com/>`_ and
`Underscore <http://underscorejs.org/>`_ are beeing used. To implement a
working MVC layout, `Backbone <http://backbonejs.org/>`_ is suggested. This
library also abstracts the use of REST resources.

For calling RPC functions and parsing the output, the library `rpc.js
<https://github.com/westonruter/json-xml-rpc>`_ is required. It adheres to
either the JSON-RPC or the XML-RPC protocol.

################## OLD

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
