class NameSpace(object):
    def __init__(self, uri, prefix=None):
        self._uri = uri
        self._lxml_uri = "{%s}" % uri
        self._prefix = prefix

    @property
    def uri(self):
        return self._uri

    @property
    def prefix(self):
        return self._prefix
    
    def __call__(self, tag):
        return self._lxml_uri + tag


class NameSpaceMap(dict):
    def __init__(self, *namespaces):
        for namespace in namespaces:
            self.add(namespace)

    def add(self, namespace):
        self[namespace.prefix] = namespace.uri
