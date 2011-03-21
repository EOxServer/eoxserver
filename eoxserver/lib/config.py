#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import os.path
from ConfigParser import ConfigParser
from osgeo.osr import SpatialReference
import logging

from eoxserver.lib.rangetype import EOxSChannel, EOxSNilValue
from eoxserver.lib.domainset import EOxSRectifiedGrid
from eoxserver.lib.exceptions import EOxSInternalError, EOxSNoSuchCoverageException

class EOxSConfig(object):
    _instances = []
    
    @classmethod
    def getConfig(cls, config_filename):
        for instance in cls._instances:
            if instance.config_filename == config_filename:
                logging.debug("EOxSConfig.getConfig: returned existing config")
                return instance
        
        instance = EOxSConfig(config_filename)
        instance.readConfig()
        cls._instances.append(instance)
        logging.debug("EOxSConfig.getConfig: loaded new config")
        
        return instance
    
    def __init__(self, config_filename):
        super(EOxSConfig, self).__init__()
        self.config_filename = config_filename
        
        self.http_service_url = ""
        self.soap_service_url = ""
        self.services = ["WCS"]
        self.extensions = []
        self.web_metadata = {}
        
        self.coverage_configs = {}

        self._parser = ConfigParser()
        self._parsed = False

    def readConfig(self):
        """\
        The readConfig method reads the main config file and extracts
        the common service parameters from the eoxs.service section; the
        config file contains the following sections and variables:
        
        [eoxs.service]       (mandatory) section containing the service
                                        parameters
        http_service_url    (mandatory) the URL where GET KVP and POST XML
                                        OWS requests are expected
        soap_service_url    (optional)  the URL where SOAP encoded OWS
                                        requests are expected
        services            (optional)  a comma separated list of OGC Web
                                        Services to be published; defaults
                                        to WCS only
        extensions          (optional)  a comma separated list of service
                                        extensions to be published;
                                        default: none
        web.*               (optional)  metadata parameters that will be
                                        tagged onto the MapServer
                                        WEB object
        [cov.<coverage_id>] (optional)  one or more coverage sections
                                        configuring a coverage; for
                                        detailed documentation of the
                                        coverage configurations please
                                        refer to the inline documentation
                                        of the getCoverageConfig() method
        [channel.<channel_name>]
                            (optional)  one or more channel sections
                                        configuring a channel; channel
                                        definitions can be used by
                                        multiple coverages; please refer
                                        to the inline documentation of
                                        the _getRangeTypeConfig method
                                        of EOxSCoverageConfig
                                        of EOxSCoverageConfig
        """
        if not self._parsed:
            try:
                self._parser.read(self.config_filename)
            except:
                raise EOxSInternalError("Cannot open config file '%s'" % self.config_filename)

            if not self._parser.has_section("eoxs.service"):
                raise EOxSInternalError("Missing mandatory 'eoxs.service' section in config file.")
            else:
                if self._parser.has_option("eoxs.service", "http_service_url"):
                    self.http_service_url = self._parser.get("eoxs.service", "http_service_url")
                else:
                    raise EOxSInternalError("Missing mandatory 'http_service_url' parameter in config file")
                
                if self._parser.has_option("eoxs.service", "soap_service_url"):
                    self.soap_service_url = self._parser.get("eoxs.service", "soap_service_url")
                    
                if self._parser.has_option("eoxs.service", "services"):
                    self.services = self._parser.get("eoxs.service", "services").split(",")

                if self._parser.has_option("eoxs.service", "extensions"):
                    self.extensions = self._parser.get("eoxs.service", "extensions").split(",")
                
                if self._parser.has_option("eoxs.service", "paging_count_default"):
                    self.paging_count_default = int(self._parser.get("eoxs.service", "paging_count_default"))
                else:
                    self.paging_count_default = 100
                
                for option_name, value in self._parser.items("eoxs.service"):
                    if option_name.startswith("web."):
                        web_option_name = option_name[4:]
    #                    if web_option_name in (
    #                        "ows_http_max_age", "ows_updatesequence",
    #                        "ows_sld_enabled", "ows_schemas_location",
    #                        
    #                    ):
                        self.web_metadata[web_option_name] = value
                        
                self._parsed = True

    def getCoverageConfig(self, coverage_id):
        if not self._parsed:
            self.readConfig()
        
        section = "cov.%s" % coverage_id
        
        if not self._parser.has_section(section):
            raise EOxSNoSuchCoverageException("Coverage '%s' not found." % coverage_id)
        else:
            if coverage_id in self.coverage_configs:
                return self.coverage_configs[coverage_id]
            else:
                coverage_config = EOxSCoverageConfig(coverage_id)
                coverage_config.readConfig(self._parser)
                self.coverage_configs[coverage_id] = coverage_config
                return coverage_config

    def getAllCoverageConfigs(self):
        if not self._parsed:
            self.readConfig()
        
        coverage_configs = []
        
        for section in self._parser.sections():
            if section.startswith("cov."):
                coverage_id = section[4:]
                coverage_configs.append(self.getCoverageConfig(coverage_id))
        
        return coverage_configs

