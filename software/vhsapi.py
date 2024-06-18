import requests
from time import sleep
from os import environ as env


class VHSApi:
    # The VHS API runs at https://api.vanhack.ca/
    # Source code is at   https://github.com/vhs/api/blob/master/lib/VHSAPI.pm
    # The online API supports a wide range of queries. (But this code does not)
    #  '<hostname>/s/<spacename>/data/<dataname>/update?value=<datavalue>'
    #  '<hostname>/s/<spacename>/data/<dataname>/fullpage'
    #  '<hostname>/s/<spacename>/data/<dataname>'
    #  '<hostname>/s/<spacename>/data/<dataname>.json'
    #  '<hostname>/s/<spacename>/data/<dataname>.txt'
    #  '<hostname>/s/<spacename>/data/<dataname>.js'
    #  '<hostname>/s/<spacename>/data/<dataname>/feed'
    #  '<hostname>/s/<spacename>/data/history/<dataname>.json'
    api_update_str = "/update?value="

    def __init__(
        self,
        api_url=env.get("API_URL", "https://api.vanhack.ca/s/vhs/data/"),
        timeout=5,
    ):
        self.api_url = api_url
        self.timeout = timeout

    def wait_for_connect(self, dataname):
        # Periodically queries the API until it receives a successful response.
        # dataname is the variable we query the API for.
        sleep_amt = 0.25
        sleep_max = 16

        while self.query(dataname) == False:
            print(f"Waiting {str(sleep_amt)}s for retry...")

            sleep(sleep_amt)

            if sleep_amt < sleep_max:
                sleep_amt *= 2

    def update_if_necessary(self, dataname, datavalue):
        # Query the dataname to see if it matches datavalue, and then
        # update with datavalue if they are different. This prevents
        # needless writes, which is important because each API variable
        # has a timestamp that is updated every time it changes.

        q = self.query(dataname)

        if q != False and q != datavalue:
            self.update(dataname, datavalue)

    def query(self, dataname):
        # Returns the value of dataname from the VHSApi server, or False if query failed.
        try:
            r = requests.get(self.api_url + dataname + ".json", timeout=self.timeout)

            if r.status_code == requests.codes.ok:
                # Expected json response in format:
                # {"last_updated":<unixtimestamp>,"name":"<dataname>","value":"<datavalue>"}
                j = r.json()

                if j["name"] == dataname:
                    print(f"VHSApi Query {dataname} is {j['value']}")

                    return j["value"]

            print(f"VHSApi Query of {dataname} failed.")
            print(f"Response code: {str(r.status_code)}")
            print(f"Response text: {r.text}")
        except Exception as e:
            print(f"VHSApi Query failed: {str(e)}")

        return False

    def update(self, dataname, datavalue):
        try:
            r = requests.get(
                self.api_url + dataname + self.api_update_str + datavalue,
                timeout=self.timeout,
            )

            if r.status_code == requests.codes.ok:
                # Expected json response in format:
                # {"result":{"value":"<datavalue>","last_updated":<unixtimestamp>,"name":"<dataname>"},"status":"OK"}
                j = r.json()

                if (
                    j["status"] == "OK"
                    and j["result"]["name"] == dataname
                    and j["result"]["value"] == datavalue
                ):
                    print(f"VHSApi Update {dataname} to {datavalue}")

                    return datavalue

            print(f"VHSApi Update of '{dataname}' failed.")
            print(f"Response code: {str(r.status_code)}")
            print(f"Response text: {r.text}")
        except Exception as e:
            print(f"VHSApi Update failed: {str(e)}")

        return False
