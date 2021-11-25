#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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

import re
import functools
import json

from django.core.exceptions import FieldDoesNotExist

from eoxserver.core.decoders import kvp, enum
from eoxserver.core.util.xmltools import NameSpace
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.services import filters
from eoxserver.resources.coverages import models


class EarthObservationExtension(object):
    """ Implementation of the OpenSearch `'EO' extension
    <http://docs.opengeospatial.org/is/13-026r8/13-026r8.html>`_.
    """

    namespace = NameSpace(
        "http://a9.com/-/opensearch/extensions/eo/1.0/", "eo"
    )

    def filter(self, qs, parameters):
        mapping, mapping_choices = filters.get_field_mapping_for_model(qs.model)
        decoder = EarthObservationExtensionDecoder(parameters)

        query_filters = []
        for filter_name, db_accessor in mapping.items():
            value = getattr(decoder, filter_name, None)

            if value:
                attr = filters.attribute(filter_name, mapping)
                if isinstance(value, list):
                    query_filters.append(filters.contains(attr, value))
                elif isinstance(value, dict):
                    if 'min' in value:
                        query_filters.append(
                            filters.compare(attr, value['min'],
                                '>=' if value['min_inclusive'] else '>',
                                mapping_choices
                            )
                        )
                    if 'max' in value:
                        query_filters.append(
                            filters.compare(attr, value['max'],
                                '<=' if value['max_inclusive'] else '<',
                                mapping_choices
                            )
                        )
                else:
                    query_filters.append(
                        filters.compare(attr, value, '=', mapping_choices)
                    )

        if query_filters:
            qs = qs.filter(
                filters.combine(query_filters, 'AND')
            )

        return qs

    def get_schema(self, collection=None, model_class=None):
        mapping, mapping_choices = filters.get_field_mapping_for_model(
            model_class or models.Product, True
        )

        schema = []
        summary = None
        if collection:
            summary = self._load_product_summary(collection)

        for key, value in mapping.items():
            param = dict(
                name=key, type=key
            )

            if summary:
                param_summary = summary.get(key)

                # leave out all parameters not present in the summary
                if not self._is_param_summary_valid(param_summary):
                    continue

                # insert information from the parameter summary
                if isinstance(param_summary, list):
                    param['options'] = param_summary
                elif isinstance(param_summary, dict):
                    min_ = param_summary.get('min')
                    max_ = param_summary.get('max')
                    if min_ is not None:
                        param['min'] = min_
                    if max_ is not None:
                        param['max'] = max_

            # use the mapping choices to get a list of options, if possible
            if 'options' not in param and value in mapping_choices:
                param['options'] = list(mapping_choices[value].keys())

            schema.append(param)

        return schema

    def _load_product_summary(self, collection):
        try:
            summary = json.loads(
                collection.collection_metadata.product_metadata_summary
            )
            return {
                filters._to_camel_case(key): value
                for key, value in summary.items()
            }
        except models.CollectionMetadata.DoesNotExist:
            pass
        return None

    def _is_param_summary_valid(self, param_summary):
        if not param_summary:
            return False

        elif isinstance(param_summary, dict):
            return param_summary.get('min') or param_summary.get('max')

        return True

    # def get_schema(self, collection):
    #     return [
    #         dict(
    #             name=key, type=key,
    #             pattern=,
    #             options=[
    #                 key for key in mapping_choices[value].keys()
    #             ] if value in mapping_choices else ()
    #         )
    #         for key, value in mapping.items()
    #     ]

float_pattern = r'[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?'
int_pattern = r'[-+]\d+'
datetime_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(([+-]\d{2}:\d{2})|Z)'

base_range_pattern = (
    r'(?P<simple>%(base)s)$|'
    '(\{(?P<list>%(base)s(?:,%(base)s)*)\})$|'
    '(?P<range>(?P<low>[\[\]]%(base)s),(?P<high>%(base)s[\[\]]))$|'
    '(?P<only_low>[\[\]]%(base)s)$|'
    '(?P<only_high>%(base)s[\[\]])$'
)

float_range_pattern = re.compile(base_range_pattern % {"base": float_pattern})
int_range_pattern = re.compile(base_range_pattern % {"base": int_pattern})
datetime_range_pattern = re.compile(
    base_range_pattern % {"base": datetime_pattern}
)

def parse_range(value, pattern, value_parser):
    match = pattern.match(value)

    if match:
        values = match.groupdict()

        if values['simple']:
            return value_parser(values['simple'])
        elif values['list']:
            return [value_parser(v) for v in values['list'].split(',')]

        elif values['range']:
            low = values['low']
            hi = values['high']
            return {
                'min': value_parser(low[1:]),
                'min_inclusive': low[0] == "[",
                'max': value_parser(hi[:-1]),
                'max_inclusive': hi[-1] == "]"
            }
        elif values['only_low']:
            low = values['only_low']
            return {
                'min': value_parser(low[1:]),
                'min_inclusive': low[0] == "["
            }
        elif values['only_high']:
            hi = values['only_high']
            return {
                'max': value_parser(hi[:-1]),
                'max_inclusive': hi[-1] == "]"
            }

    return None


