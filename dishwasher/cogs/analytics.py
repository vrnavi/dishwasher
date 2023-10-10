import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
from helpers.checks import check_if_staff
from helpers.datafiles import get_botfile, set_botfile, get_userfile, set_userfile


class Analytics(Cog):
    """
    I need to know. I NEED to know!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def stats(self, ctx):
        """[U] Shows your analytics."""
        return

    @stats.command()
    async def on(self, ctx):
        """[U] Enables analytics collection."""
        userdata = get_botfile("dishusers")
        if "nostats" not in userdata:
            userdata["nostats"] = []
        if ctx.author.id not in userdata["nostats"]:
            return await ctx.reply(
                content="You already have analytics toggled on.", mention_author=False
            )
        userdata["nostats"].remove(ctx.author.id)
        set_botfile("dishusers", json.dumps(userdata))
        return await ctx.reply(
            content="*Analytics for you have been toggled on.**\nUse `off` to turn back off, or `delete` to purge your analytics.",
            mention_author=False,
        )

    @stats.command()
    async def off(self, ctx):
        """[U] Disables analytics collection."""
        userdata = get_botfile("dishusers")
        if "nostats" not in userdata:
            userdata["nostats"] = []
        if ctx.author.id in userdata["nostats"]:
            return await ctx.reply(
                content="You already have analytics toggled off.", mention_author=False
            )
        userdata["nostats"].append(ctx.author.id)
        set_botfile("dishusers", json.dumps(userdata))
        return await ctx.reply(
            content="*Analytics for you have been toggled off.**\nUse `on` to turn back on, or `delete` to purge your analytics.",
            mention_author=False,
        )

    @stats.command()
    async def delete(self, ctx):
        """[U] Deletes analytics data."""
        useranalytics = get_userfile(ctx.author.id, "analytics")
        if not useranalytics:
            return await ctx.reply(
                content="There are no analytics to delete.", mention_author=False
            )
        set_userfile(ctx.author.id, "analytics", json.dumps({}))
        return await ctx.reply(
            content="Your user analytics have been deleted.", mention_author=False
        )

    @Cog.listener()
    async def on_command_error(self, ctx):
        await self.bot.wait_until_ready()
        userdata = get_botfile("dishusers")
        if (
            ctx.author.bot
            or "nostats" in userdata
            and ctx.author.id in userdata["nostats"]
        ):
            return
        useranalytics = get_userfile(ctx.author.id, "analytics")

        if not useranalytics:
            try:
                await ctx.author.send(
                    content="📡 **Analytics Warning**\nThis is a one-time notice to inform you that commands used are logged for analytics purposes.\nPlease see the below link for more information.\n> <https://kitchen.0ccu.lt/#Analytics>\n\nIf you do not consent to this, please run `stats off` followed by `stats delete`.\nThis will disable user analytics collection for you, and delete your analytics data."
                )
            except:
                # don't save analytics unless user is informed
                return

        if str(ctx.command) not in useranalytics:
            useranalytics[str(ctx.command)] = {
                "success": 0,
                "failure": 0,
            }

        useranalytics[str(ctx.command)]["failure"] += 1
        set_userfile(ctx.author.id, "analytics", json.dumps(useranalytics))

    @Cog.listener()
    async def on_command_completion(self, ctx):
        await self.bot.wait_until_ready()
        userdata = get_botfile("dishusers")
        if (
            ctx.author.bot
            or "nostats" in userdata
            and ctx.author.id in userdata["nostats"]
        ):
            return
        useranalytics = get_userfile(ctx.author.id, "analytics")

        if not useranalytics:
            try:
                await ctx.author.send(
                    content="📡 **Analytics Warning**\nThis is a one-time notice to inform you that commands used are logged for analytics purposes.\nPlease see the below link for more information.\n> <https://kitchen.0ccu.lt/#Analytics>\n\nIf you do not consent to this, please run `stats off` followed by `stats delete`.\nThis will disable user analytics collection for you, and delete your analytics data."
                )
            except:
                # don't save analytics unless user is informed
                return

        if str(ctx.command) not in useranalytics:
            useranalytics[str(ctx.command)] = {
                "success": 0,
                "failure": 0,
            }

        useranalytics[str(ctx.command)]["success"] += 1
        set_userfile(ctx.author.id, "analytics", json.dumps(useranalytics))


async def setup(bot):
    await bot.add_cog(Analytics(bot))
