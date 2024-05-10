import discord
from discord.ext import commands
from discord.ext.commands import Cog
import datetime
import asyncio
import typing
import random
import emoji
from helpers.checks import ismod, isadmin, ismanager
from helpers.datafiles import add_userlog
from helpers.placeholders import random_msg
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed, mod_embed, quote_embed
import io
import re


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.check_if_target_is_staff = self.check_if_target_is_staff
        self.bot.modqueue = {}

    def check_if_target_is_staff(self, target):
        return any(
            r
            == self.bot.pull_role(
                target.guild, get_config(target.guild.id, "staff", "modrole")
            )
            or r
            == self.bot.pull_role(
                target.guild, get_config(target.guild.id, "staff", "adminrole")
            )
            for r in target.roles
        )

    @commands.bot_has_permissions(kick_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["boot"])
    async def kick(self, ctx, target: discord.Member, *, reason: str = ""):
        """This kicks a user.

        Giving a `reason` will send the reason to the user.

        - `target`
        The target to kick.
        - `reason`
        The reason for the kick. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot kick Staff members.")

        add_userlog(ctx.guild.id, target.id, ctx.author, reason, "kicks")

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"**You were kicked** from `{ctx.guild.name}`."
        if reason:
            dm_message += f'\n*The given reason is:* "{reason}".'
        dm_message += "\n\nYou are able to rejoin."
        failmsg = ""

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            failmsg = "\nI couldn't DM this user to tell them."
            pass
        except discord.HTTPException:
            # Prevents kick issues on bots
            pass

        await target.kick(reason=f"[ Kick by {ctx.author} ] {reason}")
        await ctx.send(f"**{target.mention}** was KICKED.{failmsg}")

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#FFFF00")
        embed.title = "👢 Kick"
        embed.description = f"{target.mention} was kicked by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)

        if reason:
            embed.add_field(name=f"📝 Reason", value=f"{reason}", inline=False)
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason was set!**\nPlease use `{ctx.prefix}kick <user> [reason]` in the future.\Kick reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx, target: discord.User, *, reason: str = ""):
        """This bans a user.

        Giving a `reason` will send the reason to the user.

        - `target`
        The target to ban.
        - `reason`
        The reason for the ban. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            add_userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        failmsg = ""
        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            dm_message += "\n\nThis ban does not expire"
            dm_message += (
                f", but you may appeal it here:\n{get_config(ctx.guild.id, 'staff', 'appealurl')}"
                if get_config(ctx.guild.id, "staff", "appealurl")
                else "."
            )
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                failmsg = "\nI couldn't DM this user to tell them."
                pass
            except discord.HTTPException:
                # Prevents ban issues on bots
                pass

        await ctx.guild.ban(
            target, reason=f"[ Ban by {ctx.author} ] {reason}", delete_message_days=0
        )
        await ctx.send(f"**{target.mention}** is now BANNED.\n{failmsg}")

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#FF0000")
        embed.title = "⛔ Ban"
        embed.description = f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)

        if reason:
            embed.add_field(name=f"📝 Reason", value=f"{reason}", inline=False)
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `{ctx.prefix}ban <user> [reason]` in the future.\nBan reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["bandel"])
    async def dban(
        self, ctx, day_count: int, target: discord.User, *, reason: str = ""
    ):
        """This bans a user with X days worth of messages deleted.

        Giving a `reason` will send the reason to the user.

        - `day_count`
        The days worth of messages to delete.
        - `target`
        The target to kick.
        - `reason`
        The reason for the kick. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if day_count < 0 or day_count > 7:
            return await ctx.send(
                "Message delete day count must be between 0 and 7 days."
            )

        if reason:
            add_userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        failmsg = ""
        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            appealmsg = (
                f", but you may appeal it here:\n{get_config(ctx.guild.id, 'staff', 'appealurl')}"
                if get_config(ctx.guild.id, "staff", "appealurl")
                else "."
            )
            dm_message += f"\n\nThis ban does not expire{appealmsg}"
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                failmsg = "\nI couldn't DM this user to tell them."
                pass
            except discord.HTTPException:
                # Prevents ban issues on bots
                pass

        await target.ban(
            reason=f"[ Ban by {ctx.author} ] {reason}",
            delete_message_days=day_count,
        )
        await ctx.send(
            f"**{target.mention}** is now BANNED.\n{day_count} days of messages were deleted.\n{failmsg}"
        )

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#FF0000")
        embed.title = "⛔ Ban"
        embed.description = f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)

        if reason:
            embed.add_field(name=f"📝 Reason", value=f"{reason}", inline=False)
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `{ctx.prefix}dban <user> [reason]` in the future.\nBan reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def massban(self, ctx, *, targets: str):
        """This mass bans user IDs.

        You can get IDs with `pls dump` if they're banned from
        a different server with the bot. Otherwise, good luck.
        This won't DM them.

        - `targets`
        The target to ban."""
        msg = await ctx.send(f"🚨 **MASSBAN IN PROGRESS...** 🚨")
        targets_int = [int(target) for target in targets.strip().split(" ")]

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )

        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.guild.get_member(target)
            if target == ctx.author.id:
                await ctx.send(
                    random_msg("warn_targetself", authorname=ctx.author.name)
                )
                continue
            elif target == self.bot.user:
                await ctx.send(random_msg("warn_targetbot", authorname=ctx.author.name))
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(f"(re: {target}) I cannot ban Staff members.")
                continue

            add_userlog(
                ctx.guild.id,
                target,
                ctx.author,
                f"Part of a massban. [[Jump]({ctx.message.jump_url})]",
                "bans",
            )

            await ctx.guild.ban(
                target_user,
                reason=f"[ Ban by {ctx.author} ] Massban.",
                delete_message_days=0,
            )

            if not mlog:
                continue

            embed = stock_embed(self.bot)
            embed.color = discord.Colour.from_str("#FF0000")
            embed.title = "🚨 Massban"
            embed.description = f"{target_user.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
            author_embed(embed, target_user)
            mod_embed(embed, target_user, ctx.author)
            await mlog.send(embed=embed)

        await msg.edit(content=f"All {len(targets_int)} users are now BANNED.")

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def unban(self, ctx, target: discord.User, *, reason: str = ""):
        """This unbans a user.

        The `reason` won't be sent to the user, but is used for logs.

        - `target`
        The target to unban.
        - `reason`
        The reason for the unban. Optional."""

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.unban(target, reason=f"[ Unban by {ctx.author} ] {reason}")
        await ctx.send(f"{safe_name} is now UNBANNED.")

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#00FF00")
        embed.title = "🎁 Unban"
        embed.description = f"{target.mention} was unbanned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)
        if not reason:
            reason = f"**No reason provided!**\nPlease use `{ctx.prefix}unban <user> [reason]` in the future."
        embed.add_field(name=f"📝 Reason", value=reason, inline=False)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(ban_members=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["silentban"])
    async def sban(self, ctx, target: discord.User, *, reason: str = ""):
        """This bans a user silently.

        In this case, the `reason` will only be saved to the logs.

        - `target`
        The target to ban.
        - `reason`
        The reason for the ban. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            add_userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.ban(
            target, reason=f"[ Ban by {ctx.author} ] {reason}", delete_message_days=0
        )
        await ctx.send(f"{safe_name} is now silently BANNED.")

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#FF0000")
        embed.title = "⛔ Silent Ban"
        embed.description = f"{target.mention} was banned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)

        if reason:
            embed.add_field(name=f"📝 Reason", value=f"{reason}", inline=False)
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `{ctx.prefix}sban <user> [reason]` in the future.",
                inline=False,
            )
        await mlog.send(embed=embed)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["count"])
    async def msgcount(self, ctx, message: discord.Message):
        """This counts up to a certain message.

        Think of this as counting from the newest message
        up to the message you specify. Useful for purging.

        - `message`
        An ID or message link to the message to count to."""
        history = [histmsg.id async for histmsg in message.channel.history(limit=200)]
        return await ctx.reply(
            content=f"**Raw**: {history.index(message.id)}\n"
            + f"**Now**: {history.index(message.id) + 2}\n"
            + f"**With Purge**: {history.index(message.id) + 3}",
            mention_author=False,
        )

    @commands.bot_has_permissions(add_reactions=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["notify"])
    async def alert(
        self,
        ctx,
        member: discord.Member,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread] = None,
    ):
        """This alerts you when a user says a message.

        If you don't specify a `channel`, the whole
        server will be watched for a new message.
        The bot will wait up to one day for a message,
        but it may end sooner if the bot is restarted.
        Poke Ren to fix this at some point.

        - `member`
        The member you'd like to watch for a message from.
        - `channel`
        The channel you'd like to be alerted for. Optional."""

        def check(m):
            if channel:
                return m.author.id == member.id and m.channel.id == channel.id
            else:
                return m.author.id == member.id

        await ctx.message.add_reaction("⏳")
        try:
            message = await self.bot.wait_for("message", timeout=86400, check=check)
        except asyncio.TimeoutError:
            resp = await ctx.channel.send(content=ctx.author.mention)
            return await resp.edit(content="🤷⏲️", delete_after=5)
        resp = await ctx.channel.send(content=ctx.author.mention)
        embed = quote_embed(self.bot, message, ctx.message, "Alerted")
        return await resp.edit(content=None, embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.group(invoke_without_command=True, aliases=["clear"])
    async def purge(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of messages.

        Please see the sister subcommands as well, in the [documentation](https://3gou.0ccu.lt/as-a-moderator/basic-functionality/#purging).
        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel
        if limit >= 1000000:
            return await ctx.reply(
                content=f"Your purge limit of `{limit}` is too high. Are you trying to `purge from {limit}`?",
                mention_author=False,
            )
        deleted = len(await channel.purge(limit=limit))
        await ctx.send(f"🚮 `{deleted}` messages purged.", delete_after=5)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} messages in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command()
    async def bots(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of bot messages.

        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def is_bot(m):
            return any((m.author.bot, m.author.discriminator == "0000"))

        deleted = len(await channel.purge(limit=limit, check=is_bot))
        await ctx.send(f"🚮 `{deleted}` bot messages purged.", delete_after=5)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} bot messages in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(name="from")
    async def _from(
        self,
        ctx,
        target: discord.User,
        limit=50,
        channel: discord.abc.GuildChannel = None,
    ):
        """This clears a given number of user messages.

        Defaults to 50 messages in the current channel. Max of one million.

        - `target`
        The user to purge messages from.
        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def is_mentioned(m):
            return target.id == m.author.id

        deleted = len(await channel.purge(limit=limit, check=is_mentioned))
        await ctx.send(f"🚮 `{deleted}` messages from {target} purged.", delete_after=5)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = f"{str(ctx.author)} purged {deleted} messages from {target} in {channel.mention}."
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(name="with")
    async def _with(
        self,
        ctx,
        string: str,
        limit=50,
        channel: discord.abc.GuildChannel = None,
    ):
        """This clears a given number of specific messages.

        Defaults to 50 messages in the current channel. Max of one million.

        - `string`
        Messages containing this will be deleted.
        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def contains(m):
            return string in m.content

        deleted = len(await channel.purge(limit=limit, check=contains))
        await ctx.send(
            f"🚮 `{deleted}` messages containing `{string}` purged.", delete_after=5
        )

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = f"{str(ctx.author)} purged {deleted} messages containing `{string}` in {channel.mention}."
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(aliases=["emoji"])
    async def emotes(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of emotes.

        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of emotes to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        emote_re = re.compile(r":[A-Za-z0-9_]+:", re.IGNORECASE)

        def has_emote(m):
            return any(
                (
                    emoji.emoji_count(m.content),
                    emote_re.findall(m.content),
                )
            )

        deleted = len(await channel.purge(limit=limit, check=has_emote))
        await ctx.send(f"🚮 `{deleted}` emotes purged.", delete_after=5)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} emotes in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command()
    async def embeds(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of messages with embeds.

        This includes stickers, by the way, but not emoji.
        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of messages to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        def has_embed(m):
            return any((m.embeds, m.attachments, m.stickers))

        deleted = len(await channel.purge(limit=limit, check=has_embed))
        await ctx.send(f"🚮 `{deleted}` embeds purged.", delete_after=5)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} embeds in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.bot_has_permissions(manage_messages=True)
    @commands.check(ismod)
    @commands.guild_only()
    @purge.command(aliases=["reactions"])
    async def reacts(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """This clears a given number of reactions.

        This does NOT delete their messages! Just the reactions!
        Defaults to 50 messages in the current channel. Max of one million.

        - `limit`
        The limit of reactions to delete. Optional.
        - `channel`
        The channel to purge from. Optional."""
        if not channel:
            channel = ctx.channel

        deleted = 0
        async for msg in channel.history(limit=limit):
            if msg.reactions:
                deleted += 1
                await msg.clear_reactions()
        await ctx.send(f"🚮 `{deleted}` reactions purged.", delete_after=5)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} reactions in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def warn(self, ctx, target: discord.User, *, reason: str = ""):
        """This warns a user.

        Warnings will appear on their user`log`.

        - `target`
        The user to warn.
        - `reason`
        The reason for the warning. Optional."""
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot warn Staff members.")

        if reason:
            warn_count = add_userlog(
                ctx.guild.id, target.id, ctx.author, reason, "warns"
            )
        else:
            warn_count = add_userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "warns",
            )

        failmsg = ""
        if ctx.guild.get_member(target.id) is not None:
            msg = f"**You were warned** on `{ctx.guild.name}`."
            if reason:
                msg += "\nThe given reason is: " + reason
            rulesmsg = (
                f" in {get_config(ctx.guild.id, 'staff', 'rulesurl')}."
                if get_config(ctx.guild.id, "staff", "rulesurl")
                else "."
            )
            msg += (
                f"\n\nPlease read the rules{rulesmsg} " f"This is warn #{warn_count}."
            )
            try:
                await target.send(msg)
            except discord.errors.Forbidden:
                # Prevents warn issues in cases where user blocked bot
                # or has DMs disabled
                failmsg = "\nI couldn't DM this user to tell them."
                pass
            except discord.HTTPException:
                # Prevents warn issues on bots
                pass

        await ctx.send(
            f"{target.mention} has been warned. This user now has {warn_count} warning(s).\n{failmsg}"
        )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#FFFF00")
        embed.title = f"🗞️ Warn #{warn_count}"
        embed.description = f"{target.mention} was warned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)

        if reason:
            embed.add_field(name=f"📝 Reason", value=f"{reason}", inline=False)
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason was set!**\nPlease use `{ctx.prefix}warn <user> [reason]` in the future.\Warn reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["addnote"])
    async def note(self, ctx, target: discord.User, *, note: str):
        """This adds a note to a user.

        Notes will appear on their user`log`.

        - `target`
        The user to add a note to.
        - `note`
        The contents of the note."""
        add_userlog(ctx.guild.id, target.id, ctx.author, note, "notes")
        await ctx.reply(f"I added that note for you.")

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command(aliases=["echo"])
    async def say(self, ctx, *, text: str):
        """This makes the bot repeat some text.

        It will not do anything other than that.

        - `text`
        The text to repeat."""
        await ctx.send(text)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command(aliases=["send"])
    async def speak(
        self,
        ctx,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread],
        *,
        text: str,
    ):
        """This makes the bot repeat some text in a specific channel.

        If you manage the bot, it can even run commands.

        - `channel`
        The channel to post the text in.
        - `text`
        The text to repeat."""
        output = await channel.send(text)
        if ctx.author.id in self.bot.config.managers:
            output.author = ctx.author
            newctx = await self.bot.get_context(output)
            newctx.message.author = ctx.guild.me
            await self.bot.invoke(newctx)
        await ctx.reply("👍", mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def reply(
        self,
        ctx,
        message: discord.Message,
        *,
        text: str,
    ):
        """This makes the bot reply to a message.

        If you manage the bot, it can even run commands.

        - `message`
        The message to reply to. Message link preferred.
        - `text`
        The text to repeat."""
        output = await message.reply(content=f"{text}", mention_author=False)
        if ctx.author.id in self.bot.config.managers:
            output.author = ctx.author
            newctx = await self.bot.get_context(output)
            newctx.message.author = ctx.guild.me
            await self.bot.invoke(newctx)
        await ctx.reply("👍", mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def react(
        self,
        ctx,
        message: discord.Message,
        emoji: str,
    ):
        """This makes the bot react to a message with an emoji.

        It can't react with emojis it doesn't have access to.

        - `message`
        The message to reply to. Message link preferred.
        - `emoji`
        The emoji to react with."""
        emoji = discord.PartialEmoji.from_str(emoji)
        await message.add_reaction(emoji)
        await ctx.reply("👍", mention_author=False)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def typing(
        self,
        ctx,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread],
        duration: int,
    ):
        """This makes the bot type in a channel for some time.

        There's not much else to it.

        - `channel`
        The channel or thread to type in.
        - `duration`
        The length of time to type for."""
        await ctx.reply("👍", mention_author=False)
        async with channel.typing():
            await asyncio.sleep(duration)


async def setup(bot):
    await bot.add_cog(Mod(bot))
