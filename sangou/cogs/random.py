import discord
import os
import asyncio
import random
from discord.ext import commands
from discord.ext.commands import Cog
import html
import json


class Random(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def peppino(self, ctx):
        """Posts a random Peppino.

        There really isn't much else to this.

        No arguments."""
        folder = "assets/random/peppino"

        await ctx.reply(
            file=discord.File(
                folder
                + "/"
                + random.choice(
                    [
                        f
                        for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f))
                    ]
                )
            ),
            mention_author=False,
        )

    @commands.command()
    async def noise(self, ctx):
        """Posts a random Noise.

        There really isn't much else to this.

        No arguments."""
        folder = "assets/random/noise"

        await ctx.reply(
            file=discord.File(
                folder
                + "/"
                + random.choice(
                    [
                        f
                        for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f))
                    ]
                )
            ),
            mention_author=False,
        )

    @commands.command()
    async def rat(self, ctx):
        """Posts a random Rat.

        There really isn't much else to this.

        No arguments."""
        folder = "assets/random/rat"

        await ctx.reply(
            file=discord.File(
                folder
                + "/"
                + random.choice(
                    [
                        f
                        for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f))
                    ]
                )
            ),
            mention_author=False,
        )

    @commands.command()
    async def gustavo(self, ctx):
        """Posts a random Gustavo.

        There really isn't much else to this.

        No arguments."""
        folder = "assets/random/gustavo"

        await ctx.reply(
            file=discord.File(
                folder
                + "/"
                + random.choice(
                    [
                        f
                        for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f))
                    ]
                )
            ),
            mention_author=False,
        )

    @commands.command()
    async def bench(self, ctx):
        """Posts a random Bench.

        There really isn't much else to this.

        No arguments."""
        folder = "assets/random/bench"

        await ctx.reply(
            file=discord.File(
                folder
                + "/"
                + random.choice(
                    [
                        f
                        for f in os.listdir(folder)
                        if os.path.isfile(os.path.join(folder, f))
                    ]
                )
            ),
            mention_author=False,
        )


async def setup(bot):
    await bot.add_cog(Random(bot))
