#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#  unit test for asynchronous process API 
#
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Petr Blaha <petr.blaha@iguassu.cz>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 Iguassu Software Systems, a.s 
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

import uuid 
import random
import unittest
import time

#----------------------------------------------------------------------
# imports 
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ObjectDoesNotExist 
from eoxserver.resources.processes.tracker import *

PROCESS_CLASS="TEST-PROCESS"
FASTER_CLASS="FAST-PROCESS"
ASYNC_HANDLER="apt_test.testHandler"
ASYNC_TIMEOUT=60
ASYNC_TIMERET=60
SERVER_ID=1
ID1="1111111"
ID2="2222222"
ID3="3333333"
ID4="4444444"
ID5="5555555"
ID6="6666666"
ID7="7777777"
ID8="8888888"
PARAM="1234568" 
inputs={ 'key':'value' }

class TestSequenceFunctions(unittest.TestCase):
    
#    def setUp(self):


    def test_unregistred_protected(self):
        registerTaskType( PROCESS_CLASS, ASYNC_HANDLER, ASYNC_TIMEOUT, ASYNC_TIMERET )

        # enqueue task for execution 
        enqueueTask( PROCESS_CLASS, ID1, inputs, PARAM )        

        # can not  unregisterTaskType if task exist
        # self.assertRaises( TaskTypeHasInstances, unregisterTaskType, PROCESS_CLASS, True )
        self.assertRaises( ProtectedError, unregisterTaskType, PROCESS_CLASS )
        deleteTaskByIdentifier( PROCESS_CLASS, ID1 )


    def test_unregistred_taskType_force(self):
        registerTaskType( PROCESS_CLASS, ASYNC_HANDLER, ASYNC_TIMEOUT, ASYNC_TIMERET )

        # enqueue task for execution 
        enqueueTask( PROCESS_CLASS, ID2, inputs, PARAM )        

        # force  unregisterTaskType
        unregisterTaskType( PROCESS_CLASS, True )
        # delete  task
        #deleteTaskByIdentifier( PROCESS_CLASS, ID2 )


    def test_unregistred_not_registred(self):
        self.assertRaises( ObjectDoesNotExist, unregisterTaskType, "TEST-PROCESS-NOT_REGISTRED", True )


    def test_enqueue_not_registred(self):
        # enqueue task for execution 
        self.assertRaises( ObjectDoesNotExist, enqueueTask, "TEST-PROCESS-NOT_REGISTRED", ID3, inputs, PARAM )        


    def test_unregistred_taskType(self):
        registerTaskType( PROCESS_CLASS, ASYNC_HANDLER, ASYNC_TIMEOUT, ASYNC_TIMERET )

        # enqueue task for execution 
        enqueueTask( PROCESS_CLASS, ID2, inputs, PARAM )        

        deleteTaskByIdentifier( PROCESS_CLASS, ID2)
        unregisterTaskType( PROCESS_CLASS )


    def test_dequeue_more_task(self):
        registerTaskType( PROCESS_CLASS, ASYNC_HANDLER, ASYNC_TIMEOUT, ASYNC_TIMERET )

        # enue two task and dequee three 
        # enqueue task for execution 
        enqueueTask( PROCESS_CLASS, ID1, inputs, PARAM )        
        enqueueTask( PROCESS_CLASS, ID2, inputs, PARAM )        

        dequeueTask( SERVER_ID ) 
        dequeueTask( SERVER_ID )

        # test for queue empty 
        self.assertRaises( QueueEmpty, dequeueTask, SERVER_ID )
        # delete  tasks
        deleteTaskByIdentifier( PROCESS_CLASS, ID2 )
        deleteTaskByIdentifier( PROCESS_CLASS, ID1 )


    def test_full_empty_queue(self):
        # enue more task then  QUEUE_SIZE
        for t in range ( 0, getMaxQueueSize() ) :
            enqueueTask( PROCESS_CLASS, t, inputs, PARAM )
        # test for queue full

        self.assertRaises( QueueFull, enqueueTask, PROCESS_CLASS, t+1, inputs, PARAM ) 

        # clean tasks
        for t in range ( 0, getMaxQueueSize() ) : deleteTaskByIdentifier( PROCESS_CLASS, t )

        # test for queue empty 
        self.assertRaises( QueueEmpty, dequeueTask, SERVER_ID )


    def test_start_task(self):
        enqueueTask( PROCESS_CLASS, ID3, inputs, PARAM )
        id = dequeueTask( SERVER_ID )
        start = startTask( id[0] )

        # get the task ID and compare
        self.assertEqual( int( str( start[1] ) ), int( ID3 ) )
        # delete task 
        deleteTaskByIdentifier( PROCESS_CLASS, ID3 )


    #  test both setTaskResponse and  getTaskResponse
    def test_responses(self):
        enqueueTask( PROCESS_CLASS, ID4, inputs, PARAM )
        id = dequeueTask( SERVER_ID )
        setTaskResponse( id[0], "123" ) 

        response = getTaskResponse( PROCESS_CLASS, ID4 )[0]
        self.assertEqual( int( response ), 123 )
        deleteTaskByIdentifier( PROCESS_CLASS, ID4 )


    def test_task_duplicity(self):

        enqueueTask( PROCESS_CLASS, ID5, inputs, PARAM )
        # again
        self.assertRaises( IntegrityError, enqueueTask, PROCESS_CLASS, ID5, inputs, PARAM )

        deleteTaskByIdentifier( PROCESS_CLASS, ID5 )


    def test_running_task(self):
        enqueueTask( PROCESS_CLASS, ID6, inputs, PARAM )
        id = dequeueTask( SERVER_ID )
        start = startTask( id[0] )

        # inspection 
        status =  getTaskStatus( id[0] ) 

        # status is  3:"RUNNING"
        self.assertEqual( status[0], 3 )
        deleteTaskByIdentifier( PROCESS_CLASS, ID6 )


    def test_reenqueue_task(self):
        enqueueTask( PROCESS_CLASS, ID7, inputs, PARAM )
        id = dequeueTask( SERVER_ID )
        reenqueueTask( id[0], "Run now" )
        deleteTaskByIdentifier( PROCESS_CLASS, ID7 )


    def test_three_task_zombie(self):
        registerTaskType( FASTER_CLASS, 2, 2 )
        enqueueTask( FASTER_CLASS, ID1, inputs, PARAM )        
        enqueueTask( FASTER_CLASS, ID2, inputs, PARAM )        
        enqueueTask( FASTER_CLASS, ID3, inputs, PARAM )        

        id1 = dequeueTask( SERVER_ID )
        id2 = dequeueTask( SERVER_ID )
        id3 = dequeueTask( SERVER_ID )

        # first Task
        s2 =  getTaskStatus( id1[0] )

        # second Task is starting
        startTask( id2[0], "start running first" )
        s2 =  getTaskStatus( id2[0] )

        # third Task is starting
        pauseTask( id3[0], "start running third" )
        s3 =  getTaskStatus( id3[0] )

        time.sleep( 3 )
        reenqueueZombieTasks( "Up" ) 

        s1 =  getTaskStatus( id1[0] )
        s2 =  getTaskStatus( id2[0] )
        s3 =  getTaskStatus( id3[0] )

        # must be 1, 'ACCEPTED' 
        self.assertEqual( int(s1[0]) +  int(s2[0]) +  int(s3[0]), 3 )        

        deleteTaskByIdentifier( PROCESS_CLASS, ID1 )
        deleteTaskByIdentifier( PROCESS_CLASS, ID2 )
        deleteTaskByIdentifier( PROCESS_CLASS, ID3 )


    def test_set_task_status_failed(self):
        enqueueTask( PROCESS_CLASS, ID7, inputs, PARAM )
        id = dequeueTask( SERVER_ID )
        reenqueueTask( id[0], "Run now" )
    
        # start Task
        startTask( id[0], "start running" )
        # pause task 
        pauseTask( id[0] )

        taskStatus= TaskStatus( id[0] ) 
        taskStatus.setFailure( "failed" ); 

        s = taskStatus.getStatus()

        # must be 6, 'FAILED' 
        self.assertEqual( int(s[0]), 6 )        

        deleteTaskByIdentifier( PROCESS_CLASS, ID7 )


    def test_delete_retired_task(self):
        registerTaskType( FASTER_CLASS, ASYNC_HANDLER, 2, 2 )
        enqueueTask( FASTER_CLASS, ID8, inputs, PARAM )        

        id = dequeueTask( SERVER_ID )

        # second Task is starting
        startTask( id[0], "go" )

        taskStatus= TaskStatus( id[0] ) 
        taskStatus.setSuccess( "OK" ); 

        time.sleep( 5 )

        r = deleteRetiredTasks()
       
        self.assertRaises( ObjectDoesNotExist, taskStatus.getStatus )

        deleteTaskByIdentifier(	FASTER_CLASS, ID8 )

