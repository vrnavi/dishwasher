import discord
import datetime
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import ismod
from helpers.sv_config import get_config
from helpers.embeds import stock_embed


class OneShot(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.bot_has_permissions(embed_links=True)
    @commands.guild_only()
    @commands.command()
    async def staff(self, ctx):
        """This shows the currently active staff.

        It merges admins and mods together, sorry!

        No arguments."""
        adminrole = self.bot.pull_role(
            ctx.guild, get_config(ctx.guild.id, "staff", "adminrole")
        )
        modrole = self.bot.pull_role(
            ctx.guild, get_config(ctx.guild.id, "staff", "modrole")
        )

        if not adminrole and not modrole:
            return await ctx.reply(
                content="Neither an `adminrole` or a `modrole` are configured...",
                mention_author=False,
            )
        elif not adminrole:
            members = modrole.members
            color = modrole.color
        elif not modrole:
            members = adminrole.members
            color = adminrole.color
        else:
            members = list(dict.fromkeys(adminrole.members + modrole.members))
            color = modrole.color

        if ctx.guild.owner not in members:
            members.append(ctx.guild.owner)
        members = sorted(members, key=lambda v: v.joined_at)

        embed = stock_embed(self.bot)
        embed.color = color
        embed.title = "🛠️ Staff List"
        embed.description = f"Voting requirement is `{int(len(members)/2//1+1)}`."

        online = []
        away = []
        dnd = []
        offline = []
        for m in members:
            u = f"{m.mention}"
            if m.is_on_mobile():
                u += " 📱"
            if m == ctx.guild.owner:
                u += " 👑"
            if m.raw_status == "online":
                online.append(u)
            elif m.raw_status == "offline":
                offline.append(u)
            elif m.raw_status == "dnd":
                dnd.append(u)
            elif m.raw_status == "idle":
                away.append(u)
        if online:
            embed.add_field(
                name=f"🟢 Online [`{len(online)}`/`{len(members)}`]",
                value=f"{', '.join(online)}",
                inline=False,
            )
        if away:
            embed.add_field(
                name=f"🟡 Idle [`{len(away)}`/`{len(members)}`]",
                value=f"{', '.join(away)}",
                inline=False,
            )
        if dnd:
            embed.add_field(
                name=f"🔴 Do Not Disturb [`{len(dnd)}`/`{len(members)}`]",
                value=f"{', '.join(dnd)}",
                inline=False,
            )
        if offline:
            embed.add_field(
                name=f"⚫ Offline [`{len(offline)}`/`{len(members)}`]",
                value=f"{', '.join(offline)}",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.guild_only()
    @commands.command(aliases=["pingmods", "summonmods"])
    async def pingmod(self, ctx):
        """This ping the mods.

        Please only use in case of emergency.

        No arguments."""
        await ctx.reply(
            f"<@&{get_config(ctx.guild.id, 'staff', 'modrole') if get_config(ctx.guild.id, 'staff', 'modrole') else get_config(ctx.guild.id, 'staff', 'adminrole')}>, {ctx.author.display_name} is requesting assistance.",
            mention_author=False,
        )

    @commands.guild_only()
    @commands.command(aliases=["togglemod"])
    async def modtoggle(self, ctx):
        """This toggles your mod role.

        If you have Mod, it will replace it with Ex-Staff.
        Doesn't work for admins.

        No arguments."""
        """[S] Toggles your Staff role.

        If you have Staff, it will replace it with Ex-Staff, and vice versa."""
        staff_role = (
            self.bot.pull_role(ctx.guild, get_config(ctx.guild.id, "staff", "modrole"))
            if self.bot.pull_role(
                ctx.guild, get_config(ctx.guild.id, "staff", "modrole")
            )
            else self.bot.pull_role(
                ctx.guild, get_config(ctx.guild.id, "staff", "adminrole")
            )
        )
        exstaff_role = self.bot.pull_role(
            ctx.guild, get_config(ctx.guild.id, "staff", "exstaffrole")
        )

        if staff_role in ctx.author.roles:
            await ctx.author.remove_roles(
                staff_role, reason="Staff self-unassigned Staff role"
            )
            await ctx.author.add_roles(
                exstaff_role, reason="Staff self-unassigned Staff role"
            )
            await ctx.message.reply(content="`🔴 Staff`", mention_author=False)
        elif exstaff_role in ctx.author.roles:
            await ctx.author.add_roles(
                staff_role, reason="Staff self-assigned Staff role"
            )
            await ctx.author.remove_roles(
                exstaff_role, reason="Staff self-assigned Staff role"
            )
            await ctx.message.reply(content="`🟢 Staff`", mention_author=False)
        else:
            await ctx.reply(
                content="You are unable to use this command.", mention_author=False
            )


async def setup(bot):
    await bot.add_cog(OneShot(bot))
