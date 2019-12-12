#
#  Various helper subroutines needed by execute handler.
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

from django.utils.six import iteritems, itervalues
from eoxserver.services.ows.wps.util import OrderedDict
from eoxserver.services.ows.wps.parameters import (
    fix_parameter, LiteralData, BoundingBoxData, ComplexData,
    InputReference, InputData, RequestParameter,
)
from eoxserver.services.ows.wps.exceptions import (
    InvalidInputError, MissingRequiredInputError,
    InvalidInputReferenceError, InvalidInputValueError,
    InvalidOutputError, InvalidOutputDefError,
)


def parse_params(param_defs):
    """ Parse process's inputs/outputs parameter definitions. """
    if isinstance(param_defs, dict):
        param_defs = iteritems(param_defs)
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


def resolve_request_parameters(inputs, input_defs, request):
    """ Resolve request parameters. """
    for identifier, (_, input_def) in iteritems(input_defs):
        if isinstance(input_def, RequestParameter):
            inputs[identifier] = input_def.parse_request(request)
    return inputs


def decode_raw_inputs(raw_inputs, input_defs, resolver):
    """ Iterates over all input options stated in the process and parses
        all given inputs. This also includes resolving of references.
    """
    decoded_inputs = {}
    for identifier, (name, input_def) in iteritems(input_defs):
        raw_value = raw_inputs.get(identifier)
        if isinstance(input_def, RequestParameter):
            value = raw_value
        elif raw_value is not None:
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
        data=data,
        identifier=input_ref.identifier,
        title=input_ref.title,
        abstract=input_ref.abstract,
        mime_type=input_ref.mime_type,
        encoding=input_ref.encoding,
        schema=input_ref.schema,
    )


def decode_output_requests(response_form, output_defs):
    """ Complex data format selection (mimeType, encoding, schema)
        is passed as an input to the process
    """
    output_requests = {}
    for identifier, (name, output_def) in iteritems(output_defs):
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
            outputs = {list(itervalues(output_defs))[0][0]: outputs}
        else:
            outputs = dict(outputs)
    # Pack the outputs to a tuple containing:
    #   - the output data (before encoding)
    #   - the process output declaration (ProcessDescription/Output)
    #   - the output's requested form (RequestForm/Output)
    packed = OrderedDict()
    for identifier, (name, output_def) in iteritems(output_defs):
        request = response_form.get_output(identifier)
        result = outputs.get(name)
        # TODO: Can we silently skip the missing outputs? Check the standard!
        if result is not None:
            packed[identifier] = (result, output_def, request)
        elif isinstance(output_def, LiteralData) and output_def.default is not None:
            packed[identifier] = (output_def.default, output_def, request)
    return packed

