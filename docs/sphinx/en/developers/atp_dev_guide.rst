.. atp_dev_guide.rst
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

.. _atp_dev_guide:

Asynchronous Task Processing - Developers Guide 
===============================================

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

Introduction 
------------

This guide is intended to help with creation of applications using the
*Asynchronous Task Processing* subsystem. 

The first part is guiding creation of the simple task producer, i.e., an
application needing the asynchrounous processing capabilities. 

The second part helps with creation of a task consumer, i.e., the part 
of code pulling tasks from the work queue and executing them. The task  
consumer is part of Asynchronous Task Processing Daemon. 

An overview of the ATP capabilities is presented in ":ref:`atp_sum`". The
database model used in by the ATP subsystem is described in ":ref:`ATP Data
Model`". The complete API reference can be found in
":ref:`module_resources_processes_tracker`".

Simple ATP Application
----------------------

Here in this section we will prepare step-by-step a simple demo application 
making use of the ATP subsystem. The complete application is avaliable at
location:: 

    <EOxServer instal.dir.>/tools/atp_demo.py 

The prerequisite of starting the application is that the correct
path to the *EOxServer* installation and instance is set together with the
correct *Django* ``settings`` module. 

Initially the application must import the right python objects
from the :func:`~eoxserver.resources.processes.tracker` module::

    from eoxserver.resources.processes.tracker import \
        registerTaskType, enqueueTask, QueueFull, \
        getTaskStatusByIdentifier, getTaskResponse, deleteTaskByIdentifier

By this command we imported following
objects: i) task type registration function, ii) the task creation (enqueue)
subroutine, iii) an exception class risen in case of full task queue unable
to accept (most likely temporarily) new tasks, iv) task's status polling
subroutine, v) the response getter function and finanlly vi) the subroutine 
deleting an existing task. These are the ATP Python objects needed by our 
little demo application. 

Step 1 - Handler Subroutine 
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let's start with preparation of an example of subroutine to be executed -
handler subroutine. The example handler below sums sequence of numbers and
stores the result::

    def handler( taskStatus , input ) : 
        """ example ATP handler subroutine """
        sum = 0 
        # sum the values 
        for val in input : 
            try :
                sum += float( val ) 
            except ValueError: 
                # stop in case on ivalid input 
                taskStatus.setFailure("Input must be a sequence of numbers!") 
                return 
        # store the response and terminate 
        taskStatus.storeResponse( str(sum) )  

Any handler subroutine (see also
:func:`~eoxserver.resources.processes.tracker.dummyHandler`) 
receives two parameters: i) an instance of the
:class:`~eoxserver.resources.processes.tracker.TaskStatus` class 
and an input parameter. The input parameter is set during the task creation and
can be any Python object serialisable by the ``pickle`` module. 

Step 2 - New Task Type Registration 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once we have prepared the handler subroutine we can register the task type 
to be performed by this subroutine::
    
    registerTaskType( "SequenceSum" , "tools.atp_demo.handler" , 60 , 600 , 3 ) 

The :func:`~eoxserver.resources.processes.tracker.registerTaskType` subroutine
registers a new task type named "SequenceSum". Any task instance of this task
type will be processed by the ``handler`` subroutine. The handler subroutine 
is specified as importable module path. Any task instance not
processed by an ATPD within 60 seconds (measured from the moment the ATPD pulls
a task from the queue) is considered to be abandoned and it is automatically
re-enqueued for new processing. The number of the re-enqueue attempts is limited
to 3. Once a task instance is finished it will be stored for min. 10 minutes
(600 seconds) before it gets removed. 

Step 3 - Creating New Task  
^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the task handler has been registered as a new task type we can create a
task's instance::

    while True :
        try:
            enqueueTask( "SequenceSum" , "Task001" , (1,2,3,4,5) ) 
            break
        except QueueFull : # retry if queue full 
            print "QueueFull!"
            time.sleep( 5 )
    
The :func:`~eoxserver.resources.processes.tracker.enqueueTask` creates a new
task instance "Task001" of task type "SequenceSum". The tuple ``(1,2,3,4,5)`` 
is the input to the handler subroutine. In case of full task queue 
new task cannot be accepted and the
:func:`~eoxserver.resources.processes.tracker.QueueFull`` is risen. 
Since we want the task to be enqueued a simple re-try loop must be employed. 

Step 4 - Polling the task status 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

After task has been created enqueued for processing its status can be 
polled::

    while True :
        status = getTaskStatusByIdentifier( "SequenceSum" , "Task001" )
        print time.asctime() , "Status: " , status[1] 
        if status[1] in ( "FINISHED" , "FAILED" ) : break 
        time.sleep( 5 ) 

The task status is polled until the final status (``FINISHED`` or ``FAILED``) is
reached. The task must be identified by unique pair of task type and task
instance identifiers.

NOTE: The task instance is guaratied to be unique for given task type
identifier, i.e., there might be two task with the same instance identifier but
different type identifier. 

Step 5 - Getting the task results 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once the task has been finished the task response can be retrieved::

    if status[1] == "FINISHED" :
        print "Result: " , getTaskResponse( "SequenceSum" , "Task001" ) 

Step 6 - Removing the task  
^^^^^^^^^^^^^^^^^^^^^^^^^^

Finaly the result task is not needed anymore and can be removed from DB::

    deleteTaskByIdentifier( "SequenceSum" , "Task001" ) 

Executing ATP Task 
------------------



 