parse_float_range = functools.partial(
    parse_range, pattern=re.compile(float_range_pattern), value_parser=float
)

parse_int_range = functools.partial(
    parse_range, pattern=re.compile(float_range_pattern), value_parser=int
)

parse_datetime_range = functools.partial(
    parse_range, pattern=re.compile(datetime_range_pattern),
    value_parser=parse_iso8601
)


class EarthObservationExtensionDecoder(kvp.Decoder):
    productType = kvp.Parameter(num="?", type=str)
    doi = kvp.Parameter(num="?", type=str)
    platform = kvp.Parameter(num="?", type=str)
    platformSerialIdentifier = kvp.Parameter(num="?", type=str)
    instrument = kvp.Parameter(num="?", type=str)
    sensorType = kvp.Parameter(num="?", type=enum(('OPTICAL', 'RADAR', 'ALTIMETRIC', 'ATMOSPHERIC', 'LIMB'), False))
    compositeType = kvp.Parameter(num="?", type=str)
    processingLevel = kvp.Parameter(num="?", type=str)
    orbitType = kvp.Parameter(num="?", type=str)
    spectralRange = kvp.Parameter(num="?", type=str)
    wavelength = kvp.Parameter(num="?", type=parse_float_range)
    hasSecurityConstraints = kvp.Parameter(num="?", type=enum(('TRUE', 'FALSE'), False))
    dissemination = kvp.Parameter(num="?", type=str)
    recordSchema = kvp.Parameter(num="?", type=str)

    parentIdentifier = kvp.Parameter(num="?", type=str)
    productionStatus = kvp.Parameter(num="?", type=str)
    acquisitionType = kvp.Parameter(num="?", type=enum(('NOMINAL', 'CALIBRATION', 'OTHER'), False))
    orbitNumber = kvp.Parameter(num="?", type=parse_int_range)
    orbitDirection = kvp.Parameter(num="?", type=enum(('ASCENDING', 'DESCENDING'), False))
    track = kvp.Parameter(num="?", type=str)
    frame = kvp.Parameter(num="?", type=str)
    swathIdentifier = kvp.Parameter(num="?", type=str)
    cloudCover = kvp.Parameter(num="?", type=parse_int_range)
    snowCover = kvp.Parameter(num="?", type=parse_int_range)
    lowestLocation = kvp.Parameter(num="?", type=parse_float_range)
    highestLocation = kvp.Parameter(num="?", type=parse_float_range)
    productVersion = kvp.Parameter(num="?", type=str)
    productQualityStatus = kvp.Parameter(num="?", type=enum(('NOMINAL', 'DEGRADED'), False))
    productQualityDegradationTag = kvp.Parameter(num="?", type=str)
    processorName = kvp.Parameter(num="?", type=str)
    processingCenter = kvp.Parameter(num="?", type=str)
    creationDate = kvp.Parameter(num="?", type=parse_datetime_range)
    modificationDate = kvp.Parameter(num="?", type=parse_datetime_range)
    processingDate = kvp.Parameter(num="?", type=parse_datetime_range)
    sensorMode = kvp.Parameter(num="?", type=str)
    archivingCenter = kvp.Parameter(num="?", type=str)
    processingMode = kvp.Parameter(num="?", type=str)

    availabilityTime = kvp.Parameter(num="?", type=parse_datetime_range)
    acquisitionStation = kvp.Parameter(num="?", type=str)
    acquisitionSubType = kvp.Parameter(num="?", type=str)
    startTimeFromAscendingNode = kvp.Parameter(num="?", type=parse_int_range)
    completionTimeFromAscendingNode = kvp.Parameter(num="?", type=parse_int_range)
    illuminationAzimuthAngle = kvp.Parameter(num="?", type=parse_float_range)
    illuminationZenithAngle = kvp.Parameter(num="?", type=parse_float_range)
    illuminationElevationAngle = kvp.Parameter(num="?", type=parse_float_range)
    polarisationMode = kvp.Parameter(num="?", type=enum(('S', 'D', 'T', 'Q', 'UNDEFINED'), False))
    polarizationChannels = kvp.Parameter(num="?", type=str)
    antennaLookDirection = kvp.Parameter(num="?", type=str)
    minimumIncidenceAngle = kvp.Parameter(num="?", type=parse_float_range)
    maximumIncidenceAngle = kvp.Parameter(num="?", type=parse_float_range)
    acrossTrackIncidenceAngle = kvp.Parameter(num="?", type=parse_float_range)
    alongTrackIncidenceAngle = kvp.Parameter(num="?", type=parse_float_range)
    dopplerFrequency = kvp.Parameter(num="?", type=parse_float_range)
    incidenceAngleVariation = kvp.Parameter(num="?", type=parse_float_range)
