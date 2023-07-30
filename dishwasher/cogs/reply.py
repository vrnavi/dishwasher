import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import config
import datetime
import asyncio
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class Reply(Cog):
    """
    A cog that stops people from ping replying people who don't want to be.
    """

    def __init__(self, bot):
        self.bot = bot
        self.usercounts = {}
        self.counttimer.start()
        self.last_eval_result = None
        self.previous_eval_code = None

    def cog_unload(self):
        self.counttimer.cancel()

    async def handle_message_with_reference(self, message):
        reference_message = await message.channel.fetch_message(
            message.reference.message_id
        )
        reference_author = reference_message.author
        if (
            message.author.bot
            or not message.guild
            or not message.guild.get_member(reference_author.id)
            or reference_author.id == message.author.id
            or not get_config(message.guild.id, "noreply", "enable")
            or reference_author.get_role(
                get_config(message.guild.id, "noreply", "noreply_role")
            )
            is None
        ):
            return

        staff_role = get_config(message.guild.id, "staff", "staff_role")
        if staff_role and message.author.get_role(staff_role):
            return

        if reference_author in message.mentions:
            if message.author.id not in self.usercounts:
                self.usercounts[message.author.id] = 0
                cutoff_ts = datetime.datetime.now(
                    datetime.timezone.utc
                ) - datetime.timedelta(days=14)
                if message.author.joined_at >= cutoff_ts:
                    return await message.reply(
                        content="**Do not reply ping users who do not wish to be pinged.** As you are new, this first time will not be a violation.",
                        file=discord.File("assets/noreply.png"),
                        mention_author=True,
                    )

            self.usercounts[message.author.id] += 1
            counts = [
                "0️⃣",
                "1️⃣",
                "2️⃣",
                "3️⃣",
                "4️⃣",
                "5️⃣",
                "6️⃣",
                "7️⃣",
                "8️⃣",
                "9️⃣",
                "🔟",
            ]

            if self.usercounts[message.author.id] == 5:
                await message.reply(
                    content=f"{message.guild.get_role(staff_role).mention} | {message.author.mention} reached `5` reply ping violations.",
                    mention_author=False,
                )
                self.usercounts[message.author.id] = 0
                return

            try:
                await message.add_reaction("🗞️")
                await message.add_reaction(counts[self.usercounts[message.author.id]])
                await message.add_reaction("🛑")
            except discord.errors.Forbidden:
                if message.channel.permissions_for(message.guild.me).add_reactions:
                    await message.reply(
                        content=f"**Congratulations, {message.author.mention}, you absolute dumbass.**\nAs your reward for blocking me to disrupt my function, here is a time out, just for you.",
                        mention_author=True,
                    )
                    await message.author.timeout(datetime.timedelta(minutes=10))
                    return

            def check(r, u):
                return (
                    u.id == reference_author.id
                    and str(r.emoji) == "🛑"
                    and r.message.id == message.id
                )

            try:
                await self.bot.wait_for("reaction_add", timeout=15.0, check=check)
            except asyncio.TimeoutError:
                await message.clear_reaction("🛑")
            else:
                await message.clear_reaction("🗞️")
                await message.clear_reaction(counts[self.usercounts[message.author.id]])
                await message.clear_reaction("🛑")
                self.usercounts[message.author.id] -= 1
                await message.add_reaction("👍")
                await message.add_reaction(counts[self.usercounts[message.author.id]])
            return

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def reset(self, ctx, target: discord.Member):
        if target.id not in self.usercounts or self.usercounts[target.id] == 0:
            return await ctx.reply(
                content="This user doesn't have any reply ping violations.",
                mention_author=False,
            )
        else:
            self.usercounts[target.id] = 0
            return await ctx.reply(
                content="This user's reply ping counter has been reset.",
                mention_author=False,
            )

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if message.reference and message.type == discord.MessageType.reply:
            await self.handle_message_with_reference(message)

    @tasks.loop(hours=24)
    async def counttimer(self):
        await self.bot.wait_until_ready()
        self.usercounts = {}


async def setup(bot):
    await bot.add_cog(Reply(bot))
