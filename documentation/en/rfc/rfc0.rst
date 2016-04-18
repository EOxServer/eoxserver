.. RFC 0
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Meissl <stephan.meissl@eox.at>
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
   single: Project Steering Committee (PSC) Guidelines
   single: RFC; RFC 0

.. _rfc_0:

RFC 0: Project Steering Committee Guidelines
============================================

:Author: Stephan Meißl
:Created: 2011-03-02
:Last Edit: 2011-05-17
:Status: ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc0


Overview
--------

This RFC documents the EOxServer Project Steering Committee Guidelines.

(Credit: Inspired by the MapServer PSC guidelines at: 
http://mapserver.org/development/rfc/ms-rfc-23.html)


Introduction
------------

This RFC describes how the EOxServer Project Steering Committee (PSC) handles 
membership and makes decisions on all aspects, technical and non-technical, of 
the EOxServer project.

The PSC duties include:

* defining and deciding on the overall development road map
* defining and deciding on technical standards and policies like file naming 
  conventions, coding standards, etc.
* establishing a regular release cycle
* reviewing and voting on RFCs

The PSC members vote on proposals, RFCs, etc. via e-mail on the dev 
mailing list. Proposals shall be available for review for at least two days 
where a single veto delays the progress but at the end a majority of members 
may adopt a proposal.


Voting
------

Voting Procedure
~~~~~~~~~~~~~~~~

The following steps shall be followed in any voting:

* Any interested person may submit a proposal to the dev mailing list for 
  discussion. Note that this is explicitly not limited to PSC members.
* Voting on proposals shall not be closed earlier than two business days after 
  the proposal has been submitted.
* The following voting options shall be used:

  * "+1" .. support willingness to support implementation
  * "+0" .. low support
  * "0" .. no opinion
  * "-0" .. low disagreement
  * "-1" .. veto

* A veto shall include clear reasoning and alternative approaches to solve the 
  problem at hand.
* Any interested person may comment on proposals but only votes from PSC 
  members will be counted.
* A proposal may be declared accepted if it receives at least +2 and not 
  vetoes (-1).
* Vetoed proposals that cannot be revised to satisfy all PSC members may be 
  submitted for an override vote. The proposal may be declared accepted if a 
  simple majority of eligible voters votes in favor (+1). Eligible voters are 
  all PSC members that have not been declared inactive. However, it is 
  intended that in normal circumstances vetoers are convinced to withdraw 
  their veto. We are trying to reach consensus.
* Any eligible voter who has not cast a vote in the last two votes shall be 
  considered inactive. Casting a vote immediately turns the status to active.
* Upon completion of discussion and voting the author shall announce the new 
  status of the proposal (accepted, withdrawn, rejected, postponed, obsolete).
* The PSC Chair is responsible for keeping track of who is a member of the PSC 
  Membership.
* Addition and removal of members from the PSC, as well as selection of a Chair 
  should be handled as a proposal to the PSC.
* The PSC Chair adjudicates in cases of disputes about voting.

Voting is Required for
~~~~~~~~~~~~~~~~~~~~~~

* any change to committee membership (adding members, removing inactive 
  members).
* creating and dissolving of sub-committees (e.g. to manage conferences, 
  documentation, or web sites).
* changes to project infrastructure (e.g. tool, location, or substantive 
  configuration).
* anything that could cause backward compatibility issues.
* adding substantial amounts of new code.
* changing inter-subsystem APIs, or objects.
* issues of procedure.
* when releases should take place.
* anything dealing with relationships with external entities such as 
  MapServer or OSGeo.
* anything that might be controversial.


PSC Membership
--------------

The PSC is made up of individuals consisting of technical contributors 
(e.g. developers) and prominent members of the EOxServer user community.  
There is no fixed number of members for the PSC.

Adding Members
~~~~~~~~~~~~~~

Any member of the dev mailing list may nominate someone for committee 
membership at any time. Only existing PSC committee members may vote on new 
members. Nominees must receive a majority vote from existing members to be 
added to the PSC.

Stepping Down
~~~~~~~~~~~~~

If, for any reason, a PSC member is not able to fully participate then they 
certainly are free to step down. If a member is not active (e.g. no 
voting, no IRC, or e-mail participation) for a period of two months then 
the committee reserves the right to vote to cease membership.
Should that person become active again then they are certainly welcome, but 
require a nomination.


Membership Responsibilities
---------------------------

Guiding Development
~~~~~~~~~~~~~~~~~~~

Members should take an active role guiding the development of new features 
they feel passionate about. Once a change request has been accepted 
and given a green light to proceed does not mean the members are free of 
their obligation. PSC members voting "+1" for a change request are 
expected to stay engaged and ensure the change is implemented and 
documented in a way that is most beneficial to users. Note that this 
applies not only to change requests that affect code, but also those 
that affect the web site, technical infrastructure, policies, and standards.

IRC Meeting Attendance
~~~~~~~~~~~~~~~~~~~~~~

PSC members are expected to participate in pre-scheduled IRC development 
meetings. If known in advance that a member cannot attend a meeting, 
the member should let the meeting organizer know via e-mail.

Mailing List Participation
~~~~~~~~~~~~~~~~~~~~~~~~~~

PSC members are expected to be active on both the users and dev mailing lists, 
subject to open source mailing list etiquette. Non-developer members of the 
PSC are not expected to respond to coding level questions on the developer 
mailing list, however they are expected to provide their thoughts and opinions 
on user level requirements and compatibility issues when RFC discussions take 
place.


List of Members
---------------

Charter members are (in alphabetical order):

* Arndt Bonitz
* Peter Baumann
* Stephan Krause
* Stephan Meißl
* Milan Novacek
* Martin Paces
* Fabian Schindler

Stephan Meißl is declared initial Chair of the Project Steering Committee.


Voting History
--------------

:Acceptance: All charter members declared their availability via e-mail to the dev mailing list.


Traceability
------------

:Requirements: N/A
:Tickets: N/A
