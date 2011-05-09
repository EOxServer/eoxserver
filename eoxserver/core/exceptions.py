class EOxSException(Exception):
    pass
    
class InternalError(EOxSException):
    pass

class ImplementationNotFound(EOxSException):
    pass

class ImplementationAmbiguous(EOxSException):
    pass

class TypeMismatch(InternalError):
    pass

class IpcException(EOxSException):
    pass
