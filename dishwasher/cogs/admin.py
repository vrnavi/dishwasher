import discord
from discord.ext import commands
from discord.ext.commands import Cog
import traceback
import inspect
import re
import datetime
import json
import config
import random
import asyncio
import shutil
import os
from helpers.checks import check_if_bot_manager
from helpers.sv_config import get_config


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_eval_result = None
        self.previous_eval_code = None

    @commands.check(check_if_bot_manager)
    @commands.command(name="exit", aliases=["quit", "bye"])
    async def _exit(self, ctx):
        """[O] Shuts down (or restarts) the bot."""
        await ctx.message.reply(
            content=random.choice(self.bot.config.death_messages), mention_author=False
        )
        await self.bot.close()

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def getdata(self, ctx):
        """[O] Returns data files."""
        shutil.make_archive("data_backup", "zip", "data")
        await ctx.message.reply(
            content="Your current data files...",
            file=discord.File("data_backup.zip"),
            mention_author=False,
        )
        os.remove("data_backup.zip")

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def setdata(self, ctx):
        """[O] Replaces data files. This is destructive behavior!"""
        if not ctx.message.attachments:
            await ctx.reply(
                content="You need to supply the data files.", mention_author=False
            )
            return
        await ctx.message.attachments[0].save("data.zip")
        if os.path.exists("data"):
            shutil.rmtree("data")
        shutil.unpack_archive("data.zip", "data")
        await ctx.reply(content=f"{server.name}'s data saved.", mention_author=False)

    @commands.check(check_if_bot_manager)
    @commands.command(aliases=["getserverdata"])
    async def getsdata(self, ctx, server: discord.Guild = None):
        """[O] Returns server data."""
        if not server:
            server = ctx.guild
        try:
            shutil.make_archive(
                f"data/{server.id}", "zip", f"{self.bot.server_data}/{server.id}"
            )
            sdata = discord.File(f"data/{server.id}.zip")
            await ctx.message.reply(
                content=f"{server.name}'s data...",
                file=sdata,
                mention_author=False,
            )
            os.remove(f"data/{server.id}.zip")
        except FileNotFoundError:
            await ctx.message.reply(
                content="That server doesn't have any data.",
                mention_author=False,
            )

    @commands.check(check_if_bot_manager)
    @commands.command(aliases=["setserverdata"])
    async def setsdata(self, ctx, server: discord.Guild = None):
        """[O] Replaces server data files. This is destructive behavior!"""
        if not server:
            server = ctx.guild
        if not ctx.message.attachments:
            await ctx.reply(
                content="You need to supply the data file.", mention_author=False
            )
            return
        await ctx.message.attachments[0].save(f"data/{server.id}.zip")
        if os.path.exists(f"data/servers/{server.id}"):
            shutil.rmtree(f"data/servers/{server.id}")
        shutil.unpack_archive(f"data/{server.id}.zip", f"data/servers/{server.id}")
        await ctx.reply(content=f"{server.name}'s data saved.", mention_author=False)

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def getlogs(self, ctx):
        """[O] Returns the log file."""
        shutil.copy("logs/dishwasher.log", "logs/upload.log")
        await ctx.message.reply(
            content="The current log file...",
            file=discord.File("logs/upload.log", filename="dishwasher.log"),
            mention_author=False,
        )
        os.remove("logs/upload.log")

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def taillogs(self, ctx):
        """[O] Returns the last 10 lines of the log file."""
        shutil.copy("logs/dishwasher.log", "logs/upload.log")
        with open("logs/upload.log", "r+") as f:
            tail = "\n".join(f.read().split("\n")[-10:])
        os.remove("logs/upload.log")
        await ctx.message.reply(
            content=f"The current tailed log file...\n```{tail.replace('```', '')}```",
            mention_author=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def guilds(self, ctx):
        """[O] Shows the current guilds I am in."""
        guildmsg = "**I am in the following guilds:**"
        for g in self.bot.guilds:
            guildmsg += f"\n- {g.name} with `{g.member_count}` members."
        await ctx.reply(content=guildmsg, mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def permcheck(
        self,
        ctx,
        target: discord.Member = None,
        channel: discord.abc.GuildChannel = None,
    ):
        """[O] Shows the permissions."""
        if not target:
            target = ctx.guild.me
        if not channel:
            channel = ctx.channel
        await ctx.reply(
            content=f"{target}'s permissions for the current channel...\n```diff\n"
            + "\n".join(
                [
                    f"{'-' if not y else '+'} " + x
                    for x, y in iter(channel.permissions_for(ctx.guild.me))
                ]
            )
            + "```",
            mention_author=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def threadlock(self, ctx, channel: discord.TextChannel):
        """[O] Locks all threads in a given channel.."""
        msg = await ctx.reply(content="Locking threads...", mention_author=False)
        # Pull old archvied threads from the grave.
        async for t in channel.archived_threads():
            await t.edit(archived=False)
        async for t in channel.archived_threads(private=True, joined=True):
            await t.edit(archived=False)
        # Unsure if needed, but here anyway.
        channel = await ctx.guild.fetch_channel(channel.id)
        # Lock all threads.
        for t in channel.threads:
            await t.edit(locked=True)
            await t.edit(archived=True)
        await msg.edit(content="Done.")

    @commands.check(check_if_bot_manager)
    @commands.command(name="eval")
    async def _eval(self, ctx, *, code: str):
        """[O] Evaluates some code."""
        try:
            code = code.strip("` ")

            env = {
                "bot": self.bot,
                "ctx": ctx,
                "message": ctx.message,
                "server": ctx.guild,
                "guild": ctx.guild,
                "channel": ctx.message.channel,
                "author": ctx.message.author,
                "config": config,
                # modules
                "discord": discord,
                "commands": commands,
                "datetime": datetime,
                "json": json,
                "asyncio": asyncio,
                "random": random,
                "os": os,
                "get_config": get_config,
                # utilities
                "_get": discord.utils.get,
                "_find": discord.utils.find,
                # last result
                "_": self.last_eval_result,
                "_p": self.previous_eval_code,
            }
            env.update(globals())

            self.bot.log.info(f"Evaling {repr(code)}:")
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result

            if result is not None:
                self.last_eval_result = result

            self.previous_eval_code = code

            sliced_message = await self.bot.slice_message(
                repr(result), prefix="```", suffix="```"
            )
            for msg in sliced_message:
                await ctx.send(msg)
        except:
            sliced_message = await self.bot.slice_message(
                traceback.format_exc(), prefix="```", suffix="```"
            )
            for msg in sliced_message:
                await ctx.send(msg)

    async def cog_load_actions(self, cog_name):
        # Used for specific cog actions, tore out the verification cog since don't need it.
        pass

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def pull(self, ctx, auto=False):
        """[O] Performs a git pull."""
        tmp = await ctx.message.reply(content="Pulling...", mention_author=False)
        git_output = await self.bot.async_call_shell("git pull")
        allowed_mentions = discord.AllowedMentions(replied_user=False)
        if len(git_output) > 2000:
            parts = await self.bot.slice_message(git_output, prefix="```", suffix="```")
            await tmp.edit(
                content=f"Output too long. Sending in new message...",
                allowed_mentions=allowed_mentions,
            )
            for x in parts:
                await ctx.send(content=x)
        else:
            await tmp.edit(
                content=f"Pull complete. Output: ```{git_output}```",
                allowed_mentions=allowed_mentions,
            )
        if auto:
            cogs_to_reload = re.findall(r"cogs/([a-z_]*).py[ ]*\|", git_output)
            for cog in cogs_to_reload:
                cog_name = "cogs." + cog
                if cog_name not in config.initial_cogs:
                    continue

                try:
                    await self.bot.unload_extension(cog_name)
                    await self.bot.load_extension(cog_name)
                    self.bot.log.info(f"Reloaded ext {cog}")
                    await ctx.message.reply(
                        content=f":white_check_mark: `{cog}` successfully reloaded.",
                        mention_author=False,
                    )
                    await self.cog_load_actions(cog)
                except:
                    await ctx.message.reply(
                        content=f":x: Cog reloading failed, traceback: "
                        f"```\n{traceback.format_exc()}\n```",
                        mention_author=False,
                    )
                    return

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def load(self, ctx, ext: str):
        """[O] Loads a cog."""
        try:
            await self.bot.load_extension("cogs." + ext)
            await self.cog_load_actions(ext)
        except:
            await ctx.message.reply(
                content=f":x: Cog loading failed, traceback: "
                f"```\n{traceback.format_exc()}\n```",
                mention_author=False,
            )
            return
        self.bot.log.info(f"Loaded ext {ext}")
        await ctx.message.reply(
            content=f":white_check_mark: `{ext}` successfully loaded.",
            mention_author=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def unload(self, ctx, ext: str):
        """[O] Unloads a cog."""
        await self.bot.unload_extension("cogs." + ext)
        self.bot.log.info(f"Unloaded ext {ext}")
        await ctx.message.reply(
            content=f":white_check_mark: `{ext}` successfully unloaded.",
            mention_author=False,
        )

    @commands.check(check_if_bot_manager)
    @commands.command()
    async def reload(self, ctx, ext="_"):
        """[O] Reloads a cog."""
        if ext == "_":
            ext = self.lastreload
        else:
            self.lastreload = ext

        try:
            await self.bot.unload_extension("cogs." + ext)
            await self.bot.load_extension("cogs." + ext)
            await self.cog_load_actions(ext)
        except:
            await ctx.message.reply(
                content=f":x: Cog reloading failed, traceback: "
                f"```\n{traceback.format_exc()}\n```",
                mention_author=False,
            )
            return
        self.bot.log.info(f"Reloaded ext {ext}")
        await ctx.message.reply(
            content=f":white_check_mark: `{ext}` successfully reloaded.",
            mention_author=False,
        )

    @Cog.listener()
    async def on_guild_join(self, guild):
        msgs = []
        for m in config.bot_managers:
            msg = await self.bot.get_user(m).send(
                content=f"{self.bot.user.name} joined `{guild}` with `{len(guild.members)}` members.\nCheck the checkmark within an hour to leave."
            )
            await msg.add_reaction("✅")
            msgs.append(msg)

        def check(r, u):
            return (
                u.id in config.bot_managers
                and str(r.emoji) == "✅"
                and type(r.message.channel) == discord.channel.DMChannel
            )

        try:
            r, u = await self.bot.wait_for("reaction_add", timeout=600.0, check=check)
        except asyncio.TimeoutError:
            pass
        else:
            await guild.leave()
            for m in msgs:
                await m.edit(content=f"{m.content}\n\nI have left this guild.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
