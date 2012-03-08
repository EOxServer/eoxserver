.. atp_sum 
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (c) 2012 EOX IT Services GmbH 
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

.. _atp_sum:

Asynchronous Task Processing 
===========================

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

Introduction 
------------

The *Asynchronous Task Processing* (ATP) subsystem, as the name suggests,
extends the *EOxServer* functionality by the ability to process tasks
asynchronously, i.e., on background independently of the default *EOxServer's*
synchronous client requests processing.

Although the ATP is designed primarily to support asynchronous request
processing of OGC Web Services such as the Web Coverage Service transaction
extension (WCS-T) and/or the Web Processing Service (WPS), it is not limited to
these and other parts of the *EOxServer* may use it as well. 

The ATP employs the model of a single shared task queue and one or more
*Asynchronous Task Processing Daemons* (APTD) executing the pending tasks pulled
from the task queue. A single ATPD is not restricted to a single processed task
at time and it can internally process multiple tasks concurrently, e.g., by
employing a pool of parallel worker threads assigned to multiple CPU cores. 

The ATP subsystem is implemented as Django application using the DB model as the
task queue.  Although the underlying DB storage may be seen as suboptimal in
terms of the performance and latency it assures tolerance of the subsystem to
possible failures or maintenance shut-downs of both *EOxServer* and/or APTDs. 

Task
----

For the correct operation of the ATP subsystem it essential to understand the
concept of a task and its life-cycle. 

A *task* is an atomic and isolated action (amount of work) to be performed by
the *EOxServer*.  When created, each task has a handler subroutine (python code
to be executed) and set of task specific input parameters to be processed by the
handler subroutine.  When finished, the tasks produce outputs. 

The tasks may be created by different applications (*EOxServer's* apps and
services).  The tasks sharing the same handler subroutine and generic parameters
belong to the same task *type*.

The ATP is expected to be shared by multiple applications. APTDs pull the tasks
from the shared queue in First-In-First-Out fashion (regardless of the task
type) and execute the given handler subroutines. Significant benefit of this
shared nature of the APT subsystem is the control over the processing resources
(pool of workers) and isolation of the execution details from the application
(isolated from details such at the number of ATPD and working threads). 

Task's Life-cycle
^^^^^^^^^^^^^^^^^

The life-cycle of an asynchronous task, i.e., its possible states and state
transitions are displayed in Fig.3. 

.. figure:: images/processes_task_state.png
   :align: center 

   *Fig.1: ATP Task State Diagram*

Any existing task can be in one of the following states: 

 * ACCEPTED  - a new enqueued task waiting to be pulled by an ATPD (initial
 * state) SCHEDULED - a task pulled (dequeued) by an ATPD but not yet started
 * RUNNING   - a task being processed by an ATPD PAUSED    - a task which has
 * been put on hold and which is waiting to be resumed FINISHED  - a task which
 * has been finished successfully (terminal state) FAILED    - a task which has
 * been finished by a failure (terminal state)

When a task is created and enqueued for processing (ACCEPTED) it is stored in
the DB task queue waiting for an ATPD to pull the task out. In this state, it is
safely stored and protected against failures and shut-downs of both of the
producer (ATPD can access the DB) and of the ATPD (producer can access the DB).

When a task is in one of the intermediate states (SCHEDULED, RUNNING, or PAUSED)
it is being processed by an ATPD and it is vulnerable to its possible failures.
In these states, any unexpected crash of ATPD could leave a task in intermediate
state forever. Therefore each task type has assigned security time-out after
which the task is considered to be abandoned and shall be re-enqueued for new
processing (ACCEPTED). A task, however, can be re-enqueued for limited times (3
times by default).  After the number of restarts has been exceeded the task will
be rejected (FAILED).  This mechanism ensures that no task would be abandoned
unfinished after an occasional ATPD crash but also that a defective task would
get stacked in the time-out loop. 

When a task is in one of the terminal states (FINISHED or FAILED) it is safely
stored by the DB. By default a terminated task will be stored forever, however,
it is possible to specify an task type specific time-out after which the
terminated tasks will be removed automatically. 

ATP Installation and Configuration
----------------------------------

There are no specific steps to install and configure the ATP subsystem except
the basic *EOxServer* installation and configuration. The ATP is tightly coupled
with *EOxServer* and works right out of box. 

To track the status of the executed tasks and view the stored outputs auxiliary
ATP HTML views can be enabled by adding following lines to URL patterns
('url.py' configuration file) of the actual *EOxServer* instance::

    urlpatterns = patterns('',

        ... 

        (r'^process/status$', procViews.status ),
        (r'^process/status/(?P<requestType>[^/]{,64})/(?P<requestID>[^/]{,64})$', procViews.status ),
        (r'^process/task$', procViews.task ),
        (r'^process/response/(?P<requestType>[^/]{,64})/(?P<requestID>[^/]{,64})', procViews.response ),

        ... 
    )

ATP Operation 
-------------

