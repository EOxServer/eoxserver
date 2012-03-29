#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#  asynchronous process API 
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
"""This module contains the process tracker API. Process tracker is an essential part 
of the ATP (Asynchronous Task Processing) subsystem. """

#-------------------------------------------------------------------------------
import zlib
import base64 
import time 
import datetime 

try:    import cPickle as pickle
except: import pickle

from eoxserver.resources.processes.models import Type, Instance, Task, LogRecord, Response, Input
from eoxserver.resources.processes.models import STATUS2TEXT, TEXT2STATUS

#-------------------------------------------------------------------------------
# Task Queue Exceptions 

class QueueException( Exception ) : 
    """Task queue base exception.""" 

class QueueEmpty( QueueException ) : 
    """Queue exception signalising that the task queue is empty
    and no task can be pulled from it.""" 

class QueueFull( QueueException ) :
    """Queue exception signalising that the task queue is full
    and no task can be pushed to it.""" 

#-------------------------------------------------------------------------------
# define queue size - TODO: make this value configurable 

#: Actual queue size limit. 
#: Note may be removed in the future. Use 'getMaxQueueSize()' instead.
MAX_QUEUE_SIZE=64

#-------------------------------------------------------------------------------

def dummyHandler( taskStatus , input ) :
    """ Dummy ATP handler. No action implemented. 

    Prototype of an ATP handler subroutine. 

    Any ATP handler receives two parameters: 

       * 'taskStatus' - an instance of TaskStatus class 
         providing access the the actual task, 

       * 'input' - input parameters specified during the 
         task enqueueing. 
    
    """ 

# dummy lock class 

class DummyLock : 
    """ Dummy (default) lock class implementing lock interface.""" 
    def acquire( self ) : 
        """Acquire DB lock. No action impelemented!""" 

    def release( self ) :
        """Release DB lock. No action impelemented!""" 


# function wrapper guaranting exclusive access to the DB 

def dbLocker( dbLock , func , *prm , **kprm ) :
    """Grant exclusive DB access while executing the passed function.
    The 'dbLocker' function executes the 'dbLock.acquire()' and 'dbLock.release()' 
    methods on entry and exit, respectively, assuring the executed 
    function 'func' has an exclusive access to the DB. 'prm' and 'kprm' 
    are the optional 'func' function parameters. 
    The 'dbLocker' function returns the returning value of the passed
    'func' function. """ 

    dbLock.acquire()
    try: 
        rv = func( *prm , **kprm ) 
    except: 
        dbLock.release()
        raise 
    dbLock.release()
    return rv 


# task status class 

class TaskStatus : 
    """ TaskStatus provides an interface to current asynchronous 
    task. An instance of this class is exepected to be passed as 
    an input parameter to the ATP handler function when executed 
    by the ATPD. 

     * 'task_id' in an unique task identifier (string). 

     * dbLock' can be None or any class instance providing two members: 
       'dbLock.acquire()' and 'dbLock.release()'. 

    The status changing member function internally lock the access
    to the DB using the user provided 'dbLock'. In case the 'dbLock' 
    is not provided the locking is not performed (see also 'DummyLock' class).
    """ 
    # --------------------
    # constructor

    def __init__( self , task_id , dbLock = None ) : 
        """ TaskStatus constructor 

        """
        self.task_id = task_id 
        self.dbLock  = dbLock if ( dbLock is not None ) else DummyLock() ; 

    # --------------------
    # info getters 

    def getInfo( self ) :
        """Get short info about the task. Returns tuple of Type identifier,
        Instance identifier, status, and status string."""
        return dbLocker( self.dbLock , getTaskInfo , self.task_id )

    def getIdentifier( self ) : 
        """Get tuple of task Type and Instance identifiers."""
        return dbLocker( self.dbLock , getTaskIdentifier , self.task_id )

    # --------------------
    # status getter

    def getStatus( self ) : 
        """Get task status as tuple of the integer code and the string label."""
        return dbLocker( self.dbLock , getTaskStatus , self.task_id )

    # --------------------
    # status setters

    def setSuccess( self , message = "" ) : 
        """Set task status to FINISHED (i.e., success)."""
        dbLocker( self.dbLock , stopTaskSuccess , self.task_id , message )

    def setFailure( self , message = "" ) : 
        """Set task status to FAILED."""
        dbLocker( self.dbLock , stopTaskFailure , self.task_id , message )

    def setPaused( self , message = "" ) : 
        """Set task status to PAUSED."""
        dbLocker( self.dbLock , pauseTask , self.task_id , message )

    def setRunning( self , message = "" ) : 
        """Set task status to RUNNING."""
        dbLocker( self.dbLock , resumeTask , self.task_id , message )

    # --------------------
    # response setters

    def storeResponse( self, response , mimeType = "text/xml" ) : 
        """Store the task response.
        
        The response is expected to be python string (Text). However 
        binary data (such as pickled data) may be used as well.
        """

        dbLocker( self.dbLock , setTaskResponse , self.task_id , response , mimeType )

