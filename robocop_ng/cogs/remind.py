import discord
import asyncio
import time
from datetime import datetime
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.robocronp import add_job, get_crontab


class Remind(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def remindlist(self, ctx):
        """[U] Lists your reminders."""
        ctab = get_crontab()
        uid = str(ctx.author.id)
        embed = discord.Embed(title=f"Active robocronp jobs")
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            job_details = ctab["remind"][jobtimestamp][uid]
            expiry_timestr = datetime.utcfromtimestamp(int(jobtimestamp)).strftime(
                "%Y-%m-%d %H:%M:%S (UTC)"
            )
            embed.add_field(
                name=f"Reminder for {expiry_timestr}",
                value=f"Added on: {job_details['added']}, "
                f"Text: {job_details['text']}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.cooldown(1, 10, type=commands.BucketType.user)
    @commands.command(aliases=["remindme"])
    async def remind(self, ctx, when: str, *, text: str = "something"):
        """[U] Reminds you about something."""
#        if ctx.guild:
#            await ctx.message.delete()
        current_timestamp = time.time()
        expiry_timestamp = self.bot.parse_time(when)

        if current_timestamp + 5 > expiry_timestamp:
            msg = await ctx.message.reply(
                f"Minimum remind interval is 5 seconds.",
                mention_author=False
            )
            return

        expiry_datetime = datetime.utcfromtimestamp(expiry_timestamp)
        duration_text = self.bot.get_relative_timestamp(
            time_to=expiry_datetime, include_to=True, humanized=True
        )

        safe_text = await commands.clean_content().convert(ctx, str(text))
        added_on = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        add_job(
            "remind",
            ctx.author.id,
            {"text": safe_text, "added": added_on},
            expiry_timestamp,
        )

        msg = await ctx.message.reply(
            f"You'll be reminded in "
            f"DMs about `{safe_text}` in {duration_text}.",
            mention_author=False
        )


async def setup(bot):
    await bot.add_cog(Remind(bot))
