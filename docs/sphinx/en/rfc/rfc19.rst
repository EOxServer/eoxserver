.. RFC 19
  #-----------------------------------------------------------------------------
  # $Id: rfc19.rst 1996 2013-04-06 11:46:12Z locherm $
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Marko Locher <marko.locher@eox.at>
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
.. _rfc_19:

RFC 19: Migrate project repository from svn to git
==================================================

:Author: Marko Locher
:Created: 2013-04-05
:Last Edit: $Date: 2013-04-06 16:00:00 +0200 (Fr, 05 Apr 2013) $
:Status: PENDING
:Discussion: n/a

Migrating from Subversion to git and in the process also switch from Trac to github. This RFC is a work in progress and not completed yet.

Introduction
------------

While SVN suits our needs as a collaborative source code versionner, it has shortcomings that make it difficult to work with for developpers working on multiple tasks in parallel. Git’s easy branching makes it possible to set up branches for individual task, isolating code changes from other branches, thus making the switch from one task to another possible without the risk of loosing or erroneously commiting work-in-progress code. Three-way merging of different branches means that merging code from one branch to another becomes a rapid task, by only having to deal with actual conflicts in the code. Offline committing and access to entire history make working offline possible.

There is already somewhat of a consensus that the migration from SVN to git is a good move. Discussion remains as to how this transition should be performed. This RFC outlines the different options available for hosting the official repository, and the different options available for our ticket tracking.

Current investigation has retained two majors options that we could go down with:

* Repository migrated to github, use github provided issue tracking. This option will be referred to as “Github hosting”.
* Repository hosted by EOX, current trac instance migrated to hook on the new repository. This option will be referred to as “EOX hosting”

Git Workflows
-------------

Stable Branches
^^^^^^^^^^^^^^^

This document outlines a workflow for fixing bugs in our stable branches: http://www.net-snmp.org/wiki/index.php/Git_Workflow I beleive it is a very good match for our stable release management: - pick the oldest branch where the fix should be applied - commit the fix to this oldest branch - merge the old branch down to all the more recent ones, including master

Release Management
^^^^^^^^^^^^^^^^^^

Instead of freezing development during our beta cycle, a new release branch is created once the feature freeze is decided, and our betas, release and subsequent bugfix releases are tagged off of this branch. Bug fixes are committed to this new stable branch, and merged into master. New features can continue to be added to master during all the beta phase. http://nvie.com/posts/a-successful-git-branching-model/ is an interesting read even if it does not fit our stable release branches exactly.


Upgrade path for SVN users
--------------------------

For those users who do not wish to change their workflow and continue with SVN commands. This is not the recommended way to work with git, as local or remote changes might end up in having conflicts to resolve, like with svn.

Checkout the project ::

  git clone git@github.com:EOX-A/eoxserver

Update ::

  git pull origin master

Commit changes ::

  git add [list of files]
  git commit -m “Commit message”
  git push origin master

Fix a bug in a branch, and merge the fix into master ::

  git checkout feature-branch
  git add [list of files]
  git commit -m “Commit message”
  git push origin feature-branch
  git checkout master
  git merge feature-branch
  git push origin master

Tasks
-----

* import svn to git
* assign github users
* split into sub-projects (c.f. rfc83):

 * eoxserver
 * autotest
 * docs

* document release process
* migrate website scripts
* switch trac site to read-only

Voting History
--------------

N/A


Traceability
------------

:Requirements: N/A
:Tickets: N/A
