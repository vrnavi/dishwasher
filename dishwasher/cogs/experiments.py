import config
import datetime
import discord
import json
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.embeds import stock_embed


class Experiments(Cog):
    """
    Nothing in this section is under warranty.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fahstats(self, ctx, teamid: int = 1065045):
        stats = await self.bot.aiojson(f"https://api.foldingathome.org/team/{teamid}")
        embed = stock_embed(self.bot)
        embed.set_author(
            name="Folding@Home",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/FAH_Logo.svg/1894px-FAH_Logo.svg.png",
            url=f"https://stats.foldingathome.org/team/{teamid}",
        )
        embed.set_thumbnail(url=stats["logo"])
        embed.title = f"Statistics for Team {stats['name']}..."
        embed.description = f"This team was founded by {stats['founder']}."
        embed.add_field(
            name=f"📊 Rank",
            value=stats["rank"],
            inline=True,
        )
        embed.add_field(
            name=f"🗳️ Work Units",
            value=stats["wus"],
            inline=True,
        )
        embed.add_field(
            name=f"📈 Score",
            value=stats["score"],
            inline=True,
        )
        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(Experiments(bot))
