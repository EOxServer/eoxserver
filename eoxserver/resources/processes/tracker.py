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

class QueueException( Exception ) : pass 
class QueueEmpty( QueueException ) : pass 
class QueueFull( QueueException ) : pass 
class TaskTypeException( Exception ) : pass 
class TaskTypeHasInstances( TaskTypeException ) : pass 

#-------------------------------------------------------------------------------
# define queue size - TODO: make this value configurable 

MAX_QUEUE_SIZE=64  

#-------------------------------------------------------------------------------

# dummy lock class 

class DummyLock : 
    """ dummy lock class """ 
    def acquire( self ) : pass 
    def release( self ) : pass 


# function wrapper guaranting exclusive access to the DB 

def dbLocker( dbLock , func , *prm , **kprm ) :
    """ grants exlusive DB access while executes the passed function """ 
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
    """ 
        task status changing class passed to the ATP handler function

        the status setting internally lock the access to the DB using 
        the user provided dbLock. In case the dbLock is not provided 
        the locking is not performed.

        The dbLock must be a class instace providing two methos: 
        dbLock.acquire() and dbLock.release() 
    """ 
    # --------------------
    # constructor

    def __init__( self , task_id , dbLock = None ) : 
        self.task_id = task_id 
        self.dbLock  = dbLock if ( dbLock is not None ) else DummyLock() ; 

    # --------------------
    # info getters 

    def getInfo( self ) :
        """ get short info about the task - tuple of task Type and Instance identifiers, status, status string """
        return dbLocker( self.dbLock , getTaskInfo , self.task_id )

    def getIdentifier( self ) : 
        """ get tuple of task Type and Instance identifiers """
        return dbLocker( self.dbLock , getTaskIdentifier , self.task_id )

    # --------------------
    # status getter

    def getStatus( self ) : 
        """ get task status (tuple of the integer code and the string label) """
        return dbLocker( self.dbLock , getTaskStatus , self.task_id )

    # --------------------
    # status setters

    def setSuccess( self , message = "" ) : 
        """ set task status to FINISHED (aka success) """
        dbLocker( self.dbLock , stopTaskSuccess , self.task_id , message )

    def setFailure( self , message = "" ) : 
        """ set task status to FAILED """
        dbLocker( self.dbLock , stopTaskFailure , self.task_id , message )

    def setPaused( self , message = "" ) : 
        """ set task status to FAILED """
        dbLocker( self.dbLock , pauseTask , self.task_id , message )

    def setRunning( self , message = "" ) : 
        """ set task status to RUNNING """
        dbLocker( self.dbLock , resumeTask , self.task_id , message )

    # --------------------
    # response setters

    def storeResponse( self, response ) : 
        """ store the task response """
        dbLocker( self.dbLock , setTaskResponse , self.task_id , response )

# define status constants 

for key , val in TEXT2STATUS.items() : 
    setattr( TaskStatus , key , val ) 

#-------------------------------------------------------------------------------
# Task Type operations 

def registerTaskType( identifier , handler , timeout = 3600 , timeret = -1 , maxstart = 3 ) : 
    """ register new task Type, its handler (python dot path to subroutine) and optionally 
        also the task timeout in sec. (after which the task is restarted; default 3600), 
        retention time (time to keep finished task stored, for 0 or negative number the 
        task is kept forever, default -1), and finally the max. number of attempts to start
        the task including the initial start and timeout restarts (when exceeded, the task is 
        labelled as FAILED and not restarted any more; default 3) 

        When called repeatedly with the same task identifier, the first run creates new task types 
        and the subsequent calls update the task type parameters.
    """

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
    """ unregister task Type 

        By default the task Type removal will be blocked if there is any existing task 
        Instance of this type throwing a TaskTypeHasInstances exception.

        To force the Type removal wiping out the linked Instances set the 'force' parameter 
        to True.  
    """

    # MP: the instances are now protected against the cascade delete 

    if force : # remove all type instances 
        Type.objects.get( identifier=identifier ).instance_set.all().delete()  

    Type.objects.get( identifier=identifier ).delete() 

#-------------------------------------------------------------------------------
# Task Status Log Record creation 

def _logStatusChange( obj , message ): 

    obj.logrecord_set.create( time=obj.timeUpdate , status=obj.status , message=message )

#-------------------------------------------------------------------------------
# Task Queue Inspection 

def getQueueSize() :
    """ get number of enqueues tasks """ 
    return Task.objects.filter(lock=0).count()

def getMaxQueueSize() :
    """ get the max. allowed number of task the queue hold""" 
    return MAX_QUEUE_SIZE

#===============================================================================
# Task Instance operations 

#-------------------------------------------------------------------------------
# inspection 

def getTaskInfo( task_id ) : 
    """ for a task identified by the task_id get tuple of Type and Instance identifiers, Instance status and corresponding status string """   
    _inst = Instance.objects.get( id = task_id )
    return ( _inst.type.identifier , _inst.identifier , _inst.status , STATUS2TEXT[_inst.status] ) 

def getTaskIdentifier( task_id ) :
    """ for a task identified by the task_id get tuple of Type and Instance identifiers """   
    _inst = Instance.objects.get( id = task_id )
    return ( _inst.type.identifier , _inst.identifier ) 

def getTaskStatus( task_id ) :
    """ for a task identified by the task_id get tuple of Instance status and corresponding status string """   
    _inst = Instance.objects.get( id = task_id )
    return ( _inst.status , STATUS2TEXT[_inst.status] ) 

#-------------------------------------------------------------------------------
# single task manipulations 

def deleteTaskById( task_id ) : 
    """ delete task Instance of the given record ID """ 
   
    Instance.objects.filter( id = task_id ).delete()  

