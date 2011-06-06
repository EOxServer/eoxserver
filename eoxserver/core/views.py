#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from django.shotcuts import render_to_response

def index(request):
    # show overview with links to active components, resources
    return render_to_response("eoxserver/index.html")
    
def showActiveComponents(request):
    # show all active components
    pass

def showActiveComponent(request, component_id):
    # show details for active component
    # including relations to resource classes and resources
    pass

def showResourceClass(request, resource_class_id):
    # show details for resource class including resource instances
    pass

def showResource(request, resource_class_id, resource_id):
    # show details for resource including relations to active components
    pass
