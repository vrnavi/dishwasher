import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import json
import re
import datetime
import random
from helpers.checks import ismod
from helpers.sv_config import get_config


class Cotd(Cog):
    """
    A Color of The Day system.
    """

    def __init__(self, bot):
        self.bot = bot
        self.colortimer.start()
        self.voteskip = {}
        self.voteskip_cooldown = []
        self.nocfgmsg = "CoTD isn't set up for this server."
        self.colors = json.load(open("assets/colors.json", "r"))

    def cog_unload(self):
        self.colortimer.cancel()

    def enabled(self, g):
        return all(
            (
                self.bot.pull_role(g, get_config(g.id, "cotd", "cotdrole")),
                get_config(g.id, "cotd", "cotdname"),
            )
        )

    async def roll_colors(self, guild):
        color = random.choice(self.colors)
        cotd_name = get_config(guild.id, "cotd", "cotdname")
        cotd_role = self.bot.pull_role(guild, get_config(guild.id, "cotd", "cotdrole"))
        await cotd_role.edit(
            name=f'{cotd_name} - {color["name"]}',
            color=discord.Colour.from_str(color["hex"]),
            reason=f'Color of The Day: {color["name"]}',
        )
        return color

    def precedence_check(self, guild):
        return datetime.datetime.now() > datetime.datetime.now().replace(
            hour=24 - len(self.voteskip[guild.id]), minute=0, second=0
        )

    @commands.guild_only()
    @commands.command()
    async def cotd(self, ctx):
        """This shows the Color of The Day.

        It requires CoTD to be configured.

        No arguments."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        cotd_role = self.bot.pull_role(
            ctx.guild, get_config(ctx.guild.id, "cotd", "cotdrole")
        )
        inlist = False
        cotdlist = ""
        for i in self.colors:
            if i["hex"] == "#%02x%02x%02x".upper() % cotd_role.color.to_rgb():
                inlist = True
                color = i["hex"]
                cotdlist += f"\n**{i['name']}** *{i['hex']}*"
        if inlist == False:
            await ctx.send(content="The CoTD role's color is not in the color list!")
        embed = discord.Embed(
            title=f"🌈 Today's CoTD is...",
            description=f"{cotdlist}",
            color=discord.Colour.from_str(color),
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(
            text=f"{self.bot.user.name}'s Color of The Day",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_image(url=f"https://singlecolorimage.com/get/{color[1:]}/128x128")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @commands.command()
    async def voteskip(self, ctx):
        """This votes to skip the CoTD.

        It requires CoTD to be configured.
        It will move the reroll time back by an hour.

        No arguments."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)

        if ctx.guild.id in self.voteskip_cooldown:
            return await ctx.reply(
                content=f"Sorry, CoTD skipping is on cooldown. Please try again tomorrow.",
                mention_author=False,
            )

        if ctx.guild.id not in self.voteskip:
            self.voteskip[ctx.guild.id] = []

        if ctx.author.id in self.voteskip[ctx.guild.id]:
            timestamp = int(
                datetime.datetime.now()
                .replace(hour=24 - len(self.voteskip[ctx.guild.id]), minute=0, second=0)
                .timestamp()
            )
            return await ctx.reply(
                content=f"You have already voted to skip this CoTD.\nRerolling will occur `{len(self.voteskip[ctx.guild.id])}` hours earlier on <t:{timestamp}:t>, or <t:{timestamp}:R>.",
                mention_author=False,
            )

        self.voteskip[ctx.guild.id].append(ctx.author.id)

        if self.precedence_check(ctx.guild):
            self.voteskip[ctx.guild.id] = []
            self.voteskip_cooldown.append(ctx.guild.id)
            color = await self.roll_colors(ctx.guild)
            await ctx.reply(
                content=f"Vote to skip the current CoTD has passed.\nThe CoTD has been changed to **{color['name']}** *{color['hex']}*.",
                mention_author=False,
            )
        else:
            timestamp = int(
                datetime.datetime.now()
                .replace(hour=24 - len(self.voteskip[ctx.guild.id]), minute=0, second=0)
                .timestamp()
            )
            await ctx.reply(
                content=f"Your vote to skip has been recorded.\nRerolling will occur `{len(self.voteskip[ctx.guild.id])}` hours earlier on <t:{timestamp}:t>, or <t:{timestamp}:R>.",
                mention_author=False,
            )

    @commands.bot_has_permissions(embed_links=True, manage_roles=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def reroll(self, ctx):
        """This forcibly rerolls the CoTD.

        It requires CoTD to be configured.

        No arguments."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        color = await self.roll_colors(ctx.guild)
        embed = discord.Embed(
            title=f"🌈 The new CoTD is...",
            description=f"**{color['name']}** *{color['hex']}*",
            color=discord.Colour.from_str(color["hex"]),
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(
            text=f"{self.bot.user.name}'s Color of The Day",
            icon_url=self.bot.user.display_avatar.url,
        )
        embed.set_image(
            url=f"https://singlecolorimage.com/get/{color['hex'][1:]}/128x128"
        )
        await ctx.reply(
            embed=embed,
            mention_author=False,
        )

    @tasks.loop(time=[datetime.time(hour=x) for x in range(0, 24)])
    async def colortimer(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds:
            if self.enabled(g):
                if g.id not in self.voteskip:
                    self.voteskip[g.id] = []
                if self.voteskip[g.id] and self.precedence_check(g):
                    self.voteskip[g.id] = []
                    await self.roll_colors(g)
                elif int(datetime.datetime.now().strftime("%H%M")) == 0000:
                    if g.id in self.voteskip_cooldown:
                        self.voteskip_cooldown.remove(g.id)
                    await self.roll_colors(g)


async def setup(bot):
    await bot.add_cog(Cotd(bot))
