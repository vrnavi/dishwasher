import yaml
import shutil
import copy
import json
import os
from jsonschema import validate

server_data = "data/servers"
with open("assets/config.example.yml", "r") as f:
    config_stock = yaml.safe_load(f)
with open("assets/config.schema.yml", "r") as f:
    config_schema = yaml.safe_load(f)


def validate_config(config):
    validate(config, config_schema)


def make_config(sid):
    if not os.path.exists(f"{server_data}/{sid}"):
        os.makedirs(f"{server_data}/{sid}")
    shutil.copyfile("assets/config.example.yml", f"{server_data}/{sid}/config.yml")
    return config_stock


def get_config(sid, part, key):
    config = fill_config(sid)

    return config[part][key]


def fill_config(sid):
    config = (
        get_raw_config(sid)
        if os.path.exists(f"{server_data}/{sid}/config.yml")
        else make_config(sid)
    )

    if config["metadata"]["version"] < config_stock["metadata"]["version"]:
        # Version update code.

        # * to 3.
        if config["metadata"]["version"] < 3:
            config["staff"]["adminrole"] = None
            config["staff"]["modrole"] = config["staff"]["staffrole"]
            del config["staff"]["staffrole"]

        # * to 4.
        if config["metadata"]["version"] < 4:
            del config["toss"]["drivefolder"]
            config["toss"]["tosstopic"] = None

        # * to 5.
        if config["metadata"]["version"] < 5:
            if os.path.exists(f"{server_data}/{sid}/tsar.json"):
                with open(f"{server_data}/{sid}/tsar.json", "r") as f:
                    tsars = json.load(f)
                config["roles"] = []
                if tsars:
                    for name, data in tsars.items():
                        config["roles"].append(
                            {
                                "name": name,
                                "role": data["roleid"],
                                "days": data["mindays"],
                                "blacklisted": data["blacklisted"],
                                "required": data["required"],
                            }
                        )
                else:
                    config["roles"] = None
                os.remove(f"{server_data}/{sid}/tsar.json")
            else:
                config["roles"] = None
            config["overrides"] = None

        # * to 6.
        if config["metadata"]["version"] < 6:
            config["reaction"]["pollsenable"] = None

        # * to 7.
        if config["metadata"]["version"] < 7:
            del config["reaction"]["pollsenable"]

        # * to 8.
        if config["metadata"]["version"] < 8:
            config["toss"]["notificationchannel"] = config["staff"]["staffchannel"]

        set_raw_config(sid, config)

    return config


def get_raw_config(sid):
    with open(f"{server_data}/{sid}/config.yml", "r") as f:
        config = yaml.safe_load(f)
    return config


def set_raw_config(sid, contents):
    contents["metadata"]["version"] = config_stock["metadata"]["version"]
    with open(f"{server_data}/{sid}/config.yml", "w") as f:
        yaml.dump(contents, f, sort_keys=False)
