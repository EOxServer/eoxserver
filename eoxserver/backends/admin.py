# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
#
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

from django import forms
from django.contrib import admin

from eoxserver.backends.storages import get_handlers
from eoxserver.backends import models


# ==============================================================================
# choice helpers
# ==============================================================================

def get_storage_type_choices():
    return [
        (handler.name, handler.name) for handler in get_handlers()
    ]


# ==============================================================================
# Forms
# ==============================================================================


class StorageForm(forms.ModelForm):
    """ Form for `Storages`. Overrides the `format` formfield and adds choices
        dynamically.
    """

    def __init__(self, *args, **kwargs):
        super(StorageForm, self).__init__(*args, **kwargs)
        self.fields['storage_type'] = forms.ChoiceField(
            choices=[("---------", None)] + get_storage_type_choices()
        )


# ==============================================================================
# Admins
# ==============================================================================


class StorageAdmin(admin.ModelAdmin):
    form = StorageForm
    model = models.Storage

    def save_model(self, request, obj, form, change):
        if not obj.name:
            obj.name = None
        super(StorageAdmin, self).save_model(request, obj, form, change)

admin.site.register(models.Storage, StorageAdmin)
admin.site.register(models.StorageAuth)
