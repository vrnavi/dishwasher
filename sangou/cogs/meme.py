import random
import discord
from discord.ext import commands
from discord.ext.commands import Cog
import math
import random
import platform
import asyncio
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

    @commands.guild_only()
    @commands.command(aliases=["mingpods"], hidden=True)
    async def mingpod(self, ctx):
        """This ming the pods.

        Please use only in emergency of case.

        No arguments."""
        await ctx.reply(
            f"Pod Automing: {ctx.author.mention} (by **{ctx.author}**)",
            mention_author=False,
        )

    @commands.command(hidden=True)
    async def make(self, ctx):
        """This makes you something.

        Only if the bot feels like it, though.

        No arguments?"""
        resp = await ctx.reply(
            content="<:sangoueat:1182927631977558086>", mention_author=False
        )
        await asyncio.sleep(2)
        allowed_mentions = discord.AllowedMentions(replied_user=False)
        await resp.edit(
            content="<:sangouspeak:1182927625161809931>",
            allowed_mentions=allowed_mentions,
        )
        await asyncio.sleep(1)
        if ctx.author.id != 120698901236809728:
            await resp.edit(
                content="<:sangoubruh:1182927627388989491> No.",
                allowed_mentions=allowed_mentions,
            )
        else:
            await resp.edit(
                content="<:sangoucry:1182927628802469958> Okay, okay, soon!",
                allowed_mentions=allowed_mentions,
            )

    @commands.command(hidden=True)
    async def umigame(self, ctx):
        """そのくるしみにきづくにはあまりにものろまだったようで

        なんねんまえかにきえたきおくをまんねんこうらはつなぎゆく

         入力がありません。"""
        umigame = [
            "なんねんまえかにきえたきおくを",
            "まんねんこうらはつなぎゆく",
            "わられたまどのむこうに",
            "あおじろくひかるえさ",
            "みちもかけもせず",
            "まわるつきは",
            "たまごがかえるのを",
            "みまもっているのか",
            "ウミガメのなみだは",
            "しおらしいってきいた",
            "なきながらアナタは",
            "しおらしくわらった",
            "ワニたちのなみだは",
            "うそらしいってきいた",
            "ひろがったあめだまり",
            "まっかにかわった",
            "あしたもきのうもきえたまま",
            "そんなことはだれもがしっている",
            "そのくるしみにきづくには",
            "あまりにものろまだったようで",
            "　　　　のなまえはわすれてとさけんだ",
            "なきながらあなたはヘルメットはずした",
            "　　　　の　　　はわすれてとさけんだ",
            "なきながらあなたはつちにうめた",
            "　　　　の　　　は　　　　とさけんだ",
            "なきながらあなたははりをさした",
            "　　　　の　　　は　　　　と　　　　",
            "なきながらあなたはからだをとかした",
        ]
        await ctx.reply(
            content="`" + random.choice(umigame) + "`", mention_author=False
        )

    @commands.guild_only()
    @commands.command(hidden=True)
    async def egu(self, ctx):
        """DECEARING EGG

        Delicious breakfast

        No arguments."""
        egg = [
            "Return",
            "Regret",
            "Eco-production",
            "Eiffel Tower",
            "DECEARING EGG",
            "Delicious breakfast",
            "DECEARING EGG",
            "Delicious breakfast early evening soup",
            "DECEARING EGG",
            "Delicious antiperspir oeujeuguen",
            "DECEARING EGG",
            "Transportation Eastern maple Egg bag",
            "DECEAR CLEAR DOWN EGG",
            "Delicious antiperspir oeujeugyeu soujoueguen",
            "DECEARING EGUEEGEGEGE EGG",
            "Delicaceness of deep-sea squeeze trees",
            "DECEARING EGG PREPARATION PREPARATION OF EGG",
            "Delicious antiperspir oeujeugyeu soujoueguen soujou eekugegu",
            "DECEARING EGUEEGEGUGE deep-sea EEGEGEGYE EGGTAG",
            "Delicious antiperspir oeujeugyeu soujoueguen soujoueguen soujoueguoku dewaguiguigueguiguigueguigu",
            "DECEARING EGG PREPARATION PREPARATION OF EGG",
            "Eastern Airlines Transportation Education Transportation Education Transportation Education Transportation Education",
            "Dynasty Eastern Airlines Eastern Eastern Antarctica Eastern Antarctica Antarctica Antiguum",
            "Eastern Airlines Transportation Education Transportation Educational Transportation Educational Transport Education",
            "Dynasty Elements Elements of Ezujoujuu Periodic Elements of Ezujou Ezueguoku Ekogeegu Education Transportation Education",
            "Delicious antiperspir oeujeugyeu deejejuguen deejejugjejejjejjejjejjejjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj",
        ]
        await ctx.reply(content="`" + random.choice(egg) + "`", mention_author=False)

    @commands.guild_only()
    @commands.command(hidden=True)
    async def ululu(self, ctx):
        """ululu

        ulululululululululululululululululululu

        No arguments."""

        await ctx.reply(
            content="ululu" + ("lu" * random.randrange(0, 300)), mention_author=False
        )


async def setup(bot):
    await bot.add_cog(Meme(bot))
