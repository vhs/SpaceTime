# To run these unit tests from command line:
#
# python -m unittest test_timeutil
#
import time
import unittest

from timeutil import (
    is_time_str,
    str_to_time,
    time_offset_seconds,
    time_to_seconds,
    time_to_str,
)


fmt = "%H:%M:%S"
t000000 = time.strptime("00:00:00", fmt)
t041000 = time.strptime("04:10:00", fmt)
t080020 = time.strptime("08:00:20", fmt)
t225035 = time.strptime("22:50:35", fmt)


class TestTimeUtil(unittest.TestCase):

    def test_str_to_time(self):
        t = str_to_time("00:00:00")
        t2 = time.strptime("", "")
        self.assertEqual(t, t2)
        t = str_to_time("14:56:05")
        t2 = time.strptime("14:56:05", fmt)
        self.assertEqual(t, t2)

    def test_time_to_str(self):
        t = time.gmtime(0)
        self.assertEqual(time_to_str(t), "00:00:00")
        t = time.gmtime(1432757205)
        self.assertEqual(time_to_str(t), "20:06:45")

    def test_time_to_seconds_zero(self):
        t = time.gmtime(0)
        self.assertEqual(time_to_seconds(t), 0)

    def test_time_to_seconds(self):
        t = time.gmtime(1432757205)
        self.assertEqual(time_to_seconds(t), 72405)

    def test_time_offset_seconds_equal(self):
        t = time.gmtime(0)
        self.assertEqual(time_offset_seconds(t, t000000), 0)

    def test_pos_within(self):  # Offset is within the current day
        self.assertEqual(time_offset_seconds(t041000, t080020), 13820)

    def test_neg_within(self):
        self.assertEqual(time_offset_seconds(t080020, t041000), -13820)

    def test_pos_across(self):  # Offset is across two days
        self.assertEqual(time_offset_seconds(t225035, t000000), 4165)

    def test_neg_across(self):
        self.assertEqual(time_offset_seconds(t000000, t225035), -4165)

    def test_time_str(self):
        self.assertTrue(is_time_str("00:00:00"))
        self.assertTrue(is_time_str("02:34:56"))
        self.assertFalse(is_time_str("21:54:77"))
        self.assertFalse(is_time_str("12:12"))  # Need seconds
        self.assertFalse(is_time_str("2:12:34"))  # Need two digits
        self.assertFalse(is_time_str(" 2:34:56"))
        self.assertFalse(is_time_str("12.34:56"))
        self.assertFalse(is_time_str("12:34 56"))
        self.assertFalse(is_time_str("12:34:5o"))


if __name__ == "_main_":
    unittest.main()
