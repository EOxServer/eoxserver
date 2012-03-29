#-------------------------------------------------------------------------------
# $Id$
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
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)
    
class StringFormatCallback(object):
    """ Small helper class to supply a variable number of arguments to a callback 
        function and store the resulting value in the `dest` field of the parser. 
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
        
        setattr(parser.values, option.dest, self.callback(" ".join(args)))
        

class CommandOutputMixIn(object):
    def print_msg(self, msg, level=0, error=False):
        verbosity = getattr(self, "verbosity", 1)
        if verbosity > level:
            self.stdout.write(msg)
            self.stdout.write("\n")
        
        if level == 0 and error:
            logging.critical(msg)
        elif level == 1 and error:
            logging.error(msg)
        elif level in (0, 1, 2) and not error:
            logging.info(msg)
        elif level > 2:
            logging.debug(msg)
