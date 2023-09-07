import json
from discord import Member
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.userdata import fill_userdata, set_userdata


class usertime(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timezone(self, ctx, *, timezone: str = None):
        """
        Sets your timezone for use with the 'tf' command.
        Timezones must be supplied the IANA tzdb (i.e. America/Chicago) format.
        """

        userdata, uid = fill_userdata(ctx.author.id)
        if timezone == None:
            await ctx.reply(
                content=f"Your timezone is `{'not set' if not userdata[uid]['timezone'] else userdata[uid]['timezone']}`.\n"
                "To change this, enter a timezone. You can find your specific timezone with this tool.\n"
                "<https://xske.github.io/tz/>",
                mention_author=False,
            )
            return
        elif timezone not in available_timezones():
            await ctx.reply(
                content="Invalid timezone provided. For help, run `timezone` by itself.",
                mention_author=False,
            )
            return
        else:
            userdata[uid]["timezone"] = timezone
            set_userdata(json.dumps(userdata))
            await ctx.reply(
                f"Your timezone has been set to `{timezone}`.", mention_author=False
            )

    @commands.command(aliases=["tf"])
    async def timefor(self, ctx, target: Member = None, *, time: str = None):
        """Send the current time in the invoker's (or mentioned user's) time zone."""
        if time and target.id != ctx.author.id:
            # check both *have* timezones
            suserdata, suid = fill_userdata(ctx.author.id)
            tuserdata, tuid = fill_userdata(target.id)
            if not suserdata[suid]["timezone"]:
                await ctx.reply(
                    content="I have no idea what time it is for you. You can set your timezone with `timezone`.",
                    mention_author=False,
                )
                return
            elif not tuserdata[tuid]["timezone"]:
                await ctx.reply(
                    content="I don't know what time it is for {target.display_name}.",
                    mention_author=False,
                )
                return

            parsed_time = self.parse_time(time)

            if not parsed_time:
                await ctx.reply(
                    content="Given time is invalid. Try `12AM`, `12 AM`, `12:00 AM`, or `00:00`.",
                    mention_author=False,
                )
                return

            suser_timezone = ZoneInfo(suserdata[suid]["timezone"])
            tuser_timezone = ZoneInfo(tuserdata[tuid]["timezone"])

            parsed_time = datetime.combine(
                datetime.now(), parsed_time, tzinfo=tuser_timezone
            )
            parsed_time = parsed_time.astimezone(suser_timezone)

            await ctx.reply(
                content=f"`{time}` for them is `{parsed_time.strftime('%I:%M %p')}` for you.",
                mention_author=False,
            )
        else:
            userdata, uid = fill_userdata(ctx.author.id if not target else target.id)
            if not userdata[uid]["timezone"]:
                await ctx.reply(
                    content=(
                        "I have no idea what time it is for you. You can set your timezone with `timezone`."
                        if not target
                        else f"I don't know what time it is for {target.display_name}."
                    ),
                    mention_author=False,
                )
                return
            now = datetime.now(ZoneInfo(userdata[uid]["timezone"]))
            await ctx.reply(
                content=f"{'Your' if not target else 'Their'} current time is `{now.strftime('%H:%M, %Y-%m-%d')}`",
                mention_author=False,
            )
            return

    def parse_time(self, time_str: str):
        for fmt in ("%I %p", "%I%p", "%I:%M %p", "%H:%M"):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                pass
        return None


async def setup(bot: Bot):
    await bot.add_cog(usertime(bot))
