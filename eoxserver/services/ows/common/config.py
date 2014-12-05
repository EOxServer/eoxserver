#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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


from eoxserver.core.decoders import config, typelist, Choice


class CapabilitiesConfigReader(config.Reader):
    section = "services.ows"

    update_sequence     = config.Option(default="0")
    name                = config.Option(default="None")
    title               = config.Option(default="None")
    abstract            = config.Option(default="None")
    keywords            = config.Option(type=typelist(str, ","), default=[])
    fees                = config.Option(default="None")
    access_constraints  = config.Option(default="None")
    provider_name       = config.Option(default="None")
    provider_site       = config.Option(default="None")
    individual_name     = config.Option(default="None")
    position_name       = config.Option(default="None")
    phone_voice         = config.Option(default="None")
    phone_facsimile     = config.Option(default="None")
    delivery_point      = config.Option(default="None")
    city                = config.Option(default="None")
    administrative_area = config.Option(default="None")
    postal_code         = config.Option(default="None")
    country             = config.Option(default="None")
    electronic_mail_address = config.Option(default="None")
    onlineresource      = config.Option(default="None")
    hours_of_service    = config.Option(default="None")
    contact_instructions = config.Option(default="None")
    role                = config.Option(default="None")

    http_service_url = Choice(
        config.Option("http_service_url", section="services.owscommon", required=True),
        config.Option("http_service_url", section="services.ows", required=True),
    )


class WCSEOConfigReader(config.Reader):
    section = "services.ows.wcs20"
    paging_count_default = config.Option(type=int, default=None)
