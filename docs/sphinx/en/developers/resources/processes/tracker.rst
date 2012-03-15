.. Module eoxserver.resources.processes.tracker
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
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

.. _module_resources_processes_tracker:

Module eoxserver.resources.processes.tracker 
================================================

.. automodule:: eoxserver.resources.processes.tracker

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

Basic API  
---------

The *User API* section contains the basic functions and classes 
required by an actual ATP user to implement a new asynchronous application. 

Task Type Registration  
^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: registerTaskType 
.. autofunction:: unregisterTaskType 

Task Creation 
^^^^^^^^^^^^^

.. autofunction:: enqueueTask


Task Handler Subroutine 
^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: dummyHandler 

.. autoclass:: TaskStatus
   :members:


Advanced API  
------------

The *ATPD API* section contains additional functions and classes 
required for creation of ATP daemon. 

Task Manipulation 
^^^^^^^^^^^^^^^^^
Note: These functions are NOT granted to have an exlusive access
to the DB. When DB locking is required call these function 
through the 'dbLocker' wrapper. 

.. autofunction:: getTaskInfo
.. autofunction:: getTaskIdentifier
.. autofunction:: getTaskStatus
.. autofunction:: getTaskStatusByIdentifier
.. autofunction:: reenqueueTask
.. autofunction:: dequeueTask
.. autofunction:: startTask
.. autofunction:: pauseTask
.. autofunction:: resumeTask
.. autofunction:: stopTaskSuccessIfNotFinished
.. autofunction:: stopTaskSuccess
.. autofunction:: stopTaskFailure
.. autofunction:: deleteTask
.. autofunction:: deleteTaskByIdentifier

Task Processing History 
^^^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: getTaskLog 

Task Response  
^^^^^^^^^^^^^
.. autofunction:: setTaskResponse
.. autofunction:: getTaskResponse

Clean-up Tools 
^^^^^^^^^^^^^^
.. autofunction:: reenqueueZombieTasks
.. autofunction:: deleteRetiredTasks

DB Access and Locking 
^^^^^^^^^^^^^^^^^^^^^
In certain cases it my be necessary to assure mutually exclusive 
access to the underlaying DB. The proper logging mechanism is 
dependent on the actual concurrent processing implementation. 

.. autoclass:: DummyLock 
   :members:

.. autofunction:: dbLocker

Auxiliary Subroutines
^^^^^^^^^^^^^^^^^^^^^
.. autofunction:: getQueueSize
.. autofunction:: getMaxQueueSize

Auxiary Data
^^^^^^^^^^^^
.. autodata:: MAX_QUEUE_SIZE
.. autodata:: eoxserver.resources.processes.models.STATUS2TEXT
.. autodata:: eoxserver.resources.processes.models.TEXT2STATUS

Exceptions
^^^^^^^^^^
.. autoclass:: QueueException
.. autoclass:: QueueEmpty
.. autoclass:: QueueFull



