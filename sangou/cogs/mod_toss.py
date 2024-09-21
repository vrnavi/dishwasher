# Imports.
import discord
import json
import os
import asyncio
import zipfile
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord.ext.commands import Cog
from io import BytesIO
from helpers.checks import ismod
from helpers.datafiles import add_userlog, toss_userlog, get_file, set_file
from helpers.placeholders import random_msg
from helpers.archive import log_channel
from helpers.embeds import (
    stock_embed,
    mod_embed,
    author_embed,
    createdat_embed,
    joinedat_embed,
)
from helpers.sv_config import get_config


class ModToss(Cog):
    """
    The big boss toss function. It's huge.
    """

    def __init__(self, bot):
        self.bot = bot
        self.busy = {}
        self.spamcounter = {}
        self.nocfgmsg = "Tossing isn't enabled for this server."

    def enabled(self, g):
        return all(
            (
                self.bot.pull_role(g, get_config(g.id, "toss", "tossrole")),
                self.bot.pull_category(g, get_config(g.id, "toss", "tosscategory")),
                get_config(g.id, "toss", "tosschannels"),
                any(
                    [
                        self.bot.pull_role(g, get_config(g.id, "staff", "adminrole")),
                        self.bot.pull_role(g, get_config(g.id, "staff", "modrole")),
                    ]
                ),
                any(
                    [
                        self.bot.pull_channel(
                            g, get_config(g.id, "toss", "notificationchannel")
                        ),
                        self.bot.pull_channel(
                            g, get_config(g.id, "staff", "staffchannel")
                        ),
                    ]
                ),
            )
        )

    def username_system(self, user):
        if isinstance(user, int):
            return user
        return (
            f"**{self.bot.pacify_name(user.global_name)}**"
            + f" [{self.bot.pacify_name(str(user))}]"
            if user.global_name
            else f"**{self.bot.pacify_name(str(user))}**"
        )

    def is_rolebanned(self, member):
        return (
            self.bot.pull_role(
                member.guild, get_config(member.guild.id, "toss", "tossrole")
            )
            in member.roles
        )
        # this code temporarily disabled since it was interfering with users having multiple roles that the bot can't control
        # note to self: add feature later to try and remove roles on role change if it can, for server guide roles
        # if (
        #     self.bot.pull_role(
        #         member.guild, get_config(member.guild.id, "toss", "tossrole")
        #     )
        #     in member.roles
        # ):
        #     if hard:
        #         return len([r for r in member.roles if not (r.managed)]) == 2
        #     return True
        # else:
        #     return False

    def get_session(self, member):
        tosses = get_file("tosses", f"servers/{member.guild.id}/toss")
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
        adminrole = self.bot.pull_role(
            guild, get_config(guild.id, "staff", "adminrole")
        )
        modrole = self.bot.pull_role(guild, get_config(guild.id, "staff", "modrole"))
        botrole = self.bot.pull_role(guild, get_config(guild.id, "staff", "botrole"))
        tosses = get_file("tosses", f"servers/{guild.id}/toss")

        if all(
            [
                c.lower() in [g.name for g in guild.text_channels]
                for c in get_config(guild.id, "toss", "tosschannels")
            ]
        ):
            return None

        for c in get_config(guild.id, "toss", "tosschannels"):
            c = c.lower()
            if c not in [g.name for g in guild.channels]:
                if c not in tosses:
                    tosses[c] = {"tossed": {}, "untossed": [], "left": []}
                    set_file("tosses", json.dumps(tosses), f"servers/{guild.id}/toss")

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False)
                }
                for item in [adminrole, modrole, botrole, guild.me]:
                    if not item:
                        continue
                    overwrites[item] = discord.PermissionOverwrite(read_messages=True)
                tosschannel = await guild.create_text_channel(
                    c,
                    reason="Sangou Toss",
                    category=self.bot.pull_category(
                        guild, get_config(guild.id, "toss", "tosscategory")
                    ),
                    overwrites=overwrites,
                    topic=get_config(guild.id, "toss", "tosstopic"),
                )

                return tosschannel

    async def perform_toss(self, user, staff, tosschannel):
        tossrole = self.bot.pull_role(
            user.guild, get_config(user.guild.id, "toss", "tossrole")
        )
        prevroles = [
            rx
            for rx in user.roles
            if rx != user.guild.default_role and rx != tossrole and rx.is_assignable()
        ]
        failroles = [
            rx
            for rx in user.roles
            if rx != user.guild.default_role
            and rx != tossrole
            and not rx.is_assignable()
        ]

        tosses = get_file("tosses", f"servers/{user.guild.id}/toss")
        tosses[tosschannel.name]["tossed"][str(user.id)] = [
            role.id for role in prevroles
        ]
        set_file("tosses", json.dumps(tosses), f"servers/{user.guild.id}/toss")

        if prevroles:
            await user.remove_roles(
                *prevroles,
                reason=f"User tossed by {staff} ({staff.id})",
                atomic=False,
            )
        await user.add_roles(tossrole, reason="User tossed.")

        return failroles, prevroles

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["tossed", "session"])
    async def sessions(self, ctx):
        """This shows the open toss sessions.

        Use this in a toss channel to show who's in it.

        No arguments."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        embed = stock_embed(self.bot)
        embed.title = "👁‍🗨 Toss Channel Sessions..."
        embed.color = ctx.author.color
        tosses = get_file("tosses", f"servers/{ctx.guild.id}/toss")

        if ctx.channel.name in [
            c.lower() for c in get_config(ctx.guild.id, "toss", "tosschannels")
        ]:
            channels = [ctx.channel.name]
        else:
            channels = [
                c.lower() for c in get_config(ctx.guild.id, "toss", "tosschannels")
            ]

        for c in channels:
            if c in [g.name for g in ctx.guild.channels]:
                if c not in tosses or not tosses[c]["tossed"]:
                    embed.add_field(
                        name=f"🟡 #{c}",
                        value="__Empty__\n> Please close the channel.",
                        inline=True,
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
                        inline=True,
                    )
            else:
                embed.add_field(name=f"🟢 #{c}", value="__Available__", inline=True)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.bot_has_guild_permissions(
        manage_roles=True, manage_channels=True, add_reactions=True
    )
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["roleban"])
    async def toss(self, ctx, users: commands.Greedy[discord.Member]):
        """This tosses a user.

        Please refer to the tossing section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-tossing-system/).

        - `users`
        The users to toss."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)

        # Get roles, channels, and configs.
        tossrole = self.bot.pull_role(
            ctx.guild, get_config(ctx.guild.id, "toss", "tossrole")
        )
        notifychannel = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "toss", "notificationchannel")
        )
        if not notifychannel:
            notifychannel = self.bot.pull_channel(
                ctx.guild, get_config(ctx.guild.id, "staff", "staffchannel")
            )
        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )

        # User validation.
        errors = ""
        for us in users:
            if us.id == ctx.author.id:
                errors += f"\n- {self.username_system(us)}\n> You cannot toss yourself."
            elif us.id == ctx.me.id:
                errors += f"\n- {self.username_system(us)}\n> You cannot toss myself."
            elif us.top_role > ctx.author.top_role:
                errors += f"\n- {self.username_system(us)}\n> You cannot toss someone higher than yourself."
            elif us.top_role > ctx.me.top_role:
                errors += f"\n- {self.username_system(us)}\n> You cannot toss someone higher than myself."
            elif self.get_session(us) and tossrole in us.roles:
                errors += (
                    f"\n- {self.username_system(us)}\n> This user is already tossed."
                )
            else:
                continue
            users.remove(us)
        if not users:
            await ctx.message.add_reaction("🚫")
            return await notifychannel.send(
                f"Error in toss command from {ctx.author.mention}...\n- Nobody was tossed.\n```diff"
                + errors
                + "\n```\n"
            )

        # Channel validation.
        if ctx.channel.name in [
            c.lower() for c in get_config(ctx.guild.id, "toss", "tosschannels")
        ]:
            addition = True
            tosschannel = ctx.channel
        else:
            addition = False
            tosschannel = await self.new_session(ctx.guild)
            if not tosschannel:
                await ctx.message.add_reaction("🚫")
                return await notifychannel.send(
                    f"Error in toss command from {ctx.author.mention}...\n- No toss channels available.\n```diff"
                    + errors
                    + "\n```\n"
                )

        # Actually toss.
        for us in users:
            try:
                failroles, prevroles = await self.perform_toss(
                    us, ctx.author, tosschannel
                )
                await tosschannel.set_permissions(us, read_messages=True)
            except commands.MissingPermissions:
                errors += f"\n- {self.username_system(us)}\n  Missing permissions to toss this user."
                continue

            toss_userlog(
                ctx.guild.id,
                us.id,
                ctx.author,
                ctx.message.jump_url,
                tosschannel.id,
            )

            # Notifications.
            embed = stock_embed(self.bot)
            author_embed(embed, us, True)
            embed.color = ctx.author.color
            embed.title = "🚷 Toss"
            embed.description = f"{us.mention} was tossed by {ctx.author.mention} [`#{ctx.channel.name}`] [[Jump]({ctx.message.jump_url})]\n> This toss takes place in {tosschannel.mention}..."
            createdat_embed(embed, us)
            joinedat_embed(embed, us)
            if prevroles:
                prevlist = ",".join(
                    reversed(["<@&" + str(role.id) + ">" for role in prevroles])
                )
            else:
                prevlist = "None"
            embed.add_field(
                name="🎨 Previous Roles",
                value=prevlist,
                inline=False,
            )
            if failroles:
                embed.add_field(
                    name="🚫 Failed Roles",
                    value=",".join(
                        reversed(["<@&" + str(role.id) + ">" for role in failroles])
                    ),
                    inline=False,
                )
            await notifychannel.send(embed=embed)

            if mlog and mlog != notifychannel:
                embed = stock_embed(self.bot)
                embed.color = discord.Color.from_str("#FF0000")
                embed.title = "🚷 Toss"
                embed.description = f"{us.mention} was tossed by {ctx.author.mention} [`#{ctx.channel.name}`] [[Jump]({ctx.message.jump_url})]"
                mod_embed(embed, us, ctx.author)
                await mlog.send(embed=embed)

        await ctx.message.add_reaction("🚷")

        # Error notification.
        if errors:
            return await notifychannel.send(
                f"Error in toss command from {ctx.author.mention}...\n- Some users could not be tossed.\n```diff"
                + errors
                + "\n```\n"
            )
            await ctx.message.add_reaction("⚠️")

        # Start of session notification and timer.
        if not addition:
            toss_pings = ", ".join([us.mention for us in users])
            await tosschannel.send(
                f"{toss_pings}\nYou were tossed by {self.bot.pacify_name(ctx.author.display_name)}.\n"
                '> *For your reference, a "toss" is where a Staff member wishes to speak with you, one on one. This session will be archived for Staff only once completed.*'
            )

            def check(m):
                return m.author in users and m.channel == tosschannel

            try:
                msg = await self.bot.wait_for("message", timeout=300, check=check)
            except asyncio.TimeoutError:
                try:
                    pokemsg = await tosschannel.send(ctx.author.mention)
                    await pokemsg.edit(content="⏰", delete_after=5)
                except discord.NotFound:
                    return
            except discord.NotFound:
                return
            else:
                pokemsg = await tosschannel.send(ctx.author.mention)
                await pokemsg.edit(content="🫳⏰", delete_after=5)

    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.bot_has_guild_permissions(manage_roles=True, manage_channels=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["unroleban"])
    async def untoss(self, ctx, users: commands.Greedy[discord.Member] = None):
        """This untosses a user.

        Please refer to the tossing section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-tossing-system/).

        - `users`
        The users to untoss. Optional."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if ctx.channel.name not in [
            c.lower() for c in get_config(ctx.guild.id, "toss", "tosschannels")
        ]:
            return await ctx.reply(
                content="This command must be run inside of a toss channel.",
                mention_author=False,
            )

        # Get roles, channels, and configs.
        tosses = get_file("tosses", f"servers/{ctx.guild.id}/toss")
        if not users:
            users = [
                ctx.guild.get_member(int(u))
                for u in tosses[ctx.channel.name]["tossed"].keys()
            ]
        notifychannel = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "toss", "notificationchannel")
        )
        if not notifychannel:
            notifychannel = self.bot.pull_channel(
                ctx.guild, get_config(ctx.guild.id, "staff", "staffchannel")
            )
        tossrole = self.bot.pull_role(
            ctx.guild, get_config(ctx.guild.id, "toss", "tossrole")
        )

        # User validation.
        errors = ""
        for us in users:
            if not us:
                continue
            elif us.id == ctx.author.id:
                errors += (
                    f"\n- {self.username_system(us)}\n> You cannot untoss yourself."
                )
            elif us.id == ctx.me.id:
                errors += f"\n- {self.username_system(us)}\n> You cannot untoss myself."
            elif us.top_role > ctx.author.top_role:
                errors += f"\n- {self.username_system(us)}\n> You cannot untoss someone higher than yourself."
            elif us.top_role > ctx.me.top_role:
                errors += f"\n- {self.username_system(us)}\n> You cannot untoss someone higher than myself."
            elif (
                str(us.id) not in tosses[ctx.channel.name]["tossed"]
                and tossrole not in us.roles
            ):
                errors += f"\n- {self.username_system(us)}\n> This user is not already tossed."
            else:
                continue
            users.remove(us)
        if not users:
            return await ctx.reply(
                errors
                + "\n\n"
                + "There's nobody left to untoss, so nobody was untossed.",
                mention_author=False,
            )

        # Actually untoss.
        for us in users:
            self.busy[ctx.guild.id] = us.id
            roles = tosses[ctx.channel.name]["tossed"][str(us.id)]
            if us.id not in tosses[ctx.channel.name]["untossed"]:
                tosses[ctx.channel.name]["untossed"].append(us.id)
            del tosses[ctx.channel.name]["tossed"][str(us.id)]

            if roles:
                roles = [
                    ctx.guild.get_role(r)
                    for r in roles
                    if ctx.guild.get_role(r) and ctx.guild.get_role(r).is_assignable()
                ]
                await us.add_roles(
                    *roles,
                    reason=f"Untossed by {ctx.author} ({ctx.author.id})",
                    atomic=False,
                )
            await us.remove_roles(
                tossrole,
                reason=f"Untossed by {ctx.author} ({ctx.author.id})",
            )
            await ctx.channel.set_permissions(us, overwrite=None)

            # Notify.
            errors += "\n" + f"{self.username_system(us)} has been untossed."
            if notifychannel:
                embed = stock_embed(self.bot)
                author_embed(embed, us)
                embed.color = ctx.author.color
                embed.title = "🚶 Untoss"
                embed.description = f"{us.mention} was untossed by {ctx.author.mention} [`#{ctx.channel.name}`]"
                createdat_embed(embed, us)
                joinedat_embed(embed, us)
                prevlist = []
                if len(roles) > 0:
                    for role in roles:
                        prevlist.append("<@&" + str(role.id) + ">")
                    prevlist = ",".join(reversed(prevlist))
                else:
                    prevlist = "None"
                embed.add_field(
                    name="🎨 Restored Roles",
                    value=prevlist,
                    inline=False,
                )
                await notifychannel.send(embed=embed)

        set_file("tosses", json.dumps(tosses), f"servers/{ctx.guild.id}/toss")
        del self.busy[ctx.guild.id]

        if not tosses[ctx.channel.name]:
            errors += "\n\n" + "There is nobody left in this session."

        await ctx.reply(content=errors, mention_author=False)

    @commands.bot_has_guild_permissions(
        embed_links=True, add_reactions=True, manage_channels=True
    )
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def close(self, ctx, archive=True):
        """This closes a toss session.

        Please refer to the tossing section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-tossing-system/).

        - `archive`
        Whether to archive the session or not. Optional."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if ctx.channel.name not in [
            c.lower() for c in get_config(ctx.guild.id, "toss", "tosschannels")
        ]:
            return await ctx.reply(
                content="This command must be run inside of a toss channel.",
                mention_author=False,
            )

        notify_channel = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "toss", "notificationchannel")
        )
        if not notify_channel:
            notify_channel = self.bot.pull_channel(
                ctx.guild, get_config(ctx.guild.id, "staff", "staffchannel")
            )
        tosses = get_file("tosses", f"servers/{ctx.guild.id}/toss")

        if tosses[ctx.channel.name]["tossed"]:
            return await ctx.reply(
                content="You must untoss everyone first!", mention_author=True
            )

        if archive:
            async with ctx.channel.typing():
                dotraw, dotzip = await log_channel(
                    self.bot, ctx.channel, zip_files=True
                )

            users = []
            for uid in (
                tosses[ctx.channel.name]["untossed"] + tosses[ctx.channel.name]["left"]
            ):
                user = self.bot.get_user(uid)
                if not user:
                    user = await self.bot.fetch_user(uid)
                users.append(user)

            filename = (
                ctx.message.created_at.astimezone().strftime("%Y-%m-%d")
                + f" {ctx.channel.name} {ctx.channel.id}"
            )
            reply = (
                f"📕 I've archived that as: `{filename}.txt`\nThis toss session had the following users:\n- "
                + "\n- ".join([f"{self.username_system(u)} ({u.id})" for u in users])
            )
            dotraw += f"{self.bot.user} [BOT] {ctx.message.created_at.astimezone().strftime('%Y/%m/%d %H:%M')}\n{reply}"

            if not os.path.exists(
                f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}"
            ):
                os.makedirs(
                    f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}"
                )
            with open(
                f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}/{filename}.txt",
                "w",
            ) as filetxt:
                filetxt.write(dotraw)
            if dotzip:
                with open(
                    f"data/servers/{ctx.guild.id}/toss/archives/sessions/{ctx.channel.id}/{filename} (files).zip",
                    "wb",
                ) as filezip:
                    filezip.write(dotzip.getbuffer())

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
                    + f"`{len(zipfile.ZipFile(dotzip, 'r', zipfile.ZIP_DEFLATED).namelist())}` files in the zip file.",
                    inline=True,
                )

            await notify_channel.send(embed=embed)

        del tosses[ctx.channel.name]
        set_file("tosses", json.dumps(tosses), f"servers/{ctx.guild.id}/toss")

        await ctx.channel.delete(reason="Sangou Toss")
        return

    # Anti-spam subfeature.
    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.guild
            or message.author.bot
            or not self.enabled(message.guild)
            or self.is_rolebanned(message.author)
        ):
            return

        antispamwindow = get_config(message.guild.id, "toss", "antispamwindow")
        antispamlimit = get_config(message.guild.id, "toss", "antispamlimit")
        if not antispamwindow or not antispamlimit:
            return

        if (
            self.bot.pull_role(
                message.guild, get_config(message.guild.id, "staff", "modrole")
            )
            in message.author.roles
            or self.bot.pull_role(
                message.guild, get_config(message.guild.id, "staff", "adminrole")
            )
            in message.author.roles
            or message.author.id == message.guild.owner_id
            or message.author.id in self.bot.owner_ids
        ):
            return

        # Thank you to https://stackoverflow.com/a/29489919 for this function.
        def principal_period(s):
            i = (s + s).find(s, 1, -1)
            return None if i == -1 else s[:i]

        notify_channel = self.bot.pull_channel(
            message.guild, get_config(message.guild.id, "toss", "notificationchannel")
        )
        if not notify_channel:
            notify_channel = self.bot.pull_channel(
                message.guild, get_config(message.guild.id, "staff", "staffchannel")
            )
        staff_roles = [
            self.bot.pull_role(
                message.guild, get_config(message.guild.id, "staff", "modrole")
            ),
            self.bot.pull_role(
                message.guild, get_config(message.guild.id, "staff", "adminrole")
            ),
        ]

        if message.author.id not in self.spamcounter:
            self.spamcounter[message.author.id] = {}
        if "original_message" not in self.spamcounter[message.author.id]:
            self.spamcounter[message.author.id]["original_message"] = message
            return

        cutoff_ts = self.spamcounter[message.author.id][
            "original_message"
        ].created_at + timedelta(seconds=antispamwindow)

        if (
            any(
                (
                    message.content
                    == self.spamcounter[message.author.id]["original_message"].content,
                    principal_period(message.content)
                    == self.spamcounter[message.author.id]["original_message"].content,
                )
            )
            and message.created_at < cutoff_ts
        ):
            if "spamcounter" not in self.spamcounter[message.author.id]:
                self.spamcounter[message.author.id]["spamcounter"] = 1
            else:
                self.spamcounter[message.author.id]["spamcounter"] += 1
            if self.spamcounter[message.author.id]["spamcounter"] >= antispamlimit:
                self.spamcounter[message.author.id]["spamcounter"] = 0
                toss_channel = await self.new_session(message.guild)
                if not toss_channel:
                    self.spamcounter[message.author.id]["spamcounter"] += (
                        antispamlimit + 1
                    )
                    return
                failed_roles, previous_roles = await self.perform_toss(
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
                if notify_channel:
                    embed = stock_embed(self.bot)
                    author_embed(embed, message.author, True)
                    embed.color = message.author.color
                    embed.title = "🚷 Toss"
                    embed.description = f"{self.username_system(message.author)} has been tossed for hitting {antispamlimit} spam messages. {message.jump_url}\n> This toss takes place in {toss_channel.mention}..."
                    createdat_embed(embed, message.author)
                    joinedat_embed(embed, message.author)
                    prevlist = []
                    if len(previous_roles) > 0:
                        for role in previous_roles:
                            prevlist.append("<@&" + str(role.id) + ">")
                        prevlist = ",".join(reversed(prevlist))
                    else:
                        prevlist = "None"
                    embed.add_field(
                        name="🎨 Previous Roles",
                        value=prevlist,
                        inline=False,
                    )
                    if failed_roles:
                        faillist = []
                        for role in previous_roles:
                            faillist.append("<@&" + str(role.id) + ">")
                        faillist = ",".join(reversed(faillist))
                        embed.add_field(
                            name="🚫 Failed Roles",
                            value=faillist,
                            inline=False,
                        )
                    await notify_channel.send(
                        content=next(
                            staff_role
                            for staff_role in staff_roles
                            if staff_role is not None
                        ).mention,
                        embed=embed,
                    )
                    await message.add_reaction("🚷")
                    return
        else:
            self.spamcounter[message.author.id]["original_message"] = message
            self.spamcounter[message.author.id]["spamcounter"] = 0
            return

    # Rejoining after previously being tossed.
    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild):
            return
        notifychannel = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "toss", "notificationchannel")
        )
        if not notifychannel:
            notifychannel = self.bot.pull_channel(
                member.guild, get_config(member.guild.id, "staff", "staffchannel")
            )

        tosses = get_file("tosses", f"servers/{member.guild.id}/toss")
        tosschannel = None

        if "LEFTGUILD" not in tosses or str(member.id) not in tosses["LEFTGUILD"]:
            return

        for channel in tosses:
            if "left" in tosses[channel] and member.id in tosses[channel]["left"]:
                tosschannel = discord.utils.get(member.guild.channels, name=channel)
        if not tosschannel:
            tosschannel = await self.new_session(member.guild)
            # maybe a queue system here later if all are full??
        failroles, prevroles = await self.perform_toss(
            member, member.guild.me, tosschannel
        )
        tosses = get_file("tosses", f"servers/{member.guild.id}/toss")
        tosses[tosschannel.name]["tossed"][str(member.id)] = tosses["LEFTGUILD"][
            str(member.id)
        ]

        del tosses["LEFTGUILD"][str(member.id)]
        if not tosses["LEFTGUILD"]:
            del tosses["LEFTGUILD"]
        if (
            "left" in tosses[tosschannel.name]
            and member.id in tosses[tosschannel.name]["left"]
        ):
            tosses[tosschannel.name]["left"].remove(member.id)
        set_file("tosses", json.dumps(tosses), f"servers/{member.guild.id}/toss")

        await tosschannel.set_permissions(member, read_messages=True)
        tossmsg = await tosschannel.send(
            content=f"🔁 {self.username_system(member)} rejoined while tossed."
        )
        if notifychannel:
            tossmsg = await notifychannel.send(
                content=f"🔁 {self.username_system(member)} ({member.id}) rejoined while tossed. Continuing in {tosschannel.mention}..."
            )
        toss_userlog(
            member.guild.id,
            member.id,
            member.guild.me,
            tossmsg.jump_url,
            tosschannel.id,
        )
        return

    # Leaving or getting banned while tossed.
    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild):
            return

        session = self.get_session(member)
        if not session:
            return
        tosschannel = self.bot.pull_channel(member.guild, session)

        tosses = get_file("tosses", f"servers/{member.guild.id}/toss")
        if "LEFTGUILD" not in tosses:
            tosses["LEFTGUILD"] = {}
        tosses["LEFTGUILD"][str(member.id)] = tosses[session]["tossed"][str(member.id)]
        tosses[session]["left"].append(member.id)
        del tosses[session]["tossed"][str(member.id)]
        set_file("tosses", json.dumps(tosses), f"servers/{member.guild.id}/toss")

        notifychannel = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "toss", "notificationchannel")
        )
        if not notifychannel:
            notifychannel = self.bot.pull_channel(
                member.guild, get_config(member.guild.id, "staff", "staffchannel")
            )
        try:
            await member.guild.fetch_ban(member)
            out = f"🔨 {self.username_system(member)} got banned while tossed."
        except discord.NotFound:
            out = f"🚪 {self.username_system(member)} left while tossed."
        except discord.Forbidden:
            out = f"❓ {self.username_system(member)} was removed from the server.\nI do not have the Audit Log permissions to tell why."
        await notifychannel.send(out)
        tossmsg = await tosschannel.send(out)

    # In case of untoss by role removal.
    @Cog.listener()
    async def on_member_update(self, before, after):
        await self.bot.wait_until_ready()
        if not self.enabled(after.guild):
            return
        elif after.guild.id in self.busy and self.busy[after.guild.id] == after.id:
            return
        if self.is_rolebanned(before) and not self.is_rolebanned(after):
            session = self.get_session(after)
            if not session:
                return
            tosschannel = self.bot.pull_channel(after.guild, session)
            tossrole = self.bot.pull_role(
                after.guild, get_config(after.guild.id, "toss", "tossrole")
            )

            self.busy[after.guild.id] = after.id
            tosses = get_file("tosses", f"servers/{after.guild.id}/toss")
            roles = tosses[session]["tossed"][str(after.id)]
            tosses[session]["untossed"].append(after.id)
            del tosses[session]["tossed"][str(after.id)]
            set_file("tosses", json.dumps(tosses), f"servers/{after.guild.id}/toss")

            if roles:
                roles = [
                    after.guild.get_role(r)
                    for r in roles
                    if after.guild.get_role(r)
                    and after.guild.get_role(r).is_assignable()
                ]
                await after.add_roles(
                    *roles,
                    reason=f"Untossed manually.",
                    atomic=False,
                )
            await after.remove_roles(
                tossrole,
                reason=f"Untossed manually.",
            )
            await tosschannel.set_permissions(after, overwrite=None)
            tossmsg = await tosschannel.send(
                f"🚶 {self.username_system(after)} was untossed via role removal."
            )

            del self.busy[after.guild.id]

    # Remove toss data on manual delete.
    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.wait_until_ready()
        if self.enabled(channel.guild) and channel.name in [
            c.lower() for c in get_config(channel.guild.id, "toss", "tosschannels")
        ]:
            tosses = get_file("tosses", f"servers/{channel.guild.id}/toss")
            if channel.name not in tosses:
                return
            del tosses[channel.name]
            set_file("tosses", json.dumps(tosses), f"servers/{channel.guild.id}/toss")


async def setup(bot):
    await bot.add_cog(ModToss(bot))
