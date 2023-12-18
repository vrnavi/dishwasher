import discord
import asyncio
import time
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.datafiles import add_job, get_botfile, delete_job
from helpers.embeds import stock_embed, author_embed


class Remind(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(invoke_without_command=True)
    async def reminders(self, ctx):
        """This lists your reminders.

        There's not much more to it.

        No arguments."""
        ctab = get_botfile("timers")
        uid = str(ctx.author.id)
        embed = stock_embed(self.bot)
        embed.title = "⏳ Your current reminders..."
        embed.color = ctx.author.color
        author_embed(embed, ctx.author)
        idx = 0
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            idx = idx + 1
            job_details = ctab["remind"][jobtimestamp][uid]
            addedtime = job_details["added"]
            embed.add_field(
                name=f"`{idx}` | Reminder on <t:{jobtimestamp}:F>",
                value=f"*Added <t:{addedtime}:R>.*\n" f"{job_details['text']}",
                inline=False,
            )
        if not embed.fields:
            embed.description = "You do not have any reminders set."
        await ctx.send(embed=embed)

    @reminders.command()
    async def remove(self, ctx, number: int):
        """This removes a reminder.

        Use the index from the reminders command.

        - `number`
        The index of the reminder to remove."""
        ctab = get_botfile("timers")
        uid = str(ctx.author.id)
        idx = 0
        for jobtimestamp in ctab["remind"]:
            if uid not in ctab["remind"][jobtimestamp]:
                continue
            idx = idx + 1
            if idx == number:
                delete_job(jobtimestamp, "remind", uid)
                await ctx.reply(content="Reminder removed.", mention_author=False)
                return
        await ctx.reply(content="This reminder does not exist.", mention_author=False)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(aliases=["remindme"])
    async def remind(self, ctx, when: str, *, text: str = "something"):
        """This adds a new reminder.

        Spaces are welcome.

        - `when`
        The amount of time to remind you. For example, `5m`, `7w`, or a timestamp.
        - `text`
        The contents of the reminder."""
        if when.isdigit() and len(when) == 10:
            # Timestamp provided, just use that.
            expiry_timestamp = int(when)
        else:
            expiry_timestamp = self.bot.parse_time(when)
        current_timestamp = int(datetime.now().timestamp())

        if current_timestamp + 59 > expiry_timestamp:
            await ctx.message.reply(
                "Either timespan too short (minimum 1 minute from now) or incorrect format (number then unit of time, or timestamp).\nExample: `remindme 3h Watch Hacka Doll.`",
                mention_author=False,
            )
            return

        safe_text = await commands.clean_content().convert(ctx, str(text))

        add_job(
            "remind",
            ctx.author.id,
            {"text": safe_text, "added": current_timestamp},
            expiry_timestamp,
        )

        embed = discord.Embed(
            title="⏰ Reminder added.",
            description=f"You will be reminded in DMs <t:{expiry_timestamp}:R> on <t:{expiry_timestamp}:f>.",
            color=ctx.author.color,
            timestamp=datetime.now(),
        )
        embed.set_author(
            icon_url=ctx.author.display_avatar.url, name=ctx.author.display_name
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        embed.add_field(
            name="📝 Contents",
            value=f"{safe_text}",
            inline=False,
        )

        await ctx.message.reply(
            embed=embed,
            mention_author=False,
        )


async def setup(bot):
    await bot.add_cog(Remind(bot))
