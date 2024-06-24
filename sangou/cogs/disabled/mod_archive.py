import discord
import json
import os
import typing
import datetime

from io import BytesIO
import zipfile

from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import ismod, isadmin
from helpers.archive import log_channel
from helpers.sv_config import get_config
from helpers.datafiles import get_guildfile, set_guildfile, get_tossfile, set_tossfile
from helpers.embeds import stock_embed, author_embed


class ModArchives(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def archives(self, ctx, user: discord.User):
        """Views a list of saved archives for a user.

        Use `open` to open an archive.
        Doing so will be logged by the bot!

        - `user`
        The user to find archives for."""
        if ctx.guild.get_member(user.id):
            user = ctx.guild.get_member(user.id)
        uid = str(user.id)
        userlog = get_guildfile(ctx.guild.id, "userlog")
        embed = stock_embed(self.bot)
        author_embed(embed, user)
        embed.title = f"📁 {user.name}'s archives..."

        path = f"data/servers/{ctx.guild.id}/toss/archives/users/{uid}"
        if os.path.exists(path) and [f for f in os.listdir(path)]:
            filelist = "\n".join(
                [
                    "- "
                    + filename
                    + " `"
                    + self.bot.filesize(os.path.getsize(path + "/" + filename))
                    + "`."
                    for filename in [
                        filename
                        for filename in os.listdir(path)
                        if os.path.isfile(os.path.join(path, filename))
                    ]
                ]
            )
        else:
            filelist = "There are no archives for this user."

        embed.add_field(
            name="User Archives",
            value=filelist,
            inline=False,
        )

        if uid in userlog and userlog[uid]:
            for index, event in enumerate(userlog[uid]["tosses"]):
                path = f"data/servers/{ctx.guild.id}/toss/archives/sessions/{event['session_id']}"
                if "session_id" not in event or not os.path.exists(path):
                    archivelist = "There are no archives for this session."
                else:
                    archivelist = "\n".join(
                        [
                            "- "
                            + filename
                            + " `"
                            + self.bot.filesize(os.path.getsize(path + "/" + filename))
                            + "`."
                            for filename in [
                                filename
                                for filename in os.listdir(path)
                                if os.path.isfile(os.path.join(path, filename))
                            ]
                        ]
                    )

                embed.add_field(
                    name="Toss Archive " + str(index + 1),
                    value=f"<t:{event['timestamp']}:R> on <t:{event['timestamp']}:f>\n"
                    + f"__Issuer:__ <@{event['issuer_id']}> ({event['issuer_id']})\n"
                    + archivelist,
                    inline=False,
                )

        return await ctx.reply(embed=embed, mention_author=False)

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @archives.command()
    async def open(
        self, ctx, user: discord.User, *, archive: typing.Union[int, str] = None
    ):
        """This sends an archive to your DMs.

        Note that it will trace you!
        Archive should be an index for toss archives,
        or a filename for a user archive.
        Leave the archive blank to open ALL archives.

        - `user`
        The user to find archives for.
        - `archive`
        The index of the archive to pull. Optional."""
        if ctx.guild.get_member(user.id):
            user = ctx.guild.get_member(user.id)
        uid = str(user.id)
        userlog = get_guildfile(ctx.guild.id, "userlog")
        embed = stock_embed(self.bot)

        traces = get_tossfile(ctx.guild.id, "traces")
        if "sessions" not in traces:
            traces["sessions"] = {}
        if "users" not in traces:
            traces["users"] = {}

        if type(archive) == str:
            path = f"data/servers/{ctx.guild.id}/toss/archives/users/{uid}"
            if not os.path.exists(path) or not os.listdir(path):
                embed.title = "📂 About that archive..."
                embed.description = "> This user doesn't have any archives!"
                return await ctx.reply(embed=embed, mention_author=False)
            elif archive not in os.listdir(path):
                embed.title = "📂 About that archive..."
                embed.description = "> That's not a valid archive!"
                return await ctx.reply(embed=embed, mention_author=False)
            filelist = [discord.File(os.path.join(path, archive))]
            returnmsg = "Here's " + user.name + "'s `" + str(archive) + "` file."

            if str(user.id) not in traces["users"]:
                traces["users"][str(user.id)] = []
            log_data = {
                "issuer_id": ctx.author.id,
                "file": archive,
                "timestamp": int(datetime.datetime.now().timestamp()),
            }
            traces["users"][str(user.id)].append(log_data)
        elif type(archive) == int:
            if uid not in userlog:
                embed.title = "📂 About that archive..."
                embed.description = "> This user isn't in the system!"
                return await ctx.reply(embed=embed, mention_author=False)
            elif not userlog[uid]:
                embed.title = "📂 About that archive..."
                embed.description = "> This user's logs are empty!"
                return await ctx.reply(embed=embed, mention_author=False)
            caseid = userlog[uid]["tosses"][archive - 1]["session_id"]
            if not os.path.exists(
                f"data/servers/{ctx.guild.id}/toss/archives/sessions/{caseid}"
            ):
                embed.title = "📂 About that archive..."
                embed.description = "> This archive is empty!"
                return await ctx.reply(embed=embed, mention_author=False)

            path = f"data/servers/{ctx.guild.id}/toss/archives/sessions/{caseid}"
            filelist = [
                discord.File(os.path.join(path, file))
                for file in [
                    filename
                    for filename in os.listdir(path)
                    if os.path.isfile(os.path.join(path, filename))
                ]
            ]
            returnmsg = (
                "Here's " + user.name + "'s Toss Session `" + str(archive) + "` files."
            )

            if str(caseid) not in traces["sessions"]:
                traces["sessions"][str(caseid)] = []
            log_data = {
                "issuer_id": ctx.author.id,
                "timestamp": int(datetime.datetime.now().timestamp()),
            }
            traces["sessions"][str(caseid)].append(log_data)
        else:
            path = f"data/servers/{ctx.guild.id}/toss/archives/users/{uid}"
            if not os.path.exists(path) or not os.listdir(path):
                embed.title = "📂 About that archive..."
                embed.description = "> This user doesn't have any archives!"
                return await ctx.reply(embed=embed, mention_author=False)
            b = BytesIO()
            z = zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED)

            if str(user.id) not in traces["users"]:
                traces["users"][str(user.id)] = []
            for filename in os.listdir(path):
                if not os.path.isfile(os.path.join(path, filename)):
                    continue
                with open(os.path.join(path, filename), "r") as file:
                    z.writestr(filename, file.read())
                log_data = {
                    "issuer_id": ctx.author.id,
                    "file": filename,
                    "timestamp": int(datetime.datetime.now().timestamp()),
                }
                traces["users"][str(user.id)].append(log_data)

            z.close()
            b.seek(0)
            returnmsg = "Here's " + user.name + "'s files."
            filelist = [discord.File(b, "datapack.zip")]
        try:
            await ctx.author.send(
                content=returnmsg,
                files=filelist,
            )
            await ctx.reply(content="I DMed it to you!", mention_author=False)
            set_tossfile(ctx.guild.id, "traces", json.dumps(traces))
        except:
            return await ctx.reply(content="I can't DM you!", mention_author=False)

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @archives.command()
    async def trace(self, ctx, user: discord.User, *, archive: typing.Union[int, str]):
        """This views the tracelog for an archive.

        Archive should be an index for toss archives,
        or a filename for a user archive.

        - `user`
        The user to find archives for.
        - `index`
        The index of the archive to trace."""
        if ctx.guild.get_member(user.id):
            user = ctx.guild.get_member(user.id)
        uid = str(user.id)
        userlog = get_guildfile(ctx.guild.id, "userlog")
        embed = stock_embed(self.bot)
        if uid not in userlog:
            embed.title = "📂 About that archive..."
            embed.description = "> This user isn't in the system!"
            return await ctx.reply(embed=embed, mention_author=False)
        elif not userlog[uid]:
            embed.title = "📂 About that archive..."
            embed.description = "> This user's logs are empty!"
            return await ctx.reply(embed=embed, mention_author=False)
        author_embed(embed, user)
        embed.title = "🔍 Archive traces..."

        traces = get_tossfile(ctx.guild.id, "traces")
        if type(archive) == str:
            path = f"data/servers/{ctx.guild.id}/toss/archives/users/{uid}"
            if not os.path.exists(path) and [f for f in os.listdir(path)]:
                embed.title = "📂 About that archive..."
                embed.description = "> This user doesn't have any archives!"
                return await ctx.reply(embed=embed, mention_author=False)
            if archive not in [f for f in os.listdir(path)]:
                embed.title = "📂 About that archive..."
                embed.description = "> That's not a valid archive!"
                return await ctx.reply(embed=embed, mention_author=False)
            if not "users" in traces or str(user.id) not in traces["users"]:
                embed.title = "📂 About that archive..."
                embed.description = "> This archive hasn't been opened!"
                return await ctx.reply(embed=embed, mention_author=False)
            embed.description = "For `" + archive + "`."
            for index, event in enumerate(
                [
                    trace
                    for trace in traces["users"][str(user.id)]
                    if trace["file"] == archive
                ]
            ):
                embed.add_field(
                    name="Trace " + str(index + 1),
                    value=f"<t:{event['timestamp']}:R> on <t:{event['timestamp']}:f>\n"
                    + f"__Issuer:__ <@{event['issuer_id']}> ({event['issuer_id']})\n",
                    inline=False,
                )
        else:
            if uid not in userlog:
                embed.title = "📂 About that archive..."
                embed.description = "> This user isn't in the system!"
                return await ctx.reply(embed=embed, mention_author=False)
            elif not userlog[uid]:
                embed.title = "📂 About that archive..."
                embed.description = "> This user's logs are empty!"
                return await ctx.reply(embed=embed, mention_author=False)
            caseid = userlog[uid]["tosses"][archive - 1]["session_id"]
            if not os.path.exists(
                f"data/servers/{ctx.guild.id}/toss/archives/sessions/{caseid}"
            ):
                embed.title = "📂 About that archive..."
                embed.description = "> This archive is empty!"
                return await ctx.reply(embed=embed, mention_author=False)
            if not "sessions" in traces or str(caseid) not in traces["sessions"]:
                embed.title = "📂 About that archive..."
                embed.description = "> This archive hasn't been opened!"
                return await ctx.reply(embed=embed, mention_author=False)
            embed.description = "For Toss Archive `" + str(archive) + "`."
            for index, event in enumerate(traces["sessions"][str(caseid)]):
                embed.add_field(
                    name="Trace " + str(index + 1),
                    value=f"<t:{event['timestamp']}:R> on <t:{event['timestamp']}:f>\n"
                    + f"__Issuer:__ <@{event['issuer_id']}> ({event['issuer_id']})\n",
                    inline=False,
                )

        return await ctx.reply(embed=embed, mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def orbitlog(
        self,
        ctx,
        channels: commands.Greedy[
            typing.Union[discord.abc.GuildChannel, discord.Thread]
        ] = None,
    ):
        """Logs a channel from orbit.

        Be VERY careful for using this with large channels.

        - `channels`
        A list of channels to orbitlog. You can use categories too."""
        if not channels:
            channels = [ctx.channel]
        for channel in channels:
            if type(channel) == discord.CategoryChannel:
                for chnl in channel.channels:
                    channels.append(chnl)
                continue

            async with ctx.channel.typing():
                dotraw, dotzip = await log_channel(self.bot, channel, zip_files=True)
                dottxt = BytesIO()
                dottxt.write(dotraw.encode("utf-8"))
                dottxt.seek(0)

            filename = (
                ctx.message.created_at.strftime("%Y-%m-%d")
                + f" {channel.name} {channel.id}"
            )

            files = [discord.File(dottxt, filename=filename + ".txt")]
            if dotzip:
                files += [discord.File(dotzip, filename=filename + " (files).zip")]

            await ctx.send(
                content="TEMPORARY ARCHIVE MESSAGE",
                files=files,
            )


async def setup(bot):
    await bot.add_cog(ModArchives(bot))
