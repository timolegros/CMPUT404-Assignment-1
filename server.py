#  coding: utf-8 
import socketserver
from pathlib import Path
from os.path import abspath

# Copyright 2013 Abram Hindle, Eddie Antonio Santos, Timothee Legros
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
        self.connection = 'Connection: close\n'

        if file_path and (file_path.endswith('.html') or file_path.endswith('/')):
            self.content_type = 'Content-type: text/html; charset=UTF-8\n'
        elif file_path and file_path.endswith('.css'):
            self.content_type = 'Content-type: text/css; charset=UTF-8\n'
        else:
            self.content_type = 'Content-type: text/plain; charset=UTF-8\n'

        self.headers = self.expires + self.cache + self.content_type + self.connection

        if status_code == '200':
            self.formatted_response = protocol + ' 200 ' + 'OK\n' + self.headers + '\n' + content
        elif status_code == '404':
            self.formatted_response = protocol + ' 404 ' + 'Not Found\n' + self.headers
        elif status_code == '405':
            self.formatted_response = protocol + ' 405 ' + 'Method Not Allowed\n' + self.headers
        elif status_code == '301':
            self.url = 'http://127.0.0.1:8080' + file_path + '/'
            self.headers = self.expires + self.cache + self.connection + f'Location: {self.url}\n'
            self.formatted_response = protocol + ' 301 ' + 'Moved Permanently\n' + self.headers
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

        # print("Request received:\n", self.data, "\n", sep="")

        headers = self.data.split('\n')
        base = headers[0].split(" ")
        req_type = base[0]
        file = base[1].replace("%20", " ").replace("%21", "!").replace("%22", '"').replace("%23", "#")\
            .replace("%24", "$").replace("%25", "%").replace("%26", "&").replace("%27", "'").replace("%28", "(")\
            .replace("%29", ")").replace("%2B", " ")
        protocol = base[2]

        # print("Parsed Headers:", base, req_type, file, protocol)

        # return 405 if request is not of type GET
        if req_type != 'GET':
            response = ResponseObject(protocol, '405')
            # print("Response:\n", response.response, "\n", sep="")
            self.request.sendall(response.response_bytes)
            return

        # print('Absolute path:', abspath('./www' + file))
        # prevent serving any files outside the local www directory. This would trigger for a request where file
        # escapes the folder e.g. ../../../something/something
        if SERVE_FILES_PATH not in abspath('./www' + file):
            response = ResponseObject(protocol, '404')
            # print("Response:\n", response.response, "\n", sep="")
            self.request.sendall(response.response_bytes)
            return

        if file.endswith('.html') or file.endswith('.css'):
            # checks if the given path actually exists within the www directory
            path = Path('www' + file)
            if not path.exists():
                response = ResponseObject(protocol, '404')
                # print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)
                return

            # at this point we know the file exists, and we want to serve it
            with open(path) as f:
                content = f.read()
                response = ResponseObject(protocol, '200', content, file)
                # print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)
        elif file.endswith('/'):
            # checks if the given path actually exists within the www directory
            path = Path('www' + file)
            if not path.exists():
                response = ResponseObject(protocol, '404')
                # print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)
                return


                # at this point we know the directory exists and is within the local www directory
            with open(Path(path, 'index.html')) as f:
                content = f.read()
                response = ResponseObject(protocol, '200', content, file)
                # print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)
        else:
            # file does not end with .html .css or / so we must check for incorrect but fixable url (301)

            # checks if the given path actually exists within the www directory
            path = Path('www' + file + '/')
            if not path.exists():
                response = ResponseObject(protocol, '404')
                # print("Response:\n", response.response, "\n", sep="")
                self.request.sendall(response.response_bytes)
                return

            # send a response with the correct url
            response = ResponseObject(protocol, '301', None, file)
            # print("Response:\n", response.response, "\n", sep="")
            self.request.sendall(response.response_bytes)


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
