import random
import discord
from discord.ext import commands
from discord.ext.commands import Cog
import math
import random
import platform
from helpers.checks import ismod
import datetime


class Meme(Cog):
    """
    Meme commands.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.check(ismod)
    @commands.command(hidden=True, name="warm")
    async def warm_member(self, ctx, user: discord.Member):
        """This warms a user.

        :3

        - `user`
        The user to warm."""
        celsius = random.randint(15, 100)
        fahrenheit = self.bot.c_to_f(celsius)
        kelvin = self.bot.c_to_k(celsius)
        await ctx.send(
            f"{user.mention} warmed."
            f" User is now {celsius}°C "
            f"({fahrenheit}°F, {kelvin}K)."
        )

    @commands.check(ismod)
    @commands.command(hidden=True, name="chill", aliases=["cold"])
    async def chill_member(self, ctx, user: discord.Member):
        """This chills a user.

        >:3

        - `user`
        The user to chill."""
        celsius = random.randint(-50, 15)
        fahrenheit = self.bot.c_to_f(celsius)
        kelvin = self.bot.c_to_k(celsius)
        await ctx.send(
            f"{user.mention} chilled."
            f" User is now {celsius}°C "
            f"({fahrenheit}°F, {kelvin}K)."
        )

    @commands.command(hidden=True)
    async def btwiuse(self, ctx):
        """This is what the bot uses.

        Arch, btw.

        No arguments."""
        uname = platform.uname()
        await ctx.send(
            f"BTW I use {platform.python_implementation()} "
            f"{platform.python_version()} on {uname.system} "
            f"{uname.release}"
        )

    @commands.command(hidden=True)
    async def yahaha(self, ctx):
        """YAHAHA

        🍂🍂🍂

        No arguments."""
        await ctx.send(f"🍂 you found me 🍂")

    @commands.check(ismod)
    @commands.command(hidden=True, name="bam")
    async def bam_member(self, ctx, target: discord.Member):
        """Bams a user.

        owo

        - `target`
        The target to bam."""
        if target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        await ctx.send(f"{safe_name} is ̶n͢ow b̕&̡.̷ 👍̡")

    @commands.command(
        hidden=True,
        aliases=[
            "yotld",
            "yold",
            "yoltd",
            "yearoflinuxondesktop",
            "yearoflinuxonthedesktop",
        ],
    )
    async def yearoflinux(self, ctx):
        """This shows the year of Linux on the Desktop.

        It's current year guys, I swear!
        Ren develops on a Raspberry Pi, so it must be true!

        No arguments."""
        await ctx.send(
            f"{datetime.datetime.now().year} is the year of Linux on the Desktop"
        )


async def setup(bot):
    await bot.add_cog(Meme(bot))
