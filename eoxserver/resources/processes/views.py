#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#  views 
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
"""This module contains the auxilairy views of the tracked processes."""
#-------------------------------------------------------------------------------

from django.http import HttpResponse

from eoxserver.resources.processes.models import Type,Instance, LogRecord  
from eoxserver.resources.processes.tracker import TaskStatus, getTaskResponse
from eoxserver.resources.processes.models import STATUS2TEXT , STATUS2COLOR , TEXT2STATUS 

#-------------------------------------------------------------------------------

#: Status to HTML colored text conversion dinctionary (filled dynamically). 
STATUS2CTEXT = {} 

for k in STATUS2TEXT : 
    STATUS2CTEXT[k] = '<span style="color:%s">%s</span>' % ( STATUS2COLOR[k] , STATUS2TEXT[k] ) 

#-------------------------------------------------------------------------------

def task(request): 
    """Task auxiliary view."""

    status = request.GET.get('status',None) 
    rtype  = request.GET.get('type',None) 

    path = request.path.rpartition("/")[0]

    _filter = {} 
    _subtitle = "All Tasks"

    if status or rtype : 
        _subtitle = "Tasks Having:"

    if status : 
        status = str(status).upper() 
        _filter['status'] = TEXT2STATUS[status]
        _subtitle += " status=%s " % status 

    if rtype : 
        _filter['type'] = Type.objects.get(identifier=rtype) 
        _subtitle += " type=%s " % rtype

    r = [] 
    r.append('<html>')
    r.append('<head><title>Task Status</title></head>')
    r.append('<meta http-equiv="refresh" content="15">') 
    r.append('<body style="font-family:sans-serif">') 
    r.append('<table border="1" padding="2">') 
    r.append('<h2>Task Status</h2>')
    if _subtitle : r.append( '<h3>%s</h3>'%_subtitle )
    r.append('<tr style="font-style:italic;font-weight:bold"><td>Update Time</td><td>Insert Time</td><td>Request Type</td><td>Request ID</td><td>Status</td><td>Info</td></tr>')

    for item in Instance.objects.filter(**_filter).select_related().order_by("-timeUpdate") :
        status = '<a href="%s/task?status=%s">%s</a>'%( path , STATUS2TEXT[item.status] , STATUS2CTEXT[item.status] ) 
        rtype0 = item.type.identifier 
        rtype  = '<a href="%s/task?type=%s" style="color:black">%s</a>'%( path , rtype0 , rtype0 ) 
        rid    = '<a href="%s/status/%s/%s" style="color:black">%s</a>' % ( path , rtype0 , item.identifier , item.identifier ) 
        try : 
            info = "enqueued (%s)"%str(item.task_set.get().lock) 
        except : 
            if item.status in ( TaskStatus.FINISHED , TaskStatus.FAILED ) :
                info = '<a href="%s/response/%s/%s" style="color:black">response</a>' % ( path , rtype0 , item.identifier ) 
            else: 
                info = "&nbsp;"
        r.append('<tr><td>%19.19s</td><td>%19.19s</td><td>%s</td><td style="font-family:monospace;font-size:125%%">%s</td><td>%s</td></td><td>%s</td></tr>'% \
            (item.timeUpdate,item.timeInsert,rtype,rid,status,info) )
# 
    r.append('</table>') 
    r.append('</body>')
    r.append('</html>') 
    
    return HttpResponse("\n".join(r),content_type='text/html')

#-------------------------------------------------------------------------------

def status(request,requestType=None,requestID=None):
    """Task's status auxiliary view."""

    _filter   = {} 
    _subtitle = "All Tasks' History "

    if ( requestType is not None ) and ( requestID is not None ) : 
        _filter["instance"] = Type.objects.get(identifier=requestType).instance_set.get(identifier=requestID)
        _subtitle = "Single Task's History"
        
    path = request.path.rpartition("/status")[0]

    r = [] 
    r.append('<html>')
    r.append('<head><title>Task Status Log</title></head>')
    r.append('<meta http-equiv="refresh" content="15">') 
    r.append('<body style="font-family:sans-serif">') 
    r.append('<table border="1" padding="2">') 
    r.append('<h2>Process Status Log</h2>')
    if _subtitle : r.append( '<h3>%s</h3>'%_subtitle )
    r.append('<tr style="font-style:italic;font-weight:bold"><td>Time</td><td>RequestID</td><td>Status</td><td>Message</td><td>Response</td></tr>')

    for item in LogRecord.objects.filter(**_filter).select_related().order_by("-time") :
        status = STATUS2CTEXT[item.status] 
        rtype  = item.instance.type.identifier
        rid    = '<a href="%s/status/%s/%s">%s</a>' % ( path , rtype , item.instance.identifier , item.instance.identifier ) 
        response = "" 
        if ( item.status in ( TaskStatus.FINISHED , TaskStatus.FAILED ) ) : 
            response = '<a href="%s/response/%s/%s">view</a>' % ( path , rtype , item.instance.identifier ) 

        r.append('<tr><td>%19.19s</td><td style="font-family:monospace;font-size:125%%">%s</td><td>%s</td><td>%s</td><td>%s<td/></tr>'% \
            (item.time,rid,status,item.message,response) )
    r.append('</table>') 
    r.append('</body>')
    r.append('</html>') 

    return HttpResponse("\n".join(r),content_type='text/html')

#-------------------------------------------------------------------------------

def response(request,requestType,requestID): 
    """Task's response view."""

    try : 
        response , mimeType = getTaskResponse( requestType , requestID )
        return HttpResponse( response , content_type= mimeType ) 
    except Exception as e : 
        return HttpResponse('ERROR: Response not available! requestClass="%s" ; requestID = "%s" '%\
                    (requestType,requestID),status=500,content_type='text/plain') 
