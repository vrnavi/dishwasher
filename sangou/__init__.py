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
import itertools
from discord.ext import commands
from helpers.datafiles import fill_profile, get_botfile
from helpers.placeholders import random_msg


# File and stdout logs.
if not os.path.exists("logs"):
    os.makedirs("logs")
log_format = logging.Formatter(
    "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(log_format)
logfile_handler = logging.FileHandler("logs/sangou.log", mode="w")
logfile_handler.setFormatter(log_format)
log = logging.getLogger("discord")
log.setLevel(logging.INFO)
log.addHandler(stdout_handler)
log.addHandler(logfile_handler)


def cap_permutations(s):
    # thank you to https://stackoverflow.com/a/11165671
    lu_sequence = ((c.lower(), c.upper()) for c in s)
    return ["".join(x) for x in itertools.product(*lu_sequence)]


def get_userprefix(uid):
    profile = fill_profile(uid)
    if not profile:
        return []
    return profile["prefixes"]


def get_useralias(uid):
    profile = fill_profile(uid)
    if not profile:
        return []
    return profile["aliases"]


def get_prefix(bot, message):
    prefixes = []
    for prefix in config.prefixes:
        prefixes += cap_permutations(prefix)
    userprefixes = get_userprefix(message.author.id)
    if userprefixes is not None:
        return commands.when_mentioned_or(*prefixes + userprefixes)(bot, message)
    return commands.when_mentioned_or(*prefixes)(bot, message)


intents = discord.Intents.all()
intents.typing = False

bot = commands.Bot(
    command_prefix=get_prefix,
    description=config.short_desc,
    owner_ids=set(config.managers),
    intents=intents,
    enable_debug_events=True,  # for raw events (e.g. super reactions handler)
)
bot.help_command = None
bot.log = log
bot.config = config
bot.errors = []
bot.version = "0.3.1"


@bot.event
async def on_ready():
    bot.app_info = await bot.application_info()

    log.info(
        f"\nLogged in as: {bot.user.name} - {bot.user.id}"
        f"\ndpy version: {discord.__version__}"
        f"\nbot version: {bot.version}"
        "\n"
    )

    bot.session = aiohttp.ClientSession()
    bot.start_timestamp = int(datetime.datetime.now().timestamp())


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
    err = sys.exc_info()
    err_tb = "\n".join(traceback.format_exception(*err))
    log.error(f"Code error in {event_method}...\n{err_tb}")

    ctx = None
    if args:
        for arg in args:
            if type(arg) == discord.Message:
                ctx = await bot.get_context(arg)
    bot.errors.append((err, ctx, (args, kwargs)))

    err_embed = discord.Embed(
        color=discord.Color.from_str("#FF0000"),
        title="🔥 Code Error",
        description=f"In `{event_method}`...",
        timestamp=datetime.datetime.now(),
    )

    if len(err_tb) > 1024:
        split_msg = list([err_tb[i : i + 1020] for i in range(0, len(err_tb), 1020)])

        ctr = 1
        for f in split_msg:
            err_embed.add_field(
                name=f"🧩 Traceback Fragment {ctr}",
                value=f"```{f}```",
                inline=False,
            )
            ctr += 1
    else:
        err_embed.add_field(
            name=f"🔍 Traceback:",
            value=f"```{err_tb}```",
            inline=False,
        )

    err_embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)

    for m in config.managers:
        await bot.get_user(m).send(embed=err_embed)


