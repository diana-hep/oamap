#!/usr/bin/env python

# fastparquet is part of the Dask project with Apache v2.0 license.
# 
#     https://github.com/dask/fastparquet
#     https://github.com/dask/fastparquet/blob/master/LICENSE
#     https://fastparquet.readthedocs.io/en/latest/
# 
# It's better to copy parts of fastparquet than to include it as a
# dependency. We want a very small fraction of its functionality (just
# the raw columns!) without all of its dependencies. This copy is
# limited to the functions we actually use, and the OAMap maintainer
# is responsible for keeping this copy up-to-date. For this reason,
# the copy is almost exactly literal, to make comparisons easier.

"""Utils for working with the parquet thrift models."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from oamap.source._fastparquet.extra import parquet_thrift
from oamap.source._fastparquet.extra import OrderedDict

if sys.version_info[0] <= 2:
    text_type = unicode
else:
    text_type = str

def schema_tree(schema, i=0):
    root = schema[i]
    root.children = OrderedDict()
    while len(root.children) < root.num_children:
        i += 1
        s = schema[i]
        root.children[s.name] = s
        if s.num_children is not None:
            i = schema_tree(schema, i)
    if root.num_children:
        return i
    else:
        return i + 1


def schema_to_text(root, indent=[]):
    l = len(indent)
    text = "".join(indent) + '- ' + root.name + ": "
    parts = []
    if root.type is not None:
        parts.append(parquet_thrift.Type._VALUES_TO_NAMES[root.type])
    if root.converted_type is not None:
        parts.append(parquet_thrift.ConvertedType._VALUES_TO_NAMES[
                         root.converted_type])
    if root.repetition_type is not None:
        parts.append(parquet_thrift.FieldRepetitionType._VALUES_TO_NAMES[
                         root.repetition_type])
    text += ', '.join(parts)
    indent.append('|')
    if hasattr(root, 'children'):
        indent[-1] = '| '
        for i, child in enumerate(root.children.values()):
            if i == len(root.children) - 1:
                indent[-1] = '  '
            text += '\n' + schema_to_text(child, indent)
    indent.pop()
    return text


class SchemaHelper(object):
    """Utility providing convenience methods for schema_elements."""

    def __init__(self, schema_elements):
        """Initialize with the specified schema_elements."""
        self.schema_elements = schema_elements
        self.root = schema_elements[0]
        self.schema_elements_by_name = dict(
            [(se.name, se) for se in schema_elements])
        schema_tree(schema_elements)

    def __str__(self):
        return schema_to_text(self.schema_elements[0])

    def __repr__(self):
        return "<Parquet Schema with {} entries>".format(
            len(self.schema_elements))

    def schema_element(self, name):
        """Get the schema element with the given name or path"""
        root = self.root
        if isinstance(name, text_type):
            name = name.split('.')
        for part in name:
            root = root.children[part]
        return root

    def is_required(self, name):
        """Return true if the schema element with the given name is required."""
        required = True
        if isinstance(name, text_type):
            name = name.split('.')
        parts = []
        for part in name:
            parts.append(part)
            s = self.schema_element(parts)
            if s.repetition_type != parquet_thrift.FieldRepetitionType.REQUIRED:
                required = False
                break
        return required

    def max_repetition_level(self, parts):
        """Get the max repetition level for the given schema path."""
        max_level = 0
        if isinstance(parts, text_type):
            parts = parts.split('.')
        for i in range(len(parts)):
            element = self.schema_element(parts[:i+1])
            if element.repetition_type == parquet_thrift.FieldRepetitionType.REPEATED:
                max_level += 1
        return max_level

    def max_definition_level(self, parts):
        """Get the max definition level for the given schema path."""
        max_level = 0
        if isinstance(parts, text_type):
            parts = parts.split('.')
        for i in range(len(parts)):
            element = self.schema_element(parts[:i+1])
            if element.repetition_type != parquet_thrift.FieldRepetitionType.REQUIRED:
                max_level += 1
        return max_level


def _is_list_like(helper, column):
    se = helper.schema_element(
        column.meta_data.path_in_schema[0:1])
    ct = se.converted_type
    if ct != parquet_thrift.ConvertedType.LIST:
        return False
    if len(se.children) > 1:
        return False
    se2 = list(se.children.values())[0]
    if len(se2.children) > 1:
        return False
    if se2.repetition_type != parquet_thrift.FieldRepetitionType.REPEATED:
        return False
    se3 = list(se2.children.values())[0]
    if se3.repetition_type == parquet_thrift.FieldRepetitionType.REPEATED:
        return False
    return True


def _is_map_like(helper, column):
    se = helper.schema_element(
        column.meta_data.path_in_schema[0:1])
    ct = se.converted_type
    if ct != parquet_thrift.ConvertedType.MAP:
        return False
    if len(se.children) > 1:
        return False
    se2 = list(se.children.values())[0]
    if len(se2.children) != 2:
        return False
    if se2.repetition_type != parquet_thrift.FieldRepetitionType.REPEATED:
        return False
    if set(se2.children) != set(["key", "value"]):
        return False
    se3 = se2.children['key']
    if se3.repetition_type != parquet_thrift.FieldRepetitionType.REQUIRED:
        return False
    se3 = se2.children['value']
    if se3.repetition_type == parquet_thrift.FieldRepetitionType.REPEATED:
        return False
    return True
