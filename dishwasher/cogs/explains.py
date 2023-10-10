import discord
import json
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff
from helpers.embeds import stock_embed
from helpers.datafiles import get_guildfile, set_guildfile


class Snippets(Cog):
    """
    Commands for easily explaining things.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.group(aliases=["snip"], invoke_without_command=True)
    async def snippet(self, ctx, *, name=None):
        """[U] Staff defined tags."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if not name:
            embed = stock_embed(self.bot)
            embed.title = "✂️ Configured Snippets"
            embed.color = discord.Color.red()
            embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
            if not snippets:
                embed.add_field(
                    name="None",
                    value="There are no configured snippets.",
                    inline=False,
                )
            else:
                for name, snippet in list(snippets.items()):
                    embed.add_field(
                        name=name,
                        value="> " + snippet[:200] + "..."
                        if len(snippet) > 200
                        else "> " + snippet,
                        inline=False,
                    )

            return await ctx.reply(embed=embed, mention_author=False)
        else:
            if name.lower() not in snippets:
                return
            return await ctx.reply(content=snippets[name.lower()], mention_author=False)

    @commands.check(check_if_staff)
    @snippet.command()
    async def create(self, ctx, name, *, contents):
        """Creates a new snippet."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if name.lower() in snippets:
            return await ctx.reply(
                content=f"`{name}` is already a snippet.",
                mention_author=False,
            )
        elif len(contents.split()) == 1 and contents in snippets:
            return await ctx.reply(
                content=f"Aliasing is not currently supported yet.",
                mention_author=False,
            )
        snippets[name.lower()] = contents
        set_guildfile(ctx.guild.id, "snippets", json.dumps(snippets))
        await ctx.reply(
            content=f"`{name.lower()}` has been saved.",
            mention_author=False,
        )

    @commands.check(check_if_staff)
    @snippet.command()
    async def delete(self, ctx, name):
        """Deletes a snippet."""
        snippets = get_guildfile(ctx.guild.id, "snippets")
        if name.lower() not in snippets:
            return await ctx.reply(
                content=f"`{name.lower()}` is not a snippet.",
                mention_author=False,
            )
        del snippets[name.lower()]
        set_guildfile(ctx.guild.id, "snippets", json.dumps(snippets))
        await ctx.reply(
            content=f"`{name.lower()}` has been deleted.",
            mention_author=False,
        )


async def setup(bot):
    await bot.add_cog(Snippets(bot))
