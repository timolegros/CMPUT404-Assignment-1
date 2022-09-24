#  coding: utf-8 
import socketserver
from pathlib import Path
from os.path import abspath


# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore, it is derived from the Python documentation examples thus
# some code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# variable used to determine whether a requested file is actually within the local www directory
SERVE_FILES_PATH = abspath('./www')

class ResponseObject:
    def __init__(self, protocol, status_code, content=None, file_path=None):
        self.protocol = protocol
        self.status_code = status_code
        self.content = content
        self.expires = 'Expires: -1\n'
        self.cache = 'Cache-Control: private, max-age=0\n'
        self.connection = 'Connection: close\n\n'

        if file_path and file_path.endswith('.html'):
            self.content_type = 'Content-type: text/html; charset=UTF-8\n'
        elif file_path and file_path.endswith('.css'):
            self.content_type = 'Content-type: text/css; charset=UTF-8'
        else:
            self.content_type = 'Content-type: text/plain; charset=UTF-8'

        self.headers = self.expires + self.cache + self.content_type + self.connection

        if status_code == '200':
            self.formatted_response = protocol + ' 200 ' + 'OK\n' + self.headers + content
        elif status_code == '404':
            self.formatted_response = protocol + ' 404 ' + 'Not Found\n' + self.headers
        elif status_code == '405':
            self.formatted_response = protocol + ' 405 ' + 'Method Not Allowed\n' + self.headers
        elif status_code == '301':
            pass
        else:
            raise "Invalid status code"

    @property
    def response(self):
        return self.formatted_response

    @property
    def response_bytes(self):
        return bytearray(self.formatted_response.encode())


class MyWebServer(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip().decode('utf-8').replace("\r", "")

        print("Request received:\n", self.data, "\n", sep="")

        headers = self.data.split('\n')
        base = headers[0].split(" ")
        req_type = base[0]
        file = base[1]
        protocol = base[2]

        # return 405 if request is not of type GET
        if req_type != 'GET':
            response = protocol + ' 405 ' + 'Method Not Allowed\n\n'
            self.request.sendall(bytearray(response, "utf-8"))

        if file == '/':
            with open('www/index.html') as f:
                content = f.read()
                response = ResponseObject(protocol, '200', content)
                print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)
        else:
            # prevent serving any files outside the local www directory this would trigger for a request where file
            # escapes the folder e.g. ../../../something/something
            if SERVE_FILES_PATH not in abspath('./www' + file):
                response = ResponseObject(protocol, '404')
                self.request.sendall(response.response_bytes)
                return

            # checks if the given path actually exists within the www directory
            path = Path('www/' + file)
            if not path:
                response = ResponseObject(protocol, '404')
                self.request.sendall(response.response_bytes)
                return

            # at this point we know the file exists, and we want to serve it
            with open(path) as f:
                content = f.read()
                response = ResponseObject(protocol, '200', content, file)
                print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
