import json
import discord
import config
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.datafiles import get_userfile, fill_profile, set_userfile
from helpers.embeds import stock_embed, author_embed


class Shortcuts(Cog):
    """
    Commands to manage Prefixes and Aliases.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(aliases=["prefix"], invoke_without_command=True)
    async def prefixes(self, ctx):
        """This lists all of your prefixes.

        You can manage it with the `add/remove` subcommands.

        No arguments."""
        embed = stock_embed(self.bot)
        embed.title = "📣 Your current prefixes..."
        embed.description = f"Use `{ctx.prefix}{ctx.command} add/remove` to change your prefixes.\nMentioning the bot will always be a prefix."
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
        """This adds a new prefix.

        Prefixes with spaces are welcome.

        - `arg`
        The prefix to add."""
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
        """This removes a prefix.

        Refer to the index in the prefixes command.

        - `number`
        The index of the prefix to remove."""
        profile = fill_profile(ctx.author.id)
        try:
            profile["prefixes"].pop(number - 1)
            set_userfile(ctx.author.id, "profile", json.dumps(profile))
            await ctx.reply(content="Prefix removed.", mention_author=False)
        except IndexError:
            await ctx.reply(content="This prefix does not exist.", mention_author=False)

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(aliases=["alias"], invoke_without_command=True)
    async def aliases(self, ctx):
        """This lists all of your aliases.

        You can manage it with the `add/remove` subcommands.

        No arguments."""
        embed = stock_embed(self.bot)
        embed.title = "⏺️ Your current aliases..."
        embed.description = (
            f"Use `{ctx.prefix}{ctx.command} add/remove` to change your aliases."
        )
        embed.color = ctx.author.color
        author_embed(embed, ctx.author)
        profile = fill_profile(ctx.author.id)
        useraliases = profile["aliases"]
        maxaliases = config.maxaliases if config.maxaliases <= 25 else 25

        for i in range(
            max(maxaliases, len(useraliases))
        ):  # max of 24 prefixes as discord does not allow more than 25 fields in embeds
            try:
                value = (
                    list(useraliases[i].values())[0]
                    + "\n⬇️\n"
                    + list(useraliases[i].keys())[0]
                )
            except (IndexError, TypeError):
                value = "---"
            finally:
                embed.add_field(name=i + 1, value=value)
        await ctx.reply(embed=embed, mention_author=False)

    @aliases.command()
    async def add(self, ctx, command, alias):
        """This adds a new alias.

        Aliases with spaces are welcome.

        - `command`
        The command to alias.
        - `alias`
        The alias to add."""
        profile = fill_profile(ctx.author.id)
        botcommand = self.bot.get_command(command)
        if not botcommand:
            return await ctx.reply(
                content=f"`{command}` is not a valid command.",
                mention_author=False,
            )
        if self.bot.get_command(alias):
            return await ctx.reply(
                content=f"`{alias}` is already a command.",
                mention_author=False,
            )
        maxaliases = config.maxaliases if config.maxaliases <= 25 else 25
        if len(profile["aliases"]) >= maxaliases:
            return await ctx.reply(
                content=f"You have reached your limit of `{config.maxaliases}` aliases.",
                mention_author=False,
            )

        profile["aliases"].append({botcommand.qualified_name: alias})
        set_userfile(ctx.author.id, "profile", json.dumps(profile))
        return await ctx.reply(content="Alias added.", mention_author=False)

    @aliases.command()
    async def remove(self, ctx, number: int):
        """This removes an alias.

        Refer to the index in the aliases command.

        - `number`
        The index of the alias to remove."""
        profile = fill_profile(ctx.author.id)
        try:
            profile["aliases"].pop(number - 1)
            set_userfile(ctx.author.id, "profile", json.dumps(profile))
            await ctx.reply(content="Alias removed.", mention_author=False)
        except IndexError:
            await ctx.reply(content="This alias does not exist.", mention_author=False)


async def setup(bot):
    await bot.add_cog(Shortcuts(bot))
