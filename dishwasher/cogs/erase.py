import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import random
import asyncio
from helpers.sv_config import get_config
from helpers.datafiles import get_guildfile, set_guildfile


class Erase(Cog):
    """
    For when you want to be forgotten.
    """

    def __init__(self, bot):
        self.bot = bot
        self.verifycode = format(random.getrandbits(128), "x")[:10]

    def add_erased(self, guild, user, keywords, channels):
        erasequeue = get_guildfile(ctx.guild.id, "erasures")
        erasequeue[user.id] = {
            "keywords": keywords,
            "channels": channels,
            "completed": [],
        }
        set_guildfile(ctx.guild.id, "erasures", json.dumps(erasequeue))

    @commands.guild_only()
    @commands.command()
    async def erase(self, ctx, verify=None):
        erasequeue = get_guildfile(ctx.guild.id, "erasures")
        if str(ctx.author.id) in erasequeue:
            return await ctx.reply(
                content=f"You have already requested to delete your messages from `{ctx.guild.name}`.",
                mention_author=False,
            )
        if not verify:
            return await ctx.reply(
                content=f"**THIS IS A VERY DESTRUCTIVE AND IRREVERSIBLE ACTION!**\nThe `erase` command will systematically and painstakingly wipe your post history from the current server, leaving **NOTHING** behind!\nWhile this is proceeding, you may be DMed zip files containing files and images uploaded to this server.\nI __strongly__ recommend you request your Data Package first by going to the following location on your client:\n- `Settings`\n- `Privacy & Safety`\n- `Request all of my data`\nWait for it to arrive before proceeding.\n\nIf you are SURE that you want to do this, rerun this command with the following code: `{self.verifycode}`",
                delete_after=60,
            )
        if verify != self.verifycode:
            return await ctx.reply("You specified an incorrect verification code.")
        else:
            self.verifycode = format(random.getrandbits(128), "x")[:10]

            def messagecheck(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            keywordask = await ctx.reply(
                content='If you would like to delete messages by certain keywords, enter them now, separated by spaces.\nIf you would like to purge everything, simply reply "all".',
                mention_author=False,
            )

            try:
                keywordmsg = await self.bot.wait_for(
                    "message", timeout=300.0, check=messagecheck
                )
            except asyncio.TimeoutError:
                return await keywordask.edit(
                    content="Operation timed out.",
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )

            if keywordmsg.content.split()[0] == "all":
                keywords = []
            else:
                keywords = keywordmsg.content.split()

            await keywordask.edit(
                content=f"Set keywords include: `{str(keywords)}`.",
                delete_after=10,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )

            channelask = await ctx.reply(
                content='If you would like to delete messages from certain channels, enter them now (channel IDs only), separated by spaces.\nIf you would like to purge everything, simply reply "all".',
                mention_author=False,
            )

            try:
                channelmsg = await self.bot.wait_for(
                    "message", timeout=300.0, check=messagecheck
                )
            except asyncio.TimeoutError:
                return await channelask.edit(
                    content="Operation timed out.",
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )

            if channelmsg.content.split()[0] == "all":
                channels = []
            else:
                channels = channelmsg.content.split()

            await channelask.edit(
                content=f"Set channels include: `{str(channels)}`.",
                delete_after=10,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )

            add_erased(ctx.guild, ctx.author, keywords, channels)
            return await ctx.reply(
                content=f"You have requested to delete your messages from `{ctx.guild.name}`. This __cannot__ be undone.",
                mention_author=False,
            )


async def setup(bot):
    await bot.add_cog(Erase(bot))