ATP operation requires at least one ATPD to be running. Currently, there is only
one ATPD implemented in EOxServer. This ATPD uses multiple sub-processes to
process the tasks concurrently.  By default, the numbers of subprocesses equals
to the number of available CPU cores. This ATPD can be executed as follows::

    $ export PYTHONPATH=<EOxServer instal.path>:<EOxServer instance path>
    $ export DJANGO_SETTINGS_MODULE=autotest.settings
    $ <EOxServer instal.path>/tools/asyncProcServer.py

    [0x504DD5AE614D562C] INFO: Default number of working threads: 4
    [0x504DD5AE614D562C] INFO: 'autotest.settings' ... is set as the Django settings module 
    SpatiaLite version ..: 2.4.0    Supported Extensions:
        - 'VirtualShape'    [direct Shapefile access]
        - 'VirtualDbf'      [direct Dbf access]
        - 'VirtualText'     [direct CSV/TXT access]
        - 'VirtualNetwork'  [Dijkstra shortest path]
        - 'RTree'       [Spatial Index - R*Tree]
        - 'MbrCache'        [Spatial Index - MBR cache]
        - 'VirtualFDO'      [FDO-OGR interoperability]
        - 'SpatiaLite'      [Spatial SQL - OGC]
    PROJ.4 Rel. 4.7.1, 23 September 2009
    GEOS version 3.2.2-CAPI-1.6.2
    [0x504DD5AE614D562C] INFO: ATPD Asynchronous Task Processing Daemon has just been started!
    [0x504DD5AE614D562C] INFO: ATPD: id=0x504DD5AE614D562C (5786516041174439468)
    [0x504DD5AE614D562C] INFO: ATPD: hostname=localhost 
    [0x504DD5AE614D562C] INFO: ATPD: pid=3295 

The ``PYTHONPATH`` and ``DJANGO_SETTINGS_MODULE`` values can be passed as
command line arguments by the '-p' and '-s' options, respectively. The default
number of worker sub-processes can be overridden by the '-n' option::

    $ <EOxServer instal.path>/tools/asyncProcServer.py -n 6 -s "autotest.settings" -p "<EOxServer instal.path>" -p "<EOxServer instance path>"

    [0xADDB15DB482ED425] INFO: Default number of working threads: 4
    [0xADDB15DB482ED425] INFO: Setting number of working threads to: 6
    [0xADDB15DB482ED425] INFO: 'autotest.settings' ... is set as the Django settings module 
    SpatiaLite version ..: 2.4.0    Supported Extensions:
        - 'VirtualShape'    [direct Shapefile access]
        - 'VirtualDbf'      [direct Dbf access]
        - 'VirtualText'     [direct CSV/TXT access]
        - 'VirtualNetwork'  [Dijkstra shortest path]
        - 'RTree'       [Spatial Index - R*Tree]
        - 'MbrCache'        [Spatial Index - MBR cache]
        - 'VirtualFDO'      [FDO-OGR interoperability]
        - 'SpatiaLite'      [Spatial SQL - OGC]
    PROJ.4 Rel. 4.7.1, 23 September 2009
    GEOS version 3.2.2-CAPI-1.6.2
    [0xADDB15DB482ED425] INFO: ATPD Asynchronous Task Processing Daemon has just been started!
    [0xADDB15DB482ED425] INFO: ATPD: id=0xADDB15DB482ED425 (-5919113253695335387)
    [0xADDB15DB482ED425] INFO: ATPD: hostname=holly3
    [0xADDB15DB482ED425] INFO: ATPD: pid=3345

The server can be gracefully terminated by the 'Ctrl-C' or by the TERM signal. 

ATP Demo Application 
--------------------

There is a demo application of the running ATPD and of the ATP as such.  This
demo application can be executed as follows::

    $ export PYTHONPATH=/home/pacesm/O3S/eoxserver/trunk
    $ export DJANGO_SETTINGS_MODULE=autotest.settings
    $ <EOxServer instal.path>/atp_test.py
    SpatiaLite version ..: 2.4.0    Supported Extensions:
        - 'VirtualShape'    [direct Shapefile access]
        - 'VirtualDbf'      [direct Dbf access]
        - 'VirtualText'     [direct CSV/TXT access]
        - 'VirtualNetwork'  [Dijkstra shortest path]
        - 'RTree'       [Spatial Index - R*Tree]
        - 'MbrCache'        [Spatial Index - MBR cache]
        - 'VirtualFDO'      [FDO-OGR interoperability]
        - 'SpatiaLite'      [Spatial SQL - OGC]
    PROJ.4 Rel. 4.7.1, 23 September 2009
    GEOS version 3.2.2-CAPI-1.6.2
    ENQUEUE: test_5710ffb4189c4345aebde828d2bbc640 000000
    ENQUEUE: test_47e161ec633b4105a1d174759f4a933d 000001
    ENQUEUE: test_e53cf3ae654a447191e1308d805d8777 000002
    ENQUEUE: test_fb71659cb9274383a8820e0110c86e15 000003
    ENQUEUE: test_0e6e5edcdf8244d9b25a932cbd8c6112 000004
    ENQUEUE: test_be5fa7af84444c47aba731c8e816f99b 000005
    ENQUEUE: test_aae3faa14b5e4f48b8cabae7a0b01a3b 000006
    ENQUEUE: test_6be7ea23f0984efbb09181503aa1a974 000007
 
Performance considerations 
-------------------------
 
The ATP is designed for resource demanding longer running tasks (10 seconds and
more) which in case of synchronous operation could clog the system or lead to
connection time-outs.  On contrary, *light* tasks (less than 1 sec.) should
preferably be executed synchronously 
