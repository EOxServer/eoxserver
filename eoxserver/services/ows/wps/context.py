#-------------------------------------------------------------------------------
#
# Base context class
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


class ContextError(Exception):
    """ General context error. """
    pass


class BaseContext(object):
    """ Base context class.
    This is the base abstract asynchronous WPS context class defining the
    minimal common interface of a context object passed to an asynchronous
    WPS process.

    The purpose of the context is to manage status, storage and other resources
    used by the job (executed process instance).

    The actual implementation of the concrete context classes is part
    of the asynchronous implementation.
    """

    @property
    def identifier(self):
        """ Get the context specific identifier (job id.)
        """
        raise NotImplementedError

    @property
    def logger(self):
        """ Get the context specific logger. The returned logger is expected
        to be a context aware logger adapter.
        """
        raise NotImplementedError

    @property
    def workspace_path(self):
        """ Get the workspace path.
        Note that this path is expected to be the working directory when
        an asynchronous process gets executed. This allows the process
        to write safely to its working directory.
        """
        raise NotImplementedError

    def publish(self, path):
        """ Publish file from the local workspace and return its path
        and public URL.
        The input file path must be relative to the workspace path.
        Publishing of files outside of the workspace directory sub-tree
        is not allowed.
        """
        raise NotImplementedError

    def update_progress(self, progress, message):
        """ Update the StatusStarted response and set the new progress
        expressed in percent.  The progress therefore must be a number
        between 0 and 99.  An optional message can be specified.
        """
        raise NotImplementedError
