.. RFC 8: SVN Commit Management
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
   single: Commit Management
   single: RFC; RFC 8

.. _rfc_8:

RFC 8: SVN Commit Management
============================

:Author: Stephan Meißl
:Created: 2011-05-04
:Last Edit: 2011-05-18
:Status: ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc8


Overview
--------

This RFC documents the EOxServer guidelines for SVN commit access and specifies 
some guidelines for SVN committers.


(Credit: Inspired by the MapServer SVN commit management guidelines at: 
http://mapserver.org/development/rfc/ms-rfc-7.1.html)


Election to SVN Commit Access
-----------------------------

Permission for SVN commit access shall be provided to new developers only
if accepted by the EOxServer Project Steering Committee (PSC). A proposal
should be written to the PSC for new committers and voted on normally. It
is not necessary to write an RFC document for these votes. An e-mail to 
the dev mailing list is sufficient.

Removal of SVN commit access should be handled by the same procedure.  

The new committer should have demonstrated commitment to EOxServer and
knowledge of the EOxServer source code and processes to the committee's
satisfaction, usually by reporting tickets, submitting patches, and/or
actively participating in the various EOxServer forums.

The new committer should also be prepared to support any new feature or
changes that he/she commits to the EOxServer source tree in future
releases, or to find someone to which to delegate responsibility for
them if he/she stops being available to support the portions of code
that he/she is responsible for.

All committers should also be a member of the dev mailing list
so they can stay informed on policies, technical developments, and 
release preparation.


Committer Tracking
------------------

A list of all project committers will be kept in the main eoxserver 
directory (called COMMITTERS) listing for each SVN committer:

* Userid: the id that will appear in the SVN logs for this person.
* Full name: the users actual name. 
* Email address: A current email address at which the committer can be
  reached.  It may be altered in normal ways to make it harder to 
  auto-harvest. 
* A brief indication of areas of responsibility.  


SVN Administrator
-----------------

One member of the PSC will be appointed the SVN Administrator. That person 
is responsible for giving SVN commit access to folks, updating the COMMITTERS 
file, and other SVN related management. Initially Stephan Meißl will be the 
SVN Administrator.

SVN Commit Practices
--------------------

The following are considered good SVN commit practices for the EOxServer
project. 

* Use meaningful descriptions for SVN commit log entries. 
* Add a ticket reference like "(#1232)" at the end of SVN commit log entries
  when committing changes related to a ticket in Trac.
* Include changeset revision numbers like "r7622" in tickets when discussing
  relevant changes to the codebase.
* Changes should not be committed in stable branches without a corresponding
  ticket. Any change worth pushing into a stable version is worth a Trac ticket. 
* Never commit new features to a stable branch: only critical fixes. New
  features can only go in the main development trunk.
* Only ticket defects should be committed to the code during pre-release
  code freeze.  
* Significant changes to the main development version should be
  discussed on the dev maling list before making them, and larger changes will
  require an RFC approved by the PSC.
* Do not create new branches without the approval of the PSC. A Release 
  manager designated under :doc:`rfc7` is automatically granted permission to 
  create a branch, as defined by their role described in :doc:`rfc7`.
* All source code in SVN should be in Unix text format as opposed to DOS
  text mode. 
* When committing new features or significant changes to existing source
  code, the committer should take reasonable measures to insure that the
  source code continues to work.
* Include the standard EOxServer header in every new file and set the following 
  SVN properties:
  
  * svn propset svn:keywords 'Author Date Id Rev URL' <new_file>
  * svn propset svn:eol-style native <new_file>


Legal
-----

Commiters are the front line gatekeepers to keep the code base clear of
improperly contributed code. It is important to the EOxServer users and
developers to avoid contributing any code to the project without it being 
clearly licensed under the project license.

Generally speaking the key issues are that those providing code to be included
in the repository understand that the code will be released under the
EOxServer License, and that the person providing the code has the right
to contribute the code. For the committer themselves understanding about the
license is hopefully clear. For other contributors, the committer should verify
the understanding unless the committer is very comfortable that the contributor
understands the license (for instance frequent contributors).

If the contribution was developed on behalf of an employer (on work time, as
part of a work project, etc) then it is important that an appropriate
representative of the employer understand that the code will be contributed
under the EOxServer License. The arrangement should be cleared with an
authorized supervisor/manager, etc.

The code should be developed by the contributor, or the code should be from a
source which can be rightfully contributed such as from the public domain, or
from an open source project under a compatible license.

All unusual situations need to be discussed and/or documented.

Committers should adhere to the following guidelines, and may be personally
legally liable for improperly contributing code to the source repository:

* Make sure the contributor (and possibly employer) is aware of the
  contribution terms.
* Code coming from a source other than the contributor (such as adapted
  from another project) should be clearly marked as to the original
  source, copyright holders, license terms and so forth. This information
  can be in the file headers, but should also be added to the project
  licensing file if not exactly matching normal project licensing
  (eoxserver/COPYING and eoxserver/README).
* Existing copyright headers and license text should never be stripped
  from a file. If a copyright holder wishes to give up copyright they must
  do so in writing to the project before copyright messages are
  removed. If license terms are changed it has to be by agreement (written
  in email is ok) of the copyright holders.
* When substantial contributions are added to a file (such as substantial
  patches) the author/contributor should be added to the list of copyright
  holders for the file.
* If there is uncertainty about whether a change it proper to contribute
  to the code base, please seek more information from the PSC. 


Voting History
--------------

:Motion: Adopted on 2011-05-17 with +1 from Arndt Bonitz, Stephan Krause, Stephan Meißl, Milan Novacek, Martin Paces, Fabian Schindler

Traceability
------------

:Requirements: N/A
:Tickets: N/A
