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
# noinspection PyPackageRequirements
import serial
import os
import glob
import sys
import time
import argparse
import subprocess
from subprocess import Popen
import psutil
import atexit
import threading
from collections import deque
import binascii

try:
    # for python 3
    from s2m.s2m_http_server import start_server

except ImportError:
    # for python 2
    # noinspection PyUnresolvedReferences
    from s2m_http_server import start_server


# noinspection PyMethodMayBeStatic,PyProtectedMember
class S2M(threading.Thread):
    """
    This is the main class for s2m. It instantiates the http server
    and provides the processing for all messages coming from Scratch and
    the micro:bit. It will start a poll watchdog timer to automatically
    shutdown Scratch if scratch is invoked using the auto launch feature.
    """

    # noinspection PyArgumentList
    def __init__(self, client=None, com_port=None,
                 scratch_executable=None, base_path=None,
                 display_base_path=False, language='0'):
        """
        This method initializes the class. All parameters are normally filled in
        by using the command line options listed at the bottom of this file

        :param client: scratch or no_client. The no_client option if to manually
                       launch scratch.
        :param com_port: com port the micro:bit is connected to
        :param scratch_executable: path to scratch executable
        :param base_path: python path to s2m installation
        :param display_base_path: show the base path and exit.
        """

        threading.Thread.__init__(self)
        self.daemon = True

        # save the __init__ parameters
        self.client = client
        self.com_port = com_port
        self.scratch_executable = scratch_executable
        self.base_path = base_path
        self.display_base_path = display_base_path
        self.language = language

        # the scratch process id
        self.scratch_pid = None

        # the name of the scratch .sb2 that will be launched with auto-launch
        self.scratch_project = None

        # instance of pyserial used to communicate with the micro:bit
        self.ser = None

        # remember the last accelerometer z value to determine if shaken
        self.last_z = 0

        # threading event to control the thread loop
        self.stop_event = threading.Event()

        # deques to for the http sever to save commands and polls
        self.command_deque = deque()
        self.poll_deque = deque()

        # state variable to alternately service polls and commands
        self.deque_flip_flop = True

        # lock to protect poll data
        self.poll_data_lock = threading.Lock()

        # place to store the last received poll data
        self.last_poll_result = None

        # map of image names used for translations
        self.image_map = {"01": "HAPPY",
                          "02": "SAD",
                          "03": "ANGRY",
                          "04": "SMILE",
                          "05": "HEART",
                          "06": "CONFUSED",
                          "07": "ASLEEP",
                          "08": "SURPRISED",
                          "09": "SILLY",
                          "10": "FABULOUS",
                          "11": "MEH",
                          "12": "YES",
                          "13": "NO",
                          "14": "TRIANGLE",
                          "15": "DIAMOND",
                          "16": "DIAMOND_SMALL",
                          "17": "SQUARE",
                          "18": "SQUARE_SMALL",
                          "19": "TARGET",
                          "20": "STICKFIGURE",
                          "21": "RABBIT",
                          "22": "COW",
                          "23": "ROLLERSKATE",
                          "24": "HOUSE",
                          "25": "SNAKE",
                          "26": "ARROW_N",
                          "27": "ARROW_NE",
                          "28": "ARROW_E",
                          "29": "ARROW_SE",
                          "30": "ARROW_S",
                          "31": "ARROW_SW",
                          "32": "ARROW_W",
                          "33": "ARROW_NW"}

        print('\ns2m version 1.09  Copyright(C) 2017 Alan Yorinks  All rights reserved.')
        print("\nPython Version %s" % sys.version)

        # When control C is entered, Scratch will close if auto-launched
        atexit.register(self.all_done)

        # if no com port was specified, try doing auto discover.
        if com_port is None:
            print('Autodetecting serial port. Please wait...')
            if sys.platform.startswith('darwin'):
                locations = glob.glob('/dev/tty.[usb*]*')
                locations = glob.glob('/dev/tty.[wchusb*]*') + locations
                locations.append('end')
                # for everyone else, here is a list of possible ports
            else:
                locations = ['dev/ttyACM0', '/dev/ttyACM0', '/dev/ttyACM1',
                             '/dev/ttyACM2', '/dev/ttyACM3', '/dev/ttyACM4',
                             '/dev/ttyACM5', '/dev/ttyUSB0', '/dev/ttyUSB1',
                             '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4',
                             '/dev/ttyUSB5', '/dev/ttyUSB6', '/dev/ttyUSB7',
                             '/dev/ttyUSB8', '/dev/ttyUSB9',
                             '/dev/ttyUSB10',
                             '/dev/ttyS0', '/dev/ttyS1', '/dev/ttyS2',
                             '/dev/tty.usbserial', '/dev/tty.usbmodem', 'com2',
                             'com3', 'com4', 'com5', 'com6', 'com7', 'com8',
                             'com9', 'com10', 'com11', 'com12', 'com13',
                             'com14', 'com15', 'com16', 'com17', 'com18',
                             'com19', 'com20', 'com21', 'com1', 'end'
                             ]

            detected = None
            for device in locations:
                try:
                    self.micro_bit_serial = serial.Serial(port=device, baudrate=115200,
                                                          timeout=.1)
                    detected = device
                    break
                except serial.SerialException:
                    if device == 'end':
                        print('Unable to find Serial Port, Please plug in '
                              'cable or check cable connections.')
                        detected = None
                        exit()
                except OSError:
                    pass
            self.com_port = detected

            # open and close the port to flush the serial buffers
            self.micro_bit_serial.close()
            self.micro_bit_serial.open()
            time.sleep(.05)

            # send out a "poll" command to see if port is there
            cmd = 'g\n'
            cmd = bytes(cmd.encode())
            self.micro_bit_serial.write(cmd)
            time.sleep(2)
            sent_time = time.time()
            while not self.micro_bit_serial.inWaiting():
                if time.time() - sent_time > 2:
                    print('Unable to detect Serial Port, Please plug in '
                          'cable or check cable connections.')
                    sys.exit(0)
            # read and decode a line and strip it of trailing \r\n
            # save the data for the first poll received
            self.last_poll_result = self.micro_bit_serial.readline().decode().strip()

            print('{}{}\n'.format('Using COM Port:', detected))

            # get version of s2mb.py
            cmd = 'v\n'
            cmd = bytes(cmd.encode())
            self.micro_bit_serial.write(cmd)
            time.sleep(2)
            sent_time = time.time()
            while not self.micro_bit_serial.inWaiting():
                if time.time() - sent_time > 2:
                    print('Unable to retrieve version s2mb.py on the micro:bit.')
                    print('Have you flashed the latest version?')
                    sys.exit(0)

            v_string = self.micro_bit_serial.readline().decode().strip()
            print('{}{}\n'.format('s2mb Version: ', v_string))

            if self.client == 'scratch':
                self.find_base_path()
                print('Auto launching Scratch')
                self.auto_load_scratch()
            else:
                print('Please start Scratch.')

            # start the polling/command processing thread
            self.start()

            # start the http server
            try:
                start_server(self)
            except KeyboardInterrupt:
                sys.exit(0)

    def stop(self):
        """
        Stop the thread loop if running
        :return:
        """
        self.stop_event.set()

    def is_stopped(self):
        """
        Check to see if thread is stopped
        :return:
        """
        return self.stop_event.is_set()

    def find_base_path(self):
        """
        Look for the path to the Scratch operational files.
        Update self.base_path with the path
        """
        if not self.base_path:
            # get all the paths
            path = sys.path

            if not sys.platform.startswith('darwin'):
                # get the prefix
                prefix = sys.prefix
                for p in path:
                    # make sure the prefix is in the path to avoid false positives
                    if prefix in p:
                        # look for the configuration directory
                        s_path = p + '/s2m'
                        if os.path.isdir(s_path):
                            # found it, set the base path
                            self.base_path = p + '/s2m'
            else:
                for p in path:
                    # look for the configuration directory
                    s_path = p + '/s2m'
                    if os.path.isdir(s_path):
                        # found it, set the base path
                        self.base_path = p + '/s2m'

            if not self.base_path:
                print('Cannot locate s2m files on path.')
                print('Python path = ' + str(self.base_path))
                sys.exit(0)

            if self.display_base_path:
                print('Python path = ' + str(self.base_path))
                sys.exit(0)

    def auto_load_scratch(self):
        """
        This method will attempt to auto launch scratch
        """

        if self.scratch_executable == 'default':
            if sys.platform.startswith('win32'):
                self.scratch_executable = "C:/Program Files (x86)/Scratch 2/Scratch 2.exe"
            elif sys.platform.startswith('darwin'):
                self.scratch_executable = "/Applications/Scratch\ 2.app/Contents/MacOS/Scratch\ 2"
            else:
                self.scratch_executable = "/opt/Scratch\ 2/bin/Scratch\ 2"

        if self.language == '0':
            self.scratch_project = self.base_path + "/scratch_files/projects/s2m.sb2"
        elif self.language == '1':
            self.scratch_project = self.base_path + "/scratch_files/projects/s2m_ja.sb2"

        exec_string = self.scratch_executable + ' ' + self.scratch_project

        if self.scratch_executable and self.scratch_project:

            if sys.platform.startswith('win32'):
                scratch_proc = Popen(exec_string, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                self.scratch_pid = scratch_proc.pid
            else:
                # noinspection PyPep8
                exec_string = self.scratch_executable + ' ' + self.scratch_project
                scratch_proc = Popen(exec_string, shell=True)
                self.scratch_pid = scratch_proc.pid
        else:
            print('You must provide scratch executable information')

    # noinspection PyArgumentList
    def handle_poll(self):
        """
        This method sends a poll request to the micro:bit
        :return: sensor data
        """

        resp = self.send_command('g')
        resp = resp.lower()
        reply = resp.split(',')

        # if this reply is not the correct length, just toss it.
        if len(reply) != 11:
            return ''

        resp = self.build_poll_response(reply)
        return resp

    def handle_display_image(self, data):
        """
        This method is called when scratch issues a display_image

        :param data: image to display
        """
        # check if this is a translated string
        if data[2] == '_':
            key = data[:2]
            if key in self.image_map:
                data = self.image_map[key]
        self.send_command('d,' + data)

    def handle_scroll(self, data):
        """
        This method is called when scratch issues a scroll command

        :param data: text to scroll
        """

        data = self.scratch_fix(data)
        self.send_command('s,' + data)

    def handle_write_pixel(self, data):
        """
        This method is called when scratch issues a scroll command
        :param data: pixel x coord, pixel y coord, and intensity
        """
        self.send_command('p,' + data)

    def handle_display_clear(self):
        """
        This method is called when scratch issues a clear display command
        """

        self.send_command('c')

    def handle_digital_write(self, data):
        """
        This method is called when scratch issues a digital write command
        :param data: pin and value
        """

        self.send_command('t,' + data)

    def handle_analog_write(self, data):
        """
        This method is called when scratch issues an analog write command

        :param data: pin and value
        """
        self.send_command('a,' + data)

    def handle_reset_all(self):
        """
        This method is called when scratch issues a reset_all command.
        For now we are just going to ignore this command, but if we
        decide to process it, uncomment out the code below
        """

        # set all digital and analog outputs to zero
        self.send_command('t,0,0')
        self.send_command('t,1,0')
        self.send_command('t,2,0')

        self.send_command('a,0,0')
        self.send_command('a,1,0')
        self.send_command('a,2,0')

        # clear the display

        self.send_command('c')

    def build_poll_response(self, data_list):
        """
        Build an HTTP response from the raw micro:bit sensor data.

        :param data_list: raw data received from s2mb.py
        :return: response string
        """

        # reply string
        reply = ''

        # build gestures
        x = int(data_list[0])
        y = int(data_list[1])
        z = int(data_list[2])

        # left right
        if x > 0:
            right = 'true'
            left = 'false'
        else:
            right = 'false'
            left = 'true'

        # up down
        if y > 0:
            up = 'true'
            down = 'false'
        else:
            up = 'false'
            down = 'true'

        # Determine difference in z from
        # from last read to this one.

        # if difference is > 2000, define that
        # as shaken
        z_diff = abs(z - self.last_z)
        if z_diff > 2000:
            reply += 'shaken true\n'
        else:
            reply += 'shaken false\n'
        self.last_z = z

        reply += 'tilted_right ' + right + '\n'
        reply += 'tilted_left ' + left + '\n'
        reply += 'tilted_up ' + up + '\n'
        reply += 'tilted_down ' + down + '\n'

        reply += 'button_a_pressed ' + data_list[3] + '\n'
        reply += 'button_b_pressed ' + data_list[4] + '\n'
        reply += 'digital_read/0 ' + data_list[5] + '\n'
        reply += 'digital_read/1 ' + data_list[6] + '\n'
        reply += 'digital_read/2 ' + data_list[7] + '\n'
        reply += 'analog_read/0 ' + data_list[8] + '\n'
        reply += 'analog_read/1 ' + data_list[9] + '\n'
        reply += 'analog_read/2 ' + data_list[10] + '\n'

        return reply

    def send_command(self, command):
        """
        Send a command to the micro:bit over the serial interface
        :param command: command sent to micro:bit
        :return: If the command is a poll request, return the poll response
        """

        try:
            cmd = command + '\n'
            self.micro_bit_serial.write(cmd.encode())
        except serial.SerialTimeoutException:
            return command

        # wait for reply

        # read and decode a line and strip it of trailing \r\n

        if command == 'g':
            while not self.micro_bit_serial.inWaiting():
                pass
            # noinspection PyArgumentList
            data = self.micro_bit_serial.readline().decode().strip()
            return data

    def all_done(self):
        """
        Kill the scratch process
        :return:
        """
        if self.scratch_pid:
            proc = psutil.Process(self.scratch_pid)
            proc.kill()

    def scratch_fix(self, sst):
        """
        Scratch has a bug when presenting string. This method
        compensates for that bug
        :param sst: String to be scanned and fixed
        :return:
        """

        result = ''
        x = 0
        while x < len(sst):
            if sst[x] == '%':
                sx = sst[x + 1] + sst[x + 2]
                z = binascii.unhexlify(sx)
                result += z.decode("utf-8")
                x += 3
            else:
                result += sst[x]
                x += 1
        return result

    def run(self):
        """
        Watchdog thread
        :return:
        """
        while not self.is_stopped():
            self.deque_flip_flop = not self.deque_flip_flop

            # process the poll
            if self.deque_flip_flop:
                if len(self.poll_deque):
                    self.poll_deque.clear()
                    poll_result = self.handle_poll()
                    if poll_result:
                        with self.poll_data_lock:
                            self.last_poll_result = poll_result

            else:
                # process the commands

                if len(self.command_deque):
                    try:
                        cmd_list = self.command_deque.popleft()
                    except IndexError:
                        continue

                    cmd = cmd_list[0]

                    if cmd == 'display_image':
                        self.handle_display_image(cmd_list[1])

                    elif cmd == 'scroll':
                        self.handle_scroll(cmd_list[1])

                    elif cmd == 'write_pixel':
                        params = cmd_list[1:]
                        cmd_params = ",".join(params)
                        self.handle_write_pixel(cmd_params)

                    elif cmd == 'display_clear':
                        self.handle_display_clear()

                    elif cmd == 'digital_write':
                        params = cmd_list[1:]
                        cmd_params = ",".join(params)
                        self.handle_digital_write(cmd_params)

                    elif cmd == 'analog_write':
                        params = cmd_list[1:]
                        cmd_params = ",".join(params)
                        self.handle_analog_write(cmd_params)

                    elif cmd == 'reset_all':
                        self.handle_reset_all()

                    # received an unknown command, ignore it
                    else:
                        print('unknown command received: {}'.format(cmd))

            time.sleep(.001)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", dest="base_path", default="None",
                        help="Python File Path - e.g. /usr/local/lib/python3.5/dist-packages/s2m")
    parser.add_argument("-c", dest="client", default="scratch", help="default = scratch [scratch | no_client]")
    parser.add_argument("-d", dest="display", default="None", help='Show base path - set to "true"')
    parser.add_argument("-l", dest="language", default="0", help="Select Language: 0 = English, 1 = Japanese")
    parser.add_argument("-p", dest="comport", default="None", help="micro:bit COM port - e.g. /dev/ttyACMO or COM3")
    parser.add_argument("-r", dest="rpi", default="None", help="Set to TRUE to run on a Raspberry Pi")
    parser.add_argument("-s", dest="scratch_exec", default="default", help="Full path to Scratch executable")

    args = parser.parse_args()

    if args.base_path == 'None':
        user_base_path = None
    else:
        user_base_path = args.base_path

    if args.display == 'None':
        display = False
    else:
        display = True

    client_type = args.client
    if args.comport == 'None':
        comport = None
    else:
        comport = args.comport

    valid_languages = ['0', '1']
    lang = args.language

    if lang not in valid_languages:
        lang = '0'

    scratch_exec = args.scratch_exec
    # wait_time = int(args.wait)

    if args.rpi != 'None':
        # wait_time = 15
        scratch_exec = '/usr/bin/scratch2'

    # start s2m
    S2M(client=client_type, com_port=comport, scratch_executable=scratch_exec,
        base_path=user_base_path, display_base_path=display, language=lang)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
