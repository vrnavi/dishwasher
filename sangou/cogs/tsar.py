import datetime
import discord
import json
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.checks import isadmin
from helpers.datafiles import get_guildfile
from helpers.embeds import stock_embed
from helpers.sv_config import get_raw_config
from helpers.placeholders import random_msg


class TSAR(Cog):
    """
    True. Self. Assignable. Roles.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command()
    async def role(self, ctx, *, role):
        """This gives you a role, if you meet the requirements.

        For a list of all available roles, see the `roles` command.

        - `role`
        The name of the role you want."""
        tsars = get_raw_config(ctx.guild.id)["roles"]
        if not tsars:
            return await ctx.reply(
                content="You cannot get a role when no roles are configured.",
                mention_author=False,
            )
        foundrole = None
        for tsar in tsars:
            if tsar["name"].lower() == role.lower():
                foundrole = tsar
        if not foundrole:
            return await ctx.reply(
                content=f"There is no role named `{role}`.", mention_author=False
            )

        if foundrole["days"]:
            usertracks = get_guildfile(ctx.guild.id, "usertrack")
            if str(ctx.author.id) not in usertracks and foundrole["days"] != 0:
                return await ctx.reply(
                    content=f"You cannot get this role, as you must wait `{foundrole['days'] - 0}` days.",
                    mention_author=False,
                )
            elif foundrole["days"] > usertracks[str(ctx.author.id)]["truedays"]:
                return await ctx.reply(
                    content=f"You cannot get this role, as you must wait `{foundrole['days'] - usertracks[str(ctx.author.id)]['truedays']}` days.",
                    mention_author=False,
                )

        if foundrole["blacklisted"]:
            badroles = [
                self.bot.pull_role(ctx.guild, s)
                for s in foundrole["blacklisted"]
                if self.bot.pull_role(ctx.guild, s)
            ]
            if any([n in ctx.author.roles for n in badroles]):
                return await ctx.reply(
                    content=f"You cannot get this role, as you have {', '.join(['`' + r.name + '`' for r in badroles if r in ctx.author.roles])}.",
                    mention_author=False,
                )

        if foundrole["required"]:
            mustroles = [
                self.bot.pull_role(ctx.guild, s)
                for s in foundrole["required"]
                if self.bot.pull_role(ctx.guild, s)
            ]
            if any([n not in ctx.author.roles for n in mustroles]):
                return await ctx.reply(
                    content=f"You cannot get this role, as you don't have {', '.join(['`' + r.name + '`' for r in mustroles if r not in ctx.author.roles])}.",
                    mention_author=False,
                )

        actualrole = self.bot.pull_role(ctx.guild, foundrole["role"])
        if actualrole in ctx.author.roles:
            await ctx.author.remove_roles(actualrole)
            return await ctx.reply(
                content=f"`{actualrole}` was removed from your roles.",
                mention_author=False,
            )
        else:
            await ctx.author.add_roles(actualrole)
            return await ctx.reply(
                content=f"`{actualrole}` was added to your roles.", mention_author=False
            )

    @commands.bot_has_permissions(embed_links=True)
    @commands.guild_only()
    @commands.command()
    async def roles(self, ctx):
        """This lists all available roles.

        Roles are configured with the `tsar` command by server staff.

        No arguments."""
        tsars = get_raw_config(ctx.guild.id)["roles"]
        embed = stock_embed(self.bot)
        embed.title = "🎫 Assignable Roles"
        embed.description = (
            f"Use `{ctx.prefix}role` with the name to get or remove a role."
        )
        embed.color = discord.Color.gold()
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        if tsars:
            for tsar in tsars:
                role = self.bot.pull_role(ctx.guild, tsar["role"])
                if not role:
                    continue

                fieldval = (
                    f"> **Role:** {role.mention}\n"
                    + f"> **Minimum Days:** `{tsar['days']}`\n"
                    + f"> **Forbidden Roles:** "
                )
                fieldval += (
                    ", ".join(
                        [
                            self.bot.pull_role(ctx.guild, s).mention
                            for s in tsar["blacklisted"]
                            if self.bot.pull_role(ctx.guild, s)
                        ]
                    )
                    if tsar["blacklisted"]
                    else "None"
                )
                fieldval += "\n" + f"> **Required Roles: **"
                fieldval += (
                    ", ".join(
                        [
                            self.bot.pull_role(ctx.guild, s).mention
                            for s in tsar["required"]
                            if self.bot.pull_role(ctx.guild, s)
                        ]
                    )
                    if tsar["required"]
                    else "None" + "\n"
                )
                embed.add_field(
                    name=tsar["name"],
                    value=fieldval,
                    inline=False,
                )
        if not embed.fields:
            embed.add_field(
                name="None",
                value="There are no assignable roles.",
                inline=False,
            )

        return await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(TSAR(bot))
