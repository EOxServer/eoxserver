
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



