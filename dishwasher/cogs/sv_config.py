import json
import os
import discord
import datetime
import config
import asyncio
import yaml
from helpers.checks import check_if_staff, check_if_bot_manager
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.embeds import stock_embed, author_embed
from helpers.sv_config import fill_config, make_config, set_raw_config, model_config


class sv_config(Cog):
    def __init__(self, bot):
        self.bot = bot

    def validate(self, guild, configs):
        for part in configs:
            if part not in model_config:
                raise IndexError
            for key in list(configs[part].keys()):
                if key not in model_config[part]:
                    raise IndexError
                failconvert = None
                if (
                    type(configs[part][key]) == str
                    and not configs[part][key].isnumeric()
                    and model_config[part][key] != "listroleid"
                ):
                    if model_config[part][key] == "channelid":
                        failconvert = True
                        for channel in guild.channels:
                            if channel.name == configs[part][key]:
                                configs[part][key] = channel.id
                                failconvert = False
                                break
                    elif model_config[part][key] == "roleid":
                        failconvert = True
                        for role in guild.roles:
                            if role.name == configs[part][key]:
                                configs[part][key] = role.id
                                failconvert = False
                                break
                    elif model_config[part][key] == "catid":
                        failconvert = True
                        for category in guild.categories:
                            if category.name == configs[part][key]:
                                configs[part][key] = category.id
                                failconvert = False
                                break
                    if failconvert:
                        raise KeyError
                elif model_config[part][key] == "listroleid" and any(
                    [
                        type(rolepart) == str and not rolepart.isnumeric()
                        for rolepart in configs[part][key]
                    ]
                ):
                    newlist = []
                    for rolepart in configs[part][key]:
                        if not rolepart.isnumeric():
                            failconvert = True
                            for role in guild.roles:
                                if role.name == rolepart:
                                    newlist.append(role.id)
                                failconvert = False
                                continue
                            if failconvert:
                                raise KeyError
                        else:
                            newlist.append(rolepart)
                elif (
                    configs[part][key]
                    and type(model_config[part][key]) == type
                    and model_config[part][key] != type(configs[part][key])
                ):
                    raise TypeError
        return configs

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(aliases=["config"], invoke_without_command=True)
    async def configs(self, ctx, guild: discord.Guild = None):
        """[S] Gets the configuration for a guild."""
        if not guild:
            guild = ctx.guild
        if not os.path.exists(f"data/servers/{guild.id}/config.yml"):
            fill_config(guild.id)
        configs = discord.File(f"data/servers/{guild.id}/config.yml")
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

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def reset(self, ctx, guild: discord.Guild = None):
        """[O] Resets the configuration for a guild."""
        if not guild:
            guild = ctx.guild
        make_config(guild.id)
        await ctx.reply(
            content=f"The configuration for **{guild}** has been reset.",
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @configs.command()
    async def stock(self, ctx):
        """[S] Gets the stock configuration."""
        configs = discord.File(f"assets/config.example.yml")
        return await ctx.reply(
            content="Here is the latest stock configuration.",
            file=configs,
            mention_author=False,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @configs.command()
    async def set(self, ctx, guild: discord.Guild = None):
        """[S] Sets the configuration for a guild."""
        if not guild:
            guild = ctx.guild
        if not ctx.message.attachments:
            return await ctx.reply(
                content="Please provide a `config.yml` file.", mention_author=False
            )
        try:
            conffile = await ctx.message.attachments[0].read()
            config = yaml.safe_load(conffile.decode("utf-8"))
        except:
            return await ctx.reply(
                content="Malformed config.yml error.", mention_author=False
            )
        try:
            config = self.validate(guild, config)
        except KeyError:
            return await ctx.reply(
                content="Unable to convert a name to an ID.", mention_author=False
            )
        except TypeError:
            return await ctx.reply(
                content="Typing error, reread the directions.", mention_author=False
            )
        except IndexError:
            return await ctx.reply(
                content="Nonexistent setting error. Compare your config against the `stock` config.",
                mention_author=False,
            )
        set_raw_config(guild.id, config)
        return await ctx.reply(
            content="The configuration has been updated.", mention_author=False
        )


async def setup(bot: Bot):
    await bot.add_cog(sv_config(bot))
