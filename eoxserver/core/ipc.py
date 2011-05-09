#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from socket import socket, timeout, AF_INET, SOCK_STREAM
from socket import error as SocketError
from SocketServer import TCPServer, StreamRequestHandler
from threading import Thread, Lock
import errno
import time
import logging
    
from django.utils.simplejson import dumps, loads

from eoxserver.core.config import Config
from eoxserver.core.exceptions import IpcException

class Protocol(object):
    # Modes:
    # * request: return response to requesting client
    # * response: the response returned by a request
    # * broadcast: broadcast message to all clients
    # 
    # Request/Response Messages Types:
    # * hello: return server id
    # 
    # Broadcast Message Types:
    # * server_started: issued on start of server
    # * server_stopped: issued on stop of server
    # * system_startup: issued by client before starting up
    # * system_reset: issued by client before resetting
    # * system_force_reset: issued by client before resetting; forces
    #                       reset of other clients

    @classmethod
    def validate(cls, data):
        try:
            msg = cls.decode(data)
        except:
            return False
        
        if not isinstance(msg, dict):
            return False
        
        if "mode" in msg:
            if msg["mode"] not in ("request", "response", "broadcast"):
                return False
            else:
                mode = msg["mode"]
        else:
            return False
        
        if "type" in msg:
            msg_type = msg["type"]
            
            if mode in ("request", "response"):
                if msg_type != "hello":
                    return False
            elif mode == "broadcast":
                if msg_type not in (
                    "server_started", "server_stopped",
                    "system_startup", "system_reset",
                    "system_force_reset"
                ):
                    return False
        
        if mode == "response" and msg_type == "hello":
            if "svid" not in msg or "clid" not in msg:
                return False
        else:
            if "epid" not in msg:
                return False
            
        return True
    
    @classmethod
    def encodeHelloRequest(cls, ep_id):
        msg = {
            "mode": "request",
            "type": "hello",
            "epid": ep_id
        }
        return dumps(msg)
    
    @classmethod
    def encodeHelloResponse(cls, sv_id, cl_id):
        msg = {
            "mode": "response",
            "type": "hello",
            "svid": sv_id,
            "clid": cl_id
        }
        return dumps(msg)
    
    @classmethod
    def encodeServerStarted(cls, ep_id):
        msg = {
            "mode": "broadcast",
            "type": "server_started",
            "epid": ep_id
        }
        return dumps(msg)
    
    @classmethod
    def encodeServerStopped(cls, ep_id):
        msg = {
            "mode": "broadcast",
            "type": "server_stopped",
            "epid": ep_id
        }
        return dumps(msg)
        
    @classmethod
    def encodeSystemStartup(cls, ep_id):
        msg = {
            "mode": "broadcast",
            "type": "system_startup",
            "epid": ep_id
        }

    @classmethod
    def encodeSystemReset(cls, ep_id):
        msg = {
            "mode": "broadcast",
            "type": "system_reset",
            "epid": ep_id
        }
        return dumps(msg)
    
    @classmethod
    def encodeSystemForceReset(cls, ep_id):
        msg = {
            "mode": "broadcast",
            "type": "system_force_reset",
            "epid": ep_id
        }
        return dumps(msg)
        
    @classmethod
    def decode(cls, data):
        return loads(data)

class RequestHandler(StreamRequestHandler):
    def handle(self):
        data = self.rfile.readline().strip()
        logging.info("Server received: '%s'" % data)
        
        if Protocol.validate(data):
            self.wfile.write("%s\n" % data)

class Server(object):
    __lock = Lock()
    __thread = None
    __server = None
    
    @classmethod
    def start(cls):
        # simply ignore any calls if a thread has already been started
        if not cls.__thread or not cls.__thread.is_alive():
            cls.__lock.acquire()
            
            try:
                host = IpcConfigReader.getHost()
                port = IpcConfigReader.getPort()
                
                try:
                    cls.__server = TCPServer((host, port), RequestHandler)
                except SocketError:
                    if not __poll((host, port)):
                        raise
                    else:
                        return

                cls.__thread = Thread(target=cls.__server.serve_forever)
                cls.__thread.daemon = True
                cls.__thread.start()
                
                logging.info("IPC Server started.")
            finally:
                cls.__lock.release()
        
    @classmethod
    def stop(cls):
        cls.__lock.acquire()
        
        try:
            cls.__server.shutdown()
            
            cls.__thread.join()
            
            logging.info("IPC Server stopped.")
        finally:
            cls.__lock.release()
    
    @classmethod
    def reset(cls):
        cls.stop()
        
        cls.start()

