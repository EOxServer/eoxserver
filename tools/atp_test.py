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

import os
import sys
import uuid 
import time 

#----------------------------------------------------------------------
#number of test tasks 

N=1000

#----------------------------------------------------------------------

# default django settings module 
DJANGO_SETTINGS_DEFAULT = "settings"

os.environ["DJANGO_SETTINGS_MODULE"] = os.environ.get("DJANGO_SETTINGS_MODULE",DJANGO_SETTINGS_DEFAULT)

# setup search paths 

paths = [] 
#paths = [ 
#    "/home/test/o3s/sandbox_wcst" ,
#    "/home/test/o3s/sandbox_wcst_instance" ] 

for path in paths : 
    if path not in sys.path:
        sys.path.append(path)

#----------------------------------------------------------------------
# imports 

from eoxserver.resources.processes.tracker import QueueFull, registerTaskType, enqueueTask

#----------------------------------------------------------------------
# register new task handler 

PROCESS_CLASS="TEST-PROCESS"
ASYNC_HANDLER="tools.atp_test.testHandler"
ASYNC_TIMEOUT=60
ASYNC_TIMERET=60

registerTaskType( PROCESS_CLASS , ASYNC_HANDLER , ASYNC_TIMEOUT , ASYNC_TIMERET )

#----------------------------------------------------------------------
# async handler 

def testHandler( taskStatus , param ) :

    print "HANDLER:" , param 

    # change status  
    #taskStatus.setSuccess()

#----------------------------------------------------------------------

# optimal wait time 

WAIT_TIME = ( 0.05 , 0.1 , 0.2 , 0.4 , 0.8 , 1.6 , 3.2 , 6.4 , 12.8 ) 

def getWaitTime(idx ) : 

    if ( idx >= len( WAIT_TIME ) ) : return WAIT_TIME[-1]

    return WAIT_TIME[idx] 


# enqueue task 

def testEnqueue( param ) : 

    cnt = 0 ; 

    tid = "test_%s"%uuid.uuid4().hex

    while True : 
       
        try: 

            # enqueue task for execution 
            enqueueTask( PROCESS_CLASS , tid , param )
        
            print "ENQUEUE: %s" % tid , param  
        
            break 

        except QueueFull : # retry if queue full 

            print " --- QueueFull #%i - sleep: %g s"%( cnt + 1 , getWaitTime(cnt) ) 

            time.sleep(getWaitTime(cnt)) 

            cnt += 1 
            
            continue 


if __name__ == "__main__" : 


    from eoxserver.core.system import System
    # initialize the system 
    System.init()

    for i in xrange(N) : 
        
        testEnqueue("%6.6u"%i) 

        #time.sleep(0.1) 
