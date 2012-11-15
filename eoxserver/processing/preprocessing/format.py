# global format selection registry
_registry = {}

def get_format_selection(driver, *args, **kwargs):
    """ Format selection factory method. """
    
    try:
        return _registry[driver](*args, **kwargs)
    except KeyError:
        raise ValueError("No format selection available for driver '%s'" % driver)


class FormatSelectionMetaclass(type):
    """ Metaclass for format selections
    """
    def __init__(cls, name, bases, dct):
        if isinstance(dct["driver_name"], basestring):
            _registry[dct["driver_name"]] = cls
        super(FormatSelectionMetaclass, cls).__init__(name, bases, dct)


#===============================================================================
# Format selection
#===============================================================================

class FormatSelection(object):
    """ Format selection with format specific options. """
    
    __metaclass__ = FormatSelectionMetaclass
    
    
    @property
    def driver_name(self):
        raise NotImplementedError
    
    
    @property
    def extension(self):
        raise NotImplementedError
    
    
    @property
    def creation_options(self):
        return []
    


class GeoTIFFFormatSelection(FormatSelection):
    """ Format selection for GeoTIFF format.
    """
    
    SUPPORTED_COMPRESSIONS = ("JPEG", "LZW", "PACKBITS", "DEFLATE", "CCITTRLE",
                              "CCITTFAX3", "CCITTFAX4", "NONE")
    

    def __init__(self, tiling=True, compression=None, 
                 jpeg_quality=None, zlevel=None, creation_options=None):
        self.final_options = {}
        if compression:
            compression = compression.upper()
            if compression not in self.SUPPORTED_COMPRESSIONS:
                raise Exception("Unsupported compression method. Supported "
                                "compressions are: %s" 
                                % ", ".join(self.SUPPORTED_COMPRESSIONS))
            self.final_options["COMPRESS"] = compression
            
            if jpeg_quality is not None and compression == "JPEG":
                self.final_options["JPEG_QUALITY"] = jpeg_quality
            elif jpeg_quality is not None:
                raise ValueError("'jpeg_quality' can only be used with JPEG "
                                 "compression")
            
            if zlevel is not None and compression == "DEFLATE":
                self.final_options["ZLEVEL"] = zlevel
            elif zlevel is not None:
                raise ValueError("'zlevel' can only be used with DEFLATE "
                                 "compression")
            
        if tiling:
            self.final_options["TILED"] = "YES"
        
        if creation_options:
            self.final_options.update(dict(creation_options))
        
            
    driver_name = "GTiff"
    extension = ".tif"
    
    
    @property
    def creation_options(self):
        return ["%s=%s" % (key, value) 
                for key, value in self.final_options.items()]