# define status constants 

for key , val in TEXT2STATUS.items() : 
    setattr( TaskStatus , key , val ) 

#-------------------------------------------------------------------------------
# Task Type operations 

def registerTaskType( identifier , handler , timeout = 3600 , timeret = -1 , maxrestart = 2 ) : 
    """ Register new task type. 
    
    The task type 'identifier' string and 'handler' subroutine must be specified.
    The string identifier must uniquely identify the created task type.  

    Optionally, the parameters such as: task 'timeout' in sec. after which the task is restarted
    (re-enqueued for new processing), retention time ('timeret'), i.e., the time to keep finished 
    tasks stored in DB, for any non-positive number the task is kept forever), and finally the max.
    allowed number of task's restarts caused by task time-out ('maxrestart').
    When the number of restarts is exceeded, the task is labelled as FAILED and 
    not re-enqueued any more).

    When called repeatedly with the same task identifier, the first run creates new task types 
    and the subsequent calls update the task type parameters."""

    timeout  =max(0,timeout)
    timeret  = timeret if ( timeret > 0 ) else -1
    maxstart = 1 + max(0,int(maxrestart))

    try: # update existing 

        obj = Type.objects.get( identifier=identifier ) ; 

        obj.handler=handler 
        obj.timeout=timeout
        obj.timeret=timeret
        obj.maxstart=maxstart

    except Type.DoesNotExist : # insert new

        obj = Type( identifier=identifier , handler=handler , timeout=timeout , timeret=timeret , maxstart=maxstart )

    obj.save() 


def unregisterTaskType( identifier , force = False ) : 
    """ Unregister (remove) an existing task Type.

    By default, the task Type removal will fail as long as there is an existing task
    Instance raising 'django.db.models.ProtectedError' exception (a subclass of 
    django.db.IntegrityError). 

    To force the Type removal wiping out all the linked Instances set the 'force' parameter 
    to True."""

    # MP: the instances are now protected against the cascade delete 

    if force : # remove all type instances 
        Type.objects.get( identifier=identifier ).instance_set.all().delete()  

    Type.objects.get( identifier=identifier ).delete() 

#-------------------------------------------------------------------------------
# Task Status Log Record creation 

def _logStatusChange( obj , message ): 
    """ auxiliary function """ 

    obj.logrecord_set.create( time=obj.timeUpdate , status=obj.status , message=message )

#-------------------------------------------------------------------------------
# Task Queue Inspection 

def getQueueSize() :
    """Get number of enqueued tasks.""" 
    return Task.objects.filter(lock=0).count()

def getMaxQueueSize() :
    """Get the maximum allowed number of task the queue can hold.""" 
    return MAX_QUEUE_SIZE

#===============================================================================
# Task Instance operations 

#-------------------------------------------------------------------------------
# inspection 

