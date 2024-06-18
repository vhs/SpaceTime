# To run these unit tests from command line:
#
# python -m unittest test_spacetime
#

import time
import unittest
import serial

from spacetime import CRLF, SpaceTime
from timeutil import str_to_time


class TestSpaceTime(unittest.TestCase):

    def test_clear_serial(self):
        st = SpaceTime()
        st.clear_serial()
        self.assertEqual(st.serial.inWaiting(), 0)
        st.serial.write("AT\r\nRandom")
        time.sleep(0.25)
        # SpaceTime should echo 'AT\r\nRandom' and respond to AT with 'OK\r\n', hence 14 characters.
        self.assertEqual(st.serial.inWaiting(), 14)
        # Remaining in SpaceTime's input buffer should be 'Random', but we have no way to test that.
        # Clear all buffers
        st.clear_serial()
        # Verify input buffer is empty
        self.assertEqual(st.serial.inWaiting(), 0)
        # Verify SpaceTime's buffer by sending and receiving some commands.
        st.serial.write("AT" + CRLF)
        self.assertEqual(st.serial.readline(), "AT" + CRLF)
        self.assertEqual(st.serial.readline(), "OK" + CRLF)

    def test_can_read(self):
        st = SpaceTime()
        st.clear_serial()
        self.assertFalse(st.can_read())
        st.serial.write("AT")
        time.sleep(0.25)
        self.assertTrue(st.can_read())
        st.serial.read()  # Read 'A'
        self.assertTrue(st.can_read())
        st.serial.read()  # Read 'T'
        self.assertFalse(st.can_read())
        st.serial.write(CRLF)
        time.sleep(0.25)
        self.assertTrue(st.can_read())
        st.serial.readline()  # Read '\r\n'
        st.serial.readline()  # Read 'OK\r\n'
        self.assertFalse(st.can_read())

    def test_is_connected_success(self):
        st = SpaceTime()
        st.clear_serial()
        self.assertTrue(st.is_connected())
        # Make sure the buffers aren't polluted from IsConnected().
        st.serial.write(CRLF)
        self.assertFalse(st.can_read())

    def test_is_connected_timeout(self):
        st = SpaceTime()
        st.clear_serial()
        self.assertFalse(st.is_connected(timeout=0))
        st.clear_serial()

    def test_serial_command(self):
        st = SpaceTime()
        st.clear_serial()
        st.serial_command("AT")
        self.assertEqual(st.serial.readline(), "AT" + CRLF)
        self.assertEqual(st.serial.readline(), "OK" + CRLF)

    def test_set_time(self):
        st = SpaceTime()
        st.clear_serial()
        t = "14:56:05"
        st.set_time(0, str_to_time(t))
        self.assertEqual(st.serial.readline(), "ATST0=14:56:05" + CRLF)
        self.assertEqual(st.serial.readline(), "Current time: 14:56:05" + CRLF)

    def test_get_time(self):
        st = SpaceTime()
        st.clear_serial()
        st.serial.write("ATST0=14:56:05" + CRLF)
        st.serial.readline()  # Read echo of above command
        st.serial.readline()  # Read current time response
        st.serial.readline()  # Read OK
        st.set_time(0)
        self.assertEqual(st.serial.readline(), "ATST0?" + CRLF)
        self.assertEqual(st.serial.readline(), "14:56:05" + CRLF)

    def test_clear_time(self):
        st = SpaceTime()
        st.clear_serial()
        st.clear_time(1)
        self.assertEqual(st.serial.readline(), "ATST1=X" + CRLF)
        self.assertEqual(st.serial.readline(), "Closing time: Not set" + CRLF)

    # ----Read----

    def test_read_echo_text(self):
        st = SpaceTime()
        st.clear_serial()
        st.clear_time(1)
        r = st.read()
        self.assertEqual(r.type, "Echo")
        self.assertEqual(r.val, "ATST1=X" + CRLF)

    def test_read_ok(self):
        st = SpaceTime()
        st.clear_serial()
        st.serial_command("AT")
        st.serial.readline()  # Read echo of above command
        r = st.read()
        self.assertEqual(r.type, "OK")
        self.assertEqual(r.val, "OK" + CRLF)

    def test_time_set(self):
        st = SpaceTime()
        st.clear_serial()
        t = "14:56:05"
        st.set_time(0, str_to_time(t))
        st.serial.readline()  # Read echo of above command
        r = st.read()  # Read response to SetTime command
        # Response to SetTime specifies clock name 'Current'
        self.assertEqual(r.type, "Current")
        self.assertEqual(r.val, t)
        st.serial.readline()  # Read OK
        st.set_time(0)
        st.serial.readline()  # Read echo of above command
        r = st.read()  # Read response to GetTime command
        # Ambiguous because response to GetTime doesn't specify clock name
        self.assertEqual(r.type, "AmbiguousTime")
        self.assertEqual(r.val, t)

    def test_not_set(self):
        st = SpaceTime()
        st.clear_serial()
        st.clear_time(1)
        st.serial.readline()  # Read echo of above command
        r = st.read()  # Read response to ClearTime command
        # Response to SetTime specifies clock name 'Closing'
        self.assertEqual(r.type, "Closing")
        self.assertIsNone(r.val)
        st.serial.readline()  # Read OK
        st.set_time(1)
        st.serial.readline()  # Read echo of above command
        r = st.read()  # Read response to GetTime command
        # Ambiguous because response to GetTime doesn't specify clock name
        self.assertEqual(r.type, "AmbiguousTime")
        self.assertIsNone(r.val)

    def test_read_unknown(self):
        st = SpaceTime()
        st.clear_serial()
        st.serial_command("Pizza")
        r = st.read()
        self.assertEqual(r.type, "Unknown")
        self.assertEqual(r.val, "Pizza" + CRLF)
        st.clear_serial()

    def test_read_boot(self):
        # This is something that the Serial device normally sends to us,
        # but since it can't be triggered by software, we're mimicing it
        # here by using the fact that SpaceTime echoes all commands we send.
        # Normally we would never send 'SpaceTime, yay!' to the board.
        st = SpaceTime()
        st.clear_serial()
        st.serial_command("SpaceTime, yay!")
        r = st.read()
        self.assertEqual(r.type, "Boot")
        self.assertEqual(r.val, "SpaceTime, yay!" + CRLF)
        st.clear_serial()

    def test_read_timeout(self):
        st = SpaceTime()
        st.clear_serial()
        st.serial.timeout = 0
        r = st.read()
        self.assertEqual(r.type, "Unknown")
        self.assertEqual(r.val, "")


if __name__ == "__main__":
    unittest.main()
