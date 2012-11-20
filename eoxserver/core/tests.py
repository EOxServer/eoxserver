#!/usr/bin/env python
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

import logging

from django.test import TestCase

from eoxserver.core.interfaces import (
    Interface, Method, StrArg, StringArg, UnicodeArg, BoolArg, IntArg, LongArg,
    FloatArg, RealArg, ComplexArg, ListArg, DictArg, ObjectArg, PosArgs, KwArgs
)

from eoxserver.core.exceptions import TypeMismatch, InternalError


logger = logging.getLogger(__name__)

class TestInterface1(Interface):
    INTERFACE_CONF = {
        "runtime_validation_level": "trust"
    }
    
    use_str = Method(StrArg("arg"), returns=StrArg("@returns"))

    use_unicode = Method(UnicodeArg("arg"), returns=UnicodeArg("@returns"))

    use_string = Method(StringArg("arg"), returns=StringArg("@returns"))
    
    use_bool = Method(BoolArg("arg"), returns=BoolArg("@returns"))

    use_int = Method(IntArg("arg"), returns=IntArg("@returns"))

    use_long = Method(LongArg("arg"), returns=LongArg("@returns"))

    use_float = Method(FloatArg("arg"), returns=FloatArg("@returns"))

    use_real = Method(RealArg("arg"), returns=RealArg("@returns"))

    use_complex = Method(ComplexArg("arg"), returns=ComplexArg("@returns"))

    use_list = Method(ListArg("arg"), returns=ListArg("@returns"))

    use_dict = Method(DictArg("arg"), returns=DictArg("@returns"))

    use_object = Method(ObjectArg("arg"), returns=ObjectArg("@returns"))

    use_args = Method(PosArgs("args"), returns=ListArg("@returns"))

    use_kwargs = Method(KwArgs("args"), returns=DictArg("@returns"))

class TestClass1(object):
    def use_str(self, arg):
        return arg
    
    def use_unicode(self, arg):
        return arg
    
    def use_string(self, arg):
        return arg
    
    def use_bool(self, arg):
        return arg
    
    def use_int(self, arg):
        return arg
    
    def use_long(self, arg):
        return arg
    
    def use_float(self, arg):
        return arg
    
    def use_real(self, arg):
        return arg
    
    def use_complex(self, arg):
        return arg
    
    def use_list(self, arg):
        return arg
    
    def use_dict(self, arg):
        return arg
    
    def use_object(self, arg):
        return arg
    
    def use_args(self, *args):
        return list(args)
    
    def use_kwargs(self, **kwargs):
        return kwargs

class TestClass2(object):
    def use_int(self, arg):
        return arg

class TestClass3(TestClass1):
    def use_int(self, n):
        return n

class TestClass4(TestClass1):
    def use_int(self, arg, invalid):
        return arg

class TestClass5(TestClass1):
    def use_int(self, arg, *args):
        return arg

class TestClass6(TestClass1):
    def use_int(self, arg, **kwargs):
        return arg

class TestClass7(TestClass1):
    def use_int(self):
        return 1

class InterfaceImplementationTestCase(TestCase):
    def setUp(self):
        logging.basicConfig(
            filename="logs/test.log",
            format="[%(asctime)s] %(levelname)s: %(message)s",
            level=logging.DEBUG
        )
        
    def test_valid(self):
        try:
            TestInterface1.implement(TestClass1)
        except Exception, e:
            self.fail(str(e))
    
    def test_methods_missing(self):
        self.assertRaises(InternalError, TestInterface1.implement, TestClass2)
    
    def test_invalid_arg_name(self):
        self.assertRaises(InternalError, TestInterface1.implement, TestClass3)

    def test_invalid_arg_count(self):
        self.assertRaises(InternalError, TestInterface1.implement, TestClass4)
    
    def test_invalid_pos_args(self):
        self.assertRaises(InternalError, TestInterface1.implement, TestClass5)
    
    def test_invalid_kwargs(self):
        self.assertRaises(InternalError, TestInterface1.implement, TestClass6)
    
    def test_missing_arg(self):
        self.assertRaises(InternalError, TestInterface1.implement, TestClass7)

