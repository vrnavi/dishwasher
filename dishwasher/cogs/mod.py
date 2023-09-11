import discord
from discord.ext import commands
from discord.ext.commands import Cog
import config
import datetime
import asyncio
import typing
import random
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.userlogs import userlog
from helpers.placeholders import random_self_msg, random_bot_msg
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed, mod_embed
import io


class Mod(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.check_if_target_is_staff = self.check_if_target_is_staff
        self.bot.modqueue = {}

    def check_if_target_is_staff(self, target):
        return any(
            r.id == get_config(target.guild.id, "staff", "staff_role")
            for r in target.roles
        )

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def setguildicon(self, ctx, url):
        """[O] Changes the guild icon."""
        img_bytes = await self.bot.aiogetbytes(url)
        await ctx.guild.edit(icon=img_bytes, reason=str(ctx.author))
        await ctx.send(f"Done!")

        slog = get_config(ctx.guild.id, "logs", "slog_thread")
        if slog:
            slog = await self.bot.fetch_channel(slog)
            log_msg = (
                f"✏️ **Guild Icon Update**: {ctx.author} changed the guild icon."
                f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
            )
            img_filename = url.split("/")[-1].split("#")[0]  # hacky
            img_file = discord.File(io.BytesIO(img_bytes), filename=img_filename)
            await slog.send(log_msg, file=img_file)

    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["boot"])
    async def kick(self, ctx, target: discord.Member, *, reason: str = ""):
        """[S] Kicks a user."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        elif self.check_if_target_is_staff(target):
            return await ctx.send("I cannot kick Staff members.")

        userlog(ctx.guild.id, target.id, ctx.author, reason, "kicks")

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"**You were kicked** from `{ctx.guild.name}`."
        if reason:
            dm_message += f'\n*The given reason is:* "{reason}".'
        dm_message += "\n\nYou are able to rejoin."

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents kick issues in cases where user blocked bot
            # or has DMs disabled
            pass
        except discord.HTTPException:
            # Prevents kick issues on bots
            pass

        await target.kick(reason=f"[ Kick by {ctx.author} ] {reason}")
        await ctx.send(f"**{target.mention}** was KICKED.")

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

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
                value=f"**No reason was set!**\nPlease use `{config.prefixes[0]}kick <user> [reason]` in the future.\Kick reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["yeet"])
    async def ban(self, ctx, target: discord.User, *, reason: str = ""):
        """[S] Bans a user."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += (
                    f'\n*The given reason is:* "{reason}".\n\nThis ban does not expire'
                )
            dm_message += (
                f", but you may appeal it here:\n{get_config(ctx.guild.id, 'staff', 'appeal_url')}"
                if get_config(ctx.guild.id, "staff", "appeal_url")
                else "."
            )
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                pass
            except discord.HTTPException:
                # Prevents ban issues on bots
                pass

        await ctx.guild.ban(
            target, reason=f"[ Ban by {ctx.author} ] {reason}", delete_message_days=0
        )
        await ctx.send(f"**{target.mention}** is now BANNED.")

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

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
                value=f"**No reason provided!**\nPlease use `{config.prefixes[0]}ban <user> [reason]` in the future.\nBan reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["bandel"])
    async def dban(
        self, ctx, day_count: int, target: discord.User, *, reason: str = ""
    ):
        """[S] Bans a user, with n days of messages deleted."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if day_count < 0 or day_count > 7:
            return await ctx.send(
                "Message delete day count must be between 0 and 7 days."
            )

        if reason:
            userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "bans",
            )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        if ctx.guild.get_member(target.id) is not None:
            dm_message = f"**You were banned** from `{ctx.guild.name}`."
            if reason:
                dm_message += f'\n*The given reason is:* "{reason}".'
            appealmsg = (
                f", but you may appeal it here:\n{get_config(ctx.guild.id, 'staff', 'appeal_url')}"
                if get_config(ctx.guild.id, "staff", "appeal_url")
                else "."
            )
            dm_message += f"\n\nThis ban does not expire{appealmsg}"
            try:
                await target.send(dm_message)
            except discord.errors.Forbidden:
                # Prevents ban issues in cases where user blocked bot
                # or has DMs disabled
                pass
            except discord.HTTPException:
                # Prevents ban issues on bots
                pass

        await target.ban(
            reason=f"[ Ban by {ctx.author} ] {reason}",
            delete_message_days=day_count,
        )
        await ctx.send(
            f"**{target.mention}** is now BANNED.\n{day_count} days of messages were deleted."
        )

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

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
                value=f"**No reason provided!**\nPlease use `{config.prefixes[0]}dban <user> [reason]` in the future.\nBan reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def massban(self, ctx, *, targets: str):
        """[S] Bans users with their IDs, doesn't message them."""
        msg = await ctx.send(f"🚨 **MASSBAN IN PROGRESS...** 🚨")
        targets_int = [int(target) for target in targets.strip().split(" ")]
        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if mlog:
            mlog = await self.bot.fetch_channel(mlog)
        for target in targets_int:
            target_user = await self.bot.fetch_user(target)
            target_member = ctx.guild.get_member(target)
            if target == ctx.author.id:
                await ctx.send(random_self_msg(ctx.author.name))
                continue
            elif target == self.bot.user:
                await ctx.send(random_bot_msg(ctx.author.name))
                continue
            elif target_member and self.check_if_target_is_staff(target_member):
                await ctx.send(f"(re: {target}) I cannot ban Staff members.")
                continue

            userlog(
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

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def unban(self, ctx, target: discord.User, *, reason: str = ""):
        """[S] Unbans a user with their ID, doesn't message them."""

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        await ctx.guild.unban(target, reason=f"[ Unban by {ctx.author} ] {reason}")
        await ctx.send(f"{safe_name} is now UNBANNED.")

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Colour.from_str("#00FF00")
        embed.title = "🎁 Unban"
        embed.description = f"{target.mention} was unbanned by {ctx.author.mention} [{ctx.channel.mention}] [[Jump]({ctx.message.jump_url})]"
        author_embed(embed, target)
        mod_embed(embed, target, ctx.author)

        if reason:
            embed.add_field(name=f"📝 Reason", value=f"{reason}", inline=False)
        else:
            embed.add_field(
                name=f"📝 Reason",
                value=f"**No reason provided!**\nPlease use `{config.prefixes[0]}unban <user> [reason]` in the future.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command(aliases=["silentban"])
    async def sban(self, ctx, target: discord.User, *, reason: str = ""):
        """[S] Bans a user silently. Does not message them."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            userlog(ctx.guild.id, target.id, ctx.author, reason, "bans")
        else:
            userlog(
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

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

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
                value=f"**No reason provided!**\nPlease use `{config.prefixes[0]}sban <user> [reason]` in the future.",
                inline=False,
            )
        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["count"])
    async def msgcount(self, ctx, messageid: int):
        """[S] Counts a given number of messages."""
        history = [message.id async for message in ctx.channel.history(limit=200)]
        if messageid in history:
            return await ctx.reply(
                content=f"**Raw**: {history.index(messageid)}\n"
                + f"**Now**: {history.index(messageid) + 2}\n"
                + f"**With Purge**: {history.index(messageid) + 3}",
                mention_author=False,
            )
        else:
            return await ctx.reply(
                content="That message isn't in this channel.", mention_author=False
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(invoke_without_command=True, aliases=["clear"])
    async def purge(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """[S] Clears a given number of messages."""
        if not channel:
            channel = ctx.channel
        if limit >= 1000000:
            return await ctx.reply(
                content=f"Your purge limit of `{limit}` is too high. Are you trying to `purge from {limit}`?",
                mention_author=False,
            )
        deleted = len(await channel.purge(limit=limit))
        await ctx.send(f"🚮 `{deleted}` messages purged.", delete_after=5)

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} messages in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @purge.command()
    async def bots(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """[S] Clears a given number of bot messages."""
        if not channel:
            channel = ctx.channel

        def is_bot(m):
            return all((m.author.bot, m.author.discriminator != "0000"))

        deleted = len(await channel.purge(limit=limit, check=is_bot))
        await ctx.send(f"🚮 `{deleted}` bot messages purged.", delete_after=5)

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} bot messages in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @purge.command(name="from")
    async def _from(
        self,
        ctx,
        target: discord.User,
        limit=50,
        channel: discord.abc.GuildChannel = None,
    ):
        """[S] Clears a given number of messages from a user."""
        if not channel:
            channel = ctx.channel

        def is_mentioned(m):
            return target.id == m.author.id

        deleted = len(await channel.purge(limit=limit, check=is_mentioned))
        await ctx.send(f"🚮 `{deleted}` messages from {target} purged.", delete_after=5)

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = f"{str(ctx.author)} purged {deleted} messages from {target} in {channel.mention}."
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @purge.command(aliases=["emoji"])
    async def emotes(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """[S] Clears a given number of emotes."""
        if not channel:
            channel = ctx.channel

        def has_emote(m):
            return m.clean_content[:2] == "<:" and m.clean_content[-1:] == ">"

        deleted = len(await channel.purge(limit=limit, check=has_emote))
        await ctx.send(f"🚮 `{deleted}` emotes purged.", delete_after=5)

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} emotes in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @purge.command()
    async def embeds(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """[S] Clears a given number of embeds."""
        if not channel:
            channel = ctx.channel

        def has_embed(m):
            return any((m.embeds, m.attachments, m.stickers))

        deleted = len(await channel.purge(limit=limit, check=has_embed))
        await ctx.send(f"🚮 `{deleted}` embeds purged.", delete_after=5)

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} embeds in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @purge.command()
    async def reacts(self, ctx, limit=50, channel: discord.abc.GuildChannel = None):
        """[S] Clears a given number of reactions."""
        if not channel:
            channel = ctx.channel

        deleted = 0
        async for msg in channel.history(limit=limit):
            if msg.reactions:
                deleted += 1
                await msg.clear_reactions()
        await ctx.send(f"🚮 `{deleted}` reactions purged.", delete_after=5)

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "🗑 Purged"
        embed.description = (
            f"{str(ctx.author)} purged {deleted} reactions in {channel.mention}."
        )
        author_embed(embed, ctx.author)

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def warn(self, ctx, target: discord.User, *, reason: str = ""):
        """[S] Warns a user."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.check_if_target_is_staff(target):
                return await ctx.send("I cannot ban Staff members.")

        if reason:
            warn_count = userlog(ctx.guild.id, target.id, ctx.author, reason, "warns")
        else:
            warn_count = userlog(
                ctx.guild.id,
                target.id,
                ctx.author,
                f"No reason provided. ({ctx.message.jump_url})",
                "warns",
            )

        if ctx.guild.get_member(target.id) is not None:
            msg = f"**You were warned** on `{ctx.guild.name}`."
            if reason:
                msg += "\nThe given reason is: " + reason
            rulesmsg = (
                f" in {get_config(ctx.guild.id, 'staff', 'rules_url')}."
                if get_config(ctx.guild.id, "staff", "rules_url")
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
                pass
            except discord.HTTPException:
                # Prevents warn issues on bots
                pass

        await ctx.send(
            f"{target.mention} has been warned. This user now has {warn_count} warning(s)."
        )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)

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
                value=f"**No reason was set!**\nPlease use `{config.prefixes[0]}warn <user> [reason]` in the future.\Warn reasons are sent to the user.",
                inline=False,
            )

        await mlog.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["addnote"])
    async def note(self, ctx, target: discord.User, *, note: str = ""):
        """[S] Adds a note to a user."""
        userlog(ctx.guild.id, target.id, ctx.author, note, "notes")
        await ctx.send(f"Noted.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setnick", "nick"])
    async def nickname(self, ctx, target: discord.Member, *, nick: str = ""):
        """[S] Sets a user's nickname.

        Just send .nickname <user> to wipe the nickname."""

        try:
            if nick:
                await target.edit(nick=nick, reason=str(ctx.author))
            else:
                await target.edit(nick=None, reason=str(ctx.author))

            await ctx.send("Successfully set nickname.")
        except discord.errors.Forbidden:
            await ctx.send(
                "I don't have the permission to set that user's nickname.\n"
                "User's top role may be above mine, or I may lack Manage Nicknames permission."
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["echo"])
    async def say(self, ctx, *, the_text: str):
        """[S] Repeats a given text."""
        await ctx.send(the_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["send"])
    async def speak(
        self,
        ctx,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread],
        *,
        the_text: str,
    ):
        """[S] Posts a given text in a given channel."""
        output = await channel.send(the_text)
        if ctx.author.id in config.bot_managers:
            output.author = ctx.author
            newctx = await self.bot.get_context(output)
            newctx.message.author = ctx.guild.me
            await self.bot.invoke(newctx)
        await ctx.message.reply("👍", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def reply(
        self,
        ctx,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread],
        message: int,
        *,
        the_text: str,
    ):
        """[S] Replies to a message with a given text in a given channel."""
        msg = await channel.fetch_message(message)
        output = await msg.reply(content=f"{the_text}", mention_author=False)
        if ctx.author.id in config.bot_managers:
            output.author = ctx.author
            newctx = await self.bot.get_context(output)
            newctx.message.author = ctx.guild.me
            await self.bot.invoke(newctx)
        await ctx.message.reply("👍", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def react(
        self,
        ctx,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread],
        message: int,
        emoji: str,
    ):
        """[S] Reacts to a message with a given emoji in a given channel."""
        emoji = discord.PartialEmoji.from_str(emoji)
        msg = await channel.fetch_message(message)
        await msg.add_reaction(emoji)
        await ctx.message.reply("👍", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def typing(
        self,
        ctx,
        channel: typing.Union[discord.abc.GuildChannel, discord.Thread],
        duration: int,
    ):
        """[S] Sends a typing indicator for a given duration of seconds.."""
        await ctx.send("👍")
        async with channel.typing():
            await asyncio.sleep(duration)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setplaying", "setgame"])
    async def playing(self, ctx, *, game: str = ""):
        """[S] Sets the bot's currently played game name.

        Just send pws playing to wipe the playing state."""
        if game:
            await self.bot.change_presence(activity=discord.Game(name=game))
        else:
            await self.bot.change_presence(activity=None)

        await ctx.send("Successfully set game.")

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["setbotnick", "botnick", "robotnick"])
    async def botnickname(self, ctx, *, nick: str = ""):
        """[S] Sets the bot's nickname.

        Just send pws botnickname to wipe the nickname."""

        if nick:
            await ctx.guild.me.edit(nick=nick, reason=str(ctx.author))
        else:
            await ctx.guild.me.edit(nick=None, reason=str(ctx.author))

        await ctx.send("Successfully set bot nickname.")


async def setup(bot):
    await bot.add_cog(Mod(bot))
