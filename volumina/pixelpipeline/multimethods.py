import sys
import inspect

registry = {}
calling_modules = {}

class MultiMethod(object):
    def __init__(self, name):
        self.name = name
        self.typemap = {}
    def __call__(self, *args):
        types = tuple(arg.__class__ for arg in args)
        function = self.typemap.get(types)
        if function is None:
            raise TypeError("no match: %s" % str(types))
        return function(*args)
    def register(self, types, function):
        if types in self.typemap:
            raise TypeError("duplicate registration: %s" % str(types))
        self.typemap[types] = function

# decorator
def multimethod(*types):
    def register(function):
        name = function.__name__
        mm = registry.get(name)
        if mm is None:
            mm = registry[name] = MultiMethod(name)
        mm.register(types, function)
        return mm

    def noop(function):
        assert(function.__name__ in registry) # noop is only returned,
                                              # when we have seen the
                                              # function at least once
        return registry[function.__name__]

    # a single module can appear more than once under different names
    # in sys.modules; for exampe 'volumina.pixelpipeline.multimethods'
    # and 'pixelpipeline.multimethods'
    # we encountered this case, when a module is imported with its relative
    # name in a __init__.py and simultaneously in a submodule with is full
    # qualified name (this only works, when the python path points to the root
    # dir of the full qualified name)
    # As a result, the same decorator was called more than once and we got
    # multi registration errors
    # volumina.pixelpipeline.submodule:
    #     uses multimethod decorator
    #     imports another module with fqp volumina.pixelpipeline.submodule2 
    #         executes __init__.py in fq namespace
    # volumina.__init__:
    #     import pixelpipeline.submodule # executes decorators
    # volumina.module:
    #     impot pixelpipeline.submodule # executes decorators
    #
    # The following code handles this case.

    caller = sys.modules.get(inspect.currentframe().f_back.f_globals['__name__'])
    # there is a caller and it is a non built-in in module (not a function etc.)
    if caller and inspect.ismodule(caller) and hasattr(caller, '__file__'):
        module_file = caller.__file__
        module_name = caller.__name__
        # Have we encountered the module before?
        if module_file in calling_modules:
            # we are still during the first encounter of that module
            if calling_modules[module_file] is module_name:
                return register
            # we previously encountered the module in a different namespace
            # -> do not register a new multimethod, but return the old one
            else:
                return noop
        # module encountered the first time
        else:
            calling_modules[module_file] = module_name
            return register
    else:
        raise Exception("multimethod() was not called as a decorator")
