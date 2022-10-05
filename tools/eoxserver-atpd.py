#!/usr/bin/env python
#-----------------------------------------------------------------------
#
# Description:
#
#   asynchronous processing master daemon
#
#   This is the master server which keeps track of the aynchronous tasks in the
#   queue and distributes task to the workers
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

# default django settings module
DJANGO_SETTINGS_DEFAULT = "settings"
DJANGO_DB_DEFAULT = "default"

#-------------------------------------------------------------------------------

import os
import sys
import signal
import logging
import traceback
import os.path
import time
import struct
import socket
from datetime import datetime, timedelta


from multiprocessing import Lock, Process, Queue , cpu_count
from multiprocessing.queues import Empty as MPQEmpty
from multiprocessing.queues import Full as MPQFull
from django.utils.encoding import smart_str
try:    import cPickle as pickle
except: import pickle
try:
    # Python 2
    xrange
except NameError:
    # Python 3, xrange is now named range
    xrange = range
#-------------------------------------------------------------------------------

QUEUE_EMPTY_QUERY_DELAY=1.5 # time in seconds of next query to empty queue
QUEUE_PUT_TIMEOUT=1.0 # time out used by internal task queue put operation
QUEUE_CLEAN_UP_COUNT=300

#-------------------------------------------------------------------------------
# generate unique server instance ID

SERVER_ID=0
while 0 == SERVER_ID :
    tmp = os.urandom(8)
    SERVER_ID = struct.unpack( 'q' , tmp )[0]
    SERVER_ID_STR = "0x%16.16X"%( struct.unpack( 'Q' , tmp )[0] )

#-------------------------------------------------------------------------------

dbLock = Lock()
writeLock = Lock()

def write(msg) :
    writeLock.acquire()
    sys.stdout.write("[%s] %s"%(SERVER_ID_STR,msg) )
    writeLock.release()

def debug( msg ) : write( ("DEBUG: %s\n"%(msg)).encode('UTF-8') )
def info( msg ) : write( ("INFO: %s\n"%(msg)).encode('UTF-8') )
def warn( msg ) : write( ("WARNINIG: %s\n"%(msg)).encode('UTF-8') )
def error( msg ) : write( ("ERROR: %s\n"%(msg)).encode('UTF-8') )

#-------------------------------------------------------------------------------
# global worker pool

global GWP

GWP = None

#-------------------------------------------------------------------------------

# iterrupt and terminate signal handlers

class ExcTerminate( Exception ) : pass

SS = { signal.SIGINT:"SIGINT" , signal.SIGTERM:"SIGTERM" }

def signal_handler_dummy(sig, frm): pass

def signal_handler_sigint(sig, frm):
    global GWP
    if GWP is not None :
        GWP.terminate = True

def signal_handler_sigterm(sig, frm):
    global GWP
    if GWP is not None :
        GWP.terminate = True
        GWP.killChild = True # force immediate termination

#-------------------------------------------------------------------------------

class Importer( object ) :
    """ smart importer of the handler subroutine

        E.g. function 'd()' in module 'a.b.c'
            given by a path 'a.b.c.d' is imported
    """

    def __init__( self , path ) :
        """Initialize class from the given handler
        subroutine dot-path"""

        self.path = path
        self.module , _ , self.func = path.rpartition(".")
        self.modules = []
        self.handler = None

    def loadHandler( self ) :
        """ load the handler subroutine """

        if not self.handler :

            # initial list of modules
            ml0 = set( sys.modules )

            # new list of modules
            ml1 = set( sys.modules )

            self.handler = getattr( __import__( self.module , fromlist=[self.func] ) , self.func )

            # store list of loaded modules
            self.modules = ml1 - ml0

        return self.handler

    def unloadHandler( self ) :
        """ unload the handler subroutine """

        if self.handler :

            self.handler = None

            # unload the loaded modules
            for m in self.modules :
                del( sys.modules[m] )

            # store list of loaded modules
            self.modules = []