@bot.event
async def on_command_error(ctx, error):
    # We don't want to log commands that don't exist.
    if isinstance(error, commands.CommandNotFound):
        return

    log.error(
        f"An error occurred with `{ctx.command}` from "
        f"{ctx.message.author} ({ctx.message.author.id}):\n"
        f"{type(error)}: {error}"
    )

    if isinstance(error, commands.CommandInvokeError) and (
        "Cannot send messages to this user" not in str(error)
    ):
        err = (type(error.__cause__), error.__cause__, error.__cause__.__traceback__)
        err_tb = "\n".join(traceback.format_exception(*err, chain=False))
        bot.errors.append((err, ctx, ()))
        log.error(f"Code error in command {ctx.command}...\n{err_tb}")
        return await ctx.send(
            "This command broke!"
            + f"\nPaging {ctx.guild.get_member(120698901236809728).mention}!"
            if ctx.guild and ctx.guild.get_member(120698901236809728)
            else "\nPlease get help in the support server!"
        )
    elif isinstance(error, commands.NoPrivateMessage):
        return await ctx.send(random_msg("err_serversonly"))
    elif isinstance(error, commands.PrivateMessageOnly):
        return await ctx.send(random_msg("err_dmsonly"))
    elif (
        isinstance(error, commands.InvalidEndOfQuotedStringError)
        or isinstance(error, commands.ExpectedClosingQuoteError)
        or isinstance(error, commands.UnexpectedQuoteError)
    ):
        return await ctx.send(random_msg("err_quotes"))
    elif isinstance(error, commands.MissingRole):
        return await ctx.send(random_msg("err_role") + f"```{error.missing_role}```")
    elif isinstance(error, commands.BotMissingPermissions):
        roles_needed = "\n+ ".join(error.missing_permissions)
        return await ctx.send(random_msg("err_perms") + f"```diff\n+ {roles_needed}```")
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(
            random_msg("err_cooldown") + f"{error.retry_after:.1f} seconds."
        )
    elif isinstance(error, commands.CheckFailure):
        return await ctx.send(random_msg("err_checkfail"))
    elif isinstance(error, commands.MissingRequiredAttachment):
        return await ctx.send(random_msg("err_noattachment"))
    elif isinstance(error, commands.UserNotFound):
        return await ctx.send(random_msg("err_usernotfound"))
    elif isinstance(error, commands.MemberNotFound):
        return await ctx.send(random_msg("err_membernotfound"))
    elif isinstance(error, commands.CommandInvokeError) and (
        "Cannot send messages to this user" in str(error)
    ):
        return await ctx.send(random_msg("err_dmfail"))

    help_text = (
        f"Usage of this command is: ```{ctx.prefix}{ctx.command.name} "
        f"{ctx.command.signature}```\nPlease see `{ctx.prefix}help"
        f"` for more info."
    )

    if isinstance(error, commands.BadArgument):
        return await ctx.send(f"You gave incorrect arguments. {help_text}")
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f"You gave incomplete arguments. {help_text}")


@bot.event
async def on_message(message):
    await bot.wait_until_ready()

    if message.author.bot:
        return
    if (
        "botban" in get_botfile("botusers")
        and message.author.id in get_botfile("botusers")["botban"]
    ):
        return

    ctx = await bot.get_context(message)
    if not ctx.valid:

        def check(b, a):
            return a.id == message.id

        while True:
            if ctx.prefix:
                aliases = get_useralias(message.author.id)
                for alias in aliases:
                    command, alias = list(alias.items())[0]
                    if message.content.replace(ctx.prefix, "").startswith(alias):
                        message.content = message.content.replace(alias, command)
                        ctx = await bot.get_context(message)
                        break
            if ctx.valid:
                break
            try:
                author, message = await bot.wait_for(
                    "message_edit", timeout=15.0, check=check
                )
            except (asyncio.TimeoutError, discord.errors.NotFound):
                return
            else:
                ctx = await bot.get_context(message)
                if ctx.valid:
                    break
    await bot.invoke(ctx)


async def main():
    async with bot:
        for cog in [
            "cogs." + f[:-3]
            for f in os.listdir("cogs/")
            if os.path.isfile("cogs/" + f) and f[-3:] == ".py"
        ]:
            try:
                await bot.load_extension(cog)
            except:
                log.exception(f"Failed to load cog {cog}.")
        await bot.start(config.token)


if __name__ == "__main__":
    asyncio.run(main())
