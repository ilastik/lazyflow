from PyQt4.QtCore import QObject
from abc import ABCMeta, abstractmethod

from pixelpipeline.asyncabcs import _has_attributes

class InterpreterABC:
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def start( self ):
        '''Start the interpretation of an event stream.'''

    @abstractmethod    
    def stop( self ):
        '''Stop the interpretation of the event stream.'''

    @abstractmethod    
    def eventFilter( self, watched, event ):
        '''Necessary to act as a Qt event filter. '''

    @classmethod
    def __subclasshook__(cls, C):
        if cls is InterpreterABC:
            if _has_attributes(C, ['start', 'stop', 'eventFilter']):
                return True
            return False
        return NotImplemented




class EventSwitch( QObject ):
    @property
    def interpreter( self ):
        return self._interpreter

    @interpreter.setter
    def interpreter( self, interpreter ):
        # assert(isinstance(interpreter, InterpreterABC))
        # stop old interpreter before deinstalling to
        # avoid inconsistencies when eventloop and eventswitch
        # are running in different threads
        if self._interpreter:
            self._interpreter.stop()

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
