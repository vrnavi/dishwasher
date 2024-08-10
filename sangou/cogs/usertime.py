import json
from discord import Member
from datetime import datetime
from zoneinfo import ZoneInfo, available_timezones
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.datafiles import fill_profile, set_file


class usertime(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timezone(self, ctx, *, timezone: str = None):
        """This views or sets your timezone.

        Timezones must be in `America/New_York` format.
        See [this page](https://xske.github.io/tz/) to find your timezone.

        - `timezone`
        The timezone to set. Optional."""
        userdata = fill_profile(ctx.author.id)
        if timezone == None:
            await ctx.reply(
                content=f"Your timezone is `{'not set' if not userdata['timezone'] else userdata['timezone']}`.\n"
                "To change this, enter a timezone. You can find your specific timezone with this tool.\n"
                "If you want to remove your timezone, use `remove` where you'd normally put a timezone.\n"
                "<https://xske.github.io/tz/>",
                mention_author=False,
            )
            return
        elif timezone == "remove":
            userdata["timezone"] = None
            set_file("profile", json.dumps(userdata), f"users/{ctx.author.id}")
            await ctx.reply(f"Your timezone has been removed.", mention_author=False)
        elif timezone not in available_timezones():
            await ctx.reply(
                content="Invalid timezone provided. For help, run `timezone` by itself.",
                mention_author=False,
            )
            return
        else:
            userdata["timezone"] = timezone
            set_file("profile", json.dumps(userdata), f"users/{ctx.author.id}")
            await ctx.reply(
                f"Your timezone has been set to `{timezone}`.", mention_author=False
            )

    @commands.command(aliases=["tf"])
    async def timefor(self, ctx, target: Member = None, *, time: str = None):
        """This shows someone's current time.

        You can supply a time in `12AM`, `12 AM`, `12:00 AM`, or `00:00` to
        view another person's time. Running the command by itself will
        show your current time.

        - `target`
        The person you wish to see the time for. Optional.
        - `time`
        This time for you will show this time for them. Optional."""
        """Send the current time in the invoker's (or mentioned user's) time zone."""
        if time and target.id != ctx.author.id:
            # check both *have* timezones
            suserdata = fill_profile(ctx.author.id)
            tuserdata = fill_profile(target.id)
            if not suserdata["timezone"]:
                await ctx.reply(
                    content="I have no idea what time it is for you. You can set your timezone with `timezone`.",
                    mention_author=False,
                )
                return
            elif not tuserdata["timezone"]:
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

            suser_timezone = ZoneInfo(suserdata["timezone"])
            tuser_timezone = ZoneInfo(tuserdata["timezone"])

            parsed_time = datetime.combine(
                datetime.now(), parsed_time, tzinfo=tuser_timezone
            )
            parsed_time = parsed_time.astimezone(suser_timezone)

            await ctx.reply(
                content=f"`{time}` for them is `{parsed_time.strftime('%I:%M %p')}` for you.",
                mention_author=False,
            )
        else:
            userdata = fill_profile(ctx.author.id if not target else target.id)
            if not userdata["timezone"]:
                await ctx.reply(
                    content=(
                        "I have no idea what time it is for you. You can set your timezone with `timezone`."
                        if not target
                        else f"I don't know what time it is for {target.display_name}."
                    ),
                    mention_author=False,
                )
                return
            now = datetime.now(ZoneInfo(userdata["timezone"]))
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
