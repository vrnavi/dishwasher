import json
import os
import time

stock_configs = {
    "logs": {
        "mlog_thread": 0,
        "slog_thread": 0,
        "ulog_thread": 0,
    },
    "staff": {
        "staff_role": 0,
        "exstaff_role": 0,
        "staff_channel": 0,
        "rules_url": "",
        "appeal_url": "",
        "tracker_channel": 0,
    },
    "toss": {
        "enable": False,
        "toss_role": 0,
        "toss_category": 0,
        "toss_channels": [],
    },
    "archive": {
        "enable": False,
        "drive_folder": "",
        "unroleban_expiry": 0,
    },
    "surveyr": {
        "enable": False,
        "survey_channel": 0,
        "start_case": 0,
        "log_types": [],
        "log_roles": [],
    },
    "tsar": {
        "roles": {},
    },
    "autoapp": {
        "enable": False,
        "autoapp_channel": 0,
        "autoapp_id": 0,
        "autoapp_staledays": 0,
        "autoapp_name": "",
        "autoapp_msg": "",
    },
    "cotd": {
        "enable": False,
        "cotd_role": 0,
        "cotd_name": "",
    },
    "noreply": {
        "enable": False,
        "noreply_role": 0,
    },
    "misc": {
        "authorized_roles": [],
        "bot_roles": [],
        "embed_enable": False,
        "translate_enable": False,
        "burstreacts_enable": False,
        "autoreadable_enable": False,
    },
}
friendly_names = {
    "enable": "Feature Enabled",
    "mlog_thread": "Mod Log",
    "slog_thread": "Server Log",
    "ulog_thread": "User Log",
    "staff_role": "Staff Role ID",
    "exstaff_role": "Ex-Staff Role ID",
    "staff_channel": "Staff Channel ID",
    "rules_url": "Rules URL",
    "appeal_url": "Appeal URL",
    "autoapp_channel": "Auto App Channel",
    "autoapp_id": "Auto App ID",
    "autoapp_staledays": "Auto App Days Before Stale",
    "autoapp_name": "Auto App Name",
    "autoapp_msg": "Auto App Custom Message",
    "tracker_channel": "Tracker Channel ID",
    "toss_role": "Toss Role ID",
    "toss_category": "Toss Category ID",
    "toss_channels": "Names for Toss Channels",
    "drive_folder": "Google Drive Folder",
    "unroleban_expiry": "Toss Expire Time",
    "announce_channels": "Announce Channels",
    "mention_threshold": "Mention Threshold",
    "join_threshold": "Join Threshold",
    "survey_channel": "Survey Channel ID",
    "log_types": "Log Types",
    "start_case": "Starting Case #",
    "cotd_role": "Role ID",
    "cotd_name": "Role Name",
    "authorized_roles": '"Authorized" Role IDs',
    "bot_roles": "Bot Role IDs",
    "embed_enable": "Messagescan Feature Enabled",
    "translate_enable": "Translate Feature Enabled",
    "burstreacts_enable": "Burstreacts Feature Enabled",
    "burstreacts_enable": "Autoreadable Feature Enabled",
}
server_data = "data/servers"


def make_config(sid):
    if not os.path.exists(f"{server_data}/{sid}"):
        os.makedirs(f"{server_data}/{sid}")
    with open(f"{server_data}/{sid}/config.json", "w") as f:
        f.write(json.dumps(stock_configs))
        return stock_configs


def get_raw_config(sid):
    with open(f"{server_data}/{sid}/config.json", "r") as f:
        return json.load(f)


def set_raw_config(sid, contents):
    with open(f"{server_data}/{sid}/config.json", "w") as f:
        f.write(contents)


def get_config(sid, part, key):
    configs = fill_config(sid)

    if part not in configs or key not in configs[part]:
        configs = set_config(sid, part, key, stock_configs[part][key])

    return configs[part][key]


def set_config(sid, part, key, value):
    configs = fill_config(sid)

    if str(value).lower() == "none":
        value = None

    settingtype = type(stock_configs[part][key]).__name__
    if settingtype == "str":
        if value:
            pass
        else:
            value = ""
    elif settingtype == "int":
        if value:
            value = int(value)
        else:
            value = 0
    elif settingtype == "list":
        pre_cfg = configs[category][setting]
        if value:
            if value.split()[0] == "add":
                value = pre_cfg + value.split()[1:]
            elif value.split()[0] == "del":
                for v in value.split()[1:]:
                    pre_cfg.remove(v)
                value = pre_cfg
        else:
            value = []
    elif settingtype == "bool":
        value = True if str(value).title() == "True" else False
    elif settingtype == "dict":
        pass

    if part not in configs:
        configs[part] = {}
    configs[part][key] = value

    set_raw_config(sid, json.dumps(configs))
    return configs


def fill_config(sid):
    configs = (
        get_raw_config(sid)
        if os.path.exists(f"{server_data}/{sid}/config.json")
        else make_config(sid)
    )

    return configs
