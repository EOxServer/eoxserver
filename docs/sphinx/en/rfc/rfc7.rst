.. _rfc_7:

.. index::
   single: Release Guidelines
   single: RFC; RFC 7

RFC 7: Release Guidelines
=========================

:Author: Stephan Meißl
:Created: 2011-05-04
:Last Edit: 2011-05-04
:Status: PENDING
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc7


Overview
--------

This RFC documents the EOxServer release manager role and the phases of
EOxServer's release process.

(Credit: Inspired by the MapServer release guidelines at: 
http://mapserver.org/development/rfc/ms-rfc-34.html)


The EOxServer Release Manager Role
----------------------------------

For every release of EOxServer, the PSC elects a release manager via motion 
and vote on the dev mailing list.

The overall role of the release manager is to coordinate the efforts
of the developers, testers, documentation, and other contributors to
lead to a release of the best possible quality within the scheduled
timeframe. 

The PSC delegates to the release manager the responsibility and 
authority to make certain final decisions for a release, including:

* Approving or not the release of each beta, release candidate, and 
  final release
* Approving or rejecting non-trivial bug fixes or changes after the 
  feature freeze
* Maintaining the release schedule (timeline) and making changes as required

When in doubt or for tough decisions (e.g. pushing the release date by
several weeks) the release manager is free to ask the PSC to vote in 
support of some decisions, but this is not a requirement for the areas of 
responsibility above.

The release manager's role also includes the following tasks:

* Setup and maintain a release plan wiki page for each release
* Coordinate with the developers team
* Coordinate with the QA/testers team
* Coordinate with the docs/website team
* Keep track of progress via Trac milestones and ensure tickets are properly 
  targeted
* Organize IRC meetings if needed (including agenda and minutes)
* Tag source code in SVN for each beta, RC, and release
* Branch source code in SVN after the final release (trunk becomes the next
  dev version)
* Update version in files for each beta/RC/release
* Package source code distribution for each beta/RC/release
* Update appropriate website/download page for each beta/RC/release
* Make announcements on users and announce mailing lists for each release
* Produce and coordinate bugfix releases as needed after the final release

Any of the above tasks can be delegated but they still remain the ultimate
responsibility of the release manager.


The EOxServer Release Process
-----------------------------

The normal development process of a EOxServer release consists of various 
phases.

- Development phase

  The development phase usually lasts several months. New features are
  proposed via RFCs and voted by the EOxServer PSC.

- RFC freeze date

  For each release there is a certain date by which all new feature 
  proposals (RFCs) must have been submitted for review. After this date no 
  features will be accepted anymore for this particular release.

- Feature freeze date / Beta releases

  By this date all features must have been completed and all code has 
  to be integrated. Only non-invasive changes, user interface work and 
  bug fixes are done now. There are usually 3 to 4 betas and a couple of
  release candidates before the final release.

- Release Candidate

  Ideally, the last beta that is bug free. No changes to the code. 
  Should not require any migration steps apart from the ones required 
  in the betas. If any problems are found and fixed, a new release 
  candidate is issued.

- Final release / Expected release date

  Normally the last release candidate that is issued without any 
  show-stopper bugs.

- Bug fix releases

  No software is perfect. Once a sufficient large or critical number 
  of bugs have been found for a certain release, the release manager 
  releases a new bug fix release a.k.a. third-dot release.


EOxServer Version Numbering
---------------------------

EOxServer's version numbering scheme is very similar to Linux's. For 
example, a EOxServer version number of 1.2.5 can be decoded as such:

- 1: Major version number. 

  The major version number usually changes when significant new features are 
  added or when major architectural changes or backwards incompatibilities are 
  introduced.

- 2: Minor version number. 

  Increments in minor version number almost always relate to additions 
  in functionality.

- 5: Revision number. 

  Revisions are bug fixes only. No new functionality is provided in revisions.


Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
