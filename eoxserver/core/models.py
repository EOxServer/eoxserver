#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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


from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType


def get_real_content_type(obj):
    """ Helper to get the correct content type record for the type of the object.
    """
    return ContentType.objects.get_for_model(type(obj))


class Castable(models.Model):
    """ Model mix-in for 'castable' types. With this MixIn, type information and 
    completed models can be retrieved.
    """

    real_content_type = models.ForeignKey(ContentType, editable=False)

    @property
    def real_type(self):
        # if not saved, use the actual type
        if not self.id:
            return type(self)

        # this command uses the cached access of the contenttypes framework
        real_content_type = ContentType.objects.get_for_id(self.real_content_type_id)
        return real_content_type.model_class()

    
    def save(self, *args, **kwargs):
        # save a reference to the actual content type
        if not self.id:
            self.real_content_type = get_real_content_type(self)

        return super(Castable, self).save(*args, **kwargs)


    def cast(self, refresh=False):
        """'Cast' the model to its actual type, if it is not already. This 
        invokes a database lookup if the real type is not the same as the type 
        of the current model.
        """

        # don't perform a cast if not necessary
        real_type = self.real_type
        if real_type == type(self) and not refresh:
            return self

        # otherwise get the correctly typed model
        return self.real_content_type.get_object_for_this_type(pk=self.pk)


    class Meta:
        abstract = True
