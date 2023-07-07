import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import json
import re
import datetime
import random
from helpers.checks import check_if_staff, check_if_bot_manager
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

    async def roll_colors(self, guild):
        color = random.choice(self.colors)
        cotd_name = get_config(guild.id, "cotd", "cotd_name")
        cotd_role = guild.get_role(get_config(guild.id, "cotd", "cotd_role"))
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
        if not get_config(ctx.guild.id, "cotd", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        cotd_role = ctx.guild.get_role(get_config(ctx.guild.id, "cotd", "cotd_role"))
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
        if not get_config(ctx.guild.id, "cotd", "enable"):
            return await ctx.reply(self.nocfgmsg, mention_author=False)

        if ctx.guild.id in self.voteskip_cooldown:
            return await ctx.reply(
                content=f"Sorry, CoTD skipping is on cooldown. Please try again tomorrow.",
                mention_author=False,
            )

        if ctx.guild.id not in self.voteskip:
            self.voteskip[ctx.guild.id] = []

        if ctx.author.id in self.voteskip[ctx.guild.id]:
            timestamp = (
                datetime.datetime.now()
                .replace(hour=24 - len(self.voteskip[ctx.guild.id]), minute=0, second=0)
                .strftime("%s")
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
            timestamp = (
                datetime.datetime.now()
                .replace(hour=24 - len(self.voteskip[ctx.guild.id]), minute=0, second=0)
                .strftime("%s")
            )
            await ctx.reply(
                content=f"Your vote to skip has been recorded.\nRerolling will occur `{len(self.voteskip[ctx.guild.id])}` hours earlier on <t:{timestamp}:t>, or <t:{timestamp}:R>.",
                mention_author=False,
            )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def reroll(self, ctx):
        if not get_config(ctx.guild.id, "cotd", "enable"):
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

    @commands.guild_only()
    @commands.check(check_if_bot_manager)
    @commands.command()
    async def voidroll(self, ctx):
        void_role = ctx.guild.get_role(1126763114562605056)
        void_color = random.choice("0123456789abcdef") * 6
        if void_color == "000000" or void_color == "ffffff":
            void_color = str(hex(int(void_color, 16) - 1))[2:]
        await void_role.edit(
            name=f"Void Phosphor - {void_color}",
            color=discord.Colour.from_str(void_color),
            reason=f"???: #{void_color}",
        )

    @tasks.loop(time=[datetime.time(hour=x) for x in range(0, 24)])
    async def colortimer(self):
        await self.bot.wait_until_ready()
        for g in self.bot.guilds:
            if g.id == 256926147827335170:
                void_role = g.get_role(1126763114562605056)
                void_color = random.choice("0123456789abcdef") * 6
                if void_color == "000000" or void_color == "ffffff":
                    void_color = str(hex(int(void_color, 16) - 1))[2:]
                await void_role.edit(
                    name=f"Void Phosphor - #{void_color}",
                    color=discord.Colour.from_str("#" + void_color),
                    reason=f"???: #{void_color}",
                )
            if get_config(g.id, "cotd", "enable"):
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
