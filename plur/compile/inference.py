#!/usr/bin/env python

# Copyright 2017 DIANA-HEP
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast

from plur.types import *
from plur.thirdparty.meta.decompiler.instructions import make_function

class Function(Type):
    def __init__(self, res, *params):
        self.result = result
        self.params = params
        super(Function, self).__init__()

    @property
    def args(self):
        return (self.result,) + self.params

def totypedast(fcn, paramtypes, closure={}):
    if callable(fcn) and hasattr(fcn, "__code__"):
        syntaxtree = make_function(fcn.__code__)
    else:
        raise TypeError("totypedast takes a Python function as its first argument")

    if isinstance(paramtypes, dict):
        symboltable = dict(paramtypes)
    else:
        try:
            iter(paramtypes)
        except TypeError:
            raise TypeError("totypedast takes a dict of name -> type or iterable of parameter types as its second argument")
        else:
            symboltable = dict((n.id if isinstance(n, ast.Name) else n.arg, t) for n, t in zip(syntaxtree.args.args, paramtypes))

    if hasattr(fcn, "__annotations__"):
        for n, t in fcn.__annotations__:
            if n != "return" and n not in symboltable:
                symboltable[n] = t

    if not isinstance(closure, dict):
        raise TypeError("totypedast takes a Python dict (e.g. vars()) as its third argument")

    def attachtype(node, symboltable):
        node.type = None   # initially unknown

        for fieldname in node._fields:
            if isinstance(getattr(node, fieldname), ast.AST):
                attachtype(getattr(node, fieldname), symboltable)

        handlername = "do_" + node.__class__.__name__
        print node, handlername

        if handlername in globals():
            node.type = globals()[handlername](node, symboltable, closure)

    attachtype(syntaxtree, symboltable)
    return syntaxtree, symboltable

# BinOp ("left", "op", "right")
def do_BinOp(node, symboltable, closure):
    print "HERE"
    return node.left
