import discord
from discord.ext import commands
from discord.ext.commands import Cog
from discord.utils import escape_markdown
import json
import datetime
import asyncio
import os
from helpers.checks import ismod
from helpers.sv_config import get_config
from helpers.datafiles import (
    surveyr_event_types,
    new_survey,
    edit_survey,
    get_guildfile,
    set_guildfile,
)


class Surveyr(Cog):
    """
    An open source Pollr clone.
    """

    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Surveyr isn't set up for this server."
        self.bancooldown = {}

    def enabled(self, g):
        return all(
            (
                self.bot.pull_channel(g, get_config(g.id, "surveyr", "surveychannel")),
                type(get_config(g.id, "surveyr", "startingcase")) == int,
                get_config(g.id, "surveyr", "loggingtypes"),
            )
        )

    def case_handler(self, cases, surveys):
        if cases.isdigit():
            return [int(cases)]
        elif cases == "l" or cases == "latest":
            return [int(list(surveys)[-1])]
        else:
            try:
                if "-" in cases:
                    cases = cases.split("-")
                elif ".." in cases:
                    cases = cases.split("..")
                if len(cases) != 2:
                    return None
                elif cases[1] == "l" or cases[1] == "latest":
                    return range(int(cases[0]), int(list(surveys)[-1]) + 1)
                return range(int(cases[0]), int(cases[1]) + 1)
            except:
                return None

    def format_handler(self, entry):
        if entry.user.id == self.bot.user.id:
            # Recognize audit log reason formats by Sangou
            user = entry.guild.get_member_named(entry.reason.split()[3].split("#")[0])
            reason = (
                entry.reason.split("]")[1][1:]
                if entry.reason.split("]")[1][1:]
                else f"No reason was given, {user.mention}..."
            )
        else:
            user = entry.user
            reason = (
                entry.reason
                if entry.reason
                else f"No reason was given, {user.mention}..."
            )
        return user, reason

    def username_system(self, user):
        part = (
            self.bot.pacify_name(user.global_name)
            + f" [{self.bot.pacify_name(str(user))}]"
            if user.global_name
            else f"{self.bot.pacify_name(str(user))}"
        )
        return part + " (" + str(user.id) + ")"

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(invoke_without_command=True, aliases=["s"])
    async def survey(self, ctx):
        """This shows a list of recent surveys.

        Please see the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-survey-system/) for more info.

        No arguments."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        surveys = get_guildfile(ctx.guild.id, "surveys")
        if not surveys:
            await ctx.reply(content="There are no surveys yet.", mention_author=False)
        msg = []
        for i, k in enumerate(reversed(surveys)):
            if i == 5:
                break
            event_type = surveyr_event_types[surveys[k]["type"]]
            target = await self.bot.fetch_user(surveys[k]["target_id"])
            issuer = await self.bot.fetch_user(surveys[k]["issuer_id"])
            msg.append(f"`#{k}` **{event_type.upper()}** of {target} by {issuer}")
        await ctx.reply(
            content="**The last few surveys:**\n" + "\n".join(reversed(msg)),
            mention_author=False,
        )

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def manualsurvey(
        self,
        ctx,
        survey_type: str,
        member: discord.User,
        user: discord.User,
        *,
        reason: str,
    ):
        """THIS IS A DEBUG COMMAND!

        Please only run it if you are asked to!

        - `survey_type`
        The type of survey to create.
        - `member`
        The actioned member.
        - `user`
        The actioning Staff.
        - `reason`
        The reason for the action."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        surveys = get_guildfile(ctx.guild.id, "surveys")
        survey_channel = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "surveyr", "surveychannel")
        )
        msg = await survey_channel.send(content="⌛")
        caseid, timestamp = new_survey(
            ctx.guild.id, member.id, msg.id, user.id, reason, survey_type
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **{surveyr_event_types[survey_type].upper()}** on <t:{timestamp}:f>\n"
                f"**User:** " + self.username_system(member) + "\n"
                f"**Staff:** " + self.username_system(user) + "\n"
                f"**Reason:** {reason}"
            )
        )
        return

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["r"])
    async def reason(self, ctx, caseids: str, *, reason: str):
        """This edits a survey reason.

        Please see the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-survey-system/) for more info.

        - `caseids`
        The IDs to edit. Can be single (`15`) or multiple (`15..18`).
        - `reason`
        The reason to apply to the cases."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_guildfile(ctx.guild.id, "surveys"))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to update `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return
        msg = []
        for case in cases:
            try:
                survey = get_guildfile(ctx.guild.id, "surveys")[str(case)]
                msg = await self.bot.pull_channel(
                    ctx.guild, get_config(ctx.guild.id, "surveyr", "surveychannel")
                ).fetch_message(survey["post_id"])

                edit_survey(
                    ctx.guild.id,
                    case,
                    ctx.author.id,
                    reason,
                    survey["type"],
                )
                content = msg.content.split("\n")
                content[2] = f"**Staff:** " + self.username_system(ctx.author)
                content[3] = f"**Reason:** {reason}"
                await msg.edit(content="\n".join(content))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        edited = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Edited `{edited}`.", mention_author=False)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["c"])
    async def censor(self, ctx, caseids: str):
        """This censors a survey name.

        Useful for people with racist or otherwise offensive names.

        - `caseids`
        The IDs to censor. Can be single (`15`) or multiple (`15..18`)."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_guildfile(ctx.guild.id, "surveys"))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to censor `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return

        for case in cases:
            try:
                survey = get_guildfile(ctx.guild.id, "surveys")[str(case)]
                member = await self.bot.fetch_user(survey["target_id"])
                censored_username = "`" + " " * len(member.name) + "`"
                censored_globalname = (
                    "`" + " " * len(member.global_name) + "`"
                    if member.global_name
                    else ""
                )
                # todo: remove when discord completes its rollout
                if int(member.discriminator):
                    censored_username += "#" + member.discriminator
                msg = await self.bot.pull_channel(
                    ctx.guild, get_config(ctx.guild.id, "surveyr", "surveychannel")
                ).fetch_message(survey["post_id"])
                content = msg.content.split("\n")
                content[1] = (
                    f"**User:** {censored_globalname + ' [' if censored_globalname else ''}{censored_username}{']' if censored_globalname else ''} ({member.id})"
                )
                await msg.edit(content="\n".join(content))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        censored = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Censored `{censored}`.", mention_author=False)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["u"])
    async def uncensor(self, ctx, caseids: str):
        """This uncensors a survey name.

        Using it will fetch the user's latest name as well.

        - `caseids`
        The IDs to uncensor. Can be single (`15`) or multiple (`15..18`)."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_guildfile(ctx.guild.id, "surveys"))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to uncensor `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return

        for case in cases:
            try:
                survey = get_guildfile(ctx.guild.id, "surveys")[str(case)]
                member = await self.bot.fetch_user(survey["target_id"])
                msg = await self.bot.pull_channel(
                    ctx.guild, get_config(ctx.guild.id, "surveyr", "surveychannel")
                ).fetch_message(survey["post_id"])
                content = msg.content.split("\n")
                content[1] = f"**User:** " + self.username_system(member)
                await msg.edit(content="\n".join(content))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        uncensored = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Uncensored `{uncensored}`.", mention_author=False)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["re"])
    async def repost(self, ctx, caseid: str):
        """This reposts survey messages up to a case ID.

        If you botch the log, this will post what the bot has.

        - `caseid`
        The ID to repost up to. Must be single (`15`)."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(
            caseid + "..l", get_guildfile(ctx.guild.id, "surveys")
        )
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)
        if len(cases) > 20:
            warningmsg = await ctx.reply(
                f"You are trying to repost `{len(cases)}` cases. **That's more than `20`.**\nIf you're sure about that, please tick the box within ten seconds to proceed.",
                mention_author=False,
            )
            await warningmsg.add_reaction("✅")

            def check(r, u):
                return u.id == ctx.author.id and str(r.emoji) == "✅"

            try:
                await self.bot.wait_for("reaction_add", timeout=10.0, check=check)
            except asyncio.TimeoutError:
                await warningmsg.edit(content="Operation timed out.", delete_after=5)
                return

        surveychannel = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "surveyr", "surveychannel")
        )

        for case in cases:
            try:
                survey = get_guildfile(ctx.guild.id, "surveys")[str(case)]
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
            user = await self.bot.fetch_user(survey["target_id"])
            staff = await self.bot.fetch_user(survey["issuer_id"])
            try:
                msg = await surveychannel.fetch_message(survey["post_id"])
            except discord.NotFound:
                pass
            else:
                await msg.delete()
            msg = await surveychannel.send(
                content=(
                    f"`#{case}` **{surveyr_event_types[survey['type']].upper()}** on <t:{survey['timestamp']}:f>\n"
                    f"**User:** " + self.username_system(user) + "\n"
                    f"**Staff:** " + self.username_system(staff) + "\n"
                    f"**Reason:** {survey['reason']}"
                )
            )
            surveys = get_guildfile(ctx.guild.id, "surveys")
            surveys[str(case)]["post_id"] = msg.id
            set_guildfile(ctx.guild.id, "surveys", json.dumps(surveys))

        reposted = int(cases[0]) if len(cases) == 1 else f"{cases[0]}-{cases[-1]}"
        await ctx.reply(content=f"Reposted `{reposted}`.", mention_author=False)

    @commands.guild_only()
    @commands.command(aliases=["d"])
    async def dump(self, ctx, caseids: str):
        """This dumps survey user IDs.

        Use this with `massban` to ban users on other servers.

        - `caseids`
        The IDs to dump. Can be single (`15`) or multiple (`15..18`)."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(content=self.nocfgmsg, mention_author=False)
        cases = self.case_handler(caseids, get_guildfile(ctx.guild.id, "surveys"))
        if not cases:
            return await ctx.reply(content="Malformed cases.", mention_author=False)

        userids = []
        for case in cases:
            try:
                survey = get_guildfile(ctx.guild.id, "surveys")[str(case)]
                if survey["type"] == "bans":
                    userids.append(str(survey["target_id"]))
            except KeyError:
                await ctx.reply(
                    content="You sent cases that exceed the actual case list.\nThese cases have been ignored.",
                    mention_author=False,
                )
                break
        userids = list(dict.fromkeys(userids))
        with open("iddump.txt", "w") as f:
            f.write("\n".join(userids))
        await ctx.reply(file=discord.File("iddump.txt"), mention_author=False)
        os.remove("iddump.txt")

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild) or "kick" not in get_config(
            member.guild.id, "surveyr", "loggingtypes"
        ):
            return
        guild = member.guild
        survey_channel = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "surveyr", "surveychannel")
        )

        # Waiting for Discord's mistimed audit log entry.
        entry = None
        for x in range(60):
            if x == 59:
                return
            async for log in guild.audit_logs(
                limit=10,
                after=datetime.datetime.now() - datetime.timedelta(minutes=1),
                oldest_first=False,
                action=discord.AuditLogAction.kick,
            ):
                if log.target.id == member.id:
                    entry = log
                    break
            if entry:
                break
            else:
                await asyncio.sleep(1)

        user, reason = self.format_handler(entry)

        msg = await survey_channel.send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, user.id, reason, "kicks"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **KICK** on <t:{timestamp}:f>\n"
                f"**User:** " + self.username_system(member) + "\n"
                f"**Staff:** " + self.username_system(user) + "\n"
                f"**Reason:** {reason}"
            )
        )
        return

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()
        if not self.enabled(guild) or "ban" not in get_config(
            guild.id, "surveyr", "loggingtypes"
        ):
            return
        survey_channel = self.bot.pull_channel(
            guild, get_config(guild.id, "surveyr", "surveychannel")
        )

        # Waiting for Discord's mistimed audit log entry.
        entry = None
        for x in range(60):
            if x == 59:
                return
            async for log in guild.audit_logs(
                limit=10,
                after=datetime.datetime.now() - datetime.timedelta(minutes=1),
                oldest_first=False,
                action=discord.AuditLogAction.ban,
            ):
                if log.target.id == member.id:
                    entry = log
                    break
            if entry:
                break
            else:
                await asyncio.sleep(1)

        user, reason = self.format_handler(entry)

        msg = await survey_channel.send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, user.id, reason, "bans"
        )
        if guild.id not in self.bancooldown:
            self.bancooldown[guild.id] = []
        self.bancooldown[guild.id].append(member.id)

        await msg.edit(
            content=(
                f"`#{caseid}` **BAN** on <t:{timestamp}:f>\n"
                f"**User:** " + self.username_system(member) + "\n"
                f"**Staff:** " + self.username_system(user) + "\n"
                f"**Reason:** {reason}"
            )
        )

        await asyncio.sleep(2)
        try:
            await guild.fetch_ban(member)
            self.bancooldown[guild.id].remove(member.id)
        except discord.NotFound:
            reason = get_guildfile(guild.id, "surveys")[str(caseid)]["reason"]
            edit_survey(guild.id, caseid, entry.user.id, reason, "softbans")
            msg = await guild.get_channel(survey_channel).fetch_message(msg.id)
            content = msg.content.split("\n")
            content[0] = f"`#{caseid}` **SOFTBAN** on <t:{timestamp}:f>"
            await msg.edit(content="\n".join(content))
            self.bancooldown[guild.id].remove(member.id)
        return

    @Cog.listener()
    async def on_member_unban(self, guild, member):
        await self.bot.wait_until_ready()
        if (
            not self.enabled(guild)
            or "unban" not in get_config(guild.id, "surveyr", "loggingtypes")
            or guild.id in self.bancooldown
            and member.id in self.bancooldown[guild.id]
        ):
            return
        survey_channel = self.bot.pull_channel(
            guild, get_config(guild.id, "surveyr", "surveychannel")
        )

        # Waiting for Discord's mistimed audit log entry.
        entry = None
        for x in range(60):
            if x == 59:
                return
            async for log in guild.audit_logs(
                limit=10,
                after=datetime.datetime.now() - datetime.timedelta(minutes=1),
                oldest_first=False,
                action=discord.AuditLogAction.unban,
            ):
                if log.target.id == member.id:
                    entry = log
                    break
            if entry:
                break
            else:
                await asyncio.sleep(1)

        user, reason = self.format_handler(entry)

        msg = await survey_channel.send(content="⌛")
        caseid, timestamp = new_survey(
            guild.id, member.id, msg.id, user.id, reason, "unbans"
        )

        await msg.edit(
            content=(
                f"`#{caseid}` **UNBAN** on <t:{timestamp}:f>\n"
                f"**User:** " + self.username_system(member) + "\n"
                f"**Staff:** " + self.username_system(user) + "\n"
                f"**Reason:** {reason}"
            )
        )
        return

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()
        if (
            not self.enabled(member_after.guild)
            or "timeout"
            not in get_config(member_after.guild.id, "surveyr", "loggingtypes")
            and "role"
            not in get_config(member_after.guild.id, "surveyr", "loggingtypes")
        ):
            return
        guild = member_after.guild
        survey_channel = self.bot.pull_channel(
            member_after.guild,
            get_config(member_after.guild.id, "surveyr", "surveychannel"),
        )

        if (
            "timeout" in get_config(member_after.guild.id, "surveyr", "loggingtypes")
            and not member_before.timed_out_until
            and member_after.timed_out_until
        ):
            # Waiting for Discord's mistimed audit log entry.
            entry = None
            for x in range(60):
                if x == 59:
                    return
                async for log in guild.audit_logs(
                    limit=10,
                    after=datetime.datetime.now() - datetime.timedelta(minutes=1),
                    oldest_first=False,
                    action=discord.AuditLogAction.member_update,
                ):
                    if log.target.id == member_after.id and log.after.timed_out_until:
                        entry = log
                        break
                if entry:
                    break
                else:
                    await asyncio.sleep(1)

            user, reason = self.format_handler(entry)

            msg = await survey_channel.send(content="⌛")
            caseid, timestamp = new_survey(
                guild.id, member_after.id, msg.id, user.id, reason, "timeouts"
            )

            await msg.edit(
                content=(
                    f"`#{caseid}` **TIMEOUT** ending <t:{int(entry.after.timed_out_until.timestamp())}:R> on <t:{timestamp}:f>\n"
                    f"**User:** " + self.username_system(member_after) + "\n"
                    f"**Staff:** " + self.username_system(user) + "\n"
                    f"**Reason:** {reason}"
                )
            )
        elif "promote" in get_config(
            member_after.guild.id, "surveyr", "loggingtypes"
        ) or "demote" in get_config(member_after.guild.id, "surveyr", "loggingtypes"):
            role_add = []
            role_remove = []
            for role in member_after.guild.roles:
                if (
                    role == member_after.guild.default_role
                    or role.id
                    not in get_config(member_after.guild.id, "surveyr", "loggingroles")
                ):
                    continue
                elif role not in member_before.roles and role in member_after.roles:
                    # if role.id == get_config(
                    #     member_after.guild.id, "staff", "exstaffrole"
                    # ):
                    #     continue
                    # Special Role Added
                    role_add.append(role.id)
                elif role in member_before.roles and role not in member_after.roles:
                    # if role.id == get_config(
                    #     member_after.guild.id, "staff", "exstaffrole"
                    # ):
                    #     continue
                    # Special Role Removed
                    role_remove.append(role.id)

            # Waiting for Discord's mistimed audit log entry.
            entry = None
            for x in range(60):
                if x == 59:
                    return
                async for log in guild.audit_logs(
                    limit=10,
                    after=datetime.datetime.now() - datetime.timedelta(minutes=1),
                    oldest_first=False,
                    action=discord.AuditLogAction.member_update,
                ):
                    if log.target.id == member_after.id:
                        entry = log
                        break
                if entry:
                    break
                else:
                    await asyncio.sleep(1)

            user, reason = self.format_handler(entry)

            if "promote" in get_config(
                member_after.guild.id, "surveyr", "loggingtypes"
            ):
                for role in role_add:
                    msg = await survey_channel.send(content="⌛")
                    caseid, timestamp = new_survey(
                        guild.id, member_after.id, msg.id, user.id, reason, "roleadds"
                    )

                    await msg.edit(
                        content=(
                            f"`#{caseid}` **PROMOTION** to `{role.name}` on <t:{timestamp}:f>\n"
                            f"**User:** " + self.username_system(member) + "\n"
                            f"**Staff:** " + self.username_system(user) + "\n"
                            f"**Reason:** {reason}"
                        )
                    )

            if "demote" in get_config(member_after.guild.id, "surveyr", "loggingtypes"):
                for role in role_remove:
                    msg = await survey_channel.send(content="⌛")
                    caseid, timestamp = new_survey(
                        guild.id,
                        member_after.id,
                        msg.id,
                        user.id,
                        reason,
                        "roleremoves",
                    )

                    await msg.edit(
                        content=(
                            f"`#{caseid}` **DEMOTION** from `{role.name}` on <t:{timestamp}:f>\n"
                            f"**User:** " + self.username_system(member_after) + "\n"
                            f"**Staff:** " + self.username_system(user) + "\n"
                            f"**Reason:** {reason}"
                        )
                    )


async def setup(bot):
    await bot.add_cog(Surveyr(bot))
