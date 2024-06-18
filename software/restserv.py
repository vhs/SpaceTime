import threading

import web
from timeutil import is_time_str, str_to_time

# SpaceTime object, defined when RestServ() is called
spacetime = None

urls = (
    "/",
    "index",
    r"/set/open/(\d\d?):?(\d\d)",
    "setopen",
    "/set/closed?/?",
    "setclosed",
)


# Initializes a webserver with a restful API to control the SpaceTime board.
# Intended to be made available on the local VHS network, but not over the internet.
# Parameter st should be an initialized SpaceTime object.
def rest_serv(st):
    global spacetime

    spacetime = st

    th = RestServThread()

    th.daemon = True

    th.start()


# The web server runs in a thread so that app.run() doesn't block all other execution.
class RestServThread(threading.Thread):
    def run(self):
        app = web.application(urls, globals())

        app.run()


class index:
    def GET(self):  # NOSONAR
        return (
            "SpaceTime REST API\r\n"
            + "/set/open/15:30 - Sets SpaceTime to stay open until 15:30\r\n"
            + "/set/closed     - Sets SpaceTime to closed"
        )


class setopen:
    def GET(self, hours, mins):  # NOSONAR
        # Make a HH:MM:SS time string
        timestr = hours.zfill(2) + ":" + mins + ":00"

        if is_time_str(timestr):
            # Closing time is ID 1
            spacetime.set_time(1, str_to_time(timestr))

            return "SpaceTime set to " + timestr + "."

        return timestr + " is not a valid time."


class setclosed:
    def GET(self):  # NOSONAR
        # Closing time is ID 1
        spacetime.clear_time(1)

        return "SpaceTime set to closed."
