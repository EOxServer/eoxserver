#-------------------------------------------------------------------------------
#
# Storage context class
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

import errno
from logging import getLogger
from os import makedirs, chdir, rmdir, listdir
from os.path import join, isfile, isdir, exists, relpath, dirname
from shutil import move, rmtree
from urlparse import urljoin

class ContextError(Exception):
    """ General context error. """
    pass

class Context(object):
    """ Basic WPS context class
    The context manages the storage needed by the WPS output references and
    asynchronous processes.

    The context reads the configuration and creates the process temporary
    working directory and permanent directory where the results are published.

    The temporary workspace exists only during the processes execution and gets
    automatically removed when the execution ends.

    The permanent storage contains the processing outputs and it exists
    even after the process termination.
    """
    def __init__(self, path_temp, path_perm, url_base, logger=None,
                 path_perm_exists=False):
        """ Inputs:
            path_temp   - temporary storage path (aka workspace)
            path_perm   - permanent storage path (aka output bucket)
            url_base    - public URL of the output bucket
            path_perm_exists
                        - the context can be set several times by different
                          processes.  The first time the output bucket must not
                          exist but later it must exists. Whether the output
                          bucket exists or not is controlled by this process.
        """
        self.logger = logger or getLogger(__name__)
        self._path_temp = path_temp
        self._path_perm = path_perm
        self._url_base = url_base if url_base[-1] == '/' else url_base + '/'
        self._path_perm_exists = path_perm_exists

    def __enter__(self):
        # initialize context
        self.logger.info("Setting up the context.")
        # create the temporary directory
        try:
            makedirs(self._path_temp)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                raise ContextError(
                    "Temporary path must not exist! PATH=%s" % self._path_temp
                )
            raise
        self.logger.debug("created %s", self._path_perm)
        # create the permanent directory
        try:
            if self._path_perm_exists:
                if not isdir(self._path_perm):
                    # the path must be directory
                    raise ContextError(
                        "Permanent path must be an existing directory! PATH=%s"
                        % self._path_perm
                    )
            else:
                # the directory must not exist
                try:
                    makedirs(self._path_perm)
                except OSError as exc:
                    if exc.errno == errno.EEXIST:
                        raise ContextError(
                            "Permanent path must not exist! PATH=%s"
                            % self._path_perm
                        )
                    raise
                self.logger.debug("created %s", self._path_temp)
        except:
            # in case of failure remove the already existing temporary directory
            rmdir(self._path_temp)
            self.logger.debug("removed %s", self._path_perm)
            raise
        # assure we stay in the temporary directory
        chdir(self._path_temp)
        self.logger.debug("dir. changed to  %s", self._path_temp)
        return self

    def __exit__(self, type, value, traceback):
        # remove workspace
        self.logger.info("Releasing the context.")
        if isdir(self._path_temp):
            # wipe out temporary workspace
            rmtree(self._path_temp)
            self.logger.debug("removed %s", self._path_temp)
        if isdir(self._path_perm) and not listdir(self._path_perm):
            # remove permanent directory if empty
            rmdir(self._path_perm)
            self.logger.debug("removed %s", self._path_perm)

    @property
    def workspace_path(self):
        """ Get the workspace path. """
        return self._path_temp

    def publish(self, path):
        """ Publish file from the local workspace and return its path
        and public URL.
        The file path must be relative to the workspace path.
        """
        self.logger.info("Publishing %s", path)
        chdir(self._path_temp) # assure we stay in the workspace
        # check the path
        source = relpath(path)
        if '..' in source:
            self.logger.error("Attempt to publish non-local file %s", path)
            raise ContextError(
                "Only local workspace files can be published! PATH=%s" % path
            )
        if not isfile(source):
            self.logger.error("Attempt to publish non-file path %s", path)
            raise ContextError("Only files can be published! PATH=%s" % path)
        # publish the file
        target_path = join(self._path_perm, source)
        targer_url = urljoin(self._url_base, source)
        if not exists(dirname(target_path)):
            makedirs(dirname(target_path))
        move(source, target_path)
        self.logger.debug("moved %s -> %s", path, target_path)
        return target_path, targer_url