class TestInterface2(TestInterface1):
    use_many = Method(
        StrArg("a"), BoolArg("b"), IntArg("c", default=1),
        PosArgs("args"), KwArgs("kwargs")
    )

class TestClass8(TestClass1):
    IMPL_CONF = {
        "runtime_validation_level": "fail"
    }
    
    def use_many(self, a, b, c=1, *args, **kwargs):
        return (a, b, c, args, kwargs)

class InterfaceValidationTestCase(TestCase):
    def setUp(self):
        logging.basicConfig(
            filename="logs/test.log",
            format="[%(asctime)s] %(levelname)s: %(message)s",
            level=logging.DEBUG
        )
        
        self.inst = TestInterface2.implement(TestClass8)()
    
    def test_level(self):
        self.assertEqual(TestInterface2._getRuntimeValidationLevel(TestClass8), "fail")
    
    def test_str_valid(self):
        try:
            self.inst.use_str("a")
        except Exception, e:
            self.fail(str(e))

    def test_str_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_str, u'a')
        
    def test_unicode_valid(self):
        try:
            self.inst.use_unicode(u"a")
        except Exception, e:
            self.fail(str(e))

    def test_unicode_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_unicode, 'a')

    def test_string_valid(self):
        try:
            self.inst.use_string("a")
            self.inst.use_string(u"a")
        except Exception, e:
            self.fail(str(e))

    def test_string_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_string, 1)

    def test_bool_valid(self):
        try:
            self.inst.use_bool(True)
        except Exception, e:
            self.fail(str(e))

    def test_bool_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_bool, 1)

    def test_int_valid(self):
        try:
            self.inst.use_int(1)
        except Exception, e:
            self.fail(str(e))

    def test_int_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_int, 1.0)

    def test_long_valid(self):
        try:
            self.inst.use_long(2l**62)
        except Exception, e:
            self.fail(str(e))

    def test_long_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_long, 1.0)

    def test_float_valid(self):
        try:
            self.inst.use_float(1.0)
        except Exception, e:
            self.fail(str(e))

    def test_float_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_float, 1)

    def test_real_valid(self):
        try:
            self.inst.use_real(1)
            self.inst.use_real(2l**62)
            self.inst.use_real(1.0)
        except Exception, e:
            self.fail(str(e))

    def test_real_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_real, 1.0j)

    def test_complex_valid(self):
        try:
            self.inst.use_complex(1.0j)
        except Exception, e:
            self.fail(str(e))

    def test_complex_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_complex, 1.0)

    def test_list_valid(self):
        try:
            self.inst.use_list([1, 2, 3])
        except Exception, e:
            self.fail(str(e))

    def test_list_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_list, (1, 2, 3))

    def test_dict_valid(self):
        try:
            self.inst.use_dict({"a": 1, "b": 2})
        except Exception, e:
            self.fail(str(e))

    def test_dict_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_dict, (("a", 1), ("b", 2)))
        
    def test_object_valid(self):
        try:
            self.inst.use_object(self.inst)
        except Exception, e:
            self.fail(str(e))

    def test_object_invalid(self):
        self.assertRaises(TypeMismatch, self.inst.use_object, None)
        
    def test_args_valid(self):
        try:
            self.inst.use_args("a")
        except Exception, e:
            self.fail(str(e))

    def test_args_invalid(self):
        self.assertRaises(TypeError, self.inst.use_args, a="a")

    def test_kwargs_valid(self):
        try:
            self.inst.use_kwargs(a="a")
        except Exception, e:
            self.fail(str(e))

    def test_kwargs_invalid(self):
        self.assertRaises(TypeError, self.inst.use_kwargs, "a")
