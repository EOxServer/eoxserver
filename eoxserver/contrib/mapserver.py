import mapscript


class Request(mapscript.OWSRequest):
    """ Convenience wrapper class over mapscripts ``OWSRequest``. Provides a 
        more pythonic interface and adds some convenience functions.
    """

    def __init__(self, params, type=mapscript.MS_GET_REQUEST):
        self._used_keys = {}

        self.type = type
        self.set_parameters(params)


    def set_parameters(self, params):
        if self.type == mapscript.MS_GET_REQUEST:
            for key, value in params.items():
                self[key] = value
        else:
            self.postrequest = params



    def __getitem__(self, key): 
        if isinstance(key, int):
            return self.getValue(key)
        else:
            return self.getValueByName(key)


    def __setitem__(self, key, value):
        key = key.lower()
        self._used_keys.setdefault(key, 0)

        # addParameter() available in MapServer >= 6.2 
        # https://github.com/mapserver/mapserver/issues/3973
        try:
            self.addParameter(key.lower(), escape(value))
        # Workaround for MapServer 6.0
        except AttributeError:
            self._used_keys[key] += 1
            self.setParameter(
                "%s_%d" % (key, self._used_keys[key]), escape(value)
            )


    def __len__(self):
        return self.NumParams
        

class Response(object):
    """ Data class for mapserver results. 
    """
    def __init__(self, ):
        pass

    @property
    def multipart(self):
        return 
    




class MetadataMixIn(object):
    """ Mix-In for classes that wrap mapscript objects with associated metadata.
    """

    def __init__(self, metadata=None):
        super(MetadataMixIn, self).__init__()
        if metadata:
            self.setMetaData(metadata)

    def __getitem__(self, key):
        self.getMetaData(key)

    def __setitem__(self, key, value):
        self.setMetaData(key, value)

    def setMetaData(self, key_or_params, value=None, namespace=None):
        """ Convenvience method to allow setting multiple metadata values with 
            one call and optionally setting a 'namespace' for each entry.
        """
        if value is None:
            for key, value in key_or_params.items():
                if namespace:
                    key = "%s_%s" % (key, namespace)

                self.setMetaData(key, value)
        else:
            if namespace:
                key = "%s_%s" % (key_or_params, namespace)
            else:
                key = key_or_params

            return self.setMetaData(key, value)


class Map(mapscript.mapObj, MetadataMixIn):

    def dispatch(self, request):
        """ Wraps the ``OWSDispatch`` method. Perfoms all necessary steps for a 
            further handling of the result.
        """

        logger.debug("MapServer: Installing stdout to buffer.")
        mapscript.msIO_installStdoutToBuffer()
        
        try:
            logger.debug("MapServer: Dispatching.")
            ts = time.time()
            # Execute the OWS request by mapserver, obtain the status in 
            # dispatch_status (0 is OK)
            status = self.OWSDispatch(request)
            te = time.time()
            logger.debug("MapServer: Dispatch took %f seconds." % (te - ts))
        except Exception, e:
            raise InvalidRequestException(
                str(e),
                "NoApplicableCode",
                None
            )
        
        logger.debug("MapServer: Retrieving content-type.")
        try:
            content_type = mapscript.msIO_stripStdoutBufferContentType()
            mapscript.msIO_stripStdoutBufferContentHeaders()

        except mapscript.MapServerError:
            # degenerate response. Manually split headers from content
            result = mapscript.msIO_getStdoutBufferBytes()
            parts = result.split("\r\n")
            result = parts[-1]
            headers = parts[:-1]
            
            for header in headers:
                if header.lower().startswith("content-type"):
                    content_type = header[14:]
                    break
            else:
                content_type = None

        else:
            logger.debug("MapServer: Retrieving stdout buffer bytes.")
            result = mapscript.msIO_getStdoutBufferBytes()
        
        logger.debug("MapServer: Performing MapServer cleanup.")
        # Workaround for MapServer issue #4369
        msversion = mapscript.msGetVersionInt()
        if msversion < 60004 or (msversion < 60200 and msversion >= 60100):
            mapscript.msCleanup()
        else:
            mapscript.msIO_resetHandlers()
        
        return Response(result, content_type, dispatch_status)
    


class Layer(mapscript.layerObj, MetadataMixIn):
    pass
