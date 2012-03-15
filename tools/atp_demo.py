#!/usr/bin/env python
#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   asynchronous task processing - simple test task feed 
#
# Quick Start: 
#
#  1) set PYTHONPATH env.var to point to both: 
#        - EOxServer installation 
#        - EOxServer (configured) instance  
#  2) optionally set also DJANGO_SETTINGS_MODULE env.var 
#  3) run this script 
#
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@iguassu.cz>
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
# imports 

import time
from eoxserver.resources.processes.tracker import \
    registerTaskType, enqueueTask, QueueFull, \
    getTaskStatusByIdentifier, getTaskResponse, deleteTaskByIdentifier

#-------------------------------------------------------------------------------
# Step 1 - Handler subroutine 

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
    taskStatus.storeResponse( str(sum) , "text/plain" )

#-------------------------------------------------------------------------------
# make sure the following commands are not 
# executed while included as module 

if __name__ == "__main__" : 

    # delete previous task if exists 
    try : 
        deleteTaskByIdentifier( "SequenceSum" , "Task001" )
    except : pass 

#-------------------------------------------------------------------------------
# Step 2 - task registration 


    registerTaskType( "SequenceSum" , "tools.atp_demo.handler" , 60 , 600 , 3 )

#-------------------------------------------------------------------------------
# Step 3 - new task creation 
 
    while True :
        try:
            enqueueTask( "SequenceSum" , "Task001" , (1,2,3,4,5) )
            break
        except QueueFull : # retry if queue full
            print "QueueFull!"
            time.sleep( 5 )

#-------------------------------------------------------------------------------
# Step 4 - polling task status 

    while True :
        status = getTaskStatusByIdentifier( "SequenceSum" , "Task001" )
        print time.asctime() , "Status: " , status[1]
        if status[1] in ( "FINISHED" , "FAILED" ) : break
        time.sleep( 5 )

#-------------------------------------------------------------------------------
# Step 5 - getting result 

    if status[1] == "FINISHED" :
        print "Result: " , getTaskResponse( "SequenceSum" , "Task001" )

#-------------------------------------------------------------------------------
# Step 6 - removing task 

    #deleteTaskByIdentifier( "SequenceSum" , "Task001" )

#-------------------------------------------------------------------------------
