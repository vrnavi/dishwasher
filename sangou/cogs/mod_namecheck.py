import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import datetime
import asyncio
from unidecode import unidecode
from helpers.checks import ismod
from helpers.sv_config import get_config


class ModNamecheck(Cog):
    """
    Keeping names readable.
    """

    def __init__(self, bot):
        self.bot = bot
        self.readablereq = 1

    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def decancer(self, ctx, target: discord.Member):
        """This cleans unicode from a username.

        There's not much more to it.

        - `target`
        The target to clean unicode from."""
        oldname = target.display_name
        newname = unidecode(target.display_name)
        if not newname:
            newname = "Unreadable Name"
        await target.edit(nick=newname, reason="Namecheck")
        return await ctx.reply(
            content=f"Successfully decancered **{oldname}** to  `{newname}`.",
            mention_author=False,
        )

    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def dehoist(self, ctx, target: discord.Member):
        """This dehoists a user from the member list.

        It uses a specific unicode character to do so.

        - `target`
        The target to dehoist."""
        oldname = target.display_name
        await target.edit(nick="᲼" + target.display_name, reason="Namecheck")
        return await ctx.reply(
            content=f"Successfully dehoisted **{oldname}**.", mention_author=False
        )

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not get_config(member.guild.id, "reaction", "autoreadableenable"):
            return

        name = member.display_name

        # Non-Alphanumeric
        readable = len([b for b in name if b.isascii()])
        if readable < self.readablereq:
            name = unidecode(name) if unidecode(name) else "Unreadable Name"

        # Hoist
        if name[:1] in ("!", "-", ".", "(", ")", ":"):
            name = "᲼" + name

        # Validate
        if len(name) > 32:
            name = name[:29] + "..."
        if name != member.display_name:
            await member.edit(nick=name, reason="Automatic Namecheck")

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()
        if not get_config(member_after.guild.id, "reaction", "autoreadableenable"):
            return

        name = member_after.display_name

        # Non-Alphanumeric
        readable = len([b for b in name if b.isascii()])
        if readable < self.readablereq:
            name = unidecode(name) if unidecode(name) else "Unreadable Name"

        # Hoist
        if name[:1] in ("!", "-", ".", "(", ")", ":"):
            name = "᲼" + name

        # Validate
        if len(name) > 32:
            name = name[:29] + "..."
        if name != member_after.display_name:
            await member_after.edit(nick=name, reason="Automatic Namecheck")


async def setup(bot):
    await bot.add_cog(ModNamecheck(bot))
