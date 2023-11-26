import discord
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.datafiles import add_userlog, add_job
from helpers.sv_config import get_config
from helpers.placeholders import random_self_msg, random_bot_msg


class ModTimed(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @commands.check(check_if_staff)
    @commands.command()
    async def timeban(
        self, ctx, target: discord.Member, duration: str, *, reason: str = ""
    ):
        """[S] Bans a user for a specified amount of time."""
        if target == ctx.author:
            return await ctx.send(random_self_msg(ctx.author.name))
        elif target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))
        elif self.bot.check_if_target_is_staff(target):
            return await ctx.send("I cannot ban Staff members.")

        expiry_timestamp = self.bot.parse_time(duration)

        add_userlog(
            ctx.guild.id,
            target.id,
            ctx.author,
            f"{reason} (Timed, expires <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f>)",
            "bans",
        )

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )

        dm_message = f"You were banned from {ctx.guild.name}."
        if reason:
            dm_message += f' The given reason is: "{reason}".'
        dm_message += f"\n\nThis ban will expire <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f>."

        try:
            await target.send(dm_message)
        except discord.errors.Forbidden:
            # Prevents ban issues in cases where user blocked bot
            # or has DMs disabled
            pass

        await target.ban(
            reason=f"{ctx.author}, reason: {reason}", delete_message_days=0
        )
        chan_message = (
            f"⛔ **Timed Ban**: {ctx.author.mention} banned "
            f"{target.mention} expiring <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f> | {safe_name}\n"
            f"🏷 __User ID__: {target.id}\n"
        )
        if reason:
            chan_message += f'✏️ __Reason__: "{reason}"'
        else:
            chan_message += (
                "Please add an explanation below. In the future"
                f", it is recommended to use `{ctx.prefix}ban <user> [reason]`"
                " as the reason is automatically sent to the user."
            )

        add_job("unban", target.id, {"guild": ctx.guild.id}, expiry_timestamp)

        mlog = await self.bot.fetch_channel(get_config(guild.id, "logging", "modlog"))
        await mlog.send(chan_message)
        await ctx.send(
            f"{safe_name} is now BANNED. It will expire <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f>. 👍"
        )


async def setup(bot):
    await bot.add_cog(ModTimed(bot))
