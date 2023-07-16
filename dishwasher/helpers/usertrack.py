import json
import os
import time

server_data = "data/servers"


def make_usertrack(serverid):
    if not os.path.exists(f"{server_data}/{serverid}"):
        os.makedirs(f"{server_data}/{serverid}")
    with open(f"{server_data}/{serverid}/usertrack.json", "w") as f:
        f.write("{}")
        return json.loads("{}")


def get_usertrack(serverid):
    if not os.path.exists(f"{server_data}/{serverid}/usertrack.json"):
        usertracks = make_usertracks(serverid)
    with open(f"{server_data}/{serverid}/usertrack.json", "r") as f:
        return json.load(f)


def set_usertrack(serverid, contents):
    with open(f"{server_data}/{serverid}/usertrack.json", "w") as f:
        f.write(contents)


def fill_usertrack(serverid, userid, usertracks=None):
    if not usertracks:
        usertracks = get_usertrack(serverid)
    uid = str(userid)
    if uid not in usertracks:
        usertracks[uid] = {
            "jointime": 0,
            "truedays": 0,
        }

    return usertracks, uid
