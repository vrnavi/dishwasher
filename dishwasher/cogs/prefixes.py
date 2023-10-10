import json
import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.datafiles import get_userfile, fill_profile, set_userfile


class prefixes(Cog):
    """
    Commands for letting users manage their custom prefixes, run command by itself to check prefixes.
    """

    def __init__(self, bot):
        self.bot = bot

    def get_userprefix(uid):
        profile = get_userfile(uid, "profile")
        if not profile:
            return []
        return profile["prefixes"]

    @commands.group(aliases=["prefix"], invoke_without_command=True)
    async def prefixes(self, ctx):
        """[U] Lists all prefixes."""
        embed = discord.Embed(
            title="Your current prefixes...",
            description="Mentioning the bot will always be a prefix.",
            color=ctx.author.color,
        )
        embed.set_author(
            icon_url=ctx.author.display_avatar.url, name=ctx.author.display_name
        )
        uid = str(ctx.author.id)
        userprefixes = self.get_userprefix(uid)

        for i in range(
            max(config.maxprefixes, len(userprefixes))
        ):  # max of 24 prefixes as discord does not allow more than 25 fields in embeds
            try:
                value = userprefixes[i]
            except (IndexError, TypeError):
                value = "---"
            finally:
                embed.add_field(name=i + 1, value=f"{value}")
        embed.set_footer(
            text=f"Use {config.prefixes[0]}prefix add/remove to change your prefixes."
        )
        await ctx.reply(embed=embed, mention_author=False)

    @prefixes.command()
    async def add(self, ctx, *, arg: str):
        """[U] Adds a new prefix."""
        userdata = fill_profile(ctx.author.id)
        if not len(userdata["prefixes"]) >= config.maxprefixes:
            userdata["prefixes"].append(f"{arg} ")
            set_userfile(ctx.author.id, "profile", json.dumps(userdata))
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
            set_userfile(ctx.author.id, "profile", json.dumps(userdata))
            await ctx.reply(content="Prefix removed.", mention_author=False)
        except IndexError:
            await ctx.reply(content="This prefix does not exist.", mention_author=False)


async def setup(bot):
    await bot.add_cog(prefixes(bot))
