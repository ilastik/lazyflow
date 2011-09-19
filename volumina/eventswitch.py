from PyQt4.QtCore import QObject
from abc import ABCMeta, abstractmethod

from pixelpipeline.asyncabcs import _has_attributes

class InterpreterABC:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def start( self ):
        '''Hook method called after installed as an event filter.'''

    @abstractmethod    
    def finalize( self ):
        '''Hook method called just before deinstall as an event filter.'''

    @abstractmethod    
    def eventFilter( self, watched, event ):
        '''Necessary to act as a Qt event filter. '''

    @classmethod
    def __subclasshook__(cls, C):
        if cls is InterpreterABC:
            if _has_attributes(C, ['start', 'finalize', 'eventFilter']):
                return True
            return False
        return NotImplemented




class EventSwitch( QObject ):
    @property
    def interpreter( self ):
        return self._interpreter

    @interpreter.setter
    def interpreter( self, interpreter ):
        # finalize old interpreter before deinstalling to
        # avoid inconsistencies when eventloop and eventswitch
        # are running in different threads
        self._interpreter.finalize()

        # deinstall old and install new interpreter
        for view in self._imageViews:
            view.removeEventFilter( self._interpreter )
            if interpreter:
                view.installEventFilter( interpreter )
        self._interpreter = interpreter

        # start the new interpreter after installing 
        # to avoid inconcistencies
        self._interpreter.start()

    def __init__( self, imageviews, interpreter=None):
        super(EventSwitch, self).__init__()
        self._imageViews = imageviews
        self._interpreter = None
        if interpreter:
            self.interpreter = interpreter
