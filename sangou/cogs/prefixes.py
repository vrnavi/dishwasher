import json
import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.datafiles import get_userfile, fill_profile, set_userfile
from helpers.embeds import stock_embed, author_embed


class prefixes(Cog):
    """
    Commands for letting users manage their custom prefixes, run command by itself to check prefixes.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(aliases=["prefix"], invoke_without_command=True)
    async def prefixes(self, ctx):
        """[U] Lists all prefixes."""
        embed = stock_embed(self.bot)
        embed.title = "📣 Your current prefixes..."
        embed.description = f"Use `{ctx.prefix}prefix add/remove` to change your prefixes.\nMentioning the bot will always be a prefix."
        embed.color = ctx.author.color
        author_embed(embed, ctx.author)
        profile = fill_profile(ctx.author.id)
        userprefixes = profile["prefixes"]
        maxprefixes = config.maxprefixes if config.maxprefixes <= 25 else 25

        for i in range(
            max(maxprefixes, len(userprefixes))
        ):  # max of 24 prefixes as discord does not allow more than 25 fields in embeds
            try:
                value = userprefixes[i]
            except (IndexError, TypeError):
                value = "---"
            finally:
                embed.add_field(name=i + 1, value=f"{value}")
        await ctx.reply(embed=embed, mention_author=False)

    @prefixes.command()
    async def add(self, ctx, *, arg: str):
        """[U] Adds a new prefix."""
        profile = fill_profile(ctx.author.id)
        maxprefixes = config.maxprefixes if config.maxprefixes <= 25 else 25
        if not len(profile["prefixes"]) >= maxprefixes:
            profile["prefixes"].append(f"{arg} ")
            set_userfile(ctx.author.id, "profile", json.dumps(profile))
            await ctx.reply(content="Prefix added.", mention_author=False)
        else:
            await ctx.reply(
                content=f"You have reached your limit of `{config.maxprefixes}` prefixes.",
                mention_author=False,
            )

    @prefixes.command()
    async def remove(self, ctx, number: int):
        """[U] Removes a prefix."""
        profile = fill_profile(ctx.author.id)
        try:
            profile["prefixes"].pop(number - 1)
            set_userfile(ctx.author.id, "profile", json.dumps(profile))
            await ctx.reply(content="Prefix removed.", mention_author=False)
        except IndexError:
            await ctx.reply(content="This prefix does not exist.", mention_author=False)


async def setup(bot):
    await bot.add_cog(prefixes(bot))
