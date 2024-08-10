import json
import os
import time
import datetime
import math
from helpers.sv_config import get_config

# Files


def make_file(filename, subdir=None):
    path = "data" + ("/" + subdir if subdir else "")
    if not os.path.exists(path):
        os.makedirs(path)
    with open(f"{path}/{filename}.json", "w") as f:
        f.write("{}")
        return json.loads("{}")


def get_file(filename, subdir=None):
    path = "data" + ("/" + subdir if subdir else "")
    if not os.path.exists(f"{path}/{filename}.json"):
        make_file(filename, subdir)
    with open(f"{path}/{filename}.json", "r") as f:
        return json.load(f)


def set_file(filename, contents, subdir=None):
    path = "data" + ("/" + subdir if subdir else "")
    with open(f"{path}/{filename}.json", "w") as f:
        f.write(contents)


# Default Fills


def fill_usertrack(serverid, userid, usertracks=None):
    if not usertracks:
        usertracks = get_file("usertrack", f"servers/{serverid}")
    uid = str(userid)
    if uid not in usertracks:
        usertracks[uid] = {
            "jointime": 0,
            "truedays": 0,
        }

    return usertracks, uid


def fill_userlog(serverid, userid):
    userlogs = get_file("userlog", f"servers/{serverid}")
    uid = str(userid)
    if uid not in userlogs:
        userlogs[uid] = {
            "warns": {},
            "tosses": {},
            "kicks": {},
            "bans": {},
            "notes": {},
            "watch": {"state": False, "thread": None, "message": None},
        }

    return userlogs, uid


def fill_profile(userid):
    profile = get_file("profile", f"users/{userid}")
    stockprofile = {
        "prefixes": [],
        "aliases": [],
        "timezone": None,
        "replypref": None,
    }
    if not profile:
        profile = stockprofile

    # Validation
    updated = False
    for key, value in stockprofile.items():
        if key not in profile:
            profile[key] = value
            updated = True
    for key, value in profile.items():
        if key not in stockprofile:
            del profile[key]
            updated = True

    if updated:
        set_userfile(userid, "profile", json.dumps(profile))

    return profile


# Userlog Features


def add_userlog(sid, uid, issuer, reason, event_type, timestamp=None):
    userlogs, uid = fill_userlog(sid, uid)
    if not timestamp:
        timestamp = int(datetime.datetime.now().timestamp())

    log_data = {
        "issuer_id": issuer.id,
        "reason": reason,
    }
    if event_type not in userlogs[uid]:
        userlogs[uid][event_type] = {}
    userlogs[uid][event_type][str(timestamp)] = log_data
    set_file("userlog", json.dumps(userlogs), f"servers/{sid}")
    return len(userlogs[uid][event_type])


def toss_userlog(sid, uid, issuer, mlink, cid, timestamp=None):
    userlogs, uid = fill_userlog(sid, uid)
    if not timestamp:
        timestamp = int(datetime.datetime.now().timestamp())

    toss_data = {
        "issuer_id": issuer.id,
        "reason": mlink,
        "session_id": cid,
    }
    if "tosses" not in userlogs[uid]:
        userlogs[uid]["tosses"] = {}
    userlogs[uid]["tosses"][str(timestamp)] = toss_data
    set_file("userlog", json.dumps(userlogs), f"servers/{sid}")
    return len(userlogs[uid]["tosses"])


def watch_userlog(sid, uid, issuer, watch_state, tracker_thread=None, tracker_msg=None):
    userlogs, uid = fill_userlog(sid, uid)

    userlogs[uid]["watch"] = {
        "state": watch_state,
        "thread": tracker_thread,
        "message": tracker_msg,
    }
    set_file("userlog", json.dumps(userlogs), f"servers/{sid}")
    return


# Surveyr Features


def new_survey(sid, uid, mid, iid, reason, event):
    surveys = get_file("surveys", f"servers/{sid}")

    cid = (
        get_config(sid, "surveyr", "startingcase")
        if len(surveys.keys()) == 0
        else int(list(surveys)[-1]) + 1
    )

    timestamp = int(datetime.datetime.now().timestamp())
    sv_data = {
        "type": event,
        "reason": reason,
        "timestamp": timestamp,
        "target_id": uid,
        "issuer_id": iid,
        "post_id": mid,
    }
    surveys[str(cid)] = sv_data
    set_file("surveys", json.dumps(surveys), f"servers/{sid}")
    return cid, timestamp


def edit_survey(sid, cid, iid, reason, event):
    surveys = get_file("surveys", f"servers/{sid}")

    surveys[str(cid)]["type"] = event
    surveys[str(cid)]["reason"] = reason
    surveys[str(cid)]["issuer_id"] = iid

    set_file("surveys", json.dumps(surveys), f"servers/{sid}")
    return cid


# Dishtimer Features


def add_job(job_type, job_name, job_details, timestamp):
    timestamp = str(math.floor(timestamp))
    job_name = str(job_name)
    ctab = get_file("timers")

    if job_type not in ctab:
        ctab[job_type] = {}

    if timestamp not in ctab[job_type]:
        ctab[job_type][timestamp] = {}

    ctab[job_type][timestamp][job_name] = job_details
    set_file("timers", json.dumps(ctab))


def delete_job(timestamp, job_type, job_name):
    timestamp = str(timestamp)
    job_name = str(job_name)
    ctab = get_file("timers")

    del ctab[job_type][timestamp][job_name]

    # smh, not checking for empty timestamps. Smells like bloat!
    if not ctab[job_type][timestamp]:
        del ctab[job_type][timestamp]

    set_file("timers", json.dumps(ctab))