def getTaskInfo( task_id ) : 
    """Get tuple of Type identifier, Instance identifiers, Instance status and corresponding status string """   
    _inst = Instance.objects.get( id = task_id )
    return ( _inst.type.identifier , _inst.identifier , _inst.status , STATUS2TEXT[_inst.status] ) 

def getTaskIdentifier( task_id ) :
    """Get tuple of Type and Instance identifiers."""   
    _inst = Instance.objects.get( id = task_id )
    return ( _inst.type.identifier , _inst.identifier ) 

def getTaskStatus( task_id ) :
    """Get tuple of Instance status and corresponding status string.
    'task_id' is the DB record ID."""   
    _inst = Instance.objects.get( id = task_id )
    return ( _inst.status , STATUS2TEXT[_inst.status] ) 

def getTaskStatusByIdentifier( type , identifier ) : 
    """Get tuple of Instance status and corresponding status string.
    'type' is the Type string ID and 'identifier' is the Instance string ID."""
    _type = Type.objects.get( identifier=type ) 
    _inst = _type.instance_set.get( identifier=identifier )
    return ( _inst.status , STATUS2TEXT[_inst.status] ) 


#-------------------------------------------------------------------------------
# single task manipulations 

def deleteTask( task_id ) : 
    """Delete task Instance. 'task_id' is the DB record ID.""" 
    Instance.objects.filter( id = task_id ).delete()  

def deleteTaskByIdentifier( type , identifier ) : 
    """Delete task Instance. 
    'type' is the Type string ID and 'identifier' is the Instance string ID."""
    Type.objects.get( identifier=type ).instance_set.filter( identifier=identifier ).delete() 

#-------------------------------------------------------------------------------

def enqueueTask( type , identifier , input , message = "" ) :
    """ Create new task Instance of the given Type using the given 
    identifier and task inputs and enqueue this task for processing. 
    The task status is set to ACCEPTED.  

    The 'type' parameter should be the string identifier of a registered 
    task type. The string 'identifier' shall uniquely identify the created 
    task. 

    The 'input' can be any Python object serializable by the 'pickle' module. 

    The optional log 'message' can be specified.  

    In case of full task queue the QueueFull exception is risen.  
    """

    # check the queueu size 
    if getQueueSize() >= getMaxQueueSize() : 
        raise QueueFull 

    _type = Type.objects.get( identifier=type ) 

    _inst = _type.instance_set.create( identifier=identifier , status=TaskStatus.ACCEPTED ) 
        
    # log status change 
    _logStatusChange( _inst , message )
 
    # insert input picked inputs 
    _inst.input_set.create( input = base64.b64encode( zlib.compress( pickle.dumps( input ) ) ) )  
      
    # enqueue task 
    _inst.task_set.create( lock = 0 , time = _inst.timeInsert ) 


def reenqueueTask( task_id , message = "" ) : 
    """ Re-enqueue an existing task Instance identified by the given DB record ID 
    and set its status to ACCEPTED. The optional log message can be specified.  

    The task is always enqueued and can possibly increase the task queue size 
    beyond queue size limit. 
    """

    _inst = Instance.objects.get( id = task_id ) 

    # change objects status 
    _inst.status = TaskStatus.ACCEPTED
    _inst.save() 

    # log status change 
    _logStatusChange( _inst , message )

    # enqueue task 
    _inst.task_set.create( lock = 0 , time = _inst.timeInsert ) 


#-------------------------------------------------------------------------------

