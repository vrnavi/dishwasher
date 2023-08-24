import os
import sys
import logging
import logging.handlers
import asyncio
import aiohttp
import config
import random
import discord
import datetime
import traceback
from discord.ext import commands
from helpers.userdata import get_userprefix

# TODO: check __name__ for __main__ nerd

stdout_handler = logging.StreamHandler(sys.stdout)
log_format = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
stdout_handler.setFormatter(log_format)
log = logging.getLogger("discord")
log.setLevel(logging.INFO)
log.addHandler(stdout_handler)


def get_prefix(bot, message):
    # yes i know this is mangy but people wont stop complaining about not being able to use "Pls" for some reason
    prefixes = (
        [prefix.lower() for prefix in config.prefixes]
        + [prefix.upper() for prefix in config.prefixes]
        + [prefix.title() for prefix in config.prefixes]
    )
    userprefixes = get_userprefix(message.author.id)
    if userprefixes is not None:
        return commands.when_mentioned_or(*prefixes + userprefixes)(bot, message)
    return commands.when_mentioned_or(*prefixes)(bot, message)


wanted_jsons = [
    "data/dishtimers.json",
    "data/userdata.json",
]
server_data = "data/servers"
bot_data = "data/bot"
all_data = "data"

intents = discord.Intents.all()
intents.typing = False

bot = commands.Bot(
    command_prefix=get_prefix,
    description=config.bot_description,
    intents=intents,
    enable_debug_events=True,  # for raw events (e.g. super reactions handler)
)
bot.help_command = None
bot.log = log
bot.config = config
bot.wanted_jsons = wanted_jsons
bot.server_data = server_data
bot.bot_data = bot_data
bot.all_data = all_data


@bot.event
async def on_ready():
    bot.aiosession = aiohttp.ClientSession()
    bot.app_info = await bot.application_info()
    bot.log_channel = bot.get_channel(config.bot_logchannel)

    log.info(
        f"\nLogged in as: {bot.user.name} - "
        f"{bot.user.id}\ndpy version: {discord.__version__}\n"
    )

    bot.session = aiohttp.ClientSession()
    bot.start_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    )

    # Send "Dishwasher has started! x has y members!"
    guild = bot.log_channel.guild
    msg = (
        f"**{bot.user.name} is now `🟢 ONLINE`.**\n"
        f"`{guild.name}` has `{guild.member_count}` members."
    )

    await bot.log_channel.send(msg)


@bot.event
async def on_command(ctx):
    log_text = (
        f"{ctx.message.author} ({ctx.message.author.id}): " f'"{ctx.message.content}" '
    )
    if ctx.guild:  # was too long for tertiary if
        log_text += (
            f'in "{ctx.channel.name}" ({ctx.channel.id}) '
            f'on "{ctx.guild.name}" ({ctx.guild.id})'
        )
    else:
        log_text += f"in DMs ({ctx.channel.id})"
    log.info(log_text)


@bot.event
async def on_error(event_method, *args, **kwargs):
    err_info = sys.exc_info()
    format_args = repr(args) if args else " "
    format_kwargs = repr(kwargs) if kwargs else " "
    log.error(f"Error on {event_method}: {err_info}")

    err_embed = discord.Embed(
        color=discord.Color.from_str("#FF0000"),
        title="🔥 Code Error",
        timestamp=datetime.datetime.now(),
    )
    err_embed.add_field(
        name=f"Given args:",
        value=f"```{format_args}```",
        inline=False,
    )
    err_embed.add_field(
        name=f"Given kwargs:",
        value=f"```{format_kwargs}```",
        inline=False,
    )

    if len(err_info) > 1024:
        split_msg = list(
            [err_info[i : i + 1020] for i in range(0, len(err_info), 1020)]
        )
        err_embed.description = f"An error occurred...\n```{event_method}```"
        ctr = 1
        for f in split_msg:
            err_embed.add_field(
                name=f"🧩 Fragment {ctr}",
                value=f"```{f}```",
                inline=False,
            )
            ctr += 1
    else:
        err_embed.description = (
            f"An error occurred...\n```{event_method}: {err_info}```"
        )

    err_embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)

    for m in config.bot_managers:
        await bot.get_user(m).send(embed=err_embed)


