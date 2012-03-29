#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#  processes - django DB model 
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
"""This module contains the process tracker Django DB model. Process tracker 
is an essential part of the ATP (Asynchronous Task Processing) subsystem. """

#-------------------------------------------------------------------------------

from django.db import models

#-------------------------------------------------------------------------------

#: status code to text conversion dictionary
STATUS2TEXT  = { 0:"UNDEFINED", 1:"ACCEPTED", 2:"SCHEDULED", 3:"RUNNING", 4:"PAUSED", 5:"FINISHED", 6:"FAILED" } 

#: status code to color conversion dictionary
STATUS2COLOR = { 0:"magenta", 1:"brown", 2:"darkcyan", 3:"green", 4:"maroon", 5:"blue", 6:"red" } 

#: status text to code reverse conversion dictionary (filled dynamically) 
TEXT2STATUS  = dict( map( lambda item : ( item[1] , item[0] ) , STATUS2TEXT.items() ) )

#-------------------------------------------------------------------------------

class Type( models.Model ) : 
    """ 
        Task Type.
        
        DB fields: 
            identifier   - process class ID; 
            handler      - python dot path to handler function;
            timeout      - time in second after which the unfinished process is 
                           considered to be abandoned and it is restarted 
                           (number of restarts is limited by maxstart, default timeout is 3600 s);
            timeret      - retention time - period of time to keep finished processes
                           in case of zero or negative value the results will be kept forever 
                           (default is -1);
            maxstart     - max. number of attempt to execute the task (first run and possible restarts)
                           When the number of (re)starts is exceeded the task is marked as failed 
                           and rejected from further processing. (default is 3).

    """
    identifier = models.CharField( max_length=64   , unique=True , blank=False , null=False, editable = False )
    handler    = models.CharField( max_length=1024 , blank=False , null=False, editable = False )
    maxstart   = models.IntegerField( default = 3 , blank = False , null = False , editable = False ) 
    timeout    = models.FloatField( default = 3600.0 , blank = False , null = False , editable = False ) 
    timeret    = models.FloatField( default = -1.0 , blank = False , null = False , editable = False ) 

    def __unicode__( self ) :
        return unicode( self.identifier ) 

    def __str__( self ) : return unicode(self).encode("utf8")

    class Admin : pass


class Instance( models.Model ) : 
    """ 
        Task Instance.

        DB fields: 
            type         - process class of this instance;
            identifier   - process instance ID;
            status       - current status of the process; 
            timeInsert   - instance creation time (aka enqueue or insert time );
            timeUpdate   - instance last status update time.

    """
    type        = models.ForeignKey( Type , blank=False , null=False , editable = False , on_delete = models.PROTECT ) 
    identifier  = models.CharField( max_length=64 , blank=False , null=False, editable = False )
    timeInsert  = models.DateTimeField( auto_now_add=True , editable = False )
    timeUpdate  = models.DateTimeField( auto_now=True , editable = False )
    status      = models.IntegerField( null=False , editable = False )

    class Meta: unique_together = (('identifier','type'),)

    def __unicode__( self ) :
        return u"%s::%s"%( self.type.identifier , self.identifier ) 

    def __str__( self ) : return unicode(self).encode("utf8")

    class Admin : pass


class Task( models.Model ): 
    """ 
        Task queue.

        DB fields: 
            instance   - process instance.
    """
    instance     = models.ForeignKey( Instance , blank=False , null=False , editable = False )
    time         = models.DateTimeField( auto_now=True, editable = False )
    lock         = models.BigIntegerField( default = 0 )  

    def __unicode__( self ) :
        return u"%s::%s"%( self.instance.type.identifier , self.instance.identifier ) 

    def __str__( self ) : return unicode(self).encode("utf8")

    class Admin : pass


class LogRecord( models.Model ): 
    """ 
        Task status change Log.

        DB fields: 
            instance   - process instance;
            time       - time-stamp of the log record;
            status     - status code of the process instance;
            message    - text message associated to the log message.

    """
    instance     = models.ForeignKey( Instance , blank=False , null=False , editable = False )
    time         = models.DateTimeField( auto_now=True, editable = False )
    status       = models.IntegerField( null=False , choices = STATUS2TEXT.items(), editable = False )
    message      = models.TextField( editable = False )

    # pid - local process ID 

    def __unicode__( self ) :

        message = unicode(self.message) 
        if ( 28 < len(message) ) : 
            message = u"%s ..."%message[:28] 

        return u'%22.22s [%s] %s\t%s' % ( self.time , self.instance , STATUS2TEXT[self.status] , message ) 

    def __str__( self ) : return unicode(self).encode("utf8")
 
    class Admin : pass


class Response( models.Model ): 
    """ 
        Task Response storage.

        DB fields: 
            instance   - process instance;
            response   - process XML response (if not in plain text GZIP+BASE64 is applied).

    """
    instance  = models.ForeignKey( Instance , blank=False , null=False , editable = False , unique = True )
    response  = models.TextField( editable = False )
    mimeType  = models.TextField( editable = True )

    def __unicode__( self ) : return unicode( self.instance )  

    def __str__( self ) : return unicode(self).encode("utf8")

    class Admin : pass


class Input( models.Model ): 
    """ 
        Process Input storage. 

        DB fields: 
            instance   - process instance;
            input      - task inputs.

    """
    instance    = models.ForeignKey( Instance , blank=False , null=False , editable = False , unique = True )
    input       = models.TextField( editable = False ) # store the data as Base64 encoded pickle object

    def __unicode__( self ) : return unicode( self.instance )  

    def __str__( self ) : return unicode(self).encode("utf8")

    class Admin : pass 


