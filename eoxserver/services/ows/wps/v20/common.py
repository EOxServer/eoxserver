# -------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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
# -------------------------------------------------------------------------------


from eoxserver.services.ows.wps.interfaces import ProcessInterface

from ows.wps.types import ProcessSummary
from ows.common.types import Metadata


def encode_process_summary(process: ProcessInterface) -> ProcessSummary:
    identifier = getattr(process, "identifier", type(process).__name__)
    return ProcessSummary(
        identifier=identifier,
        title=getattr(process, "title", identifier),
        abstract=getattr(process, "description", process.__doc__),
        keywords=[],  # TODO: which value to use?
        metadata=[
            Metadata(
                about=key,
                href=value,
            )  # TODO: check if this translation makes sense?
            for key, value in getattr(process, "metadata", {}).items()
        ],
        sync_execute=getattr(process, "synchronous", False),
        async_execute=getattr(process, "asynchronous", False),
        by_value=False,  # TODO: which value to use?
        by_reference=False,  # TODO: which value to use?
        version=getattr(process, "version", "1.0.0"),
        model=None,  # TODO: which value to use?
    )