def deleteTask( identifier ) : 
    """ delete task Instance of the given task identifier """ 
   
    Instance.objects.filter( identifier = identifier ).delete()  

#-------------------------------------------------------------------------------

def enqueueTask( type , identifier , input , message = "" ) :
    """ create a new task Instance of the 'type' (Type identifier)
        using the given identifier and inputs and enqueue the 
        task for processing. The task status is set to ACCEPTED.  
        The input can be anything serializable by the 'pickle' module. 
        The optional log message can be specified.  

        In case the actual queue size exceeds the queue size limit 
        the QueueFull exception is thrown. 
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
    """ re-enqueue an existing task Instance identified by the given record ID 
        and set its status to ACCEPTED. 
        The optional log message can be specified.  

        The task enqueue is always performed and can possibly increase the task queue size 
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
    """ 
        try to dequeue a single task from the pending task queue. 

        An unique serverID must be provided to prevent collisions with the other 
        servers pulling tasks from the queue. 

        The function returns list of the dequeue tasks. There is rare but still possible 
        chance that the function returns either zero or more than one tasks and 
        the user must take this into consideration. 

        The returned dequeued tasks are set to have status SCHEDULED. 

        In case of an empty queue the QueueEmpty exception is risen. 
    """

    while True : 
        # identify taks candidate 
        try : 

            id = Task.objects.filter( lock=0 ).order_by("time")[:1].get().id 

        except Task.DoesNotExist : 

            raise QueueEmpty 
    
        # lock candidate assuming atomicity of a single SQL UPDATE statement  
        if ( Task.objects.filter( id=id , lock=0 ).update( lock=serverID ) ) :
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
    """ 
        get the inputs of the task Instance identified by the given record ID
        and set the task's status to RUNNING 
    """

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

    _inst = Instance.objects.get( id = task_id ) 

    # change objects status 
    _inst.status = status  
    _inst.save() 

    # log status change 
    _logStatusChange( Instance.objects.get( id = task_id ) , message )  

def _getTaskStatus( task_id ) : 
    
    return Instance.objects.get( id = task_id ).status 


def stopTaskSuccessIfNotFinished( task_id , message = "" ) :
    """ set status of task instance identified by the given record ID 
        to FINISHED if its status has not been already set to FINISHED
        or FAILED yet
    """ 
    if _getTaskStatus( task_id ) not in ( TaskStatus.FINISHED , TaskStatus.FAILED ) : 
        _setTaskStatus( task_id , message , TaskStatus.FINISHED ) 

def stopTaskSuccess( task_id , message = "" ) : 
    """ set status of task instance identified by the given record ID to FINISHED """
    _setTaskStatus( task_id , message , TaskStatus.FINISHED ) 

def stopTaskFailure( task_id , message = "" ) : 
    """ set status of task instance identified by the given record ID to FAILED """
    _setTaskStatus( task_id , message , TaskStatus.FAILED ) 

def pauseTask( task_id , message = "" ) : 
    """ set status of task instance identified by the given record ID to PAUSED """
    _setTaskStatus( task_id , message , TaskStatus.PAUSED ) 

def resumeTask( task_id , message = "" ) : 
    """ set status of task instance identified by the given record ID to RUNNING """
    _setTaskStatus( task_id , message , TaskStatus.RUNNING ) 

#-------------------------------------------------------------------------------
#task response manipulation 

def setTaskResponse( task_id , response ) : 
    """ for task Instance identified by the given record ID set the response data 
        
        The response is expected to be python string (Text). However binary data 
        (such as pickled data) may be used as well
    """

    _inst = Instance.objects.get( id = task_id ) 

    # save the response  
    _inst.response_set.create( response = base64.b64encode( zlib.compress( response ) ) )  


def getTaskResponse( type , identifier ) : 
    """ for task Instance identified by the given record ID return the response data 
        
        The response is expected to be python string (Text). However binary data 
        (such as pickled data) may be used as well
    """

    _type = Type.objects.get( identifier=type ) 

    _inst = _type.instance_set.get( identifier=identifier ) 

    _resp = _inst.response_set.get() 

    return zlib.decompress( base64.b64decode( _resp.response ) ) 

#-------------------------------------------------------------------------------
# clean-up functions 

def reenqueueZombieTasks( message = "" ) : 
    """ find tasks exceeding their timeout and try to reenqueue them again 
        for processing. Tasks exceeding the number of allowed start are rejected 
        marking them as FAILED 
    """
    
    # TODO restart limit 

    STATUS = (TaskStatus.PAUSED,TaskStatus.RUNNING,TaskStatus.SCHEDULED)

    l = [] 

    for ttype in Type.objects.all() : 

        # reference time to detect timedout tasks 
        timeRef = datetime.datetime.today() - datetime.timedelta(0,ttype.timeout)
        
        for task in ttype.instance_set.filter( status__in = STATUS , timeUpdate__lt = timeRef ) : 

            l.append( ( task.id , str(task) ) ) 

            # reenqueue timed-out tasks 
            reenqueueTask( task.id , message ) 

    return l 



def deleteRetiredTasks() : 
    """ find finished task Instances (FINISHED or FAILED) exceeding their retention
        time and remove them 
    """ 

    STATUS = (TaskStatus.FINISHED,TaskStatus.FAILED)

    l = [] 

    for ttype in Type.objects.all() : 

        # skip types with no timeout 
        if ( ttype.timeret <= 0 ) : continue 

        # reference time to detect timedout tasks 
        timeRef = datetime.datetime.today() - datetime.timedelta(0,ttype.timeret)

        for task in ttype.instance_set.filter( status__in = STATUS , timeUpdate__lt = timeRef ) : 

            l.append( ( task.id , str(task) ) ) 

            deleteTaskById( task.id ) 

    return l 

#-------------------------------------------------------------------------------

