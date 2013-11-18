#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from textwrap import dedent

from django.test import TestCase

from eoxserver.core.util import multiparttools as mp
from eoxserver.services.result import result_set_from_raw_data





class MultipartTest(TestCase):
    """ Test class for multipart parsing/splitting
    """

    example_multipart = dedent("""\
        MIME-Version: 1.0\r
        Content-Type: multipart/mixed; boundary=frontier\r
        \r
        This is a message with multiple parts in MIME format.\r
        --frontier
        Content-Type: text/plain\r
        \r
        This is the body of the message.\r
        --frontier
        Content-Type: application/octet-stream\r
        Content-Transfer-Encoding: base64\r
        \r
        PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==\r
        --frontier--
    """)

    def test_multipart_iteration(self):
        parsed = map(
            lambda i: (i[0], str(i[1])), mp.iterate(self.example_multipart)
        )

        self.assertEqual([
                ({"MIME-Version": "1.0", "Content-Type": "multipart/mixed; boundary=frontier"}, ""),
                ({"Content-Type": "text/plain"}, "This is the body of the message."),
                ({"Content-Type": "application/octet-stream", "Content-Transfer-Encoding": "base64"}, "PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==")
            ], parsed
        )


class ResultSetTestCase(TestCase):

    example_multipart = dedent("""\
        MIME-Version: 1.0\r
        Content-Type: multipart/mixed; boundary=frontier\r
        \r
        This is a message with multiple parts in MIME format.\r
        --frontier
        Content-Type: text/plain\r
        Content-Disposition: attachmet; filename="message.msg"\r
        Content-Id: message-part\r
        \r
        This is the body of the message.\r
        --frontier
        Content-Type: application/octet-stream\r
        Content-Transfer-Encoding: base64\r
        \r
        PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==\r
        --frontier--
    """)


    def test_result_set_from_raw(self):
        result_set = result_set_from_raw_data(self.example_multipart)
        self.assertTrue(len(result_set) == 2)

        first = result_set[0]
        second = result_set[1]

        self.assertEqual(str(first.data), "This is the body of the message.")
        self.assertEqual(first.content_type, "text/plain")
        self.assertEqual(first.filename, "message.msg")
        self.assertEqual(first.identifier, "message-part")
        self.assertEqual(str(second.data), "PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==")

