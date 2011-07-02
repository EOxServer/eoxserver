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

import types
import logging

from eoxserver.core.exceptions import InternalError, TypeMismatch, ConfigError

global RUNTIME_VALIDATION_LEVEL

RUNTIME_VALIDATION_LEVEL = "trust"

class Constant(object):
    def __init__(self, value):
        self.value = value

class Arg(object):
    def __init__(self, name, **kwargs):
        self.name = name
        
        if "default" in kwargs:
            self.default = kwargs["default"]
            self.optional = True
        else:
            self.default = None
            self.optional = False
    
    def isOptional(self):
        return self.optional
    
    def isValid(self, arg_value):
        return (self.optional and self.default == arg_value) or \
               self.isValidType(arg_value)
    
    def isValidType(self, arg_value):
        return True
        
    def getExpectedType(self):
        return ""

class StrArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, str)
            
    def getExpectedType(self):
        return "str"
        
class UnicodeArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, unicode)
        
    def getExpectedType(self):
        return "unicode"
    
class StringArg(Arg):
    def isValidType(self, arg_value):
        return (isinstance(arg_value, str) or isinstance(arg_value, unicode))
    
    def getExpectedType(self):
        return "str' or 'unicode"
        
class BoolArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, bool)
        
    def getExpectedType(self):
        return "bool"
        
class IntArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, int)
    
    def getExpectedType(self):
        return "int"

class LongArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, long)
    
    def getExpectedType(self):
        return "long"

class FloatArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, float)

    def getExpectedType(self):
        return "float"

class RealArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, int) or \
               isinstance(arg_value, long) or \
               isinstance(arg_value, float)
    
    def getExpectedType(self):
        return "int', 'long' or 'float"

class ComplexArg(Arg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, complex)
    
    def getExpectedType(self):
        return "complex"

class IterableArg(Arg):
    def isValidType(self, arg_value):
        return hasattr(arg_value, "__iter__")
    
    def getExpectedType(self):
        return "iterable (pseudo-type)"
    
class SubscriptableArg(Arg):
    def isValidType(self, arg_value):
        return hasattr(arg_value, "__getitem__")
    
    def getExpectedType(self):
        return "subscriptable (pseudo-type)"

class ListArg(IterableArg, SubscriptableArg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, list)
    
    def getExpectedType(self):
        return "list"

class DictArg(IterableArg, SubscriptableArg):
    def isValidType(self, arg_value):
        return isinstance(arg_value, dict)
        
    def getExpectedType(self):
        return "dict"

class ObjectArg(Arg):
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
    def __init__(self, name, **kwargs):
        self.name = name
        self.optional = True
        self.default = None
    
class Method(object):
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
        
        logging.debug("validateType(): start validation")
        
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

        logging.debug("validateType(): finish validation")
        
        if len(msgs) > 0:
            raise TypeMismatch("\n".join(msgs))
    
    def validateReturnType(self, method_name, ret_value):
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
    __metaclass__ = InterfaceMetaClass
    
    @classmethod
    def implement(InterfaceCls, ImplementationCls):
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
            
            logging.debug("Interface._getClassDict(): Interface Methods: %s" % str(interface_methods))
            
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
            
class ValidationDescriptor(object):
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
    def __init__(self, method, func, instance):
        self.method = method
        self.func = func
        self.instance = instance

class WarningDescriptor(ValidationDescriptor):
    def _wrap(self, instance):
        return WarningWrapper(self.method, self.func, instance)

class WarningWrapper(ValidationWrapper):
    def __call__(self, *args, **kwargs):
        try:
            self.method.validateType(self.func.func_name, *args, **kwargs)
        except TypeMismatch, e:
            logging.warn(str(e))
        
        ret_value = self.func(self.instance, *args, **kwargs)
        
        try:
            self.method.validateReturnType(self.func.func_name, ret_value)
        except TypeMismatch, e:
            logging.warn(str(e))
        
        return ret_value

class FailingDescriptor(ValidationDescriptor):
    def _wrap(self, instance):
        return FailingWrapper(self.method, self.func, instance)

class FailingWrapper(ValidationWrapper):
    def __call__(self, *args, **kwargs):
        self.method.validateType(self.func.func_name, *args, **kwargs)
    
        ret_value = self.func(self.instance, *args, **kwargs)
        
        self.method.validateReturnType(self.func.func_name, ret_value)
        
        return ret_value

class IntfConfigReader(object):
    def __init__(self, config):
        self.config = config
        
    def validate(self):
        value = self.getRuntimeValidationLevel()
        
        if value and value not in ("trust", "warn", "fail"):
            raise ConfigError("'runtime_validation_level' parameter must be one of: 'trust', 'warn' or 'fail'.")

    def getRuntimeValidationLevel(self):
        self.config.getConfigValue("core.interfaces", "runtime_validation_level")
