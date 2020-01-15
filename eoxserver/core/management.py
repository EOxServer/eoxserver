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

import os
import sys
from optparse import make_option

import django
try:
    # Django versions >= 1.9
    from django.utils.module_loading import import_module
except ImportError:
    # Django versions < 1.9
    from django.utils.importlib import import_module
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from django.utils import termcolors

import eoxserver


class CommandNotFound(Exception):
    def __init__(self, cmdname):
        self.cmdname = cmdname


class EOxServerAdminCommand(BaseCommand):
    def execute(self, *args, **kwargs):
        return self.handle(*args, **kwargs)


def get_commands():
    import eoxserver.core.commands
    command_dir = os.path.dirname(eoxserver.core.commands.__file__)
    command_names = [
        f[:-3] for f in os.listdir(command_dir)
        if not f.startswith('_') and f.endswith('.py')
    ]

    commands = {}
    for name in command_names:
        try:
            module = import_module("eoxserver.core.commands.%s" % name)
            commands[name] = module.Command()

        except ImportError:
            raise

    return commands


def print_possible_commands(commands, stream=sys.stdout):
    stream.write(
        "Type 'eoxserver-admin.py help <subcommand>' "
        "for help on a specific subcommand.\n\n"
    )
    stream.write(
        "Possible commands are:\n" +
        "\t%s" % ("\n\t".join(commands.keys())) +
        "\n"
    )


def execute_from_commandline():
    try:
        subcommand = sys.argv[1]
    except IndexError:
        subcommand = 'help'

    commands = get_commands()

    if subcommand in ('help', '--help', '-h'):
        try:
            cmd = commands[sys.argv[2]]
            cmd.print_help(sys.argv[0], sys.argv[2])
        except IndexError:
            # TODO print general help
            print ("Usage: %s <command-name> [args]" % sys.argv[0])
            print_possible_commands(commands)
        except KeyError:
            print ("Command '%s' not found.\n" % sys.argv[2])
            print_possible_commands(commands)

    elif subcommand == '--version':
        print (eoxserver.get_version())

    else:
        try:
            command = commands[subcommand]
        except KeyError:
            print ("Command '%s' not found.\n" % sys.argv[1])
            print_possible_commands(commands)
            sys.exit(1)

        try:
            command.run_from_argv(sys.argv)
        except CommandError as e:
            print (termcolors.colorize("Error: %s" % e, fg="red"))
            sys.exit(1)
