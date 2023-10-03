import discord
import json

# Basic bot config, insert your token here, update description if you want, put owner IDs, and log channel ID.
prefixes = ["pws ", "dish "]
token = "token-goes-here"
bot_description = "Dishwasher, a spaghetti bot."
bot_managers = [120698901236809728]
bot_logchannel = 1006820351134683186

# If you forked Dishwasher, put your repo here
source_url = "https://github.com/vrnavi/dishwasher"

# The bot description to be used in the about command.
embed_desc = (
    "Dishwasher is maintained by `renavi`, as a Dishwasher in her kitchen."
    " I am presently washing her dishes. I am also a fork of "
    "[robocop-ng](https://github.com/reswitched/robocop-ng)."
)

# [cogs.prefixes] The maximum number of prefixes allowed.
# MUST be 24 or under.
maxprefixes = 6

# The cogs the bot will load on startup.
initial_cogs = [
    "cogs.common",
    "cogs.admin",
    "cogs.cotd",
    "cogs.explains",
    "cogs.mod",
    "cogs.mod_antiraid",
    "cogs.mod_archive",
    "cogs.mod_locks",
    "cogs.mod_observation",
    "cogs.mod_note",
    "cogs.mod_userlog",
    "cogs.mod_report",
    "cogs.mod_timed",
    "cogs.mod_toss",
    "cogs.mod_watch",
    "cogs.namecheck",
    "cogs.sv_configs",
    "cogs.autoapps",
    "cogs.basic",
    "cogs.oneshot",
    "cogs.logs",
    "cogs.remind",
    "cogs.reply",
    "cogs.dishtimer",
    "cogs.meme",
    "cogs.surveyr",
    "cogs.usertime",
    "cogs.prefixes",
    "cogs.messagescan",
    "cogs.burstreacts",
    "cogs.tsar",
    "cogs.usertrack",
]

# This section is for various API keys.
# [cogs.messagescan] DeepL Translator API key.
deepl_key = "key_goes_here"
# [cogs.basic] Catbox Account Key
# Will default to anonymous upload if not supplied.
catbox_key = "key_goes_here"

# Channels that will be cleaned every minute/hour.
minutely_clean_channels = []
hourly_clean_channels = []

# == Only if you want to use cogs.pin ==
# Used for the pinboard. Leave empty if you don't wish for a gist pinboard.
github_oauth_token = ""
# Channels and roles where users can pin messages
allowed_pin_channels = []
allowed_pin_roles = []


# Used for the bot's random options.
# No touch!
placeholders = json.load(open("assets/placeholders.json", "r"))
# Change this to set the playing type.
game_type = discord.ActivityType.listening
# This is a list of all the "games" to play.
game_names = placeholders["games"]
# These appear when doing pws quit.
death_messages = placeholders["deaths"]
# These appear when the bot tells you not to do a command to itself.
target_bot_messages = placeholders["if_target_bot"]
# These appear when the bot tells you not to do a command to yourself.
target_self_messages = placeholders["if_target_self"]
# Currently unused.
tarot_cards = placeholders["tarot"]
