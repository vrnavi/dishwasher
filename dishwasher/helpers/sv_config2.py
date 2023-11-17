import json
import configparser
import os
import time
import shutil

server_data = "data/servers"


def make_config(sid):
    if not os.path.exists(f"{server_data}/{sid}"):
        os.makedirs(f"{server_data}/{sid}")
    shutil.copyfile("assets/stockguildconfig.ini", f"{server_data}/{sid}/config.ini")
    config = configparser.ConfigParser()
    config.read(f"{server_data}/{sid}/config.ini")
    return config


def get_raw_config(sid):
    with open(f"{server_data}/{sid}/config.ini", "r") as f:
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
        pre_cfg = configs[part][key]
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
