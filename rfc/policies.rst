.. RFC Policies
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
   single: RFC; RFC Policies

.. _rfc_policies:

RFC Policies
============

:Author: Stephan Krause, Stephan Meißl
:Date: 2011-05-13

This document contains the policies that govern the life cycle of
Requests for Comments (RFCs). It may be changed by submitting an RFC for
discussion and vote following the provisions of this document.

In this document the terms *shall*, *should* and *may* have a
normative meaning, that is well known from software engineering and 
standards definition:

* *shall*: indicates an absolute requirement to be strictly followed
* *should*: indicates a recommendation
* *may*: indicates an option


Status of RFCs
--------------

Every RFC has a status. That status may be one of:

* **IN PREPARATION**: Some text for the RFC has been posted, but that is
  not the version to be submitted for discussion and voting. An RFC that
  has this status is still work in progress.
* **PENDING**: The text of the RFC has been submitted for discussion. It
  may still be altered by the RFC authors in order to reflect the state
  of the discussion.
* **WITHDRAWN**: The text of the RFC has been withdrawn.
* **VOTING ACTIVE**: The text of the RFC has been frozen and voting is
  going on.
* **ACCEPTED**: A vote has been held on the RFC and it has been
  accepted. Implementation has started.
* **REJECTED**: A vote has been held on the RFC and it has been
  rejected. The RFC is not going to be implemented and the discussion
  is closed.
* **POSTPONED**: A vote has been held on the RFC and it has been
  postponed to a later stage of development. The RFC may be reopened any
  time.
* **OBSOLETE**: A vote has been held on the RFC and it has been declared
  obsolete. It has been superseded by another RFC or it is not
  considered applicable any more.
  
The status IN PREPARATION may be declared by the authors of the
RFC. They may move it to PENDING once they consider it ready for
discussion and submission to a vote. Any further status changes shall
be declared according to the results of the discussion and the voting 
(see :doc:`rfc0`).

The following status changes are possible:

* from IN PREPARATION to PENDING, WITHDRAWN
* from PENDING to WITHDRAWN or via VOTING ACTIVE to ACCEPTED, REJECTED,
  POSTPONED
* from ACCEPTED via VOTING ACTIVE to PENDING, POSTPONED, OBSOLETE
* from POSTPONED to PENDING or via VOTING ACTIVE to ACCEPTED, REJECTED,
  OBSOLETE


Creation of RFCs
----------------

Any one who has write access to the EOxServer SVN may submit an RFC. It
shall obey the rules of the :doc:`howto`. The initial status of the
RFC is IN PREPARATION, lest the authors deem it to be mature for
discussion from the start, in which case they may submit it as PENDING. The 
RFC shall be assigned the next possible consecutive number.

When beginning work on an RFC the authors shall inform the PSC chair.

As long as the RFC is IN PREPARATION or PENDING, only the authors of the
RFC shall edit it. Anyone else who wants to contribute to the document
shall submit his or her text to the discussion page. The authors may
also decide to let him or her become a co-author who has all the rights
of an author.

Authors may choose to support their RFC by implementing the needed changes 
and committing them to a subdirectory of the sandbox directory for review.


Discussion Pages
----------------

Any RFC, especially those still IN PREPARATION, shall have a discussion page
on the EOxServer Trac Wiki (http://eoxserver.org/wiki). The design
and the location of the discussion page is detailed in the :doc:`howto`.

The discussion page may include links to preliminary implementations 
which have been committed to a sandbox subdirectory.


Pending RFCs
------------

PENDING RFCs are submitted for discussion. They may still be edited to
reflect the state of the discussion or to correct errors. They should
not be altered in a radical manner though, changing the proposed
solution completely. In this case the authors may withdraw the RFC and
propose another one.

An RFC shall be PENDING for at least two business days (in Austria) till
a vote can be held on it (see :doc:`rfc0`).


Withdrawal of RFCs
------------------

The authors may withdraw an RFC at any time as long as it is IN
PREPARATION or PENDING. The RFC status will change to WITHDRAWN. The
authors may decide to leave the text as is or remove everything except
for the basic information as defined in the :doc:`howto`.


Voting on RFCs
--------------

The voting on RFCs is defined in the first RFC: :doc:`rfc0`.
