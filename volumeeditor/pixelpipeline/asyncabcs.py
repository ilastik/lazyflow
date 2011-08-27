from abc import ABCMeta, abstractmethod

def _has_attribute( cls, attr ):
    if any(attr in B.__dict__ for B in cls.__mro__):
        return True
    return False

def _has_attributes( cls, attrs ):
    if all(_has_attribute(cls, a) for a in attrs):
        return True
    return False
    

#*******************************************************************************
# R e q u e s t A B C                                                          *
#*******************************************************************************

class RequestABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def wait( self ):
        ''' doc '''

    @abstractmethod
    def notify( self, callback, **kwargs ):
        pass

    @abstractmethod
    def cancelLock(self):
        pass
    
    @abstractmethod
    def cancelUnlock(self):
        pass
    
    @abstractmethod
    def canceled(self):
        pass

    @abstractmethod
    def cancel( self ):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is RequestABC:
            if _has_attributes(C, ['wait', 'notify']):
                return True
            return False
        return NotImplemented



#*******************************************************************************
# S o u r c e A B C                                                            *
#*******************************************************************************

class SourceABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def request( self, slicing ):
        pass

    @abstractmethod
    def setDirty( self, slicing ):
        pass

    @classmethod
    def __subclasshook__(cls, C):
        if cls is SourceABC:
            if _has_attributes(C, ['request', 'setDirty']):
                return True
            return False
        return NotImplemented