def dequeueTask( serverID , message = "" ) : 
    """ Attempt to dequeue a single task from the task queue. 
    An unique serverID must be provided to prevent collisions with the other 
    ATPDs pulling tasks from the same queue. 

    The function returns list of the dequeue tasks. There is rare but still 
    possible chance that the function returns either zero or more than one 
    tasks and the user must take this into consideration. 

    The returned dequeued tasks' status is set to SCHEDULED. 

    In case of an empty queue the QueueEmpty exception is risen."""

    while True : 
        # identify taks candidate 
        try : 

            id = Task.objects.filter( lock=0 ).order_by("time")[:1].get().id 

        except Task.DoesNotExist : 

            raise QueueEmpty 
    
        # lock candidate assuming atomicity of a single SQL UPDATE statement  
        if ( Task.objects.filter( id=id , lock=0 ).update( lock=serverID , time = datetime.datetime.now() ) ) :
            break 
            
    # Process locked objects 
    idx = []
    for item in Task.objects.filter( lock=serverID ).order_by("time") : 
        
        # keep the instance ID  
        idx.append( item.instance_id ) 

        # change objects status 
        item.instance.status = TaskStatus.SCHEDULED 
        item.instance.save() 

        # log status change 
        _logStatusChange( Instance.objects.get( id = item.instance_id ) , message )  

        # delete item 
        item.delete() 

    return idx 

#-------------------------------------------------------------------------------

def startTask( task_id , message = "" ) : 
    """Get the inputs of the task Instance identified by the given DB record ID
    and set the task's status to RUNNING"""

    _inst = Instance.objects.get( id = task_id ) 

    # extract data 
    typeID = _inst.type.identifier 
    typeHn = _inst.type.handler
    instID = _inst.identifier
    input  =  pickle.loads( zlib.decompress( base64.b64decode( _inst.input_set.get().input ) ) )  
    
    # change objects status 
    _inst.status = TaskStatus.RUNNING 
    _inst.save() 

    # log status change 
    _logStatusChange( Instance.objects.get( id = task_id ) , message )  

    return ( typeID , instID , typeHn , input )


#-------------------------------------------------------------------------------
# simple task status setting 

def _setTaskStatus( task_id , message , status ) : 
    """ auxiliary function """ 

    _inst = Instance.objects.get( id = task_id ) 

    # change objects status 
    _inst.status = status  
    _inst.save() 

    # log status change 
    _logStatusChange( Instance.objects.get( id = task_id ) , message )  

def _getTaskStatus( task_id ) : 
    """ auxiliary function """ 
    
    return Instance.objects.get( id = task_id ).status 


def stopTaskSuccessIfNotFinished( task_id , message = "" ) :
    """Set status of task Instance identified by the given DB record ID 
    to FINISHED if its status has not been set to FINISHED
    or FAILED yet.""" 

    if _getTaskStatus( task_id ) not in ( TaskStatus.FINISHED , TaskStatus.FAILED ) : 
        _setTaskStatus( task_id , message , TaskStatus.FINISHED ) 

def stopTaskSuccess( task_id , message = "" ) : 
    """Set status of task Instance identified by the given DB record ID to FINISHED."""
    _setTaskStatus( task_id , message , TaskStatus.FINISHED ) 

def stopTaskFailure( task_id , message = "" ) : 
    """Set status of task instance identified by the given DB record ID to FAILED."""
    _setTaskStatus( task_id , message , TaskStatus.FAILED ) 

def pauseTask( task_id , message = "" ) : 
    """Set status of task instance identified by the given DB record ID to PAUSED."""
    _setTaskStatus( task_id , message , TaskStatus.PAUSED ) 

def resumeTask( task_id , message = "" ) : 
    """Set status of task instance identified by the given DB record ID to RUNNING."""
    _setTaskStatus( task_id , message , TaskStatus.RUNNING ) 

#-------------------------------------------------------------------------------
#task response manipulation 

def setTaskResponse( task_id , response , mimeType = "text/xml" ) : 
    """Set response of task Instance identified by the given DB record ID.
        
    The response is expected to be python string (Text). However binary data 
    (such as pickled data) may be used as well.
    
    It is safe to call this function repeatedly. First call creates a new Response 
    record and the successive calls update the existing Response record. 
    """

    _inst = Instance.objects.get( id = task_id ) 

    _tmp = base64.b64encode( zlib.compress( response ) )  

    try: # try to update existing response first 

        _resp = Response.objects.get( instance = _inst )
        _resp.mineType = mimeType 
        _resp.response = _tmp 
        _resp.save() 

    except Response.DoesNotExist : # create new response  

        _inst.response_set.create( mimeType = mimeType , response = _tmp )  


