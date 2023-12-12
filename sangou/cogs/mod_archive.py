# This Cog contains code from Archiver, which was made by Roadcrosser.
# https://github.com/Roadcrosser/archiver
import discord
import json
import os
import httplib2
import re
import datetime
import config
import asyncio
import textwrap
import zipfile

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import ismod
from helpers.archive import log_whole_channel, get_members
from helpers.sv_config import get_config


class ModArchive(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Archival isn't set up for this server."

    @commands.guild_only()
    @commands.check(ismod)
    @commands.command(aliases=["archives"])
    async def archive(self, ctx, *, args=None):
        if not get_config(ctx.guild.id, "toss", "drivefolder"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            "data/service_account.json", "https://www.googleapis.com/auth/drive"
        )
        credentials.authorize(httplib2.Http())
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        folder = get_config(ctx.guild.id, "toss", "drivefolder")

        try:
            await ctx.channel.typing()
        except:
            pass

        if ctx.channel.name in get_config(ctx.guild.id, "toss", "tosschannels"):
            out = await log_whole_channel(self.bot, ctx.channel, zip_files=True)
            zipped_files = out[1]
            out = out[0]

            user = f"unspecified (logged by {ctx.author})"
            users = None
            if args:
                try:
                    users = [
                        await self.bot.fetch_user(uid)
                        for uid in [int(arg) for arg in args.split()]
                    ]
                except:
                    return await ctx.reply(
                        content="Fetching the users failed. Either a user ID doesn't exist, or you specified them incorrectly..",
                        mention_author=False,
                    )
            if not args:
                try:
                    users = [
                        await self.bot.fetch_user(uid)
                        for uid in self.bot.tosscache[ctx.guild.id][ctx.channel.name]
                    ]
                except:
                    return await ctx.reply(
                        content="The toss cache is empty. Please specify user IDs to archive instead.",
                        mention_author=False,
                    )
            user = f"{users[0].name} {users[0].id}"

            fn = ctx.message.created_at.strftime("%Y-%m-%d") + " " + str(user)

            reply = f"📕 Archived as: `{fn}.txt`"

            out += f"{ctx.message.created_at.strftime('%Y-%m-%d %H:%M')} {self.bot.user.name}: {reply}"
            if users:
                out += "\nThis toss session had the following users:"
                for u in users:
                    out += f"\n- **{u.global_name}** [{u}] ({u.id})"

            f = drive.CreateFile(
                {
                    "parents": [{"kind": "drive#fileLink", "id": folder}],
                    "title": fn + ".txt",
                }
            )
            f.SetContentString(out)
            f.Upload()

            modch = self.bot.get_channel(
                get_config(ctx.guild.id, "staff", "staffchannel")
            )

            embed = discord.Embed(
                title="📁 Toss Channel Archived",
                description=f"{ctx.channel.name}'s session was archived by {ctx.author.mention} ({ctx.author.id})",
                color=ctx.author.color,
                timestamp=datetime.datetime.now(),
            )
            embed.set_footer(
                text=self.bot.user.name, icon_url=self.bot.user.display_avatar
            )
            embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
            embed.add_field(
                name="🔗 Text",
                value=f"[{fn}.txt](https://drive.google.com/file/d/{f['id']})",
                inline=True,
            )

            if zipped_files:
                f_zip = drive.CreateFile(
                    {
                        "parents": [{"kind": "drive#fileLink", "id": folder}],
                        "title": fn + " (files).zip",
                    }
                )
                f_zip.content = zipped_files
                f_zip["mimeType"] = "application/zip"
                f_zip.Upload()

                embed.add_field(
                    name="📦 Files",
                    value=f"[{fn} (files).zip](https://drive.google.com/file/d/{f_zip['id']})",
                    inline=True,
                )

            await ctx.send(content=reply)
            await modch.send(embed=embed)

            return True
        else:
            limit = 10
            query = f"'{folder}' in parents"
            args = re.sub("[^a-zA-Z0-9 ]", "", args) if args else None
            title = "Results"
            if not args:
                await ctx.send(
                    "Error: Unable to search archives. Please specify arguments."
                )
                return

            search_term = args

            query += f" and title contains '{search_term}'"
            title += " for " + search_term

            fl = drive.ListFile({"q": query}).GetList()
            fl_count = len(fl)
            unlisted_fl_count = fl_count - limit
            fl = fl[:limit]
            msg = "No Results."
            if fl:
                msg = "\n".join(
                    [
                        "[`{title}`](https://drive.google.com/file/d/{id})".format(**f)
                        for f in fl
                    ]
                )
                if unlisted_fl_count > 0:
                    msg += f"\nand **{unlisted_fl_count}** more..."
            await ctx.send(
                embed=discord.Embed(
                    title=title,
                    url="https://drive.google.com/drive/folders/{}".format(folder),
                    description=msg,
                    color=ctx.guild.me.color,
                )
            )

        return True


async def setup(bot):
    await bot.add_cog(ModArchive(bot))
