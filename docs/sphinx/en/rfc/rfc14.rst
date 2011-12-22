.. RFC 14: Asynchronous Task Processing (ATP)
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@iguassu.cz>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 Iguassu Software Systems a.s.
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

.. _rfc_14:

RFC 14: Asynchronous Task Processing (ATP)
==========================================

:Author:     Martin Paces 
:Created:    2011-10-25
:Last Edit:  2011-12-09 
:Status:     ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc14

This RFC describes the Asynchronous Task Processing subsystem of the *EOxServer*. 

Introduction
------------

The *Asynchronous Task Processing* (ATP) subsystem, as the name suggests, extends the EOxServer functionality
by ability to process tasks asynchronously, i.e., on background independently of the default EOxServer's 
synchronous client requests processing. 

Although the ATP is designed primarily to support asynchronous request processing of OGC Web Services such 
as the Web Coverage Service transaction extension and/or the Web Processing Service, it is not limited 
to these and other application may use it as well. 

The ATP employs the model of a single central task queue and one or more 
*Asynchronous Task Processing Daemons* (APTD) executing the pending tasks 
pulled from the task queue. A single ATPD is not restricted 
to a single processed task at time and can internally process multiple tasks concurrently, 
e.g., by employing a pool of worker processes assigned to multiple CPU cores. 

The ATP subsystem is implemented as Django application using the DB model as the task queue. 
The underlying DB storage although it may be seen as suboptimal in terms of the performance 
and latency it assure tolerance of the subsystem to possible failures or maintenance 
shut-downs of both EOxServer or APTDs. 

The ATP can be shared by multiple application at time as each task has its type (application 
to which it belongs) and each type of the task has a predefined handler subroutine. The 
shared nature of the APT subsystem allows fine control over the processing resources, e.g., 
the number of concurrently running task matching number of available CPU cores. 

The ATP is primarily designed for resource demanding longer running tasks (10 seconds and more) 
which in case of synchronous operation could clog the system or lead to connection time-outs. 
On contrary, *light* tasks (less than 1 sec.) should preferably be executed synchronously 
as the extra ATP latency might be unfavourable.

Asynchronous Task Processing
----------------------------

.. figure:: resources/rfc14/processes_task_state.png
   :align: center
   
   *Fig.1: ATP Task State Diagram*

The ATP subsystem is capable of tracking of the tasks during their life cycle depicted 
by the Task state diagram Fig.1. The task can be in one of the following states: 

 * ACCEPTED  - a new enqueued task waiting to be pulled by the processing daemon 
 * SCHEDULED - a task pulled (dequeued) by the processing daemon but not yet stared  
 * RUNNING   - a task being processed by the processing daemon 
 * PAUSED    - a task which has been put on hold by the processing daemon and which is waiting to be resumed
 * FINISHED  - a task which has been finished successfully (terminal state)
 * FAILED    - a task which has been finished by a failure (terminal state)

When a task becomes identified as staled (by exceeding the type specific time-out) it may be re-enqueued, 
i.e., the processing shall be terminated, enqueued as a new task again changing its status from 
one of the non-terminal states (SCHEDULED, RUNNING, PAUSED) to ACCEPTED. This procedure is implemented 
to avoid abandoned "zombie" tasks left, e.g., by an aborted processing daemon. However, this procedure 
is repeated only limited times (the count is task type specific, three by default), once the allowed 
restart's count is exceeded the task is marked as FAILED.

The history of the task's state transition is logged in order to provide information to the system operator.

The finished tasks are kept recorded for ever by default, however, this can changed by a task type (application) 
specific retention time, which allow automatic removal of out-dated tasks, e.g., one day, week or month after 
their finish. 

To inspect the state of the APT subsystem, a couple of simple DJango html views has been created.  


ATP DB Model 
~~~~~~~~~~~~

.. figure:: resources/rfc14/processes_db_model.png
   :align: center
   
   *Fig.2: ATP DB model*

The APT Django DB model consists of six classes as depicted in Fig.2.

 * Type - defining the type of task instance, its unique identifier, task handler (python subroutine),
 	and the type specific parameters such as maximum unsuccessful attempts to start the task execution, 
	time-out after the which the task is considered to be abandoned and re-enqueued for processing
	(e.g., due to ATPD failure), retention time to keep the record of the finished task.
 
 * Instance - defining a single task instance, its identifier and current state. 

 * Inputs - record holding input parameters stored serialized (pickled) Python object 

 * Response - record holding the optional tasks output (most likely an XML response document or serialized Python object)

 * LogRecord - single log entry. The log keeps history of the task's state transition. 

 * Task - single task queue record. The task table holds the accepted tasks, their enqueuetime, ATPD assignment. 


ATP API 
~~~~~~~

The ATP subsystem provides simple API which allows: 

 * registering of new task type and its parameters (repeated registration updates the parameters)
 * removal of unused task types (provided there is no instance of the removed type)

 * enqueueing of new task instance and input parameters (implies creation of new task instance)
 * dequeueing of enqueued instance (used by APTD) 
 * removal of finished tasks 
 * re-enqueueing of a non terminal state task

 * changing of the task status 
 * adding and retrieval of the response (output) 

Further the mandatory function prototype to define new handlers is given. 


Governance
----------

Source Code Location
~~~~~~~~~~~~~~~~~~~~

http://eoxserver.org/svn/sandbox/sandbox_wcst

RFCs and Decision Process
~~~~~~~~~~~~~~~~~~~~~~~~~

*TBD*

License
~~~~~~~

The APT implementation shall be distributed under the terms of :ref:`EOxServer's MapServer-like license <EOxServer Open License>`. 

Wiki, Trac, Tickets
~~~~~~~~~~~~~~~~~~~

*TBD*

References
----------


Voting History
--------------

:Motion: To accept RFC 14 
:Voting Start: 2011-12-15 
:Voting End: 2011-12-22
:Result: +4 for ACCEPTED

Traceability
------------

:Requirements: *N/A*
:Tickets:      *N/A*