class EOxSCoverageConfig(object):
    def __init__(self,
        coverage_id,
        type='',
        filename='',
        data_dirs=None,
        image_pattern='*',
        strict=False,
        metadata=None,
        grid=None,
        range_type=None,
        services='all',
        extensions='all',
        acquisition_time=''
    ):
        super(EOxSCoverageConfig, self).__init__()
        self.coverage_id = coverage_id
        self.type = type
        self.filename = filename

        if data_dirs is None:
            self.data_dirs = []
        else:
            self.data_dirs = data_dirs

        self.image_pattern = image_pattern
        self.strict = strict

        if metadata is None:
            self.metadata = {}
        else:
            self.metadata = metadata

        self.grid = grid

        if range_type is None:
            self.range_type = []
        else:
            self.range_type = range_type

        self.services = services
        self.extensions = extensions
        self.acquisition_time = acquisition_time
        
        self._parser = None

    def readConfig(self, src):
        """\
        This method reads the coverage config from the section
        'cov.<coverage_id>' in the config file. The config file contains the
        following elements:
        
        [cov.<coverage_id>] (mandatory) section that contains the
                                        coverage config
        type                (mandatory) type of the coverage:
                                        * "file": single file
                                        * "multi": multiple files
                                        * "eo.collection": EO Collection
                                        * "eo.mosaic": EO Mosaic
                                        * "eo.composite": EO Composite
                                        * "eo.scene": EO Scene
        filename            (mandatory for types "file" and "eo.scene")
                                        File name of the input file
        layer.*             (optional)  Metadata to tag onto the
                                        MapServer LAYER object
                                        representing the coverage
        grid.dim            (optional)  The dimension of the grid
                                        (default: 2)
        grid.low            (optional)  The grid coordinates of the lower
                                        bounds of the grid relative to
                                        the origin;
                                        format: (<coord_1>,...,<coord_n>)
                                        default: (0,0)
        grid.high           (mandatory for types "multi", "eo.mosaic",
                             "eo.composite")
                                        The grid coordinates of the lower
                                        bounds of the grid relative to
                                        the origin;
                                        format: (<coord_1>,...,<coord_n>)
        grid.axis_labels    (optional)  A comma separated list of axis
                                        labels default: x,y for
                                        projected CRS;
                                        lon,lat for geographic CRS
        grid.srid           (mandatory for types "multi", "eo.mosaic",
                             "eo.composite")
                                        SRID of the grid CRS
        grid.origin         (mandatory for types "multi", "eo.mosaic",
                             "eo.composite")
                                        CRS coordinates of the grid origin;
                                        format: (<coord_1>,...,<coord_n>)
        grid.offset.<axis_label>
                            (mandatory for types "multi", "eo.mosaic",
                             "eo.composite")
                                        CRS coordinates of the grid offset
                                        vector for the axis denoted by
                                        <axis_label>;
                                        format: (<coord_1>,...,<coord_n>)
        range_type          (mandatory for types "multi", "eo.mosaic",
                             "eo.composite")
                                        A comma separated list of channel
                                        names; see method
                                        _getRangeTypeConfig for detailed
                                        documentation of range type
                                        configuration
        services            (optional)  A comma separated list of
                                        services which will be enabled
                                        for the coverage (defaults to
                                        WCS)
        extensions          (optional)  service extensions to be enabled
                                        for the coverage
        """
        if isinstance(src, ConfigParser):
            self._parser = src
        else:
            self._parser = ConfigParser()
            self._parser.read(src)
        
        section = "cov.%s" % self.coverage_id
        
        if not self._parser.has_section(section):
            raise EOxSNoSuchCoverageException("Coverage '%s' not found." % self.coverage_id)
        else:
            if self._parser.has_option(section, "type"):
                self.type = self._parser.get(section, "type")
            else:
                raise EOxSInternalError("Mandatory parameter 'type' missing for coverage '%s'" % self.coverage_id)
            
            if self._parser.has_option(section, "filename"):
                self.filename = self._parser.get(section, "filename")
            elif self.type in ("file", "eo.scene"):
                raise EOxSInternalError("Mandatory parameter 'filename' missing for coverage '%s'" % self.coverage_id)
                
            if self._parser.has_option(section, "data_dirs"):
                self.data_dirs = self._parser.get(section, "data_dirs").split(",")
            elif self.type == "eo.collection":
                raise EOxSInternalError("Mandatory parameter 'data_dirs' missing for coverage '%s'" % self.coverage_id)
            
            if self._parser.has_option(section, "image_pattern"):
                self.image_pattern = self._parser.get(section, "image_pattern")
            
            if self._parser.has_option(section, "strict"):
                self.strict = bool(self._parser.get(section, "strict"))

            for option_name, value in self._parser.items(section):
                if option_name.startswith("layer."):
                    lyr_option_name = option_name[6:]
                    self.metadata[lyr_option_name] = value

            self._getGridConfig()
            
            self._getRangeTypeConfig()
            
            if self._parser.has_option(section, "services"):
                self.services = self._parser.get(section, "services").split(",")
            
            if self._parser.has_option(section, "extensions"):
                self.services = self._parser.get(section, "extensions").split(",")
    
    def _getGridConfig(self):
        section = "cov.%s" % self.coverage_id
        
        has_grid = False
        for option in self._parser.options(section):
            if option.startswith("grid."):
                has_grid = True
                break

        if not has_grid:
            if self.type in ("multi", "eo.mosaic", "eo.composite"):
                raise EOxSInternalError("Missing mandatory grid parameters for coverage '%s'" % self.coverage_id)
            else:
                self.grid = None

        else:
            grid = EOxSRectifiedGrid()
            
            if self._parser.has_option(section, "grid.dim"):
                grid.dim = self._parser.getint(section, "grid.dim")
            
            if self._parser.has_option(section, "grid.low"):
                low = []
                for value in self._parser.get(section, "grid.low").lstrip("(").rstrip(")").split(","):
                    low.append(int(value))
                grid.low = tuple(low)
            
            if self._parser.has_option(section, "grid.high"):
                high = []
                for value in self._parser.get(section, "grid.high").lstrip("(").rstrip(")").split(","):
                    high.append(int(value))
                grid.high = tuple(high)
            elif self.type == "eo.collection":
                raise EOxSInternalError("Missing mandatory parameter 'grid.high' for coverage '%s'" % self.coverage_id)
            
            if self._parser.has_option(section, "grid.srid"):
                grid.srid = self._parser.getint(section, "grid.srid")
            elif self.type == "eo.collection":
                raise EOxSInternalError("Missing mandatory parameter 'grid.srid' for coverage '%s'" % self.coverage_id)
            
            if self._parser.has_option(section, "grid.axis_labels"):
                grid.axis_labels = self._parser.get(section, "grid.axis_labels").split(",")
            elif self.type == "eo.collection":
                srs = SpatialReference()
                srs.ImportFromEPSG(grid.srid)
                if srs.IsGeographic():
                    grid.axis_labels = ('lon','lat')
                else:
                    grid.axis_labels = ('x','y')
            
            if self._parser.has_option(section, "grid.origin"):
                origin = []
                for value in self._parser.get(section, "grid.origin").lstrip("(").rstrip(")").split(","):
                    origin.append(float(value))
                grid.origin = tuple(origin)
            elif self.type == "eo.collection":
                raise EOxSInternalError("Missing mandatory parameter 'grid.origin' for coverage '%s'" % self.coverage_id)
            
            offsets = []
            for axis_label in grid.axis_labels:
                if self._parser.has_option(section, "grid.offset.%s" % axis_label):
                    offset = []
                    for value in self._parser.get(section, "grid.offset.%s" % axis_label).lstrip("(").rstrip(")").split(","):
                        offset.append(float(value))
                    offsets.append(offset)
                elif self.type == "eo.collection":
                    raise EOxSInternalError("Missing mandatory parameter 'grid.offset.%s' for coverage '%s'" % (axis_label, self.coverage_id))
            grid.offsets = tuple(offsets)
            
            self.grid = grid

    def _getRangeTypeConfig(self):
        """\
        [channel.<channel_name>]        Section containing range type
                                        information for the channel
                                        <channel_name>
        identifier          (optional)  Identifier of the channel
        description         (optional)  Description of the channel
        definition          (optional)  Definition of the channel
                                        content: default:
                                        'http://opengis.net/def/property/OGC/0/Radiance',
        quality             (optional)  currently unused
        nil_values          (optional)  a list of the form
                                        (<nil_value>;<reason>),...
                                        possible values for <reason>:
                                        * AboveDetectionRange
                                        * BelowDetectionRange
                                        * inapplicable
                                        * missing
                                        * template
                                        * unknown
                                        * withheld
                                        default: none
        uom                 (optional)  Unit of measure;
                                        default: W/cm2
        allowed_values_start (optional) lower limit of allowed values;
                                        default: 0
        allowed_values_end  (optional)  upper limit of allowed values
                                        default: 255
        allowed_values_significant_figures
                            (optional)  number of significant figures;
                                        default: 3
        """
        
        cov_section = "cov.%s" % self.coverage_id

        if self._parser.has_option(cov_section, "range_type"):
            channel_names = self._parser.get(cov_section, "range_type").split(",")

            for channel_name in channel_names:
                channel = EOxSChannel(channel_name)

                channel_section = "channel.%s" % channel_name

                if self._parser.has_section(channel_section):
                    
                    if self._parser.has_option(channel_section, "identifier"):
                        channel.identifier = self._parser.get(channel_section, "identifier")
                        
                    if self._parser.has_option(channel_section, "description"):
                        channel.description = self._parser.get(channel_section, "description")
                    
                    if self._parser.has_option(channel_section, "definition"):
                        channel.definition = self._parser.get(channel_section, "definition")
                    
                    if self._parser.has_option(channel_section, "quality"):
                        channel.quality = self._parser.get(channel_section, "quality")
                    
                    if self._parser.has_option(channel_section, "nil_values"):
                        nil_value_defs = self._parser.get(channel_section, "nil_values").split(",")
                        
                        for nil_value_def in nil_value_defs:
                            tmp = nil_value_def.lstrip("(").rstrip(")").split(";")
                            if tmp[1] in ("inapplicable", "missing", "template", "unknown", "withheld"):
                                channel.nil_values.append(EOxSNilValue(tmp[0], "urn:ogc:def:nil:OGC:1.0:%s" % tmp[1]))
                            elif tmp[1] in ("AboveDetectionRange", "BelowDetectionRange"):
                                channel.nil_values.append(EOxSNilValue(tmp[0], "urn:ogc:def:nil:OGC::%s" % tmp[1]))

                    if self._parser.has_option(channel_section, "uom"):
                        channel.uom = self._parser.get(channel_section, "uom")
                    
                    if self._parser.has_option(channel_section, "allowed_values_start"):
                        channel.allowed_values_start = self._parser.get(channel_section, "allowed_values_start")

                    if self._parser.has_option(channel_section, "allowed_values_end"):
                        channel.allowed_values_start = self._parser.get(channel_section, "allowed_values_end")

                    if self._parser.has_option(channel_section, "allowed_values_significant_figures"):
                        channel.allowed_values_start = self._parser.get(channel_section, "allowed_values_significant_figures")

                self.range_type.append(channel)

        elif self.type in ("multi", "eo.mosaic", "eo.composite"):
            raise EOxSInternalError("Missing mandatory parameter 'range_type' for coverage '%s'" % self.coverage_id)
