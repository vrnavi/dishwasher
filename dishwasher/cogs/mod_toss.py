# This Cog contains code from Tosser2, which was made by OblivionCreator.
import discord
import json
import os
import asyncio
import random
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord.ext.commands import Cog
import httplib2
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
from helpers.checks import check_if_staff
from helpers.userlogs import userlog
from helpers.placeholders import random_self_msg, random_bot_msg
from helpers.archive import log_whole_channel, get_members
from helpers.embeds import stock_embed, username_system, mod_embed
from helpers.sv_config import get_config


class ModToss(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.tosscache = {}
        self.spamcounter = {}
        self.nocfgmsg = "Tossing isn't enabled for this server."

    def pacify_name(self, name):
        return discord.utils.escape_markdown(name.replace("@", "@ "))

    def username_system(self, user):
        return (
            "**"
            + self.pacify_name(user.global_name)
            + f"** [{self.pacify_name(str(user))}]"
            if user.global_name
            else f"**{self.pacify_name(str(user))}**"
        )

    # Thank you to https://stackoverflow.com/a/29489919 for this function.
    def principal_period(self, s):
        i = (s + s).find(s, 1, -1)
        return None if i == -1 else s[:i]

    def get_user_list(self, ctx, user_ids):
        user_id_list = []
        invalid_ids = []

        if user_ids.isnumeric():
            tmp_user = ctx.guild.get_member(int(user_ids))
            if tmp_user is not None:
                user_id_list.append(tmp_user)
            else:
                invalid_ids.append(user_ids)
        else:
            if ctx.message.mentions:
                for u in ctx.message.mentions:
                    user_id_list.append(u)
            user_ids_split = user_ids.split()
            for n in user_ids_split:
                if n.isnumeric():
                    user = ctx.guild.get_member(int(n))
                    if user is not None:
                        user_id_list.append(user)
                    else:
                        invalid_ids.append(n)

        return user_id_list, invalid_ids

    def is_rolebanned(self, member, hard=True):
        roleban = [
            r
            for r in member.guild.roles
            if r.id == get_config(member.guild.id, "toss", "toss_role")
        ]
        if roleban:
            if get_config(member.guild.id, "toss", "toss_role") in [
                r.id for r in member.roles
            ]:
                if hard:
                    return len([r for r in member.roles if not (r.managed)]) == 2
                return True

    async def new_session(self, guild):
        staff_role = guild.get_role(get_config(guild.id, "staff", "staff_role"))
        bot_roles = [
            guild.get_role(int(r)) for r in get_config(guild.id, "misc", "bot_roles")
        ]
        for c in get_config(guild.id, "toss", "toss_channels"):
            if c not in [g.name for g in guild.channels]:
                if not os.path.exists(f"{self.bot.server_data}/{guild.id}/toss/{c}"):
                    os.makedirs(f"{self.bot.server_data}/{guild.id}/toss/{c}")
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    staff_role: discord.PermissionOverwrite(read_messages=True),
                }
                for x in bot_roles:
                    overwrites[x] = discord.PermissionOverwrite(read_messages=True)
                toss_channel = await guild.create_text_channel(
                    c,
                    reason="Dishwasher Toss3",
                    category=guild.get_channel(
                        get_config(guild.id, "toss", "toss_category")
                    ),
                    overwrites=overwrites,
                    topic="The rolebanned channel. You likely won't get banned, but don't leave immediately, or you will be banned.",  # i need to replace this
                )
                return toss_channel

    async def perform_toss(self, user, staff, toss_channel):
        toss_role = user.guild.get_role(get_config(user.guild.id, "toss", "toss_role"))
        roles = []
        for rx in user.roles:
            if rx != user.guild.default_role and rx != toss_role:
                roles.append(rx)

        with open(
            rf"{self.bot.server_data}/{user.guild.id}/toss/{toss_channel.name}/{user.id}.json",
            "w",
        ) as file:
            file.write(json.dumps([role.id for role in roles]))

        prev_roles = " ".join([f"`{role.name}`" for role in roles])

        await user.add_roles(toss_role, reason="User tossed.")
        fail_roles = []
        if roles:
            for rr in roles:
                if not rr.is_assignable():
                    fail_roles.append(rr.name)
                    roles.remove(rr)
            await user.remove_roles(
                *roles,
                reason=f"User tossed by {staff} ({staff.id})",
                atomic=False,
            )

        bad_roles_msg = (
            f"\nI was unable to remove the following role(s): **{', '.join(fail_roles)}**"
            if len(fail_roles) > 0
            else ""
        )

        return bad_roles_msg, prev_roles

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def sessions(self, ctx):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        embed = stock_embed(self.bot)
        embed.title = "👁‍🗨 Toss Channel Sessions..."
        embed.color = ctx.author.color
        for c in get_config(ctx.guild.id, "toss", "toss_channels"):
            if c in [g.name for g in ctx.guild.channels]:
                if not os.path.exists(
                    f"{self.bot.server_data}/{ctx.guild.id}/toss/{c}"
                ) or not os.listdir(f"{self.bot.server_data}/{ctx.guild.id}/toss/{c}"):
                    embed.add_field(
                        name=f"🟡 #{c}",
                        value="__Empty__\n> Please close the channel.",
                        inline=False,
                    )
                else:
                    userlist = "\n".join(
                        [
                            f"> {self.username_system(user)}"
                            for user in [
                                await self.bot.fetch_user(u)
                                for u in [
                                    uf[:-5]
                                    for uf in os.listdir(
                                        f"{self.bot.server_data}/{ctx.guild.id}/toss/{c}"
                                    )
                                ]
                            ]
                        ]
                    )
                    embed.add_field(
                        name=f"🔴 #{c}",
                        value=f"__Occupied__\n{userlist}",
                        inline=False,
                    )
            else:
                embed.add_field(name=f"🟢 #{c}", value="__Available__", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["roleban"])
    async def toss(self, ctx, *, user_ids):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)
        alreadytossed = [
            tossed
            for dsub in [
                os.listdir(channel)
                for channel in [
                    dirs[0]
                    for dirs in os.walk(f"{self.bot.server_data}/{ctx.guild.id}/toss")
                ]
            ]
            for tossed in dsub
        ]

        staff_channel = get_config(ctx.guild.id, "staff", "staff_channel")
        modlog_channel = get_config(ctx.guild.id, "logs", "mlog_thread")
        staff_role = ctx.guild.get_role(get_config(ctx.guild.id, "staff", "staff_role"))
        toss_role = ctx.guild.get_role(get_config(ctx.guild.id, "toss", "toss_role"))

        output = ""

        for us in user_id_list:
            if us.id == ctx.author.id:
                output += "\n" + random_self_msg(ctx.author.name)
            elif us.id == self.bot.application_id:
                output += "\n" + random_bot_msg(ctx.author.name)
            elif str(us.id) + ".json" in alreadytossed and toss_role in us.roles:
                output += "\n" + f"{self.username_system(us)} is already tossed."
            else:
                continue
            user_id_list.remove(us)
        if not user_id_list:
            return await ctx.reply(
                output
                + "\n\n"
                + "There's nobody left in the list to toss, so nobody was tossed.",
                mention_author=False,
            )
        if all(
            [
                c in ctx.guild.channels
                for c in get_config(ctx.guild.id, "toss", "toss_channels")
            ]
        ):
            return await ctx.reply(
                content="I cannot toss them. All sessions are currently in use.",
                mention_author=False,
            )

        toss_pings = ", ".join([us.mention for us in user_id_list])

        if ctx.channel.name in get_config(ctx.guild.id, "toss", "toss_channels"):
            addition = True
            toss_channel = ctx.channel
        else:
            addition = False
            toss_channel = await self.new_session(ctx.guild)

        for us in user_id_list:
            try:
                bad_roles_msg, prev_roles = await self.perform_toss(
                    us, ctx.author, toss_channel
                )
                await toss_channel.set_permissions(us, read_messages=True)

                userlog(
                    ctx.guild.id,
                    us.id,
                    ctx.author,
                    f"[Jump]({ctx.message.jump_url}) to toss event.",
                    "tosses",
                )

                if staff_channel:
                    await ctx.guild.get_channel(staff_channel).send(
                        f"{self.username_system(us)} has been tossed in `#{ctx.channel.name}` by {self.username_system(ctx.author)}. {us.mention}\n"
                        f"**ID:** {us.id}\n"
                        f"**Created:** <t:{int(us.created_at.timestamp())}:R> on <t:{int(us.created_at.timestamp())}:f>\n"
                        f"**Joined:** <t:{int(us.joined_at.timestamp())}:R> on <t:{int(us.joined_at.timestamp())}:f>\n"
                        f"**Previous Roles:**{prev_roles}{bad_roles_msg}\n\n"
                        f"{toss_channel.mention}"
                    )

                if modlog_channel:
                    embed = stock_embed(self.bot)
                    embed.color = discord.Color.from_str("#FF0000")
                    embed.title = "🚷 Toss"
                    embed.description = f"{us.mention} was tossed by {ctx.author.mention} [`#{ctx.channel.name}`] [[Jump]({ctx.message.jump_url})]"
                    mod_embed(embed, us, ctx.author)

                    mlog = await self.bot.fetch_channel(modlog_channel)
                    await mlog.send(embed=embed)

            except commands.MissingPermissions:
                invalid_ids.append(us.name)

        output += "\n" + "\n".join(
            [f"{self.username_system(us)} has been tossed." for us in user_id_list]
        )

        if invalid_ids:
            output += (
                "\n\n"
                + "I was unable to toss these users: "
                + ", ".join([str(iv) for iv in invalid_ids])
            )

        output += (
            "\n\nPlease change the topic. **Discussion of tossed users will lead to warnings.**"
            if ctx.channel.permissions_for(ctx.guild.default_role).read_messages
            or len(ctx.channel.members) >= 100
            else ""
        )
        await ctx.reply(content=output, mention_author=False)

        if not addition:
            await toss_channel.send(
                f"{toss_pings}\nYou were tossed by {self.pacify_name(ctx.author.global_name) if ctx.author.global_name else self.pacify_name(ctx.author.name)}.\n"
                '*For your reference, a "toss" is where a Staff member wishes to speak with you, one on one.*\n'
                "**Do NOT leave the server, or you will be instantly banned.**"
            )

            if any([us.raw_status != "offline" for us in user_id_list]):
                await toss_channel.send("⏰ Please respond within `5 minutes`.")

                def check(m):
                    return m.author in user_id_list and m.channel == toss_channel

                try:
                    msg = await self.bot.wait_for(
                        "message", timeout=60 * 5, check=check
                    )
                except asyncio.TimeoutError:
                    pokemsg = await toss_channel.send(ctx.author.mention)
                    await pokemsg.edit(content="⏰", delete_after=5)
                except discord.NotFound:
                    # The channel probably got deleted before anything could happen.
                    return
                else:
                    pokemsg = await toss_channel.send(ctx.author.mention)
                    await pokemsg.edit(
                        content="⏰🔨 Tossed user sent a message. Timer destroyed.",
                        delete_after=5,
                    )

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["unroleban"])
    async def untoss(self, ctx, *, user_ids=None):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if ctx.channel.name not in get_config(ctx.guild.id, "toss", "toss_channels"):
            return await ctx.reply(
                content="This command must be run inside of a toss channel.",
                mention_author=False,
            )

        if not user_ids:
            nagmsg = await ctx.reply(
                content="**⚠️ Warning**\nThis will untoss all users and end the session. Are you sure you want to do this?\nUse `untoss all` in the future to skip this warning.",
                mention_author=False,
            )
            await nagmsg.add_reaction("✅")
            await nagmsg.add_reaction("❎")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) in ["✅", "❎"]

            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=30.0, check=check
                )
            except asyncio.TimeoutError:
                return await nagmsg.edit(content="Operation timed out.", delete_after=5)

            if str(reaction) == "❎":
                return await nagmsg.edit(content="Operation cancelled.", delete_after=5)
            elif str(reaction) == "✅":
                user_ids = " ".join(
                    [
                        record[:-5]
                        for record in os.listdir(
                            f"{self.bot.server_data}/{ctx.guild.id}/toss/{ctx.channel.name}"
                        )
                    ]
                )
        elif user_ids == "all":
            user_ids = " ".join(
                [
                    record[:-5]
                    for record in os.listdir(
                        f"{self.bot.server_data}/{ctx.guild.id}/toss/{ctx.channel.name}"
                    )
                ]
            )

        user_id_list, invalid_ids = self.get_user_list(ctx, user_ids)
        staff_channel = get_config(ctx.guild.id, "staff", "staff_channel")
        toss_role = ctx.guild.get_role(get_config(ctx.guild.id, "toss", "toss_role"))
        output = ""

        for us in user_id_list:
            if us.id == self.bot.application_id:
                output += "\n" + random_bot_msg(ctx.author.name)
            elif us.id == ctx.author.id:
                output += "\n" + random_self_msg(ctx.author.name)
            elif (
                str(us.id) + ".json"
                not in os.listdir(
                    f"{self.bot.server_data}/{ctx.guild.id}/toss/{ctx.channel.name}"
                )
                and toss_role not in us.roles
            ):
                output += "\n" + f"{self.username_system(us)} is not already tossed."
            else:
                continue
            user_id_list.remove(us)
        if not user_id_list:
            return await ctx.reply(
                output
                + "\n\n"
                + "There's nobody left in the list to untoss, so nobody was untossed.",
                mention_author=False,
            )

        for us in user_id_list:
            try:
                with open(
                    rf"{self.bot.server_data}/{ctx.guild.id}/toss/{ctx.channel.name}/{us.id}.json"
                ) as file:
                    roles = json.loads(file.read())
                os.remove(
                    rf"{self.bot.server_data}/{ctx.guild.id}/toss/{ctx.channel.name}/{us.id}.json"
                )
            except FileNotFoundError:
                roles = []

            if roles:
                roles = [ctx.guild.get_role(r) for r in roles]
                for r in roles:
                    if not r or not r.is_assignable():
                        roles.remove(temp_role)
                await us.add_roles(
                    *roles,
                    reason=f"Untossed by {ctx.author} ({ctx.author.id})",
                    atomic=False,
                )
            await us.remove_roles(
                toss_role,
                reason=f"Untossed by {ctx.author} ({ctx.author.id})",
            )

            await ctx.channel.set_permissions(us, overwrite=None)

            if ctx.guild.id not in self.bot.tosscache:
                self.bot.tosscache[ctx.guild.id] = {}
            if ctx.channel.name not in self.bot.tosscache[ctx.guild.id]:
                self.bot.tosscache[ctx.guild.id][ctx.channel.name] = []
            self.bot.tosscache[ctx.guild.id][ctx.channel.name].append(us.id)

            restored = " ".join([f"`{rx.name}`" for rx in roles])
            output += (
                "\n"
                + f"{self.username_system(us)} has been untossed.\n**Roles Restored:** {restored}"
            )
            if staff_channel:
                await ctx.guild.get_channel(staff_channel).send(
                    f"{self.username_system(us)} has been untossed in {ctx.channel.mention} by {self.username_system(ctx.author)}.\n**Roles Restored:** {restored}"
                )

        if invalid_ids:
            output += (
                "\n\n"
                + "I was unable to untoss these users: "
                + ", ".join([str(iv) for iv in invalid_ids])
            )

        if not os.listdir(
            f"{self.bot.server_data}/{ctx.guild.id}/toss/{ctx.channel.name}"
        ):
            output += "\n\n" + "There is nobody left in this session."

        await ctx.reply(content=output, mention_author=False)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def close(self, ctx, archive=True):
        if not get_config(ctx.guild.id, "toss", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if ctx.channel.name not in get_config(ctx.guild.id, "toss", "toss_channels"):
            return await ctx.reply(
                content="This command must be run inside of a toss channel.",
                mention_author=False,
            )
        staff_channel = self.bot.get_channel(
            get_config(ctx.guild.id, "staff", "staff_channel")
        )
        log_channel = self.bot.get_channel(
            get_config(ctx.guild.id, "logs", "mlog_thread")
        )
        if archive:
            out = await log_whole_channel(self.bot, ctx.channel, zip_files=True)
            zipped_files = out[1]
            out = out[0]
            user = f"unspecified (logged by {ctx.author})"
            users = None
            try:
                users = [
                    ctx.guild.get_member(uid)
                    for uid in self.bot.tosscache[ctx.guild.id][ctx.channel.name]
                ]
                user = f"{users[0].name} {users[0].id}"
            except:
                return await ctx.reply(
                    content="The toss cache is empty. Untoss someone first.",
                    mention_author=False,
                )

            fn = ctx.message.created_at.strftime("%Y-%m-%d") + " " + str(user)
            reply = f"📕 Archived as: `{fn}.txt`"
            out += f"{ctx.message.created_at.strftime('%Y-%m-%d %H:%M')} {self.bot.user.name}: {reply}"
            out += "\nThis toss session had the following users:"
            for u in users:
                out += f"\n- {self.username_system(u)} ({u.id})"

            if get_config(ctx.guild.id, "archive", "enable"):
                credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    "data/service_account.json", "https://www.googleapis.com/auth/drive"
                )
                credentials.authorize(httplib2.Http())
                gauth = GoogleAuth()
                gauth.credentials = credentials
                drive = GoogleDrive(gauth)
                folder = get_config(ctx.guild.id, "archive", "drive_folder")

                f = drive.CreateFile(
                    {
                        "parents": [{"kind": "drive#fileLink", "id": folder}],
                        "title": fn + ".txt",
                    }
                )
                f.SetContentString(out)
                f.Upload()

                embed = stock_embed(self.bot)
                embed.title = "📁 Toss Channel Archived"
                embed.description = f"`#{ctx.channel.name}`'s session was archived by {ctx.author.mention} ({ctx.author.id})"
                embed.color = ctx.author.color
                embed.set_author(
                    name=ctx.author, icon_url=ctx.author.display_avatar.url
                )
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

                if staff_channel or log_channel:
                    channel = staff_channel if staff_channel else log_channel
                    await channel.send(embed=embed)
            else:
                if not staff_channel or log_channel:
                    return await ctx.reply(
                        content="You don't have anywhere for me to send the archives to.\nPlease configure either a staff channel or a moderation log channel, and then try again.",
                        mention_author=False,
                    )
                files = [discord.File(out, filename=fn + ".txt")]
                if zipped_files:
                    files.append(
                        discord.File(zipped_files, filename=fn + " (files).zip")
                    )
                channel = staff_channel if staff_channel else log_channel
                await channel.send(
                    content=f"📁 Toss Session Archive\n`#{ctx.channel.name}`'s session was archived by {ctx.author.mention} ({ctx.author.id})",
                    files=files,
                )
        await ctx.channel.delete(reason="Dishwasher Toss3")
        return

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.guild
            or message.author.bot
            or not get_config(message.guild.id, "toss", "enable")
            or self.is_rolebanned(message.author)
            or message.guild.get_role(
                get_config(message.guild.id, "staff", "staff_role")
            )
            in message.author.roles
        ):
            return
        staff_channel = message.guild.get_channel(
            get_config(message.guild.id, "staff", "staff_channel")
        )
        staff_role = message.guild.get_role(
            get_config(message.guild.id, "staff", "staff_role")
        )
        if message.author.id not in self.spamcounter:
            self.spamcounter[message.author.id] = {}
        if "original_message" not in self.spamcounter[message.author.id]:
            self.spamcounter[message.author.id]["original_message"] = message
            return
        cutoff_ts = self.spamcounter[message.author.id][
            "original_message"
        ].created_at + timedelta(seconds=10)
        if (
            message.content
            == self.spamcounter[message.author.id]["original_message"].content
            or self.principal_period(message.content)
            == self.spamcounter[message.author.id]["original_message"].content
            and message.created_at < cutoff_ts
        ):
            if "spamcounter" not in self.spamcounter[message.author.id]:
                self.spamcounter[message.author.id]["spamcounter"] = 1
            else:
                self.spamcounter[message.author.id]["spamcounter"] += 1
            if self.spamcounter[message.author.id]["spamcounter"] == 5:
                toss_channel = await self.new_session(message.guild)
                bad_roles_msg, prev_roles = await self.perform_toss(
                    message.author, message.guild.me, toss_channel
                )
                await toss_channel.set_permissions(message.author, read_messages=True)
                await toss_channel.send(
                    content=f"{message.author.mention}, you were rolebanned for spamming."
                )
                userlog(
                    message.guild.id,
                    message.author.id,
                    message.guild.me,
                    f"Tossed for hitting `5` spam messages.",
                    "tosses",
                )
                if staff_channel:
                    await staff_channel.send(
                        f"{staff_role.mention}\n"
                        f"{self.username_system(message.author)} has been tossed for hitting 5 spam messages.\n"
                        f"**ID:** {message.author.id}\n"
                        f"**Created:** <t:{int(message.author.created_at.timestamp())}:R> on <t:{int(message.author.created_at.timestamp())}:f>\n"
                        f"**Joined:** <t:{int(message.author.joined_at.timestamp())}:R> on <t:{int(message.author.joined_at.timestamp())}:f>\n"
                        f"**Previous Roles:**{prev_roles}{bad_roles_msg}\n\n"
                        f"{toss_channel.mention}"
                    )
                return
        else:
            self.spamcounter[message.author.id]["original_message"] = message
            self.spamcounter[message.author.id]["spamcounter"] = 0
            return

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not get_config(member.guild.id, "toss", "enable"):
            return
        staff_channel = member.guild.get_channel(
            get_config(member.guild.id, "staff", "staff_channel")
        )
        try:
            for p in os.listdir(f"{self.bot.server_data}/{member.guild.id}/toss"):
                for c in os.listdir(
                    f"{self.bot.server_data}/{member.guild.id}/toss/{p}"
                ):
                    if member.id == c[:-5]:
                        session = p
                        break
                if session:
                    break
        except:
            return
        if not session:
            return

        toss_channel = await self.new_session(message.guild)
        bad_roles_msg, prev_roles = await self.perform_toss(
            message.author, message.guild.me, toss_channel
        )
        await toss_channel.set_permissions(message.author, read_messages=True)
        await toss_channel.send(
            content=f"{member.mention}, you were previously rolebanned. As such, a new session has been made for you here."
        )
        os.replace(
            f"{self.bot.server_data}/{member.guild.id}/toss/{session}/{member.id}",
            f"{self.bot.server_data}/{member.guild.id}/toss/{toss_channel.name}/{member.id}",
        )
        if staff_channel:
            await staff_channel.send(
                content=f"🔁 {self.username_system(member)} ({member.id}) rejoined while tossed. Continuing in {toss_channel.mention}..."
            )
        return

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if not get_config(member.guild.id, "toss", "enable"):
            return
        if self.is_rolebanned(member):
            session = None
            try:
                for p in os.listdir(f"{self.bot.server_data}/{member.guild.id}/toss"):
                    for c in os.listdir(
                        f"{self.bot.server_data}/{member.guild.id}/toss/{p}"
                    ):
                        if member.id == c[:-5]:
                            self.bot.tosscache[member.guild.id][p].append(member.id)
                            os.replace(
                                f"{self.bot.server_data}/{after.guild.id}/toss/{p}/{c}",
                                f"{self.bot.server_data}/{after.guild.id}/toss/left_while_tossed/{c}",
                            )
                            for channel in member.guild.channels:
                                if channel.name == p:
                                    session = p
                            break
                    if session:
                        break
            except:
                return
            staff_channel = member.guild.get_channel(
                get_config(member.guild.id, "staff", "staff_channel")
            )
            try:
                await member.guild.fetch_ban(member)
            except discord.NotFound:
                out = f"🚪 {self.username_system(member)} left while tossed."
                if staff_channel:
                    await staff_channel.send(out)
                if session:
                    await session.send(out)
            else:
                out = f"🔨 {self.username_system(member)} got banned while tossed."
                if staff_channel:
                    await staff_channel.send(out)
                if session:
                    await session.send(out)

    @Cog.listener()
    async def on_member_update(self, before, after):
        await self.bot.wait_until_ready()
        if not get_config(after.guild.id, "toss", "enable"):
            return
        if self.is_rolebanned(before) and not self.is_rolebanned(after):
            try:
                for p in os.listdir(f"{self.bot.server_data}/{after.guild.id}/toss"):
                    for c in os.listdir(
                        f"{self.bot.server_data}/{after.guild.id}/toss/{p}"
                    ):
                        if after.id == c[:-5]:
                            self.bot.tosscache[after.guild.id][p].append(after.id)
                            os.remove(
                                f"{self.bot.server_data}/{after.guild.id}/toss/{p}/{c}"
                            )
            except:
                return

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.wait_until_ready()
        if (
            get_config(channel.guild.id, "toss", "enable")
            and channel.name in get_config(channel.guild.id, "toss", "toss_channels")
            and channel.guild.id in self.bot.tosscache
            and channel.name in self.bot.tosscache[channel.guild.id]
        ):
            self.bot.tosscache[channel.guild.id][channel.name] = []


async def setup(bot):
    await bot.add_cog(ModToss(bot))
