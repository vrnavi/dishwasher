import random
import config
import discord
import datetime
import json

placeholders = json.load(open("assets/placeholders.json", "r"))
game_type = discord.ActivityType.listening
game_names = placeholders["games"]
death_messages = placeholders["deaths"]
target_bot_messages = placeholders["if_target_bot"]
target_self_messages = placeholders["if_target_self"]

speak = "<:sangouspeak:1182927625161809931>"

angry = "<:sangoubaka:1182927626919223376>"
unamused = "<:sangoubruh:1182927627388989491>"
crying = "<:sangoucry:1182927628802469958>"
dizzy = "<:sangoudizzy:1182927629695860757>"
sleeping = "<:sangousleep:1182927635706298438>"

drunk = "<:sangoudrunk:1182927630736044132>"
eating = "<:sangoueat:1182927631977558086>"
fear = "<:sangoufear:1182927633290379304>"
smug = "<:sangouhehe:1182927835460026448>"
huh = "<:sangouhuh:1182927894989783101>"
love = "<:sangoulove:1182927665028661310>"


def random_self_msg(authorname):
    return random.choice(target_self_messages).format(authorname=authorname)


def random_bot_msg(authorname):
    return random.choice(target_bot_messages).format(authorname=authorname)


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
