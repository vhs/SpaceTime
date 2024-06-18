import requests
from time import sleep
from os import environ as env

from exceptions import InvalidApiKeyException


class WebApi:
    # The isvhsopen.com Web API is at https://isvhsopen.com/api/status/
    # It is different from the VHS API at https://api.vanhack.ca/
    # Source code is at https://github.com/vhs/isvhsopen
    # An API Key must be obtained and added to this file to make updates possible.

    # Example queries:
    # GET https://isvhsopen.com/api/status/
    # POST https://isvhsopen.com/api/status/open?key=ISVHSOPEN_API_KEY&until=12:30
    # POST https://isvhsopen.com/api/status/closed?key=ISVHSOPEN_API_KEY

    def __init__(
        self,
        api_url=env.get("ISVHSOPEN_URL", "https://isvhsopen.com/api/status/"),
        api_key=env.get("ISVHSOPEN_API_KEY"),
        timeout=5,
    ):
        if api_key is None:
            raise InvalidApiKeyException("Missing ISVHSOPEN_API_KEY")

        self.api_url = api_url
        self.api_key = api_key
        self.timeout = timeout

    def wait_for_connect(self):
        # Periodically queries the API until it receives a successful response.
        sleep_amt = 0.25
        sleep_max = 1616

        while self.query() == False:
            print(f"Waiting {str(sleep_amt)}s for retry...")

            sleep(sleep_amt)

            if sleep_amt < sleep_max:
                sleep_amt *= 2

    def query(self, dataname=None):
        # Returns the value of dataname from the isvhsopen server, or False if query failed.
        # If dataname is None or '', returns the full json response, or False if query failed.
        try:
            # Query should return a json object with all status info
            r = requests.get(self.api_url, timeout=self.timeout)

            if r.status_code == requests.codes.ok:
                # Expected json response in format:
                # {"status":"open","last":"2015-12-06T20:05:17.669Z","_events":{"change":[null,null]},"_eventsCount":1,"openUntil":"2015-12-07T12:32:00.000Z"}
                # {"status":"closed","last":"2015-12-06T20:07:09.232Z","_events":{"change":[null,null]},"_eventsCount":1}
                j = r.json()

                if dataname:
                    val = j.get(dataname)

                    # val is the value of dataname, or None if no such dataname exists
                    if val:
                        print(f"isvhsopen Query {dataname} is {val}")

                        return val
                else:
                    # No dataname was specified, so return full json response
                    return j

            print(f"isvhsopen Query of '{dataname}' failed.")
            print(f"Response code: {str(r.status_code)}")
            print(f"Response text: {r.text}")
        except Exception as e:
            print(f"isvhsopen Query failed: {str(e)}")

        return False

    def update(self, door_status, until=""):
        # Updates the isvhsopen.com WebAPI with the current door status.
        # Valid values for doorStatus are 'open' and 'closed'
        # The until parameter is ignored by the server if doorStatus == 'closed'
        # Returns the json response object from the update if successful, or False if failed.
        try:
            d = {"key": self.api_key, "until": until}

            p = requests.post(self.api_url + door_status, data=d, timeout=self.timeout)

            if p.status_code == requests.codes.ok:
                # Expected json response in format:
                # {"result":"ok","status":"open","last":"2015-12-06T20:05:17.669Z","openUntil":"2015-12-07T12:32:00.000Z"}
                # {"result":"ok","status":"closed","last":"2015-12-06T20:07:09.232Z"}
                j = p.json()

                if j["result"] == "ok" and j["status"] == door_status:
                    # Note we're just trusting that openUntil was set correctly
                    print(
                        f"isvhsopen Update door status to '{door_status}' until {str(j.get('openUntil'))}"
                    )
                    return j

            print(f"isvhsopen Update door status to {door_status} failed.")
            print(f"Response code: {str(p.status_code)}")
            print(f"Response text: {p.text}")
        except Exception as e:
            print(f"isvhsopen Update failed: {str(e)}")

        return False
