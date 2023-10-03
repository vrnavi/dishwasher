import json
import os
import time


server_data = "data/servers"


def make_reportlog(serverid):
    if not os.path.exists(f"{server_data}/{serverid}"):
        os.makedirs(f"{server_data}/{serverid}")
    with open(f"{server_data}/{serverid}/reportlog.json", "w") as f:
        f.write("{}")
        return json.loads("{}")


def get_reportlog(serverid):
    if not os.path.exists(f"{server_data}/{serverid}/reportlog.json"):
        make_reportlog(serverid)
    with open(f"{server_data}/{serverid}/reportlog.json", "r") as f:
        return json.load(f)


def set_reportlog(serverid, contents):
    with open(f"{server_data}/{serverid}/reportlog.json", "w") as f:
        f.write(contents)
