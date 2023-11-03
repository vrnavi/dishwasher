import random
import discord
from discord.ext import commands
from discord.ext.commands import Cog
import math
import random
import platform
from helpers.checks import check_if_staff
import datetime


class Meme(Cog):
    """
    Meme commands.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.check(check_if_staff)
    @commands.command(hidden=True, name="warm")
    async def warm_member(self, ctx, user: discord.Member):
        """Warms a user :3"""
        celsius = random.randint(15, 100)
        fahrenheit = self.bot.c_to_f(celsius)
        kelvin = self.bot.c_to_k(celsius)
        await ctx.send(
            f"{user.mention} warmed."
            f" User is now {celsius}°C "
            f"({fahrenheit}°F, {kelvin}K)."
        )

    @commands.check(check_if_staff)
    @commands.command(hidden=True, name="chill", aliases=["cold"])
    async def chill_member(self, ctx, user: discord.Member):
        """Chills a user >:3"""
        celsius = random.randint(-50, 15)
        fahrenheit = self.bot.c_to_f(celsius)
        kelvin = self.bot.c_to_k(celsius)
        await ctx.send(
            f"{user.mention} chilled."
            f" User is now {celsius}°C "
            f"({fahrenheit}°F, {kelvin}K)."
        )

    @commands.command(hidden=True, aliases=["thank"])
    async def gild(self, ctx, user: discord.Member):
        """Gives a star to a user"""
        await ctx.send(f"{user.display_name} gets a :star:, yay!")

    @commands.command(hidden=True)
    async def btwiuse(self, ctx):
        """btw i use arch"""
        uname = platform.uname()
        await ctx.send(
            f"BTW I use {platform.python_implementation()} "
            f"{platform.python_version()} on {uname.system} "
            f"{uname.release}"
        )

    @commands.command(hidden=True)
    async def yahaha(self, ctx):
        """secret command"""
        await ctx.send(f"🍂 you found me 🍂")

    @commands.command(hidden=True)
    async def peng(self, ctx):
        """heck tomger"""
        await ctx.send(f"🐧")

    @commands.command(hidden=True, aliases=["outstanding"])
    async def outstandingmove(self, ctx):
        """Posts the outstanding move meme"""
        await ctx.send(
            "https://cdn.discordapp.com/attachments"
            "/371047036348268545/528413677007929344"
            "/image0-5.jpg"
        )

    @commands.command(hidden=True)
    async def bones(self, ctx):
        await ctx.send("https://cdn.discordapp.com/emojis/443501365843591169.png?v=1")

    @commands.command(hidden=True)
    async def headpat(self, ctx):
        await ctx.send("https://cdn.discordapp.com/emojis/465650811909701642.png?v=1")

    @commands.check(check_if_staff)
    @commands.command(hidden=True, name="bam")
    async def bam_member(self, ctx, target: discord.Member):
        """Bams a user owo"""
        if target == self.bot.user:
            return await ctx.send(random_bot_msg(ctx.author.name))

        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        await ctx.send(f"{safe_name} is ̶n͢ow b̕&̡.̷ 👍̡")

    @commands.command(hidden=True)
    async def memebercount(self, ctx):
        """Checks memeber count, as requested by dvdfreitag"""
        await ctx.send("Fuck, IDK, dude.")

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
        """Shows the year of Linux on the desktop"""
        await ctx.send(
            f"{datetime.datetime.now().year} is the year of Linux on the Desktop"
        )


async def setup(bot):
    await bot.add_cog(Meme(bot))
