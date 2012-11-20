#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

"""
This module contains the core logic for interface declaration and validation.
"""

import types
import logging

from eoxserver.core.exceptions import InternalError, TypeMismatch, ConfigError


logger = logging.getLogger(__name__)

global RUNTIME_VALIDATION_LEVEL

RUNTIME_VALIDATION_LEVEL = "trust"

#-------------------------------------------------------------------------------
# Argument classes
#-------------------------------------------------------------------------------

class Arg(object):
    """
    This is the common base class for arguments of any kind; it can be used
    in interface declarations as well to represent an argument of arbitrary
    type.
    
    The constructor requires a ``name`` argument which denotes the argument
    name. The validation will check at class creation time if the method of an
    implementing class defines an argument of the given name, so you should
    always use valid Python variable names here (you can use arbitrary strings
    for return value declarations though).
    
    Furthermore, the constructor accepts a ``default`` keyword argument which
    defines a default value for the declared argument. The validation will
    check at class creation time if this default value is present in the
    implementing class and fail if it is not.
    
    Its methods are intended for internal use in runtime validation.
    """
    
    def __init__(self, name, **kwargs):
        self.name = name
        
        if "default" in kwargs:
            self.default = kwargs["default"]
            self.optional = True
        else:
            self.default = None
            self.optional = False
    
    def isOptional(self):
        """
        Returns ``True`` if the argument is optional, meaning that a default
        value has been defined for it, ``False`` otherwise.
        """
        
        return self.optional
    
    def isValid(self, arg_value):
        """
        Returns ``True`` if ``arg_value`` is an acceptable value for the
        argument, ``False`` otherwise. Acceptable values are either the default
        value if it has been defined or values of the expected type.
        """
        
        return (self.optional and self.default == arg_value) or \
               self.isValidType(arg_value)
    
    def isValidType(self, arg_value):
        """
        Returns ``True`` if the argument value ``arg_value`` has a valid type,
        ``False`` otherwise. This method is overridden by :class:`Arg`
        subclasses in order to check for individual types. The base class
        implementation always returns ``True`` meaning that all types of
        argument values are accepted.
        """
        
        return True
        
    def getExpectedType(self):
        """
        Returns the expected type name; used in error messages only. This
        method is overridden by :class:`Arg` subclasses in order to customize
        error reporting. The base class implementation returns ``""``.
        """
        
        return ""

class StrArg(Arg):
    """
    Represents an argument of type :class:`str`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, str)
            
    def getExpectedType(self):
        return "str"
        
class UnicodeArg(Arg):
    """
    Represents an argument of type :class:`unicode`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, unicode)
        
    def getExpectedType(self):
        return "unicode"
    
class StringArg(Arg):
    """
    Represents an argument of types :class:`str` or :class:`unicode`.
    """
    def isValidType(self, arg_value):
        return (isinstance(arg_value, str) or isinstance(arg_value, unicode))
    
    def getExpectedType(self):
        return "str' or 'unicode"
        
class BoolArg(Arg):
    """
    Represents an argument of type :class:`bool`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, bool)
        
    def getExpectedType(self):
        return "bool"
        
class IntArg(Arg):
    """
    Represents an argument of type :class:`int`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, int)
    
    def getExpectedType(self):
        return "int"

class LongArg(Arg):
    """
    Represents an argument of type :class:`long`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, long)
    
    def getExpectedType(self):
        return "long"

class FloatArg(Arg):
    """
    Represents an argument of type :class:`float`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, float)

    def getExpectedType(self):
        return "float"

class RealArg(Arg):
    """
    Represents a real number argument, i.e. an argument of types :class:`int`,
    :class:`long` or :class:`float`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, int) or \
               isinstance(arg_value, long) or \
               isinstance(arg_value, float)
    
    def getExpectedType(self):
        return "int', 'long' or 'float"

class ComplexArg(Arg):
    """
    Represents a complex number argument of type :class:`complex`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, complex)
    
    def getExpectedType(self):
        return "complex"

