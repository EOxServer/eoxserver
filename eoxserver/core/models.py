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


class Castable(models.Model):
    """ Model mix-in for 'castable' types. With this MixIn, type information and
        completed models can be retrieved.
    """

    @property
    def real_type(self):
        # if not saved, use the actual type
        if not self.id:
            return type(self)

        return self.type_registry[self.real_content_type]

    def __init__(self, *args, **kwargs):
        super(Castable, self).__init__(*args, **kwargs)
        if not self.id:
            for type_id, cls in self.type_registry.items():
                if cls == type(self):
                    self.real_content_type = type_id
                    break

    def cast(self, refresh=False):
        """'Cast' the model to its actual type, if it is not already. This
        invokes a database lookup if the real type is not the same as the type
        of the current model.
        """

        # don't perform a cast if not necessary
        real_type = self.real_type
        if real_type == type(self) and not refresh:
            return self

        return self.real_type.objects.get(pk=self.pk)

    class Meta:
        abstract = True
