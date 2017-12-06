"""
 Copyright (c) 2017 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import sys

try:
    # for python2
    # noinspection PyCompatibility,PyUnresolvedReferences
    from BaseHTTPServer import BaseHTTPRequestHandler
    # noinspection PyCompatibility
    from BaseHTTPServer import HTTPServer

except ImportError:
    # for python3
    # noinspection PyCompatibility.BaseHTTPRequestHandler,PyUnresolvedReferences,PyCompatibility
    from http.server import BaseHTTPRequestHandler
    # noinspection PyCompatibility,PyUnresolvedReferences
    from http.server import HTTPServer


# noinspection PyMethodMayBeStatic,PyUnresolvedReferences
class GetHandler(BaseHTTPRequestHandler):
    """
    This class contains the HTTP server that Scratch2 communicates with.
    Scratch sends HTTP GET requests and this class processes those requests.
    """

    # this is a 'classmethod' because we need to set data before starting
    # the HTTP server.
    # noinspection PyMethodParameters
    s2m = None

    @classmethod
    def set_items(cls, s2m):
        """
        This class method allows setting of some class variables
        :param s2m:
        :return:
        """
        # create a reference to the s2m class
        cls.s2m = s2m

    # noinspection PyPep8Naming
    def do_GET(self):
        """
        Scratch2 only sends HTTP GET commands. This method processes them.
        :return: None
        """

        # skip over the / in the command
        cmd = self.path[1:]

        # create a list containing the command and all of its parameters
        cmd_list = str.split(cmd, '/')

        # add the poll or command to the appropriate deque
        # and send an HTTP response to Scratch
        if cmd_list[0] == 'poll':
            if self.s2m.ignore_poll:
                self.send_resp('ok')
            else:
                self.send_resp(self.s2m.handle_poll())
                self.s2m.ignore_poll = False
        else:
            # self.s2m.command_deque.append(cmd_list)
            self.process_command(cmd_list)

    # we can't use the standard send_response since we don't conform to its
    # standards, so we craft our own response handler here
    def send_resp(self, response):
        """
        This method sends Scratch an HTTP response to an HTTP GET command.
        :param response: Response string sent to Scratch
        :return: None
        """

        try:
            slen = str(len(response))
        except TypeError:
            # in case of any error, just reply with ok and continue on
            response = 'ok'
            slen = str(len(response))
        crlf = "\r\n"
        http_response = "HTTP/1.1 200 OK" + crlf
        http_response += "Content-Type: text/html; charset=ISO-8859-1" + crlf
        http_response += "Content-Length" + slen + crlf
        http_response += "Access-Control-Allow-Origin: *" + crlf
        http_response += crlf
        # add the response to the nonsense above
        http_response += str(response + crlf)
        # send it out the door to Scratch
        try:
            self.wfile.write(http_response.encode())
        except ConnectionResetError:
            pass
        # end of GetHandler class

    def process_command(self, cmd_list):
        """
        This method provides processing for each command. It translates the
        Scratch command into a command that matches the s2mb.py file
        loaded onto the micro:bit.
        :param cmd_list:
        :return:
        """
        cmd = cmd_list[0]

        # process commands

        # create a display image command, send it to
        # the micro:bit and send an HTTP reply to Scratch
        if cmd == 'display_image':
            resp = self.s2m.handle_display_image(cmd_list[1])
            self.send_resp(resp)

        # create a scroll command, send it to
        # the micro:bit and send an HTTP reply to Scratch
        elif cmd == 'scroll':
            resp = self.s2m.handle_scroll(cmd_list[1])
            self.send_resp(resp)

        # create a write pixel command, send it to
        # the micro:bit and send an HTTP reply to Scratch
        elif cmd == 'write_pixel':
            params = cmd_list[1:]
            cmd_params = ",".join(params)
            resp = self.s2m.handle_write_pixel(cmd_params)
            self.send_resp(resp)

        # create a clear display command, send it to
        # the micro:bit and send an HTTP reply to Scratch
        elif cmd == 'display_clear':
            resp = self.s2m.handle_display_clear()
            self.send_resp(resp)

        # create a digital write command, send it to
        # the micro:bit and send an HTTP reply to Scratch
        elif cmd == 'digital_write':
            params = cmd_list[1:]
            cmd_params = ",".join(params)
            resp = self.s2m.handle_digital_write(cmd_params)
            self.send_resp(resp)

        # create a analog write command, send it to
        # the micro:bit and send an HTTP reply to Scratch
        elif cmd == 'analog_write':
            params = cmd_list[1:]
            cmd_params = ",".join(params)
            resp = self.s2m.handle_analog_write(cmd_params)
            self.send_resp(resp)

        elif cmd == 'reset_all':
            resp = self.s2m.handle_reset_all()
            self.send_resp(resp)

        # received an unknown command, just send a response to Scratch
        else:
            self.send_resp('OK')


def start_server(handler):
    """
    This function populates class variables with essential data and
    instantiates the HTTP Server
    :param handler:
    :return: none.
    """

    GetHandler.set_items(handler)
    try:
        server = HTTPServer(('localhost', 50209), GetHandler)
        print('Starting HTTP Server!')
        print('Use <Ctrl-C> to exit the extension.')
        print('Please make sure you save your Scratch project BEFORE pressing Ctrl-C.\n')
    except OSError:
        print('HTTP Socket may already be in use - restart Program and Scratch')
        sys.exit(0)
    try:
        # start the server
        server.serve_forever()
    except KeyboardInterrupt:
        print("You Hit Control-C.  Goodbye !")
        raise KeyboardInterrupt
    except Exception:
        raise
