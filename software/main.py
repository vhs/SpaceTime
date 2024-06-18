import socket
import time

from restserv import (
    rest_serv,
)  # Webserver for REST API to allow updates from the VHS network
from timeutil import str_to_time, time_offset_seconds, time_to_str
from vhsapi import VHSApi  # api.vanhack.ca
from webapi import WebApi  # isvhsopen.com/api/status/

from spacetime import SpaceTime

dbg_show_all_serial = False  # If true, prints out all received serial messages
last_clock_sync = 0  # Time of last clock sync with SpaceTime
last_heartbeat = 0  # Time of last update with isvhsopen.com WebApi
door_status_cache = (
    ""  # The last known door status, to send periodic heartbeat to WebApi
)
api_var_ip = "spacetime_ip"
max_clock_drift = (
    10  # Allowable error (in seconds) between SpaceTime clock and system clock
)


def update_door_status(web_api, closing_time):
    global last_heartbeat, door_status_cache

    # Save current time and door status to send periodic heartbeats to WebAPI
    last_heartbeat = time.time()

    door_status_cache = closing_time

    # Update WebAPI with door status. WebAPI is smart enough
    # to ignore duplicate submissions, so unnecessary updates
    # aren't harmful and do not affect the timestamp.
    if closing_time == None:
        web_api.update("closed")
    else:
        # Removing seconds part
        closing_time = closing_time[:5]

        web_api.update("open", closing_time)


def process_serial_msg(msg, web_api, st):

    if msg.type == "Current" or msg.type == "AmbiguousTime":
        global last_clock_sync

        # SpaceTime is telling us what it thinks is the current time
        # It's telling us either because the user just set it, or
        # because we asked it.
        # Currently, we never ask for the Closing time, so if we receive
        # an AmbiguousTime, we can safely assume it is the Current time.

        last_clock_sync = time.time()
        cur_time = time.localtime(last_clock_sync)

        should_update = True

        if msg.val != None:
            # Check if SpaceTime time is close to current system time
            space_time_drift = time_offset_seconds(cur_time, str_to_time(msg.val))

            # Don't bother updating SpaceTime if time is within 10s of system time
            should_update = abs(space_time_drift) > max_clock_drift
        if should_update:
            print(f"Synchronizing SpaceTime's clock to {time_to_str(cur_time)}")

            # SpaceTime Current clockID = 0
            st.set_time(0, cur_time)

    elif msg.type == "Closing":
        # SpaceTime is telling us the status of closing time.
        # It's telling us because the user just set it, because
        # we asked for it, or because it just expired.

        print(
            f"SpaceTime reports that Closing time is {'not set' if msg.val == None else msg.val}"
        )

        # Update WebAPI
        update_door_status(web_api, msg.val)
    elif msg.type == "OK":
        return  # Can ignore 'OK' responses
    elif msg.type == "Echo":
        return  # SpaceTime echoes all commands sent to it, so we can ignore these
    elif msg.type == "Boot":
        print("SpaceTime has just been reset!")
        print("Resetting Web API variables and setting SpaceTime's clock")

        update_door_status(web_api, None)

        # Query SpaceTime's clock. Its response will trigger us to update it if necessary.
        st.get_time(0)
    else:
        print(f"Serial message ignored: '{msg.val}'")


def get_local_ip():
    # Returns the machine's local IP address as a string, or 'unknown' if error.
    ip = "unknown"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()
    except Exception as e:
        print(f"IP lookup failed: {e}")

    return ip


def should_sync_clock():
    # Sync the clock every 24h, and do it when we're around
    # 40-50s in the current minute (to minimize the chance of the clock
    # jumping back 1min or forward 2min).
    _24h = 86400  # seconds in 24h

    cur_time = time.time()

    if cur_time - last_clock_sync > _24h:
        cur_time = time.localtime(cur_time)

        if 40 < cur_time.tm_sec < 50:
            return True

    return False


def should_send_heartbeat():
    # Send a heartbeat to isvhsopen.com every 15min
    _15min = 900  # seconds in 15min

    cur_time = time.time()

    return cur_time - last_heartbeat > _15min


def setup():
    # Connects to the internet, updates local IP address
    # on VHS Api, connects to SpaceTime Serial, updates
    # Web Api variables, and queries SpaceTime's clock
    # (to trigger an update upon its response).
    # returns initialized (WebAPI, SpaceTime)

    print("Initializing SpaceTime...")

    vhs = VHSApi()
    web = WebApi()
    st = SpaceTime()

    print("Connecting to the internet...")
    web.wait_for_connect()
    print("Connected!")

    # Update the machine's local IP on the VHS Api. The timestamp can serve as a boot history.
    vhs.update(api_var_ip, get_local_ip())

    print(f"Initializing Serial connection with SpaceTime ({st.serial.name})...")

    while not st.is_connected():
        print("Failed to init Serial connection with SpaceTime. Trying again...")

    print("Initialized!")

    print("Initializing webserver for REST API (only available to LAN)")

    rest_serv(st)

    # Query Closing time (this is the only time we do this)
    # in case RPi was rebooted but SpaceTime wasn't.
    st.set_time(1)  # Closing time is ID 1

    st.read()  # Ignore the echo of the GetTime command

    ct = st.read()  # Read the response

    # It is an unlabeled time, but we know it should be Closing time
    if ct.type == "AmbiguousTime":
        ct.type = "Closing"

        # Update Web Api if necessary
        process_serial_msg(ct, web, st)

    # Query SpaceTime's clock. Its response will trigger us to update it if necessary.
    st.set_time(0)  # Current time is ID 0

    return web, st


def loop(web, st):
    # Check for new Serial messages every second.
    # If there is a Serial message to read, read and process it.
    if st.can_read():
        msg = st.read()

        if dbg_show_all_serial:
            dbgmsg = "SerialDbg " + msg.type + ": " + str(msg.val)

            print((dbgmsg if not dbgmsg.endswith("\r\n") else dbgmsg[:-2]))

        process_serial_msg(msg, web, st)
    elif should_sync_clock():
        # Query SpaceTime's clock. Its response will trigger us to update it if necessary.
        st.get_time(0)

        # Give SpaceTime enough time to respond so that we only send one st.get_time(0) per sync period.
        time.sleep(0.5)
    elif should_send_heartbeat():
        print("Sending Heartbeat to Web API...")

        update_door_status(web, door_status_cache)
    else:
        time.sleep(1)


def main():
    # Run setup and then loop indefinitely
    web, st = setup()

    # Loop indefinitely - Catch and report any unhandled exceptions,
    # but try to keep going anyway.
    while 1:
        try:
            loop(web, st)
        except Exception as e:
            print(f"Exception in main loop! {e}")

            # Give some time for whatever caused the error to go away.
            # Also don't want to flood a log file with identical exceptions.
            time.sleep(5)


if __name__ == "__main__":
    main()
