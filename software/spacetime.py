import time

import serial

from timeutil import is_time_str, time_to_str


CRLF = "\r\n"


class SerialMsg:
    def __init__(self, msgtype, msgval):
        self.type = msgtype
        self.val = msgval


class SpaceTime:
    # See Serial protocol for communicating with SpaceTime at:
    # https://github.com/BruceFletcher/SpaceTime/blob/master/sw/serial.c
    BAUD = 57600

    def __init__(self, serial_device_name="/dev/ttyAMA0"):
        self.serial = serial.Serial(serial_device_name, self.BAUD, timeout=1)

    def clear_serial(self):
        # Clear the local Serial buffers as well as SpaceTime's buffer

        # Send a newline to ensure SpaceTime buffer is emptied
        self.serial.write(CRLF)
        self.serial.flush()  # Ensure the CRLF is sent
        time.sleep(0.25)  # Give SpaceTime some time to respond
        self.serial.flushOutput()  # Discard any data in the out buffer
        self.serial.flushInput()  # Discard any data in the input buffer

    def can_read(self):
        # Checks whether there is serial data waiting to be read from SpaceTime
        return self.serial.inWaiting() > 0

    def is_connected(self, timeout=10, writedelay=0.25):
        # Queries SpaceTime over Serial connection and waits for proper acknowledgement.
        # Will return within 'timeout' seconds, and queries are sent every 'writedelay' seconds.
        # Returns True if SpaceTime acknowledges, and False if timeout exceeded.

        start_time = time.time()

        while 1:
            #'AT' should trigger SpaceTime to respond with 'OK'
            self.serial.write("AT" + CRLF)

            while self.can_read():
                # Check if received value is expected acknowledgement from SpaceTime
                if self.serial.readline() == "OK" + CRLF:
                    # We have verified the serial connection!
                    self.clear_serial()

                    return True

            # Return false if time exceeded
            if time.time() - start_time > timeout:
                return False

            # Add small delay between writes in case SpaceTime is offline or busy
            time.sleep(writedelay)

    def read(self):
        # Returns a SerialMsg with type as 'Current' or 'Closing' time, and
        # val as a struct_time or None if time is cleared. Other types:
        # AmbiguousTime (for time queries that reply without clock name. Similar to above.)
        # OK (for 'OK' response)
        # AT Command Echo (for our commands that were echoed back by SpaceTime)
        # Boot (for the message that SpaceTime sends upon startup)
        # Unknown (for any other serial message)
        # For all of these, val = the full message received

        data = self.serial.readline()

        if data.startswith("OK"):
            return SerialMsg("OK", data)
        elif data.startswith("AT"):
            # SpaceTime echoes all AT Commands that we sent to it
            return SerialMsg("Echo", data)
        elif data.startswith("Closing time: ") or data.startswith("Current time: "):
            msgtype = data[:7]  # Both 'Current' and 'Closing' are 7 chars long

            timeval = None

            if not data.endswith("Not set" + CRLF):
                timeval = data[
                    14:-2
                ]  # Refers to all the text after 'Closing time: ' and before \r\n

            return SerialMsg(msgtype, timeval)
        elif data == "SpaceTime, yay!" + CRLF:
            # SpaceTime says this on boot/reset
            return SerialMsg("Boot", data)
        elif data.startswith("Not set"):
            # If we query SpaceTime for a particular clock's time, it returns with
            # either 'Not set' or an 'HH:MM:SS' time, but no label specifying which
            # clock it refers to.
            return SerialMsg("AmbiguousTime", None)
        else:
            if is_time_str(data[0:-2]):  # [0:-2] removes the \r\n
                return SerialMsg("AmbiguousTime", data[0:-2])

            return SerialMsg("Unknown", data)

    def serial_command(self, cmd):
        # Sends serial command to SpaceTime
        self.serial.write(cmd + CRLF)

    def set_time(self, clock_id, timestruct):
        # ATST<n>=04:23:11
        # Triggers SpaceTime to set selected clock's time and return it, ex:
        # Current time: hh:mm:ss\r\n
        # OK\r\n
        t = time_to_str(timestruct)

        self.serial_command("ATST" + str(clock_id) + "=" + t)

    def set_time(self, clock_id):
        # ATST<n>?
        # Triggers SpaceTime to return selected clock's time, ex:
        # Current time: hh:mm:ss\r\n
        # OK\r\n
        self.serial_command("ATST" + str(clock_id) + "?")

    def clear_time(self, clock_id):
        # ATST<n>=X
        # Triggers SpaceTime to clear clock's time, ex:
        # Closing time: Not set\r\n
        # OK\r\n
        self.serial_command("ATST" + str(clock_id) + "=X")
