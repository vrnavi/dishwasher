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
from helpers.datafiles import get_userfile, get_botfile
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
    profile = get_userfile(uid, "profile")
    if not profile:
        return []
    return profile["prefixes"]


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
bot.version = "0.1.1"


@bot.event
async def on_ready():
    bot.app_info = await bot.application_info()

    log.info(
        f"\nLogged in as: {bot.user.name} - "
        f"{bot.user.id}\ndpy version: {discord.__version__}\n"
        f"bot version: {bot.version}\n"
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

    for m in config.managers:
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

    bot.errors.append((ctx, error))

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send(random_msg("err_serversonly", ctx))
    elif isinstance(error, commands.PrivateMessageOnly):
        return await ctx.send(random_msg("err_dmsonly", ctx))
    elif (
        isinstance(error, commands.InvalidEndOfQuotedStringError)
        or isinstance(error, commands.ExpectedClosingQuoteError)
        or isinstance(error, commands.UnexpectedQuoteError)
    ):
        return await ctx.send(random_msg("err_quotes", ctx))
    elif isinstance(error, commands.MissingRole):
        return await ctx.send(
            random_msg("err_role", ctx) + f"```{error.missing_role}```"
        )
    elif isinstance(error, commands.BotMissingPermissions):
        roles_needed = "\n+ ".join(error.missing_permissions)
        return await ctx.send(random_msg("err_perms", ctx) + f"```diff\n+ {roles_needed}```")
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(
            random_msg("err_cooldown", ctx) + f"{error.retry_after:.1f} seconds."
        )
    elif isinstance(error, commands.CheckFailure):
        return await ctx.send(random_msg("err_checkfail", ctx))
    elif isinstance(error, commands.MissingRequiredAttachment):
        return await ctx.send(random_msg("err_noattachment", ctx))
    elif isinstance(error, commands.UserNotFound):
        return await ctx.send(random_msg("err_usernotfound", ctx))
    elif isinstance(error, commands.MemberNotFound):
        return await ctx.send(random_msg("err_membernotfound", ctx))
    elif isinstance(error, commands.CommandInvokeError) and (
        "Cannot send messages to this user" in str(error)
    ):
        return await ctx.send(random_msg("err_dmfail", ctx))

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
            try:
                b, a = await bot.wait_for("message_edit", timeout=15.0, check=check)
            except (asyncio.TimeoutError, discord.errors.NotFound):
                return
            else:
                ctx = await bot.get_context(a)
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
