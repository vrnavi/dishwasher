import random
import discord
import datetime
import yaml

with open("assets/placeholders.yml", "r") as f:
    placeholders = yaml.safe_load(f)
game_type = discord.ActivityType.listening
game_names = placeholders["games"]


def random_msg(variant, **fills):
    shorthands = placeholders["shorthands"]
    string = random.choice(placeholders[variant])
    if fills:
        for name in fills.keys():
            if not "{" + name + "}" in string:
                continue
            string = string.replace("{" + name + "}", fills[name])
    return string.format(**shorthands)


def create_log_embed(bot, color, title, desc, author, fields, thumbnail=None):
    embed = discord.Embed(
        color=color,
        title=title,
        description=desc,
        timestamp=datetime.datetime.now(),
    )
    embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)
    embed.set_author(
        name=str(author),
        icon_url=author.display_avatar.url,
    )
    return embed