class IterableArg(Arg):
    """
    Represents an iterable argument.
    """
    def isValidType(self, arg_value):
        return hasattr(arg_value, "__iter__")
    
    def getExpectedType(self):
        return "iterable (pseudo-type)"
    
class SubscriptableArg(Arg):
    """
    Represents a subscriptable argument.
    """
    def isValidType(self, arg_value):
        return hasattr(arg_value, "__getitem__")
    
    def getExpectedType(self):
        return "subscriptable (pseudo-type)"

class ListArg(IterableArg, SubscriptableArg):
    """
    Represents an argument of type :class:`list`.
    """
    def isValidType(self, arg_value):
        return isinstance(arg_value, list)
    
    def getExpectedType(self):
        return "list"

class DictArg(IterableArg, SubscriptableArg):
    """
    Represents an argument of type :class:`dict`.
    """
    
    def isValidType(self, arg_value):
        return isinstance(arg_value, dict)
        
    def getExpectedType(self):
        return "dict"

class ObjectArg(Arg):
    """
    Represents an new-style class argument. The range of accepted objects can
    be restricted by providing the ``arg_class`` keyword argument to the
    constructor. Runtime validation will then check if the argument value is
    an instance of ``arg_class`` (or one of its subclasses) and fail otherwise.
    """
    
    def __init__(self, name, **kwargs):
        super(ObjectArg, self).__init__(name, **kwargs)
        
        if "arg_class" in kwargs:
            try:
                issubclass(kwargs["arg_class"], object)
            except:
                raise InternalError("Argument class must be a new-style class.")
                
            self.arg_class = kwargs["arg_class"]
        else:
            self.arg_class = object
    
    def isValidType(self, arg_value):
        return isinstance(arg_value, self.arg_class)
    
    def getExpectedType(self):
        return self.arg_class.__name__

