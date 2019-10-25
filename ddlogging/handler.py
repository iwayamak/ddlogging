# -*- coding:utf-8 -*-

"""
Datadog logs logging handler
"""

__author__ = "Katsuya Iwayama <iwayamak@matsubabreak.com>"
__status__ = "beta"
__version__ = "0.1.0"
__date__ = "25 Oct 2019"

import time
import json
import os
import logging
import socket
import ssl
import sys


class DatadogLogsHandler(logging.Handler):
    """
    Datadog logs logging handler
    """

    def __init__(self, *args, **kwargs):
        super(DatadogLogsHandler, self).__init__(level=kwargs.pop('level', logging.NOTSET))
        self.sourcecategory = kwargs.pop('source_category', 'ddlogging')
        self.source = kwargs.pop('source', 'python')
        self.service = kwargs.pop('service', None)
        self.host = kwargs.pop('host', socket.gethostname())
        self.api_key = kwargs.pop('api_key', os.environ.get('DD_API_KEY', ''))
        self.ssl = kwargs.pop('ssl', True)
        self.blocking = kwargs.pop('blocking', False)
        self.sock = None
        self.retry_time = None
        #
        # Exponential backoff parameters (Same as SocketHandler)
        #
        self.retry_start = kwargs.pop('retry_start', 1.0)
        self.retry_max = kwargs.pop('retry_max', 30.0)
        self.retry_factor = kwargs.pop('retry_factor', 2.0)

    def _make_socket(self, timeout=1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        port = 10514
        if self.ssl:
            sock = ssl.wrap_socket(sock)
            port = 10516
        try:
            sock.connect(('lambda-intake.logs.datadoghq.com', port))
            sock.setblocking(self.blocking)
        except OSError:
            sock.close()
            raise
        return sock

    def _create_socket(self):
        """
        Try to create a socket, using an exponential backoff with
        a max retry time.
        """
        now = time.time()
        if self.retry_time is None:
            attempt = True
        else:
            attempt = (now >= self.retry_time)
        if attempt:
            try:
                self.sock = self._make_socket()
                self.retry_time = None  # next time, no delay before trying
            except OSError:
                # Creation failed, so set the retry time and return.
                if self.retry_time is None:
                    self.retry_period = self.retry_start
                else:
                    self.retry_period = self.retry_period * self.retry_factor
                    if self.retry_period > self.retry_max:
                        self.retry_period = self.retry_max
                self.retry_time = now + self.retry_period

    def _send(self, send_data):
        """
        Send a string to the socket.
        """
        while 1:
            if self.sock is None:
                self._create_socket()
            try:
                self.sock.sendall(send_data)
                break
            except Exception as e:
                print('{}: {}'.format(e, json.loads(send_data.decode('utf-8')[33:])['msg']), file=sys.stderr)
                self.sock.close()
                self.sock = None
                time.sleep(3)

    def _make_send_data(self, record):
        log = self.format(record)
        if isinstance(log, str):
            log = {'message': log}
        elif not isinstance(log, dict):
            raise Exception(
                'Cannot send the entry as it must be either a string or a dict.'
                + 'Provided entry: '
                + str(log)
            )
        status = 'info'
        if record.levelno >= logging.ERROR:
            status = 'error'
        elif record.levelno == logging.WARNING:
            status = 'warning'
        service = self.service
        if service is None:
            service = record.name
        log.update({
            'ddsourcecategory': self.sourcecategory,
            'ddsource': self.source,
            'service': service,
            'host': self.host,
            'status': status})
        log = '{} {}\n'.format(self.api_key, json.dumps(log)).encode('utf-8')
        return log

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            log = self._make_send_data(record)
            self._send(log)
        except Exception:
            self.handleError(record)

    def close(self):
        """
        Closes the socket.
        """
        self.acquire()
        try:
            sock = self.sock
            if sock:
                sock.close()
                self.sock = None
            logging.Handler.close(self)
        finally:
            self.release()