class Client(object):
    __lock = Lock()
    __thread = None
    __socket = None
    __stop_flag = False
    
    @classmethod
    def start(cls, callback):
        # simply ignore any calls if a thread has already been started
        if not cls.__thread or not cls.__thread.is_alive():
            cls.__lock.acquire()
            
            try:
                
                host = IpcConfigReader.getHost()
                port = IpcConfigReader.getPort()

                cls.__socket = socket(AF_INET, SOCK_STREAM)
                cls.__socket.connect((host, port))

                cls.__thread = Thread(target=cls.__listen, args=(callback,))
                cls.__thread.daemon = True
                cls.__thread.start()
                
                logging.info("IPC Client started.")
            finally:
                
                cls.__lock.release()
                
    @classmethod
    def stop(cls):
        cls.__lock.acquire()
        
        try:
            cls.__stop_flag = True
        
            cls.__thread.join()
        
            cls.__socket.close()
            
            logging.info("IPC Client stopped.")
        finally:
            cls.__stop_flag = False
            
            cls.__lock.release()

    @classmethod
    def reset(cls, callback):
        # stop thread
        cls.stop()
        
        cls.start(cls, callback)
    
    @classmethod
    def send(cls, msg):
        if cls.__stop_flag:
            raise IpcException("Cannot send messages during shutdown process.")
        else:
            cls.__lock.acquire()
            
            try:
                if Protocol.validate(msg):
                    cls.__socket.send("%s\n" % msg)
                    logging.info("Sent '%s'" % msg)
                else:
                    raise InternalError("Invalid message: '%s'" % msg)
            finally:
                cls.__lock.release()

    @classmethod
    def __listen(cls, callback):
        cls.__socket.settimeout(IpcConfigReader.getTimeout())
        buffer_size = IpcConfigReader.getBufferSize()
        
        while not cls.__stop_flag:
            try:
                data = cls.__socket.recv(buffer_size)
                
                if data and not cls.__stop_flag:
                    logging.info("IPC Client received: '%s'" % data)
                    
                    callback(data)
            except Exception, e:
                logging.debug(str(e))

class IpcConfigReader(object):
    @classmethod
    def validate(cls):
        msgs = []
        
        if Config.ipcEnabled():
            if Config.getInstanceConfigValue("core.ipc", "port") is None:
                msgs.append("Missing mandatory 'port' parameter in 'core.ipc' section")
            else:
                try:
                    cls.getPort()
                except TypeError:
                    raise msgs.append("Mandatory 'port' parameter must be integer value.")
        
        try:
            cls.getTimeout()
        except TypeError:
            raise msgs.append("'timeout' parameter must be float value.")
        
        try:
            cls.getBufferSize()
        except TypeError:
            raise msgs.append("'buffer_size' parameter must be int value.")
        
        if msgs:
            raise ConfigError("\n".join(msgs))
    
    @classmethod
    def ipcEnabled(cls):
        enabled_str = Config.getInstanceConfigValue("core.ipc", "enabled")
        
        if enabled_str and enabled_str.lower() == "true":
            return True
        else:
            return False
    
    @classmethod
    def getHost(cls):
        return Config.getConfigValue("core.ipc", "host")
    
    @classmethod
    def getPort(cls):
        return int(Config.getInstanceConfigValue("core.ipc", "port"))
    
    @classmethod
    def getTimeout(cls):
        return float(Config.getConfigValue("core.ipc", "timeout"))

    @classmethod
    def getBufferSize(cls):
        return int(Config.getConfigValue("core.ipc", "buffer_size"))

def __poll(host, port, ep_id):
    # Try to connect to the given socket
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((host, port))
    except:
        return False
    
    data = Protocol.encodeHelloRequest(ep_id)
    s.send(data)
    
    received = None
    s.settimeout(IpcConfigReader.getTimeout())
    start_time = time.time()
    
    while time.time() - start_time < IpcConfigReader.getTimeout():
        try:
            received = s.recv(IpcConfigReader.getBufferSize())
            
            if received:
                msg = Protocol.decode(received)
                if msg.get("mode") == "response" and \
                   msg.get("type") == "hello" and \
                   msg.get("clid") == ep_id:
                    return True
        except timeout:
            return False
    
    return False