@bot.event
async def on_command_error(ctx, error):
    # We don't want to log commands that don't exist.
    if isinstance(error, commands.CommandNotFound):
        return

    log.error(
        f"An error occurred with `{ctx.message.content}` from "
        f"{ctx.message.author} ({ctx.message.author.id}):\n"
        f"{type(error)}: {error}"
    )

    guildmsg = (
        f"**Guild:** {ctx.guild.name}\n**Channel:** {ctx.channel.name}\n**Link:** {ctx.message.jump_url}\n"
        if ctx.guild
        else ""
    )
    err_log_embed = discord.Embed(
        color=ctx.author.color,
        title="⚠️ Command Error",
        description=(
            f"An error occurred...\n"
            f"**Command:** `{ctx.message.content}`\n"
            f"**User:** {ctx.message.author} ({ctx.message.author.id})\n"
            f"{guildmsg}"
            f"```{type(error)}: {error}```"
        ),
        timestamp=datetime.datetime.now(),
    )
    err_log_embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)
    err_log_embed.set_author(
        name=f"{bot.escape_message(ctx.author)}",
        icon_url=f"{ctx.author.display_avatar.url}",
    )

    for m in config.bot_managers:
        await bot.get_user(m).send(embed=err_log_embed)

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send("This command doesn't work in DMs.")
    elif isinstance(error, commands.MissingPermissions):
        roles_needed = "\n- ".join(error.missing_perms)
        return await ctx.send(
            f"**Error: Missing Permissions**\n"
            "You don't have the right permissions to run this command. You need: "
            f"```- {roles_needed}```"
        )
    elif isinstance(error, commands.BotMissingPermissions):
        roles_needed = "\n-".join(error.missing_perms)
        return await ctx.send(
            f"**Error: Missing Permissions**\n"
            "I don't have the right permissions to run this command. "
            "I need: "
            f"```- {roles_needed}```"
        )
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(
            f"**Error: Ratelimited**\n"
            "You're being ratelimited. Try in "
            f"{error.retry_after:.1f} seconds."
        )
    elif isinstance(error, commands.CheckFailure):
        return await ctx.send(
            f"**Error: Check Failure**\n"
            "You might not have the right permissions "
            "to run this command, or you may not be able "
            "to run this command in the current channel."
        )
    elif isinstance(error, commands.CommandInvokeError) and (
        "Cannot send messages to this user" in str(error)
    ):
        return await ctx.send(
            f"**Error: DM Failure**\n"
            "I can't DM you. You either have me blocked, or have DMs "
            f"blocked, either globally or for this server.\n"
            "Please resolve that, then "
            "try again."
        )

    help_text = (
        f"Usage of this command is: ```{ctx.prefix}{ctx.command.name} "
        f"{ctx.command.signature}```\nPlease see `{ctx.prefix}help"
        f"` for more info."
    )

    # Keep a list of commands that involve mentioning users
    # and can involve users leaving/getting banned
    ಠ_ಠ = ["warn", "kick", "ban"]

    if isinstance(error, commands.BadArgument):
        # and if said commands get used, add a specific notice.
        if ctx.command.name in ಠ_ಠ:
            help_text = (
                "This probably means that user left (or already got kicked/banned).\n"
                + help_text
            )

        return await ctx.send(f"You gave incorrect arguments. {help_text}")
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f"You gave incomplete arguments. {help_text}")


@bot.event
async def on_message(message):
    await bot.wait_until_ready()
    # Insert botban stuff here.
    if message.author.bot:
        return

    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.invoke(ctx)
    else:

        def check(b, a):
            return a.id == message.id

        while True:
            try:
                b, a = await bot.wait_for(
                    "message_edit", timeout=15.0, check=check
                )
            except asyncio.TimeoutError:
                return
            except discord.errors.NotFound:
                return
            else:
                ctx = await bot.get_context(a)
                if ctx.valid:
                    await bot.invoke(ctx)
                    return


if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists(server_data):
    os.makedirs(server_data)

for wanted_json in wanted_jsons:
    if not os.path.exists(wanted_json):
        with open(wanted_json, "w") as f:
            f.write("{}")


async def main():
    async with bot:
        for cog in config.initial_cogs:
            try:
                await bot.load_extension(cog)
            except:
                log.exception(f"Failed to load cog {cog}.")
        await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