class PosArgs(Arg):
    """
    Represents arbitrary positional arguments as supported by Python with
    the ``method(self, *args)`` syntax. The range of accepted objects can
    be restricted by providing the ``arg_class`` keyword argument to the
    constructor. Runtime validation will then check if the argument value is
    an instance of ``arg_class`` (or one of its subclasses) and fail otherwise.
    
    Note that a :class:`PosArgs` argument declaration can only be followed by
    a :class:`KwArgs` declaration, otherwise validation will fail.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.optional = True
        self.default = None
        
        if "arg_class" in kwargs:
            try:
                if issubclass(kwargs["arg_class"], object):
                    self.arg_class = kwargs["arg_class"]
                else:
                    raise InternalError("Argument class must be a new-style class.")
            except:
                raise InternalError("Argument class must be a new-style class.")
        else:
            self.arg_class = None
    
    def isValidType(self, arg_value):
        return self.arg_class is None or isinstance(arg_value, self.arg_class)
    
    def getExpectedType(self):
        if self.arg_class is None:
            return "any"
        else:
            return self.arg_class.__name__

class KwArgs(Arg):
    """
    Represents arbitrary keyword arguments as supported by Python with the
    ``method(self, **kwargs)`` syntax. Note that this must always be the
    last input argument declaration in a method, otherwise validation will fail.
    """
    def __init__(self, name, **kwargs):
        self.name = name
        self.optional = True
        self.default = None

#-------------------------------------------------------------------------------
# Method class
#-------------------------------------------------------------------------------

class Method(object):
    """
    The :class:`Method` is used for method declarations in interfaces. Its
    constructor accepts an arbitrary number of positional arguments representing
    input arguments to the method to be defined, and one optional keyword
    argument ``returns`` which represents the methods return value, if any.
    
    All arguments must be instances of :class:`Arg` or one of its subclasses.
    
    The methods of the :class:`Method` class are intended for internal use by
    the :class:`Interface` validation algorithms only.
    """
    def __init__(self, *args, **kwargs):
        self.validateArgs(args)
        
        self.named_args = []
        self.pos_args = None
        self.kwargs = None
        
        for arg in args:
            if isinstance(arg, PosArgs):
                self.pos_args = arg
            elif isinstance(arg, KwArgs):
                self.kwargs = arg
            else:
                self.named_args.append(arg)

        self.returns = kwargs.get("returns", None)
            
    def validateArgs(self, args):
        """
        Validate the input arguments. That is, check if they are in the 
        right order and no argument is defined more than once. Raises
        :exc:`~.InternalError` if the arguments do not validate.
        
        Used internally by the constructor during instance creation.
        """
        opt_args_flag = False
        pos_args_flag = False
        kwargs_flag = False
        
        names = []
        
        for arg in args:
            if not isinstance(arg, Arg):
                raise InternalError("Method arguments must be instances of Arg.")
            
            if opt_args_flag:
                if not arg.isOptional():
                    raise InternalError("Mandatory arguments must precede optional arguments.")
            
            if pos_args_flag:
                if not isinstance(arg, KwArgs):
                    raise InternalError("Only keyword arguments may follow optional positional argument block.")
            
            if kwargs_flag:
                raise InternalError("No arguments allowed after keyword arguments block.")
            
            if arg.isOptional():
                opt_args_flag = True
            if isinstance(arg, PosArgs):
                pos_args_flag = True
            elif isinstance(arg, KwArgs):
                kwargs_flag = True
            
            if arg.name in names:
                raise InternalError("Argument named '%s' appears multiple times." % arg.name)
            else:
                names.append(arg.name)

    def validateImplementation(self, impl_method):
        """
        This method is at implementation class creation time to check if the
        implementing class method conforms to the method declaration. It expects
        the corresponding method as its single input argument ``impl_method``.
        It makes extensive use of Python's great introspection capabilities.
        
        Raises :exc:`~.InternalError` in case the implementation does not
        validate.
        """
        
        if len(self.named_args) != impl_method.func_code.co_argcount - 1:
            raise InternalError("Number of arguments does not match")
        
        for i in range(0, len(self.named_args)):
            if self.named_args[i].name != impl_method.func_code.co_varnames[i+1]:
                raise InternalError("Expected argument named '%s', got '%s'." % (self.named_args[i].name, impl_method.func_code.co_varnames[i+1]))
        
        if self.pos_args is not None and impl_method.func_code.co_flags & 4 == 0:
            raise InternalError("Expected positional argument block.")
        
        if self.kwargs is not None and impl_method.func_code.co_flags & 8 == 0:
            raise InternalError("Expected keyword argument block.")

    def validateType(self, method_name, *args, **kwargs):
        """
        This method is called for runtime argument type validation. It gets the
        input of the implementing method and checks it against the argument
        declarations.
        
        Raises :exc:`~.TypeMismatch` if validation fails.
        """
        
        # map arguments to self.named_args, self.pos_args and
        # self.kwargs
        
        intf_named_args = {}
        
        for arg in self.named_args:
            intf_named_args[arg.name] = arg

        impl_named_args = {}
        impl_pos_args = []
        impl_kwargs = {}
        
        for i in range(0, min(len(self.named_args), len(args))):
            impl_named_args[self.named_args[i].name] = (self.named_args[i], args[i])
        
        if len(args) > len(self.named_args):
            if self.pos_args is not None:
                impl_pos_args = args[len(self.named_args):]
            else:
                self._raiseWrongNumberOfArguments(method_name, len(args))
        
        for name, arg_value in kwargs.items():
            if name in intf_named_args:
                if name in impl_named_args:
                    raise TypeError("%s() got multiple values for keyword argument '%s'" % (
                        method_name,
                        name
                    ))
                else:
                    impl_named_args[name] = (intf_named_args[name], arg_value)
            else:
                if self.kwargs is not None:
                    impl_kwargs[name] = arg_value
                else:
                    raise TypeError("%s() got an unexpected keyword argument '%s'" % (
                        method_name,
                        name
                    ))
        
        if len(impl_named_args) < len(filter(lambda arg: not arg.isOptional(), self.named_args)):
            self._raiseWrongNumberOfArguments(method_name, len(impl_named_args), len(kwargs) > 0)
                
        # finally, validate
        
        msgs = []
        
        logger.debug("validateType(): start validation")
        
        for arg, arg_value in impl_named_args.values():
            if not arg.isValid(arg_value):
                msgs.append("%s(): Invalid type for argument '%s'. Expected '%s', got '%s'." % (
                    method_name,
                    arg.name,
                    arg.getExpectedType(),
                    str(type(arg_value))
                ))
        
        if self.pos_args is not None:
            if not self.pos_args.isValid(impl_pos_args):
                msgs.append("%s(): Invalid type for positional arguments. Expected '%s' only." % (
                    method_name,
                    self.pos_args.getExpectedType()
                ))

        logger.debug("validateType(): finish validation")
        
        if len(msgs) > 0:
            raise TypeMismatch("\n".join(msgs))
    
    def validateReturnType(self, method_name, ret_value):
        """
        This method is called for runtime argument type validation. It expects
        the method name ``method_name`` and the return value ``ret_value`` as
        input and checks the return value against the return value declaration,
        if any.
        
        Raises :exc:`~.TypeMismatch` if validation fails.
        """
        
        if self.returns is not None and \
           not self.returns.isValid(ret_value):
            raise TypeMismatch("%s(): Invalid return type. Expected '%s', got '%s'" % (
                method_name,
                self.returns.getExpectedType(),
                str(type(ret_value))
            ))

    def _raiseWrongNumberOfArguments(self, method_name, argcount, kwargs_present=False):
        if any(map(lambda arg : arg.isOptional(), self.named_args)):
            if argcount > len(self.named_args):
                adverb = "at most"
                count = len(self.named_args)
            else:
                adverb = "at least"
                count = len(filter(lambda arg : not arg.isOptional(), self.named_args))
        else:
            adverb = "exactly"
            count = len(self.named_args)
            
        if kwargs_present:
            prefix = "non-keyword "
        else:
            prefix = ""
        
        raise TypeError("%s() takes %s %d %sarguments (%d given)" % (
            method_name,
            adverb,
            count,
            prefix,
            argcount
        ))

#-------------------------------------------------------------------------------
# Interface class
#-------------------------------------------------------------------------------

class InterfaceMetaClass(type):
    def __new__(cls, name, bases, class_dict):
        if "INTERFACE_CONF" in class_dict:
            local_conf = class_dict["INTERFACE_CONF"]
        else:
            local_conf = {}
            
        class_dict["__iconf__"] = cls._mergeConfs(local_conf, bases, "__iconf__")
        
        return type.__new__(cls, name, bases, class_dict)
    
    @classmethod
    def _mergeConfs(mcls, local_conf, bases, conf_name):
        base_confs = []
        for base in bases:
            if hasattr(base, conf_name):
                base_confs.append(getattr(base, conf_name))
        
        conf = {}
        for base_conf in reversed(base_confs):
            conf.update(base_conf)
        conf.update(local_conf)
        
        return conf

class Interface(object):
    """
    This is the base class for all interface declarations. Derive from it or
    one of its subclasses to create your own interface declaration.
    
    The :class:`Interface` class has only class variables (the method
    declarations) and class methods.
    """
    
    __metaclass__ = InterfaceMetaClass
    
    @classmethod
    def implement(InterfaceCls, ImplementationCls):
        """
        This method takes an implementing class as input, validates it, and
        returns the implementation.
        
        In the validation step, :meth:`Method.validateImplementation`
        is called for each method declared in the interface.
        :exc:`~.InternalError` is raised if a method is not found or if
        the method signature does not match the declaration.
        
        If validation has passed, the implementation is getting prepared. The
        implementation inherits from the implementing class. The ``__ifclass__``
        magic attribute is added to the class dictionary. If runtime
        validation has been enabled, the methods of the implementing class
        defined in the interface are replaced by descriptors (instances of
        :class:`WarningDescriptor` or  :class:`FailingDescriptor`).
        
        Finally, the implementation class is generated and returned.
        """
        
        name = InterfaceCls._getName(ImplementationCls)
        bases = InterfaceCls._getBases(ImplementationCls)
        
        InterfaceCls._validateImplementation(bases)
        
        class_dict = InterfaceCls._getClassDict(ImplementationCls, bases)
        
        return type(name, bases, class_dict)
    
    @classmethod
    def _getName(InterfaceCls, ImplementationCls):
        return "_Impl_%s_%s" % (ImplementationCls.__module__.replace(".", "_"), ImplementationCls.__name__)
    
    @classmethod
    def _getBases(InterfaceCls, ImplementationCls):
        bases = (ImplementationCls,)
        
        return bases
    
    @classmethod
    def _getClassDict(InterfaceCls, ImplementationCls, bases):
        # Runtime validation levels
        # * "trust" - do not enforce type checking at runtime (default)
        # * "warn" - print warnings to the log file if type check fails
        # * "fail" - raise exception if type check fails
        runtime_validation_level = InterfaceCls._getRuntimeValidationLevel(ImplementationCls)
        
        if runtime_validation_level.lower() == "trust":
            class_dict = {}
            
        elif runtime_validation_level.lower() == "warn":
            class_dict = {}

            interface_methods = InterfaceCls._getMethods()
            
            for name, method in interface_methods.items():
                func = InterfaceCls._getBaseMethod(name, bases)
                class_dict[name] = WarningDescriptor(method, func)

        elif runtime_validation_level.lower() == "fail":
            class_dict = {}
            
            interface_methods = InterfaceCls._getMethods()
            
            logger.debug("Interface._getClassDict(): Interface Methods: %s" % str(interface_methods))
            
            for name, method in interface_methods.items():
                func = InterfaceCls._getBaseMethod(name, bases)
                class_dict[name] = FailingDescriptor(method, func)

        else:
            class_dict = {}
            
        class_dict.update({"__ifclass__": InterfaceCls})
        
        return class_dict

    @classmethod
    def _validateImplementation(InterfaceCls, bases):
        interface_methods = InterfaceCls._getMethods()
        
        implementation_dict = {}
        for base in reversed(bases):
            for cls in reversed(base.__mro__): # TODO: check if this gives the right MRO in the case of multiple inheritance 
                for name, attr in cls.__dict__.items():
                    if type(attr) is types.FunctionType:
                        implementation_dict[name] = attr
        
        for name, method in interface_methods.items():
            if name in implementation_dict:
                method.validateImplementation(implementation_dict[name])
            else:
                raise InternalError("Method '%s' not found in implementation." % name)
    
    @classmethod
    def _getMethods(InterfaceCls):
        interface_methods = {}
        
        for name, attr in InterfaceCls.__dict__.items():
            if isinstance(attr, Method):
                interface_methods[name] = attr
        
        for InterfaceBase in reversed(InterfaceCls.__mro__):
            for name, attr in InterfaceBase.__dict__.items():
                if isinstance(attr, Method):
                    interface_methods[name] = attr
        
        return interface_methods
    
    @classmethod
    def _getBaseMethod(InterfaceCls, method_name, bases):
        for base in bases:
            for cls in base.__mro__:
                if method_name in cls.__dict__:
                    return cls.__dict__[method_name]
        
        raise InternalError("Base method %s() not found." % method_name)
    
    @classmethod
    def _getRuntimeValidationLevel(InterfaceCls, ImplementationCls):
        global_level = RUNTIME_VALIDATION_LEVEL.lower()
        intf_level = InterfaceCls.__iconf__.get("runtime_validation_level")
        if "IMPL_CONF" in ImplementationCls.__dict__:
            impl_level = ImplementationCls.IMPL_CONF.get("runtime_validation_level")
        else:
            impl_level = None
        
        levels = (global_level, intf_level, impl_level)
        
        if "fail" in levels:
            return "fail"
        elif "warn" in levels:
            return "warn"
        else:
            return "trust"

#-------------------------------------------------------------------------------
# Descriptors and Wrappers
#-------------------------------------------------------------------------------

class ValidationDescriptor(object):
    """
    This is the common base class for :class:`WarningDescriptor` and
    :class:`FailingDescriptor`. The constructor expects the method declaration
    ``method`` and the implementing function ``func`` as input.
    
    The :meth:`__get__` method returns a callable wrapper around the 
    instance it is called with, the method declaration and the function that
    implements the method. It is that object
    that gets finally invoked when runtime validation is enabled.
    """
    
    def __init__(self, method, func):
        self.method = method
        self.func = func
        
    def __get__(self, instance, owner):
        if instance is not None:
            return self._wrap(instance)
        else:
            raise InternalError("%s() is not a class method." % self.func.func_name)
    
    def _wrap(self, instance):
        return None

class ValidationWrapper(object):
    """
    This is the common base class for :class:`WarningWrapper` and
    :class:`FailingWrapper`. Its constructor expects the method declaration,
    the implementing function and the instance as input.
    """
    def __init__(self, method, func, instance):
        self.method = method
        self.func = func
        self.instance = instance

class WarningDescriptor(ValidationDescriptor):
    def _wrap(self, instance):
        return WarningWrapper(self.method, self.func, instance)

class WarningWrapper(ValidationWrapper):
    """
    This wrapper is callable. Its :meth:`__call__` method expects arbitrary
    positional and keyword arguments, validates them against the method
    declaration using :meth:`Method.validateType`, calls the implementing
    function with these arguments and returns whatever it returns, calling
    :meth:`Method.validateReturnType`.
    
    If the validation methods raise a :exc:`~.TypeMismatch` exception the
    exception text is logged as a warning, but the normal process of execution
    goes on.
    """
    def __call__(self, *args, **kwargs):
        try:
            self.method.validateType(self.func.func_name, *args, **kwargs)
        except TypeMismatch, e:
            logger.warning(str(e))
        
        ret_value = self.func(self.instance, *args, **kwargs)
        
        try:
            self.method.validateReturnType(self.func.func_name, ret_value)
        except TypeMismatch, e:
            logger.warning(str(e))
        
        return ret_value

class FailingDescriptor(ValidationDescriptor):
    def _wrap(self, instance):
        return FailingWrapper(self.method, self.func, instance)

class FailingWrapper(ValidationWrapper):
    """
    This wrapper is callable. Its :meth:`__call__` method expects arbitrary
    positional and keyword arguments, validates them against the method
    declaration using :meth:`Method.validateType`, calls the implementing
    function with these arguments and returns whatever it returns, calling
    :meth:`Method.validateReturnType`.
    
    If the validation methods raise a :exc:`~.TypeMismatch` exception it will
    not be caught and thus cause the program to fail.
    """
    def __call__(self, *args, **kwargs):
        self.method.validateType(self.func.func_name, *args, **kwargs)
    
        ret_value = self.func(self.instance, *args, **kwargs)
        
        self.method.validateReturnType(self.func.func_name, ret_value)
        
        return ret_value
        
#-------------------------------------------------------------------------------
# Config Reader
#-------------------------------------------------------------------------------

class IntfConfigReader(object):
    """
    This is the configuration reader for :mod:`eoxserver.core.interfaces`.
    
    Its constructor expects a :class:`Config` instance ``config`` as input.
    """
    
    def __init__(self, config):
        self.config = config
        
    def validate(self):
        """
        Validates the configuration. Raises :exc:`~.ConfigError` if the
        ``runtime_validation_level`` configuration setting in the
        ``core.interfaces`` section contains an invalid value.
        """
        value = self.getRuntimeValidationLevel()
        
        if value and value not in ("trust", "warn", "fail"):
            raise ConfigError("'runtime_validation_level' parameter must be one of: 'trust', 'warn' or 'fail'.")

    def getRuntimeValidationLevel(self):
        """
        Returns the global runtime validation level setting or ``None`` if it
        is not defined.
        """
        self.config.getConfigValue("core.interfaces", "runtime_validation_level")
