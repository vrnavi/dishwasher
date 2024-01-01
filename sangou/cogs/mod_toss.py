# This Cog contained code from Tosser2, which was made by OblivionCreator.
import discord
import json
import os
import asyncio
import random
import zipfile
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord.ext.commands import Cog
from io import BytesIO
from helpers.checks import ismod
from helpers.datafiles import add_userlog, toss_userlog, get_tossfile, set_tossfile
from helpers.placeholders import random_msg
from helpers.archive import log_whole_channel, get_members
from helpers.embeds import stock_embed, username_system, mod_embed
from helpers.sv_config import get_config


class ModToss(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.busy = False
        self.spamcounter = {}
        self.nocfgmsg = "Tossing isn't enabled for this server."

    def enabled(self, gid):
        if (
            not get_config(gid, "toss", "tossrole")
            or not get_config(gid, "toss", "tosscategory")
            or not get_config(gid, "toss", "tosschannels")
        ):
            return False
        else:
            return True

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

    def is_rolebanned(self, member, hard=True):
        roleban = [
            r
            for r in member.guild.roles
            if r.id == get_config(member.guild.id, "toss", "tossrole")
        ]
        if roleban:
            if get_config(member.guild.id, "toss", "tossrole") in [
                r.id for r in member.roles
            ]:
                if hard:
                    return len([r for r in member.roles if not (r.managed)]) == 2
                return True

    def get_session(self, member):
        tosses = get_tossfile(member.guild.id, "tosses")
        if not tosses:
            return None
        session = None
        if "LEFTGUILD" in tosses and str(member.id) in tosses["LEFTGUILD"]:
            session = False
        for channel in tosses:
            if channel == "LEFTGUILD":
                continue
            if str(member.id) in tosses[channel]["tossed"]:
                session = channel
                break
        return session

    async def new_session(self, guild):
        staff_role = guild.get_role(
            get_config(guild.id, "staff", "modrole")
            if get_config(guild.id, "staff", "modrole")
            else get_config(guild.id, "staff", "adminrole")
        )
        bot_role = guild.get_role(get_config(guild.id, "staff", "botrole"))
        tosses = get_tossfile(guild.id, "tosses")

        for c in get_config(guild.id, "toss", "tosschannels"):
            if c not in [g.name for g in guild.channels]:
                if c not in tosses:
                    tosses[c] = {"tossed": {}, "untossed": [], "left": []}
                    set_tossfile(guild.id, "tosses", json.dumps(tosses))

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    guild.me: discord.PermissionOverwrite(read_messages=True),
                    staff_role: discord.PermissionOverwrite(read_messages=True),
                    bot_role: discord.PermissionOverwrite(read_messages=True),
                }
                toss_channel = await guild.create_text_channel(
                    c,
                    reason="Sangou Toss",
                    category=guild.get_channel(
                        get_config(guild.id, "toss", "tosscategory")
                    ),
                    overwrites=overwrites,
                    topic=get_config(guild.id, "toss", "tosstopic"),
                )

                return toss_channel

    async def perform_toss(self, user, staff, toss_channel):
        toss_role = user.guild.get_role(get_config(user.guild.id, "toss", "tossrole"))
        roles = []
        for rx in user.roles:
            if rx != user.guild.default_role and rx != toss_role:
                roles.append(rx)

        tosses = get_tossfile(user.guild.id, "tosses")
        tosses[toss_channel.name]["tossed"][str(user.id)] = [role.id for role in roles]
        set_tossfile(user.guild.id, "tosses", json.dumps(tosses))

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
    @commands.check(ismod)
    @commands.bot_has_permissions(embed_links=True)
    @commands.command()
    async def sessions(self, ctx):
        """This shows the open toss sessions.

        There's not much more to this.

        No arguments."""
        if not self.enabled(ctx.guild.id):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        embed = stock_embed(self.bot)
        embed.title = "👁‍🗨 Toss Channel Sessions..."
        embed.color = ctx.author.color
        tosses = get_tossfile(ctx.guild.id, "tosses")

        for c in get_config(ctx.guild.id, "toss", "tosschannels"):
            if c in [g.name for g in ctx.guild.channels]:
                if c not in tosses:
                    embed.add_field(
                        name=f"🟡 #{c}",
                        value="__Empty__\n> Please delete the channel.",
                        inline=False,
                    )
                else:
                    userlist = "\n".join(
                        [
                            f"> {self.username_system(user)}"
                            for user in [
                                await self.bot.fetch_user(str(u))
                                for u in tosses[c]["tossed"].keys()
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
    @commands.check(ismod)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.command(aliases=["roleban"])
    async def toss(self, ctx, users: commands.Greedy[discord.Member]):
        """This tosses a user.

        Please refer to the tossing section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-tossing-system/).

        - `users`
        The users to toss."""
        if not self.enabled(ctx.guild.id):
            return await ctx.reply(self.nocfgmsg, mention_author=False)

        tosses = get_tossfile(ctx.guild.id, "tosses")

        staff_channel = get_config(ctx.guild.id, "staff", "staffchannel")
        modlog_channel = get_config(ctx.guild.id, "logging", "modlog")
        staff_role = ctx.guild.get_role(
            get_config(ctx.guild.id, "staff", "modrole")
            if get_config(ctx.guild.id, "staff", "modrole")
            else get_config(ctx.guild.id, "staff", "adminrole")
        )
        toss_role = ctx.guild.get_role(get_config(ctx.guild.id, "toss", "tossrole"))

        output = ""
        invalid = []

        for us in users:
            if us.id == ctx.author.id:
                output += "\n" + random_msg(
                    "warn_targetself", authorname=ctx.author.name
                )
            elif us.id == self.bot.application_id:
                output += "\n" + random_msg(
                    "warn_targetbot", authorname=ctx.author.name
                )
            elif self.get_session(us) and toss_role in us.roles:
                output += "\n" + f"{self.username_system(us)} is already tossed."
            else:
                continue
            users.remove(us)
        if not users:
            return await ctx.reply(
                output + "\n\n" + "There's nobody left to toss, so nobody was tossed.",
                mention_author=False,
            )

        if ctx.channel.name in get_config(ctx.guild.id, "toss", "tosschannels"):
            addition = True
            toss_channel = ctx.channel
        elif all(
            [
                c in [g.name for g in ctx.guild.channels]
                for c in get_config(ctx.guild.id, "toss", "tosschannels")
            ]
        ):
            return await ctx.reply(
                content="I cannot toss them. All sessions are currently in use.",
                mention_author=False,
            )
        else:
            addition = False
            toss_channel = await self.new_session(ctx.guild)

        toss_pings = ", ".join([us.mention for us in users])

        for us in users:
            try:
                bad_roles_msg, prev_roles = await self.perform_toss(
                    us, ctx.author, toss_channel
                )
                await toss_channel.set_permissions(us, read_messages=True)
            except commands.MissingPermissions:
                invalid.append(us.name)
                continue

            toss_userlog(
                ctx.guild.id,
                us.id,
                ctx.author,
                ctx.message.jump_url,
                toss_channel.id,
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

        output += "\n" + "\n".join(
            [f"{self.username_system(us)} has been tossed." for us in users]
        )

        if invalid:
            output += (
                "\n\n"
                + "I was unable to toss these users: "
                + ", ".join([str(iv) for iv in invalid])
            )

        output += (
            "\n\nPlease change the topic. **Discussion of tossed users may lead to warnings.**"
            if ctx.channel.permissions_for(ctx.guild.default_role).read_messages
            or len(ctx.channel.members) >= 100
            else ""
        )
        await ctx.reply(content=output, mention_author=False)

        if not addition:
            await toss_channel.send(
                f"{toss_pings}\nYou were tossed by {self.pacify_name(ctx.author.global_name) if ctx.author.global_name else self.pacify_name(ctx.author.name)}.\n"
                '> *For your reference, a "toss" is where a Staff member wishes to speak with you, one on one.*'
            )

            def check(m):
                return m.author in users and m.channel == toss_channel

            try:
                msg = await self.bot.wait_for("message", timeout=300, check=check)
            except asyncio.TimeoutError:
                pokemsg = await toss_channel.send(ctx.author.mention)
                await pokemsg.edit(content="⏰", delete_after=5)
            except discord.NotFound:
                # The channel probably got deleted before anything could happen.
                return
            else:
                pokemsg = await toss_channel.send(ctx.author.mention)
                await pokemsg.edit(content="🫳⏰", delete_after=5)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(ismod)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.bot_has_permissions(manage_roles=True, manage_channels=True)
    @commands.command(aliases=["unroleban"])
    async def untoss(self, ctx, users: commands.Greedy[discord.Member] = None):
        """This untosses a user.

        Please refer to the tossing section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-tossing-system/).

        - `users`
        The users to untoss. Optional."""
        if not self.enabled(ctx.guild.id):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if ctx.channel.name not in get_config(ctx.guild.id, "toss", "tosschannels"):
            return await ctx.reply(
                content="This command must be run inside of a toss channel.",
                mention_author=False,
            )

        tosses = get_tossfile(ctx.guild.id, "tosses")
        if not users:
            users = [
                ctx.guild.get_member(int(u))
                for u in tosses[ctx.channel.name]["tossed"].keys()
            ]

        staff_channel = get_config(ctx.guild.id, "staff", "staffchannel")
        toss_role = ctx.guild.get_role(get_config(ctx.guild.id, "toss", "tossrole"))
        output = ""
        invalid = []

        for us in users:
            if us.id == self.bot.application_id:
                output += "\n" + random_msg(
                    "warn_targetbot", authorname=ctx.author.name
                )
            elif us.id == ctx.author.id:
                output += "\n" + random_msg(
                    "warn_targetself", authorname=ctx.author.name
                )
            elif (
                str(us.id) not in tosses[ctx.channel.name] and toss_role not in us.roles
            ):
                output += "\n" + f"{self.username_system(us)} is not already tossed."
            else:
                continue
            users.remove(us)
        if not users:
            return await ctx.reply(
                output
                + "\n\n"
                + "There's nobody left to untoss, so nobody was untossed.",
                mention_author=False,
            )

        for us in users:
            self.busy = True
            roles = tosses[ctx.channel.name]["tossed"][str(us.id)]
            if us.id not in tosses[ctx.channel.name]["untossed"]:
                tosses[ctx.channel.name]["untossed"].append(us.id)
            del tosses[ctx.channel.name]["tossed"][str(us.id)]

            if roles:
                roles = [ctx.guild.get_role(r) for r in roles]
                for r in roles:
                    if not r or not r.is_assignable():
                        roles.remove(r)
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

            restored = " ".join([f"`{rx.name}`" for rx in roles])
            output += (
                "\n"
                + f"{self.username_system(us)} has been untossed.\n**Roles Restored:** {restored}"
            )
            if staff_channel:
                await ctx.guild.get_channel(staff_channel).send(
                    f"{self.username_system(us)} has been untossed in {ctx.channel.mention} by {self.username_system(ctx.author)}.\n**Roles Restored:** {restored}"
                )

        set_tossfile(ctx.guild.id, "tosses", json.dumps(tosses))
        self.busy = False

        if invalid:
            output += (
                "\n\n"
                + "I was unable to untoss these users: "
                + ", ".join([str(iv) for iv in invalid])
            )

        if not tosses[ctx.channel.name]:
            output += "\n\n" + "There is nobody left in this session."

        await ctx.reply(content=output, mention_author=False)

    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.command()
    async def close(self, ctx, archive=True):
        """This closes a toss session.

        Please refer to the tossing section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-tossing-system/).

        - `archive`
        Whether to archive the session or not. Optional."""
        if not self.enabled(ctx.guild.id):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if ctx.channel.name not in get_config(ctx.guild.id, "toss", "tosschannels"):
            return await ctx.reply(
                content="This command must be run inside of a toss channel.",
                mention_author=False,
            )

        staff_channel = self.bot.get_channel(
            get_config(ctx.guild.id, "staff", "staffchannel")
        )
        log_channel = self.bot.get_channel(
            get_config(ctx.guild.id, "logging", "modlog")
        )
        tosses = get_tossfile(ctx.guild.id, "tosses")

        if tosses[ctx.channel.name]["tossed"]:
            return await ctx.reply(
                content="You must untoss everyone first!", mention_author=True
            )

        if archive:
            if not staff_channel or not log_channel:
                return await ctx.reply(
                    content="You don't have anywhere for me to send the archives to.\nPlease configure either a staff channel or a moderation log channel, and then try again.",
                    mention_author=False,
                )

            async with ctx.channel.typing():
                dotraw, dotzip = await log_whole_channel(
                    self.bot, ctx.channel, zip_files=True
                )

            users = [
                await self.bot.fetch_user(uid)
                for uid in tosses[ctx.channel.name]["untossed"]
                + tosses[ctx.channel.name]["left"]
            ]
            user = f""

            filename = (
                ctx.message.created_at.astimezone().strftime("%m-%d-%Y")
                + f" {ctx.channel.name} {ctx.channel.id}"
            )
            reply = (
                f"📕 I've archived that as: `{filename}.txt`\nThis toss session had the following users:\n- "
                + "\n- ".join([f"{self.username_system(u)} ({u.id})" for u in users])
            )
            dotraw += f"\n{ctx.message.created_at.astimezone().strftime('%m/%d/%Y %H:%M')} {self.bot.user} [BOT]\n{reply}"

            if not os.path.exists(
                f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}"
            ):
                os.makedirs(
                    f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}"
                )
            with open(
                f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}/{filename}.txt",
                "w",
            ) as txtfile:
                txtfile.write(dotraw)
            if dotzip:
                with open(
                    f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}/{filename} (files).zip",
                    "w",
                ) as zipfile:
                    zipfile.write(dotzip.getbuffer())

            embed = stock_embed(self.bot)
            embed.title = "📦 Toss Session Closed"
            embed.description = f"`#{ctx.channel.name}`'s session was closed by {ctx.author.mention} ({ctx.author.id})."
            embed.color = ctx.author.color
            embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)

            embed.add_field(
                name="🗒️ Text",
                value=f"{filename}.txt\n"
                + f"`"
                + str(len(dotraw.split("\n")))
                + "` lines, "
                + f"`{len(dotraw.split())}` words, "
                + f"`{len(dotraw)}` characters.",
                inline=True,
            )
            if dotzip:
                embed.add_field(
                    name="📁 Files",
                    value=f"{filename} (files).zip"
                    + "\n"
                    + f"`{len(zipfile.ZipFile(dotzip, 'w', zipfile.ZIP_DEFLATED).infolist())}` files in the zip file.",
                    inline=True,
                )

            channel = staff_channel if staff_channel else log_channel
            await channel.send(embed=embed)

        del tosses[ctx.channel.name]
        set_tossfile(ctx.guild.id, "tosses", json.dumps(tosses))

        await ctx.channel.delete(reason="Sangou Toss")
        return

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.guild
            or message.author.bot
            or not self.enabled(message.guild.id)
            or self.is_rolebanned(message.author)
            or self.get_session(message.author)
            or message.guild.get_role(get_config(message.guild.id, "staff", "modrole"))
            in message.author.roles
            or message.guild.get_role(
                get_config(message.guild.id, "staff", "adminrole")
            )
            in message.author.roles
        ):
            return

        staff_channel = message.guild.get_channel(
            get_config(message.guild.id, "staff", "staffchannel")
        )
        staff_role = message.guild.get_role(
            get_config(message.guild.id, "staff", "modrole")
            if get_config(message.guild.id, "staff", "modrole")
            else get_config(message.guild.id, "staff", "adminrole")
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
            any(
                (
                    message.content
                    == self.spamcounter[message.author.id]["original_message"].content,
                    self.principal_period(message.content)
                    == self.spamcounter[message.author.id]["original_message"].content,
                )
            )
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

                toss_userlog(
                    message.guild.id,
                    message.author.id,
                    message.guild.me,
                    message.jump_url,
                    toss_channel.id,
                )
                if staff_channel:
                    await staff_channel.send(
                        f"{staff_role.mention}\n"
                        f"{self.username_system(message.author)} has been tossed for hitting 5 spam messages. {message.jump_url}\n"
                        f"**ID:** {message.author.id}\n"
                        f"**Created:** <t:{int(message.author.created_at.timestamp())}:R> on <t:{int(message.author.created_at.timestamp())}:f>\n"
                        f"**Joined:** <t:{int(message.author.joined_at.timestamp())}:R> on <t:{int(message.author.joined_at.timestamp())}:f>\n"
                        f"**Previous Roles:**{prev_roles}{bad_roles_msg}\n\n"
                        f"{toss_channel.mention}"
                    )
                await message.reply(
                    content=f"{self.username_system(message.author)} has been tossed for hitting 5 spam messages.",
                    mention_author=False,
                )
                return
        else:
            self.spamcounter[message.author.id]["original_message"] = message
            self.spamcounter[message.author.id]["spamcounter"] = 0
            return

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild.id):
            return
        staff_channel = member.guild.get_channel(
            get_config(member.guild.id, "staff", "staffchannel")
        )

        tosses = get_tossfile(member.guild.id, "tosses")
        toss_channel = None

        if "LEFTGUILD" in tosses and str(member.id) in tosses["LEFTGUILD"]:
            for channel in tosses:
                if "left" in tosses[channel] and member.id in tosses[channel]["left"]:
                    toss_channel = discord.utils.get(
                        member.guild.channels, name=channel
                    )
                    break
            if toss_channel:
                toss_role = member.guild.get_role(
                    get_config(member.guild.id, "toss", "tossrole")
                )
                await member.add_roles(toss_role, reason="User tossed.")
                tosses[toss_channel.name]["tossed"][str(member.id)] = tosses[
                    "LEFTGUILD"
                ][str(member.id)]
                tosses[toss_channel.name]["left"].remove(member.id)
            else:
                toss_channel = await self.new_session(member.guild)
                bad_roles_msg, prev_roles = await self.perform_toss(
                    member, member.guild.me, toss_channel
                )
                tosses = get_tossfile(member.guild.id, "tosses")
                tosses[toss_channel.name]["tossed"][str(member.id)] = tosses[
                    "LEFTGUILD"
                ][str(member.id)]
        else:
            return

        del tosses["LEFTGUILD"][str(member.id)]
        if not tosses["LEFTGUILD"]:
            del tosses["LEFTGUILD"]
        set_tossfile(member.guild.id, "tosses", json.dumps(tosses))

        await toss_channel.set_permissions(member, read_messages=True)
        await toss_channel.send(
            content=f"🔁 {self.username_system(member)} rejoined while tossed."
        )
        if staff_channel:
            await staff_channel.send(
                content=f"🔁 {self.username_system(member)} ({member.id}) rejoined while tossed. Continuing in {toss_channel.mention}..."
            )
        return

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild.id):
            return

        session = self.get_session(member)
        if not session:
            return

        tosses = get_tossfile(member.guild.id, "tosses")
        if "LEFTGUILD" not in tosses:
            tosses["LEFTGUILD"] = {}
        tosses["LEFTGUILD"][str(member.id)] = tosses[session]["tossed"][str(member.id)]
        tosses[session]["left"].append(member.id)
        del tosses[session]["tossed"][str(member.id)]
        set_tossfile(member.guild.id, "tosses", json.dumps(tosses))

        staff_channel = member.guild.get_channel(
            get_config(member.guild.id, "staff", "staffchannel")
        )
        toss_channel = discord.utils.get(member.guild.channels, name=session)
        try:
            await member.guild.fetch_ban(member)
            out = f"🔨 {self.username_system(member)} got banned while tossed."
        except discord.NotFound:
            out = f"🚪 {self.username_system(member)} left while tossed."
        except discord.Forbidden:
            out = f"❓ {self.username_system(member)} was removed from the server.\nI do not have Audit Log permissions to tell why."
        if staff_channel:
            await staff_channel.send(out)
        if toss_channel:
            await toss_channel.send(out)

    @Cog.listener()
    async def on_member_update(self, before, after):
        await self.bot.wait_until_ready()
        if not self.enabled(after.guild.id):
            return
        while self.busy:
            await asyncio.sleep(1)
        if self.is_rolebanned(before) and not self.is_rolebanned(after):
            session = self.get_session(after)
            if not session:
                return

            tosses = get_tossfile(after.guild.id, "tosses")
            tosses[session]["untossed"].append(after.id)
            del tosses[session]["tossed"][str(after.id)]
            set_tossfile(after.guild.id, "tosses", json.dumps(tosses))

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.wait_until_ready()
        if self.enabled(channel.guild.id) and channel.name in get_config(
            channel.guild.id, "toss", "tosschannels"
        ):
            tosses = get_tossfile(channel.guild.id, "tosses")
            if channel.name not in tosses:
                return
            del tosses[channel.name]
            set_tossfile(channel.guild.id, "tosses", json.dumps(tosses))


async def setup(bot):
    await bot.add_cog(ModToss(bot))
