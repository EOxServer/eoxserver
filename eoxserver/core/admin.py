#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

"""
This module provides the admin for the core.
"""

from django.contrib.gis import admin
from django.contrib.admin.util import unquote
from django import template
from django.shortcuts import render_to_response

from eoxserver.core.models import Component

admin.site.disable_action('delete_selected')

class ComponentAdmin(admin.ModelAdmin):
    list_display = ('impl_id', 'intf_id', 'enabled')
    list_editable = ('enabled', )
    readonly_fields = ('impl_id', 'intf_id')
    ordering = ('impl_id', )
    search_fields = ('impl_id', 'intf_id')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Component, ComponentAdmin)

class ConfirmationAdmin(admin.ModelAdmin):
    """
    Specialized :class:`django.contrib.admin.ModelAdmin`.
    The :class:`ConfirmationAdmin` allows to request a
    confirmation from the user when certain changes
    are made to the underlying :class:`Model`.
    """
    
    # template path for the confirmation form
    confirmation_form_template = None
    
    def change_view(self, request, object_id, *args, **kwargs):
        """
        This method overrides the :class:`django.contrib.admin.ModelAdmin`s
        `change_view` method to hook in a confirmation page.
        """
        
        if request.method == 'POST' and request.POST.get('confirmation') != "done":
            obj = self.get_object(request, unquote(object_id))
            
            # get the changes from the model
            diff = self.get_changes(request, object_id)#self.get_differences(old_values, new_values)
            
            # hook if the confirmation is required
            msg = self.require_confirmation(diff)
            
            if msg:
                opts = self.model._meta
                context = {
                    'post': request.POST.items(),
                    'opts': opts,
                    'root_path': self.admin_site.root_path,
                    'app_label': opts.app_label,
                    'original': obj,
                    'object_id': object_id,
                    'has_change_permission': self.has_change_permission(request, obj),
                    'confirmation': msg
                }
                context_instance = template.RequestContext(request)
                return render_to_response(self.confirmation_form_template or [
                    "admin/%s/%s/change_confirmation.html" % (opts.app_label, opts.object_name.lower()),
                    "admin/%s/change_confirmation.html" % opts.app_label,
                    "admin/change_confirmation.html",
                ], context, context_instance=context_instance)
        
        # Here we build the "normal GUI"
        return super(ConfirmationAdmin, self).change_view(request, object_id, *args, **kwargs)
    
    def get_new_object(self, request, instance):
        """
        Get the changed model with the data from the form.
        Convenience method.
        """
        ModelForm = self.get_form(request, instance)
        form = ModelForm(request.POST, request.FILES, instance=instance)
        
        if form.is_valid():
            return self.save_form(request, form, change=True)
        else:
            return instance
    
    def get_changes(self, request, object_id):
        obj = self.get_object(request, unquote(object_id))
        old_values = dict([(field.name, field.value_from_object(obj)) for field in obj._meta.fields])
        new_obj = self.get_new_object(request, obj)
        new_values = dict([(field.name, field.value_from_object(obj)) for field in new_obj._meta.fields])
        
        return self.get_differences(old_values, new_values)
    
    def get_differences(self, first, second):
        """
        Convenience method to get the differences
        between two dict-like objects.
        """
        diff = {}
        for key, value2 in second.iteritems():
            value1 = first.get(key)
            if value1 != value2:
                diff[key] = (value1, value2)
        return diff
    
    def require_confirmation(self, diff):
        """
        Hook to check if a confirmation is required.
        Override this method in subclasses to enable
        or disable the confirmation.
        * ``diff`` is a dictionary where the keys are 
            the names of the changed fields and the values
            are tuples with two entries: the old and the 
            new value.
            
        To enable the confirmation return a string message
        which is shown to the user. 
        Otherwise return False.
        """
        return False