def getTaskResponse( type , identifier ) : 
    """Return a tuple of task response and its MIME type. Task Instance
    is identified by an unique pair of Type and Instance string identifiers 
    'type' and 'identifier', respectively.
        
    The response is expected to be python string (Text). However binary data 
    (such as pickled data) may be used as well."""

    _type = Type.objects.get( identifier=type ) 
    _inst = _type.instance_set.get( identifier=identifier )
    _resp = _inst.response_set.get() 

    return ( zlib.decompress( base64.b64decode( _resp.response ) ) , _resp.mimeType ) 

#-------------------------------------------------------------------------------
# log message extraction 

def getTaskLog( type , identifier ) : 
    """Return list of log records sorted by time for the task identified by 
    the task Type and Instance identifiers. Each log record is a tuple 
    of three fields: time-stamp, status tuple (see get task status), and logged
    message."""

    _type = Type.objects.get( identifier=type ) 
    _inst = _type.instance_set.get( identifier=identifier )

    log = []

    for item in LogRecord.objects.filter( instance = _inst ).select_related().order_by("time") :
        log.append( ( item.time , ( item.status , STATUS2TEXT[item.status] ) , item.message ) ) 

    return log 

#-------------------------------------------------------------------------------
# clean-up functions 

def reenqueueZombieTasks( message = "" ) : 
    """Find all tasks exceeding their time-out and try to re-enqueue them again.
    Tasks exceeding the number of allowed start are rejected and marked as FAILED."""
    
    # TODO restart limit 

    PULL_TIMEOUT = 60 
    STATUS = (TaskStatus.PAUSED,TaskStatus.RUNNING,TaskStatus.SCHEDULED)

    l = [] 

    for ttype in Type.objects.all() : 

        # reference time to detect timedout tasks 
        timeRef = datetime.datetime.today() - datetime.timedelta(0,ttype.timeout)
        
        # detect tasks pulled by ATPD 
        for _inst in ttype.instance_set.filter( status__in = STATUS , timeUpdate__lt = timeRef ) : 

            l.append( ( _inst.id , str(_inst) ) ) 

            # reenqueue timed-out tasks 
            reenqueueTask( _inst.id , message ) 

    # reference time to detect timedout tasks 
    timeRef = datetime.datetime.today() - datetime.timedelta(0,PULL_TIMEOUT)

    # detect tasks stacked during the pulling  
    for _task in Task.objects.exclude( lock = 0 ).filter( time__lt = timeRef ) : 

        id = _task.instance_id 
        l.append( ( id , str(_task.instance) ) ) 

        # set status to SCHEDULED 
        Instance.objects.filter( id = id ).update( status = TaskStatus.SCHEDULED ) 

        # remove queue entry 
        _task.delete() 

        # reenqueue timed-out tasks 
        reenqueueTask( id , message ) 

    return l 


def deleteRetiredTasks() : 
    """Find all FINISHED or FAILED task Instances exceeding their retention 
    time and remove them.""" 

    STATUS = (TaskStatus.FINISHED,TaskStatus.FAILED)

    l = [] 

    for ttype in Type.objects.all() : 

        # skip types with no timeout 
        if ( ttype.timeret <= 0 ) : continue 

        # reference time to detect timedout tasks 
        timeRef = datetime.datetime.today() - datetime.timedelta(0,ttype.timeret)

        for task in ttype.instance_set.filter( status__in = STATUS , timeUpdate__lt = timeRef ) : 

            l.append( ( task.id , str(task) ) ) 

            deleteTask( task.id ) 

    return l 

#-------------------------------------------------------------------------------

