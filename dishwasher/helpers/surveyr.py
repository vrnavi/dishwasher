import json
import os
import datetime
from discord.utils import escape_markdown
from helpers.sv_config import get_config

surveyr_event_types = {
    "bans": "Ban",
    "unbans": "Unban",
    "kicks": "Kick",
    "softbans": "Softban",
    "timeouts": "Timeout",
    "promotes": "Promotion",
    "demotes": "Demotion",
}
server_data = "data/servers"


def pacify_name(name):
    return escape_markdown(name.replace("@", "@ "))


def username_system(user):
    part1 = (
        pacify_name(user.global_name) + f" [{pacify_name(str(user))}]"
        if user.global_name
        else f"{pacify_name(str(user))}"
    )
    part2 = " (" + str(user.id) + ")"
    return part1 + part2


def make_surveys(serverid):
    if not os.path.exists(f"{server_data}/{serverid}"):
        os.makedirs(f"{server_data}/{serverid}")
    with open(f"{server_data}/{serverid}/surveys.json", "w") as f:
        f.write("{}")
    return json.loads("{}")


def get_surveys(serverid):
    if not os.path.exists(f"{server_data}/{serverid}/surveys.json"):
        make_surveys(serverid)
    with open(f"{server_data}/{serverid}/surveys.json", "r") as f:
        return json.load(f)


def set_surveys(serverid, contents):
    with open(f"{server_data}/{serverid}/surveys.json", "w") as f:
        f.write(contents)


def new_survey(sid, uid, mid, iid, reason, event):
    surveys = (
        get_surveys(sid)
        if os.path.exists(f"{server_data}/{sid}/surveys.json")
        else make_surveys(sid)
    )

    cid = (
        get_config(sid, "surveyr", "start_case")
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
    set_surveys(sid, json.dumps(surveys))
    return cid, timestamp


def edit_survey(sid, cid, iid, reason, event):
    survey = get_surveys(sid)

    sv_data = {
        "type": event,
        "reason": reason,
        "issuer_id": iid,
    }
    for k, v in sv_data.items():
        survey[str(cid)][k] = v
    set_surveys(sid, json.dumps(survey))
    return cid
