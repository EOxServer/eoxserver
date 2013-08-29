#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from urlparse import urlparse

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import ConnectedStorageInterface


class RasdamanStorage(Component):
    implements(ConnectedStorageInterface)

    name = "rasdaman"

    def validate(self, url):
        parsed = urlparse(url)

        if not parsed.hostname:
            raise ValidationError(
                "Invalid Rasdaman URL: could not determine hostname."
            )
        if parsed.scheme and parsed.scheme.lower() != "rasdaman":
            raise ValidationError(
                "Invalid Rasdaman URL: invalid scheme 's'." % parsed.scheme
            )


    def connect(self, url, location, format):
        parsed = urlparse(url)

        # hostname + path -> hostname
        # port -> port
        # user -> user
        # password -> password
        # fragment -> dbname

        # location can either be an oid, collection or query

        if format == "rasdaman/oid":
            query = "select ( a [$x_lo:$x_hi,$y_lo:$y_hi] ) from %s as a where oid(a)=%f" % () # TODO
        elif format == "rasdaman/collection":
            query = "select ( a [$x_lo:$x_hi,$y_lo:$y_hi] ) from %s as a" % location
        elif format == "rasdaman/query":
            query = location

        parts = {
            "host": parsed.hostname + "/" + parsed.path,
            "query": query
        }

        if parsed.port is not None:
            parts["port"] = parsed.port
        if parsed.username is not None:
            parts["user"] = parsed.username
        if parsed.password is not None:
            parts["password"] = parsed.password
        if parsed.fragment:
            parts["database"] = parsed.fragment

        return "rasdaman: " + " ".join(
            map(lambda k, v: "%s='v'" % (k, v), parts.items())
        )
