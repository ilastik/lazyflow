from abc import ABCMeta, abstractmethod

class RequestABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def wait( self ):
        pass

    @abstractmethod
    def notify( self, callback, **kwargs ):
        pass

class ArraySourceABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def request( self, slicing ):
        pass

class ImageSourceABC:
    __metaclass__ = ABCMeta

    @abstractmethod
    def request( self, rect ):
        pass
