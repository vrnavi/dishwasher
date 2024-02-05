import json
import os
import discord
import datetime
import config
import asyncio
import yaml
from helpers.checks import isadmin, ismanager
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.embeds import stock_embed, author_embed
from helpers.sv_config import fill_config, make_config, set_raw_config, validate_config


class sv_config(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.check(isadmin)
    @commands.bot_has_permissions(embed_links=True, attach_files=True)
    @commands.group(aliases=["config"], invoke_without_command=True)
    async def configs(self, ctx):
        """This gets the configuration for your server.

        Please see the [documentation](https://3gou.0ccu.lt/as-an-administrator/server-configuration/) for more information.

        No arguments."""
        if not os.path.exists(f"data/servers/{ctx.guild.id}/config.yml"):
            fill_config(ctx.guild.id)
        configs = discord.File(f"data/servers/{ctx.guild.id}/config.yml")
        embed = stock_embed(self.bot)
        author_embed(embed, ctx.author)
        embed.title = "⚙️ Your server's configuration..."
        embed.description = (
            f"- `{ctx.prefix}configs set` to set the server configuration file.\n"
            + f"- `{ctx.prefix}configs reset` to reset the server configuration file.\n"
            + f"- `{ctx.prefix}configs stock` to view the latest stock configuration file."
        )
        embed.color = ctx.author.color

        return await ctx.reply(embed=embed, file=configs, mention_author=False)

    @commands.check(ismanager)
    @configs.command()
    async def reset(self, ctx, guild: discord.Guild = None):
        """This resets the configuration for a guild.

        Dev only command. Server admins should use the `stock` command.

        - `guild`
        The guild to reset configs for."""
        if not guild:
            guild = ctx.guild
        make_config(guild.id)
        await ctx.reply(
            content=f"The configuration for **{guild}** has been reset.",
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(isadmin)
    @commands.bot_has_permissions(attach_files=True)
    @configs.command()
    async def stock(self, ctx):
        """This gets the latest stock configuration.

        Stock configurations include comments to aid in filling out.

        No arguments."""
        configs = discord.File(f"assets/config.example.yml")
        return await ctx.reply(
            content="Here is the latest stock configuration.",
            file=configs,
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(isadmin)
    @configs.command()
    async def set(self, ctx, attachment: discord.Attachment):
        """This sets the guild configuration.

        If it tells you the config is invalid, please compare
        against the `stock` configuration.

        - `attachment`
        The config file, upload this please."""
        try:
            conffile = await attachment.read()
            config = yaml.safe_load(conffile.decode("utf-8"))
        except:
            return await ctx.reply(
                content="Malformed config.yml error.", mention_author=False
            )
        try:
            validate_config(config)
        except Exception as e:
            return await ctx.reply(
                f"I had trouble understanding what you wanted.\nIn `{e.json_path}` as `{e.instance}`:\n```{e.message}```",
                mention_author=False,
            )
        set_raw_config(ctx.guild.id, config)
        return await ctx.reply(
            content="The configuration has been updated.", mention_author=False
        )


async def setup(bot: Bot):
    await bot.add_cog(sv_config(bot))
