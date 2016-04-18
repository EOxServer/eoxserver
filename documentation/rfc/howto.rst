.. RFC Guidelines
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
   single: RFC; RFC Guidelines

.. _rfc_howto:

Guidelines for Requests for Comments
====================================

:Author: Stephan Krause
:Date: 2011-02-19
:Last Edit: $Date$
:Discussion: http://eoxserver.org/wiki/DiscussionRfcTemplate

This document contains instructions for writing RFCs as well as a
template for RFCs. Please read it carefully before submitting your own
requests.

In this document the terms *shall*, *should* and *may* have a
normative meaning that is well known from software engineering and 
standards definition:

* *shall*: indicates an absolute requirement to be strictly followed
* *should*: indicates a recommended item
* *may*: indicates an optional item

Location of an RFC
------------------

The text of an RFC shall be located in the EOxServer SVN Trunk in the 
directory ``docs/en/rfc`` under the file name ``rfc<number>.rst``. It
will be published automatically on the Request For Comments site once
the documentation has been built anew.

Discussion Page
---------------

Once the RFC status has been moved to PENDING, it is required that
the authors create a discussion page for the RFC on the EOxServer Trac
Wiki. A :ref:`disc_template` is included below.

Structure of an RFC
-------------------

Heading
~~~~~~~

The page heading shall be in the format "RFC <number>: <title>".

Basic Information
~~~~~~~~~~~~~~~~~

The RFC shall start with a block containing the author(s) of the
request, the creation date, the date of the last edit and its status,
like in the following example:

  :Author: John Doe
  :Created: 2011-02-18
  :Last Edit: $Date$
  :Status: PENDING
  :Discussion: http://eoxserver.org/wiki/DiscussionRfcTemplate
  
Description of the RFC
~~~~~~~~~~~~~~~~~~~~~~

The first one or two paragraphs shall contain a short description of the
RFC. They should give a high-level overview of the propositions of the
request.
  
Introduction
~~~~~~~~~~~~

The first section of the RFC shall be called "Introduction". It should
contain a motivation for the RFC, describe the problem(s) the
RFC addresses and give an overview of the proposed solution. It should
contain forward references to the sections where specific items are
discussed further where applicable.

Keep the introduction short and simple! It is not the place to go into
the details, this should be done in the sections of the body of the RFC.

Body of the RFC
~~~~~~~~~~~~~~~

The body of the RFC starts right after the introduction. It may start
with a more in-depth description of the motivation for the RFC and the
problems to address if this cannot be discussed exhaustively in the
introduction. Following that the proposed solution should be described
in detail and as vividly as possible.

Use examples, tables and pictures where appropriate! Use references to
external resources, to the documentation, to other RFCs, to the
EOxServer Trac or to the source code.

The body of the RFC may be contained in one section or structured
in sections, subsections and subsubsections or even further. 

Voting History
~~~~~~~~~~~~~~

The penultimate section of the RFC shall be called "Voting History". It
shall contain the records of the votes held on subject of the RFC. As
long as the RFC is in preparation or pending, the section body shall be
"N/A". Example of a voting record:

  :Motion: To accept RFC 1
  :Voting Start: 2011-03-01
  :Voting End: 2011-03-02
  :Result: 3 ACCEPTED, 0 PENDING

Traceability
~~~~~~~~~~~~

The last section of the RFC shall be called "Traceability". It shall
contain references to the requirements that have motivated the request
if applicable. Furthermore, if the request was accepted, it shall
contain references to the tickets in the EOxServer Trac system that
concern its implementation. Example:

  :Requirements: O3S_CAP_100
  :Tickets: #1
  
Where possible, the requirements and tickets shall be hyperlinked to the
respective resources (e.g. requirements document, requirement tracing
system, EOxServer Trac).

Template for RFCs
-----------------

Here is a template you should use for your RFCs. Please replace the
items in brackets <> by the appropriate text::

  .. _rfc_<number>:

  RFC <number>: <title>
  =====================

  :Author: <author name>
  :Created: <date when RFC was created: YYYY-MM-DD>
  :Last Edit: <date of last edit: YYYY-MM-DD, please use subversion keyword "Date">
  :Status: <one of: IN PREPARATION, PENDING, WITHDRWAWN, VOTING ACTIVE,
            ACCEPTED, REJECTED, POSTPONED, OBSOLETE>
  :Discussion: <external link to discussion page on EOxServer Trac>

  <short description of the RFC>

  Introduction
  ------------
  
  <Mandatory. Overview of motivation, addressed problems and proposed
   solution>
   
  <Section title>
  ---------------
  
  <Any number of sections may follow.>
  
  <Subsection title>
  ~~~~~~~~~~~~~~~~~~
  
  <They may have any number of subsections.>
  
  <Subsubsection title>
  ^^^^^^^^^^^^^^^^^^^^^
  
  <And even subsubsections.>
  
  Voting History
  --------------
  
  <Voting Records or "N/A">
  
  :Motion: <Text of the motion>
  :Voting Start: <YYYY-MM-DD>
  :Voting End: <YYYY-MM-DD>
  :Result: <Result>
  
  Traceability
  ------------
  
  :Requirements: <links to requirements or "N/A">
  :Tickets: <links to tickets or "N/A">

.. _disc_template:

Template for RFC Discussion Pages
---------------------------------

RFC Discussion pages shall have the URL
``http://eoxserver.org/wiki/DiscussionRfc<number>``. They shall be
referenced on the page http://eoxserver.org/wiki/RfcDiscussions.

::

  = Discussion Page RFC <number>: <title> =

  '''RFC <number>:''' [<link>]

  == Template Comment ==

  <comment text>

  ''Author: <author name> | Created: <date and time of creation: YYYY-MM-DD HH:MM:SS>''
  ----

  == Discussion ==
