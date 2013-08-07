from eoxserver.core.decoders import config, typelist, Choice


class CapabilitiesConfigReader(config.Reader):
    section = "services.ows"

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
