#-------------------------------------------------------------------------------
#
#  various WPS utilities
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

from urllib2 import urlopen, Request, URLError
from contextlib import closing
from urlparse import urlparse
from logging import getLogger

try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from eoxserver.core.util.multiparttools import iterate as iterate_multipart
from eoxserver.services.ows.wps.parameters import (
    fix_parameter, LiteralData, BoundingBoxData, ComplexData,
    InputReference, InputData,
)
from eoxserver.services.ows.wps.exceptions import (
    InvalidInputError, MissingRequiredInputError,
    InvalidInputReferenceError, InvalidInputValueError,
    InvalidOutputError, InvalidOutputDefError,
)


def parse_params(param_defs):
    """ Parse process's inputs/outputs parameter definitions. """
    if isinstance(param_defs, dict):
        param_defs = param_defs.iteritems()
    return OrderedDict(
        (param.identifier, (name, param)) for name, param in (
            (name, fix_parameter(name, param)) for name, param in param_defs
        )
    )


def check_invalid_inputs(inputs, input_defs):
    """Check that there are no undefined inputs."""
    invalids = set(inputs) - set(input_defs)
    if invalids:
        raise InvalidInputError(invalids.pop())
    return inputs


def check_invalid_outputs(outputs, output_defs):
    """Check that there are no undefined outputs."""
    invalids = set(outputs) - set(output_defs)
    if invalids:
        raise InvalidOutputError(invalids.pop())
    return outputs


def parse_named_parts(request):
    """ Extract named parts of the multi-part request
    and return them as dictionary
    """
    parts = {}
    if request.method == 'POST':
        content_type = request.META.get("CONTENT_TYPE", "")
        if content_type.startswith("multipart"):
            parts = dict(
                (content_id, data) for content_id, data in (
                    (headers.get("Content-Id"), data)
                    for headers, data in iterate_multipart(
                        request.body, headers={"Content-Type": content_type}
                    )
                ) if content_id
            )
    return parts


class InMemoryURLResolver(object):
    # pylint: disable=too-few-public-methods, no-self-use
    """ Simple in-memory URL resolver.
    The resolver resolves references and returns them as data strings.
    """

    def __init__(self, parts=None, logger=None):
        self.parts = parts or {}
        self.logger = logger or getLogger(__name__)

    def __call__(self, href, body, headers):
        """ Resolve reference URL. """
        self.logger.debug(
            "Resolving reference: %s%s", href, "" if body is None else " (POST)"
        )
        url = urlparse(href)
        if url.scheme == "cid":
            return self._resolve_multipart(url.path)
        elif url.scheme in ('http', 'https'):
            return self._resolve_http(href, body, headers)
        else:
            raise ValueError("Unsupported URL scheme %r!" % url.scheme)

    def _resolve_multipart(self, content_id):
        """ Resolve multipart-related."""
        try:
            return self.parts[content_id]
        except KeyError:
            raise ValueError("No part with content-id %r." % content_id)

    def _resolve_http(self, href, body=None, headers=None):
        """ Resolve the HTTP request."""
        try:
            with closing(urlopen(Request(href, body, dict(headers)))) as fobj:
                return fobj.read()
        except URLError as exc:
            raise ValueError(str(exc))


def decode_raw_inputs(raw_inputs, input_defs, resolver):
    """ Iterates over all input options stated in the process and parses
        all given inputs. This also includes resolving of references.
    """
    decoded_inputs = {}
    for identifier, (name, input_def) in input_defs.iteritems():
        raw_value = raw_inputs.get(identifier)
        if raw_value is not None:
            if isinstance(raw_value, InputReference):
                if not input_def.resolve_input_references:
                    # do not resolve reference if this is explicitly required
                    # by the input definition
                    decoded_inputs[name] = raw_value
                    continue
                try:
                    raw_value = _resolve_reference(raw_value, resolver)
                except ValueError as exc:
                    raise InvalidInputReferenceError(identifier, exc)
            try:
                value = _decode_input(input_def, raw_value)
            except ValueError as exc:
                raise InvalidInputValueError(identifier, exc)
        elif input_def.is_optional:
            value = getattr(input_def, 'default', None)
        else:
            raise MissingRequiredInputError(identifier)
        decoded_inputs[name] = value
    return decoded_inputs


def _decode_input(input_def, raw_value):
    """ Decode raw input and check it against the allowed values."""
    if isinstance(input_def, LiteralData):
        return input_def.parse(raw_value.data, raw_value.uom)
    elif isinstance(input_def, BoundingBoxData):
        return input_def.parse(raw_value.data)
    elif isinstance(input_def, ComplexData):
        return input_def.parse(
            raw_value.data, raw_value.mime_type,
            raw_value.schema, raw_value.encoding, urlsafe=raw_value.asurl
        )
    else:
        raise TypeError("Unsupported parameter type %s!"%(type(input_def)))


def _resolve_reference(input_ref, resolver):
    """ Get the input passed as a reference."""
    # prepare HTTP/POST request
    if input_ref.method == "POST":
        if input_ref.body_href is not None:
            input_ref.body = resolver(
                input_ref.body_href, None, input_ref.headers
            )
        if input_ref.body is not None:
            ValueError("Missing the POST request body!")
    else:
        input_ref.body = None
    data = resolver(input_ref.href, input_ref.body, input_ref.headers)
    return InputData(
        input_ref.identifier, input_ref.title, input_ref.abstract, data,
        None, None, input_ref.mime_type, input_ref.encoding, input_ref.schema
    )


def decode_output_requests(response_form, output_defs):
    """ Complex data format selection (mimeType, encoding, schema)
        is passed as an input to the process
    """
    output_requests = {}
    for identifier, (name, output_def) in output_defs.iteritems():
        request = response_form.get_output(identifier)
        if isinstance(output_def, ComplexData):
            format_ = output_def.get_format(
                request.mime_type,
                request.encoding,
                request.schema
            )
            if format_ is None:
                raise InvalidOutputDefError(identifier, (
                    "Invalid complex data format! "
                    "mimeType=%r encoding=%r schema=%r" % (
                        request.mime_type,
                        request.encoding,
                        request.schema
                    )
                ))
            output_requests[name] = {
                "mime_type": format_.mime_type,
                "encoding": format_.encoding,
                "schema": format_.schema,
                "as_reference": request.as_reference,
            }
    return output_requests


def pack_outputs(outputs, response_form, output_defs):
    """ Collect data, output declaration and output request for each item."""
    # Normalize the outputs to a dictionary.
    if not isinstance(outputs, dict):
        if len(output_defs) == 1:
            outputs = {output_defs.values()[0][0]: outputs}
        else:
            outputs = dict(outputs)
    # Pack the outputs to a tuple containing:
    #   - the output data (before encoding)
    #   - the process output declaration (ProcessDescription/Output)
    #   - the output's requested form (RequestForm/Output)
    packed = OrderedDict()
    for identifier, (name, output_def) in output_defs.iteritems():
        request = response_form.get_output(identifier)
        result = outputs.get(name)
        # TODO: Can we silently skip the missing outputs? Check the standard!
        if result is not None:
            packed[identifier] = (result, output_def, request)
        elif isinstance(output_def, LiteralData) and output_def.default is not None:
            packed[identifier] = (output_def.default, output_def, request)
    return packed
