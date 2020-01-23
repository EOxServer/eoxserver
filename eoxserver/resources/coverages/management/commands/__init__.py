#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

import logging
import traceback
from optparse import OptionValueError

import django
from django.db import transaction
from django.core.management.base import CommandParser


logger = logging.getLogger(__name__)


def _variable_args_cb(option, opt_str, value, parser):
    """ Helper function for optparse module. Allows
        variable number of option values when used
        as a callback.
    """
    args = []
    for arg in parser.rargs:
        if not arg.startswith('-'):
            args.append(arg)
        else:
            break

    del parser.rargs[:len(args)]

    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)


class StringFormatCallback(object):
    """ Small helper class to supply a variable number of arguments to a
    callback function and store the resulting value in the `dest` field of the
    parser.
    """

    def __init__(self, callback):
        self.callback = callback

    def __call__(self, option, opt_str, value, parser):
        args = []
        for arg in parser.rargs:
            if not arg.startswith('-'):
                args.append(arg)
            else:
                del parser.rargs[:len(args)]
                break

        try:
            setattr(parser.values, option.dest, self.callback(" ".join(args)))
        except ValueError as e:
            raise OptionValueError(str(e))


class CommandOutputMixIn(object):
    """ Helper mix-in class to ease the handling of user message reporting.
    """

    def print_err(self, msg):
        " Print an error message which is both logged and written to stderr. "

        logger.error(msg)
        self.stderr.write("ERROR: %s\n" % msg)

    def print_wrn(self, msg):
        """ Print a warning message, which is logged and posibly written to
            stderr, depending on the set verbosity.
        """

        logger.warning(msg)

        if 0 < max(0, getattr(self, "verbosity", 1)):
            self.stderr.write("WARNING: %s\n" % msg)

    def print_msg(self, msg, level=1):
        """ Print a basic message with a given level. The message is possibly
            logged and/or written to stderr depending on the verbosity setting.
        """

        # three basic level of info messages
        # level == 0 - always printed even in the silent mode - not recommended
        # level == 1 - normal info suppressed in silent mode
        # level >= 2 - debuging message (additional levels allowed)
        # messages ALWAYS logged (as either info or debug)

        level = max(0, level)
        verbosity = max(0, getattr(self, "verbosity", 1))

        # everything with level 2 or higher is DEBUG
        if level >= 2:
            prefix = "DEBUG"
            logger.debug(msg)

        # levels 0 (silent) and 1 (default-verbose)
        else:
            prefix = "INFO"
            logger.info(msg)

        if level <= verbosity:
            self.stdout.write("%s: %s\n" % (prefix, msg))

    def print_traceback(self, e, kwargs):
        """ Prints a traceback/stacktrace if the traceback option is set.
        """
        if kwargs.get("traceback", False):
            self.print_msg(traceback.format_exc())


def create_parser(cmd, kwargs):
    if django.VERSION[0] < 2:
        return CommandParser(cmd, **kwargs)
    else:
        return CommandParser(**kwargs)

class SubParserMixIn(object):
    def add_subparser(self, parser, name, *args, **kwargs):
        if not getattr(self, 'subparsers', None):
            self.subparsers = parser.add_subparsers(
                title="subcommands",
                parser_class=lambda **kw: create_parser(self, kw)
            )
        subparser = self.subparsers.add_parser(name, *args, **kwargs)
        subparser.set_defaults(subcommand=name)

        subparser.add_argument('--traceback', action="store_true", default=False)
        subparser.add_argument('--settings', nargs=1)
        subparser.add_argument('--pythonpath', nargs=1)
        subparser.add_argument('--no-color', action="store_true", default=False)

        return subparser