def taskDispatch( taskID , threadID ) :
    """
        task dispatcher

        based on the request class the right request hadler is used
        to process the asynchronous requets
    """
    # status logger
    pStatus = TaskStatus( taskID , dbLock )

    try:

        # get task parameters
        requestType , requestID , requestHandler , inputs = dbLocker( dbLock , startTask , taskID )

        info( "[%3.3i] PROCESS: %s %s is running ... " % ( threadID , requestType , requestID ) )

        # create importer object
        imp = Importer( requestHandler )

        # try to load the right module and handler
        imp.loadHandler()

        # execute handler - proper status logging is duty of the callback
        imp.handler( pStatus , inputs )

        # try to unload the handler
        imp.unloadHandler()

        # if no terminating status has been set do it right now
        dbLocker( dbLock , stopTaskSuccessIfNotFinished , taskID )

        info( "[%3.3i] PROCESS: %s %s is finished ... " % ( threadID , requestType , requestID ) )

    except (KeyboardInterrupt,SystemExit): raise
    except Exception as e :

        pStatus.setFailure( smart_str((e) )

        # finish the task
        error( "[%3.3i] %s " % ( threadID , smart_str((e) ) )


#-------------------------------------------------------------------------------


def worker( queue , id ) :
    """ worker function executed by worker subprocesses """

    #def signal_handler(sig, frm): raise KeyboardInterrupt
    #signal.signal( signal.SIGINT,  signal_handler )
    # use the dummy hadlers
    signal.signal( signal.SIGINT,  signal_handler_dummy )
    #signal.signal( signal.SIGTERM, signal_handler_dummy )

    try :

        while True :

            try :
                item = queue.get()
            except IOError as e :
                warn( str(e) )
                continue

            # gracefull termination
            if ( item is None ) : break

            # run the task
            taskDispatch( item , id )

    except (KeyboardInterrupt,SystemExit): pass

    info( "[%3.3i] PROCESS: termination " % id )

def cleanup() :
    """ cleanup function performing reenquing of zombie tasks """

    tasks = dbLocker( dbLock , reenqueueZombieTasks , "Reenqueued by ATPD after timeout." )

    for (id,task) in tasks :
        warn( "[MASTER] Task %i:%s renqueued after timeout!"%(id,task) )

    tasks = dbLocker( dbLock , deleteRetiredTasks )

    for (id,task) in tasks :
        info( "[MASTER] Task %i:%s deleted after expiration!"%(id,task) )


class WorkerPool( object ) :

    def __init__( self , nthread ) :

        self.queue     = Queue( nthread )
        self.terminate = False
        self.killChild = False
        self.proces    = []

        # start subprocesses
        for i in xrange( nthread ) :
            p = Process( target=worker , args=( self.queue , i ) )
            p.start()
            self.proces.append(p)


    def __del__( self ) :

        # if possible process gracefull termination
        debug( "[MASTER]: enqueueing terminators ... " )
        for p in self.proces :
            self.queue.put( None )

        if not self.killChild :
            debug( "[MASTER]: joining subprocesses ... " )
            for p in self.proces :
                p.join()
        else :
            debug( "[MASTER]: terminating subprocesses ... " )
            for p in self.proces :
                p.terminate()


    def startLoop( self ) :

        # reenqueue hanging tasks
        # TODO: reenqueuePendingTasks()

        cnt = 0
        taskIds = []
        self.terminate = False

        while not self.terminate :

            try:

                # get a pending task from the queue
                taskIds = dbLocker( dbLock , dequeueTask , SERVER_ID )

            except QueueEmpty : # no task to be processed

                # perform DB cleanup
                cleanup()

                # wait some ammount of time
                time.sleep( QUEUE_EMPTY_QUERY_DELAY )

                # clear counter
                cnt = 0

                continue

            # send task to worker
            for taskId in list(taskIds) :
                while not self.terminate :
                    try : self.queue.put(taskId,True,QUEUE_PUT_TIMEOUT)
                    except MPQFull : continue
                    taskIds.remove(taskId)
                    break

            # increment counter
            cnt += 1

            # perform DB cleanup
            if ( cnt > QUEUE_CLEAN_UP_COUNT ) :
                cleanup()
                cnt = 0

        info( "[MASTER]: termination in progress ... " )

        # try to reenequeue processes taken from the DB task queue
        for item in taskIds :
            debug( "[MASTER]: reenquing task ID=%i ... " % item )
            dbLocker( dbLock , reenqueueTask , item , message = "Reenqued by ATPD." )
        try:
            while True :
                item = self.queue.get(False)
                debug( "[MASTER]: reenquing task ID=%i ... " % item )
                dbLocker( dbLock , reenqueueTask , item , message = "Reenqued by ATPD." )
        except MPQEmpty : pass
#-------------------------------------------------------------------------------

def usage() :
    """ print usage info """

    s = []
    s.append( "USAGE: %s [-h][-p <directory>][-s <module>][-d <db name>][-n <integer>] " % ( os.path.basename( sys.argv[0] ) ) )
    s.append( "" )
    s.append( "PARAMETERS: " )
    s.append( "    -h   print this info" )
    s.append( "    -p   append an addition Python search path (can be repeated)" )
    s.append( "    -n   number of worker instance to be started ( N >= 1 , number of CPUs used by default )" )
    s.append( "    -s   django settings module (default '%s')"%DJANGO_SETTINGS_DEFAULT )
    #s.append( "    -d   django DB name (default '%s')"%DJANGO_DB_DEFAULT )
    s.append( "" )

    return "\n".join(s)


#-------------------------------------------------------------------------------

if __name__ == "__main__" :

    # django settings module

    DJANGO_SETTINGS = os.environ.get("DJANGO_SETTINGS_MODULE",DJANGO_SETTINGS_DEFAULT)
    DJANGO_DB       = DJANGO_DB_DEFAULT

    # try to get number of CPUs

    try :
        NTHREAD = cpu_count()
    except NotImplementedError :
        NTHREAD = 1
        warn( "Failed to get number of CPUs! Setting to 1 asynchronous execution thread." )

    info( "Default number of working threads: %i" % NTHREAD )

    # parse commandline arguments

    idx = 1
    while idx < len(sys.argv) :
        arg = sys.argv[idx] ; idx +=1 ;
        if arg == '-p' :
            sys.path.append( sys.argv[idx] )
            info("'%s' ... adding to Python search path." % sys.argv[idx] )
            idx += 1
        elif arg == '-s' :
            DJANGO_SETTINGS = sys.argv[idx]
            idx += 1
        elif arg == '-d' :
            DJANGO_DB = sys.argv[idx]
            idx += 1
        elif arg == '-n' :
            NTHREAD = max( 1 , int(sys.argv[idx]) )
            info("Setting number of working threads to: %i" % NTHREAD )
            idx += 1
        elif arg == '-h' :
            sys.stderr.write(usage()) ; sys.exit(0)
        else :
            sys.stderr.write(usage())
            error( "Invalid commandline option '%s' !" % arg )
            sys.exit(1)

    #-------------------------------------------------------------------
    # initialize the working enviroment

    # django settings module
    os.environ["DJANGO_SETTINGS_MODULE"] = DJANGO_SETTINGS
    info("'%s' ... is set as the Django settings module " % DJANGO_SETTINGS )
    info("'%s' ... is set as the Django database " % DJANGO_DB )

    #usingDB = DJANGO_DB # ???

    # once the search path is set -> load the required modules
    from eoxserver.core.system import System
    from eoxserver.resources.processes.tracker import TaskStatus, QueueEmpty, \
            dequeueTask, startTask, reenqueueTask, stopTaskSuccessIfNotFinished, \
            reenqueueZombieTasks, deleteRetiredTasks, dbLocker

    # initialize the system
    System.init()
    #-------------------------------------------------------------------

    info( "ATPD Asynchronous Task Processing Daemon has just been started!")
    info( "ATPD: id=%s (%i)" % ( SERVER_ID_STR , SERVER_ID ) )
    info( "ATPD: hostname=%s" % socket.getfqdn() )
    info( "ATPD: pid=%i " % os.getpid() )

    #-------------------------------------------------------------------
    # start the worker pool

    GWP = WorkerPool( NTHREAD )

    # use the GWP terminating hadlers
    signal.signal( signal.SIGINT,  signal_handler_sigint )
    signal.signal( signal.SIGTERM, signal_handler_sigterm )

    # start the main loop
    GWP.startLoop()

    # use the dummy hadlers
    signal.signal( signal.SIGINT,  signal_handler_dummy )
    signal.signal( signal.SIGTERM, signal_handler_dummy )

    del GWP
