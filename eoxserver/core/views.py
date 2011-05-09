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
