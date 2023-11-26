import json
import discord
import datetime
import config
import asyncio
from helpers.checks import check_if_staff, check_if_bot_manager
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.embeds import stock_embed
from helpers.sv_config import (
    fill_config,
    make_config,
    set_config,
    stock_configs,
    friendly_names,
)


class sv_config(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.group(invoke_without_command=True)
    async def configs(self, ctx, guild: discord.Guild = None):
        """[S] Gets the configuration for a guild."""
        if not guild:
            guild = ctx.guild
        configs = fill_config(guild.id)

        navigation_reactions = ["⏹", "⬅️", "➡", "⬆", "⬇️", "⏺"]

        embed = stock_embed(self.bot)
        embed.title = "⚙️ Server Configuration Editor"
        embed.color = ctx.author.color
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="⏳", value="Loading...", inline=False)
        hindex = 1
        hlimit = len(configs.items())
        vindex = 0
        pagemode = "play"
        configmsg = await ctx.reply(embed=embed, mention_author=False)
        for e in navigation_reactions:
            await configmsg.add_reaction(e)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in navigation_reactions

        def messagecheck(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        while True:
            page = list(configs.items())[hindex - 1]
            vlimit = len(page[1])
            embed.description = f"Page `{hindex}` of `{hlimit}` for server {guild}.\nTweak a setting with `{ctx.prefix}configs set {page[0]} <setting> <value>`."
            lines = ""
            for i, (k, v) in enumerate(page[1].items()):
                friendly = f"**{friendly_names[k]}**\n" if k in friendly_names else ""
                if pagemode == "rec" and vindex == i + 1:
                    setting = f"> **`{k}`**"
                    key = k
                    value = v
                else:
                    setting = f"`{k}`" if vindex != i + 1 else f"> `{k}`"
                if not v and str(v) != "False" and str(v) != "None":
                    v = f"Not Configured ({type(v).__name__})"
                if str(v) == "None":
                    v = "Forcibly Disabled"
                lines += f"\n{friendly}{setting}\n{v}"
            embed.set_field_at(
                index=0,
                name=page[0].title(),
                value=lines,
                inline=False,
            )
            allowed_mentions = discord.AllowedMentions(replied_user=False)
            await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

            if pagemode == "play":
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=30.0, check=reactioncheck
                    )
                except asyncio.TimeoutError:
                    return await configmsg.edit(
                        content="Operation timed out.",
                        embed=None,
                        delete_after=5,
                        allowed_mentions=allowed_mentions,
                    )

                if str(reaction) == "⏹":
                    return await configmsg.edit(
                        content="Operation cancelled.",
                        embed=None,
                        delete_after=5,
                        allowed_mentions=allowed_mentions,
                    )
                elif str(reaction) == "⬅️":
                    if hindex != 1:
                        hindex -= 1
                    vindex = 0
                    await configmsg.remove_reaction("⬅️", ctx.author)
                elif str(reaction) == "➡":
                    if hindex != hlimit:
                        hindex += 1
                    vindex = 0
                    await configmsg.remove_reaction("➡", ctx.author)
                elif str(reaction) == "⬆":
                    if vindex != 0:
                        vindex -= 1
                    await configmsg.remove_reaction("⬆", ctx.author)
                elif str(reaction) == "⬇️":
                    if vindex != vlimit:
                        vindex += 1
                    await configmsg.remove_reaction("⬇️", ctx.author)
                elif str(reaction) == "⏺":
                    pagemode = "rec"
                    await configmsg.remove_reaction("⏺", ctx.author)
                    continue
            elif pagemode == "rec":
                if configs[page[0]][key] == None:
                    await ctx.send(
                        content="This setting has been administratively disabled by the bot owner. You cannot edit it.",
                        delete_after=5,
                    )
                    pagemode = "play"
                    continue
                editingmsg = f"**Editing** the setting `{key}`.\n\nThis setting is a"
                settingtype = type(configs[page[0]][key]).__name__
                if settingtype == "str":
                    editingmsg += " string. Set this by replying with whatever."
                elif settingtype == "int":
                    editingmsg += "n integer. Set this by replying with a number."
                elif settingtype == "list":
                    editingmsg += " list. Set this by replying with a list of whatevers, separated by spaces.\nYou can also prefix the list with `add` or `del` to add or remove specific items."
                elif settingtype == "bool":
                    editingmsg += (
                        " boolean. Set this by replying with `true` or `false`."
                    )
                elif settingtype == "dict":
                    editingmsg += f" dictionary, and requires in-depth configuration. You must configure this from a different command, `{page[0].lower()}`."
                    pagemode = "play"
                    continue
                if value:
                    editingmsg += '\nYou can also reply with "none" to remove the current value, or "stop" to cancel the operation.'
                configsuppmsg = await ctx.send(content=editingmsg)

                try:
                    message = await self.bot.wait_for(
                        "message", timeout=300.0, check=messagecheck
                    )
                except asyncio.TimeoutError:
                    await configsuppmsg.delete()
                    return await configmsg.edit(
                        content="Operation timed out.",
                        embed=None,
                        delete_after=5,
                        allowed_mentions=allowed_mentions,
                    )

                if message.content == "stop":
                    await configsuppmsg.delete()
                    return await configmsg.edit(
                        content="Operation cancelled.",
                        embed=None,
                        delete_after=5,
                        allowed_mentions=allowed_mentions,
                    )
                elif key == "enable" and message.content == "true":
                    for k, v in configs[page[0]].items():
                        if not v and type(v).__name__ != "bool":
                            await ctx.send(
                                content="This setting cannot be changed unless the other settings in the category are properly configured.\nPlease configure these settings first, then try again.",
                                delete_after=5,
                            )
                            pagemode = "play"
                            continue

                try:
                    configs = set_config(ctx.guild.id, page[0], key, message.content)
                except:
                    await configsuppmsg.edit(
                        content="You gave an invalid value. Please try again while following the instructions of what to send.",
                        delete_after=5,
                    )
                    pagemode = "play"
                    continue
                else:
                    await configsuppmsg.edit(
                        content=f"**{page[0].title()}/**`{key}` has been updated with a new value of `{configs[page[0]][key]}`.",
                        delete_after=5,
                    )
                    pagemode = "play"
                    continue

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
    async def set(self, ctx, category, setting, *, value=None):
        """[S] Sets the configuration for a guild."""
        configs = fill_config(ctx.guild.id)
        category = category.lower()
        setting = setting.lower()
        if category not in configs or setting not in configs[category]:
            if category not in stock_configs or setting not in stock_configs[category]:
                return await ctx.reply(
                    content="You specified an invalid category or setting.",
                    mention_author=False,
                )
            else:
                configs = set_config(
                    ctx.guild.id, category, setting, stock_configs[category][setting]
                )
        if configs[category][setting] == None:
            return await ctx.reply(
                content="This setting has been administratively disabled by the bot owner.",
                mention_author=True,
            )
        elif configs[category][setting] == "enable" and value == "true":
            for k, v in configs[category].items():
                if not v and type(v).__name__ != "bool":
                    return await ctx.reply(
                        content="This setting cannot be changed unless the other settings in the category are properly configured.\nPlease configure these settings first, then try again.",
                        mention_author=False,
                    )

        try:
            configs = set_config(ctx.guild.id, category, setting, value)
            return await ctx.reply(
                content=f"**{category.title()}/**`{setting}` has been updated with a new value of `{configs[category][setting]}`.",
                mention_author=False,
            )
        except:
            return await ctx.reply(
                content="You gave an invalid value. If you don't know what you're doing, use `pls configs` interactively.",
                mention_author=False,
            )

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def disable(self, ctx, guild: discord.Guild, category, setting):
        """[O] Forcibly disables a setting for a guild."""
        configs = fill_config(ctx.guild.id)
        if category not in configs or setting not in configs[category]:
            configs = set_config(
                ctx.guild.id, category, setting, stock_configs[category][setting]
            )
        set_config(ctx.guild.id, category, setting, None)
        return await ctx.reply(
            content=f"{guild}'s **{category.title()}/**`{setting}` has been DISABLED.",
            mention_author=False,
        )

    @commands.check(check_if_bot_manager)
    @configs.command()
    async def enable(self, ctx, guild: discord.Guild, category, setting):
        """[O] Forcibly enables a setting for a guild."""
        configs = fill_config(ctx.guild.id)
        if category not in configs or setting not in configs[category]:
            configs = set_config(
                ctx.guild.id, category, setting, stock_configs[category][setting]
            )
        defaults = {
            "str": "",
            "bool": False,
            "int": 0,
            "list": [],
        }
        set_config(
            ctx.guild.id,
            category,
            setting,
            defaults[type(stock_configs[category][setting]).__name__],
        )
        return await ctx.reply(
            content=f"{guild}'s **{category.title()}/**`{setting}` has been ENABLED.",
            mention_author=False,
        )


async def setup(bot: Bot):
    await bot.add_cog(sv_config(bot))
