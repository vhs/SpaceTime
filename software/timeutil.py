import time
import re

timeFormatStr = "%H:%M:%S"

re24HourTime = re.compile("^(2[0-3]|[01]\d):([0-5]\d):([0-5]\d)")


def str_to_time(str):
    return time.strptime(str, timeFormatStr)


def time_to_str(t):
    return time.strftime(timeFormatStr, t)


def time_to_seconds(t):
    return t.tm_sec + 60 * (t.tm_min + 60 * t.tm_hour)


def time_offset_seconds(t1, t2):
    # Returns the offset between two times (ignoring dates), in seconds.
    # Will choose the shortest offset, even if it crosses a date boundry,
    # so the result will always be within -12h and +12h.
    _12h = 43200  # Number of seconds in 12 hours
    _24h = 86400
    s1 = time_to_seconds(t1)
    s2 = time_to_seconds(t2)
    diff = s2 - s1

    # if abs(diff) is greater than 12h, then the diff across a day boundary will be smaller
    if diff > _12h:
        diff -= _24h
    elif diff < -_12h:
        diff += _24h

    return diff


def is_time_str(str):
    # Optimized test for time-formatted string, returns True if format matches "HH:MM:SS"
    return len(str) == 8 and ":" == str[2] == str[5] and re24HourTime.match(str)
