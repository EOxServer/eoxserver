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

import os
import sys

from django.utils.importlib import import_module

class Command():
    def execute(self):
        raise NotImplementedError()

def get_commands():
    import eoxserver.core
    command_dir = os.path.join(os.path.dirname(eoxserver.core.__file__), "commands")
    command_names = [f[:-3] for f in os.listdir(command_dir)
                                if not f.startswith('_') and f.endswith('.py')]
    
    commands = {}
    for name in command_names:
        try:
            module = import_module("eoxserver.core.commands.%s"%name)
            try:
                commands[name] = module.__dict__['execute']
            except KeyError:
                print module.__dict__
                raise 
                for value in module.__dict__.values():
                    if issubclass(value, Command):
                        commands[name] = getattr(value(), 'execute')
        except ImportError:
            raise
    
    return commands
    

def execute_from_commandline():
    commands = get_commands()
    try:
        commands[sys.argv[1]](sys.argv[2:])
    except IndexError:
        print "Usage: %s <command-name> [args]" % sys.argv[0]
    except KeyError:
        print("Command '%s' not found." % sys.argv[1])
        print("Possible commands are:")
        for name in commands.keys():
            print("\t%s" % name)
        
    