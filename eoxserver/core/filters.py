#-----------------------------------------------------------------------
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
#-----------------------------------------------------------------------

"""
This module defines interfaces for filter expressions and filters.
These can be used to refine searches for resources.
"""

from eoxserver.core.system import System
from eoxserver.core.interfaces import *
from eoxserver.core.registry import (
    RegisteredInterface, FactoryInterface
)
from eoxserver.core.exceptions import InvalidExpressionError

class FilterExpressionInterface(RegisteredInterface):
    """
    Filter expressions can be used to constrain searches for
    resources using a factory. They provide a uniform way to
    define these constraints without respect to the concrete
    resource implementation.
    
    Internally, filter expressions are translated to filters (i.e.
    implementations of :class:`~.FilterInterface`) that can be applied
    to a resource.
    
    The binding method for filter expressions is ``factory``, i.e.
    implementations are accessible through a factory that implements
    :class:`~.FactoryInterface`. Developers have to write their own
    factory implementations for each category of expressions.
    
    .. method:: getOpName
    
       This method shall return the operator name. The name can depend
       on the instance data but does not have to. Depending on the
       factory implementation, the name may or may not vary with the
       instance data.
    
    .. method:: getOpSymbol
    
       This method shall return the operator symbol if applicable or 
       ``None`` otherwise. Depending on the factory implementation,
       the symbol may or may not vary with the instance data
    
    .. method:: getNumOperands
    
       This method shall return the number of operands required by
       the operator. Depending on the factory implementation the
       number may or may not vary with the instance data.
    
    .. method:: getOperands
    
       This method shall return a tuple of operands the instance was
       initialized with.
    
    .. method:: initialize(**kwargs)
    
       This method shall initialize the expression; it takes keyword
       arguments; each implementation has to define the arguments it
       accepts individually.
    
    :Interface ID: core.filters.FilterExpression
    """
    REGISTRY_CONF = {
        "name": "Filter Expression Interface",
        "intf_id": "core.filters.FilterExpression",
        "binding_method": "factory"
    }
    
    getOpName = Method(
        returns = StringArg("@return")
    )
    
    getOpSymbol = Method(
        returns = StringArg("@return", default=None)
    )
    
    getNumOperands = Method(
        returns = IntArg("@return")
    )
    
    getOperands = Method(
        returns = ObjectArg("@return", arg_class=tuple)
    )
    
    initialize = Method(
        KwArgs("kwargs")
    )
    
class FilterInterface(RegisteredInterface):
    """
    Filter expressions are translated to filters that can be applied
    to a given :class:`~django.db.queries.QuerySet`. This is the
    interface for this operation.
    
    Binding to implementations of this interface is possible using
    key-value-pair matching.
    
    :Interface ID: core.filters.Filter
    :KVP keys: 
        * ``core.filters.res_class_id``: the implementation ID of the
          resource class
        * ``core.filters.expr_class_id``: the implementation ID of the
          filter expression class
    
    .. method:: applyToQuerySet(expr, qs)
    
       This method shall apply a given filter expression ``expr`` to a
       given Django :class:`~django.db.queries.QuerySet` ``qs`` and
       return the resulting :class:`~django.db.queries.QuerySet`.
       
    .. method:: resourceMatches(expr, res)
       
       This method shall return ``True`` if the resource wrapped by
       ``res`` matches the filter expression ``expr``, ``False``
       otherwise.
    """
    REGISTRY_CONF = {
        "name": "Filter Interface",
        "intf_id": "core.filters.Filter",
        "binding_method": "kvp",
        "registry_keys": (
            "core.filters.res_class_id",
            "core.filters.expr_class_id"
        )
    }
    

    applyToQuerySet = Method(
        ObjectArg("expr"), # a filter expression
        ObjectArg("qs"), # a Django QuerySet
        returns = ObjectArg("@return") # a Django QuerySet
    )
    
    resourceMatches = Method(
        ObjectArg("expr"), # a filter expression
        ObjectArg("res"), # a resource wrapper
        returns = BoolArg("@return")
    )

class SimpleExpression(object):
    """
    An implementation of :class:`FilterExpressionInterface` intended to
    serve as a base class for simple expressions.
    """
    #: The operator name of the simple expression; has to be overridden
    #: by concrete implementations
    OP_NAME = ""
    
    #: The operator symbol of the simple expression; ``None`` by
    #: default; has to be overridden by concrete implementations
    OP_SYMBOL = None
    
    #: The expected number of operands; has to be overridden by
    #: concrete implementations
    NUM_OPS = 1
    
    def __init__(self):
        self.__operands = None
    
    def getOpName(self):
        """
        Returns the operator name.
        """
        return self.OP_NAME
        
    def getOpSymbol(self):
        """
        Returns the operator symbol if applicable, ``None`` by default.
        """
        return self.OP_SYMBOL
        
    def getNumOperands(self):
        """
        Returns the expected number of operands.
        """
        return self.NUM_OPS
    
    def getOperands(self):
        """
        Returns the operands of the simple expression instance.
        """
        return self.__operands
    
    def initialize(self, **kwargs):
        """
        Initialize the simple expression instance. This method accepts
        one optional keyword argument, namely ``operands`` which is
        expected to be a tuple of operands.
        
        Raises :exc:`~.InternalError` in case the number of operands
        does not match.
        
        .. note:: Further validation steps may be added by concrete
                  implementations.
        """
        operands = kwargs.get("operands", ())
        
        self._validateOperands(operands)
        
        self.__operands = operands

    def _validateOperands(self, operands):
        if len(operands) != self.getNumOperands():
            raise InvalidExpressionError(
                "Expected %d operands, got %d." % (
                    self.getNumOperands(),
                    len(operands)
            ))

class SimpleExpressionFactory(object):
    """
    This is the base class for a simple expression factory.
    """
    def __init__(self):
        # Create an index of expressions using their operator names
        ExpressionClasses = System.getRegistry().getFactoryImplementations(self)
        
        self.__op_index = {}
        
        for ExpressionCls in ExpressionClasses:
            expr = ExpressionCls()
            self.__op_index[expr.getOpName()] = ExpressionCls
        
        logging.debug("SimpleExpressionFactory.__init__(): operator index of '%s': %s" % (
            self.__get_impl_id__(), str(self.__op_index.keys())
        ))
    
    def get(self, **kwargs):
        """
        Returns a filter expression. The method accepts two keyword
        arguments:
        
        * ``op_name`` (mandatory): the operator name for the expression
        * ``operands`` (optional): a tuple of operands for the
          expression; the number and type of expected operands is
          defined by each filter expression class individually
          
        The method raises :exc:`~.InternalError` if the ``op_name``
        parameter is missing or unknown.
        """
        if "op_name" in kwargs:
            op_name = kwargs["op_name"]
        else:
            raise InternalError("Missing mandatory 'op_name' parameter.")
        
        operands = kwargs.get("operands", ())
        
        if op_name in self.__op_index:
            ExpressionCls = self.__op_index[op_name]
        else:
            raise InternalError("Unknown operator name '%s'." % op_name)
        
        expr = ExpressionCls()
        expr.initialize(operands=operands)
        
        return expr
    
    def find(self, **kwargs):
        """
        Returns a list of filter expressions. The method accepts a
        single, optional keyword argument ``op_list`` which is
        expected to be a list of dictionaries of the form::
        
            {
                "op_name": <operator_name>,
                "operands": <operand_tuple>
            }
        
        The dictionaries will be passed as keyword arguments to
        :meth:`get`
        """
        op_list = kwargs.get("op_list", [])
        
        return [self.get(**op_entry) for op_entry in op_list]
