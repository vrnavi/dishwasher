import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import datetime
import json
import asyncio
from helpers.datafiles import get_guildfile, set_guildfile
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed
from helpers.placeholders import random_msg


class ModReport(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleaner.start()

    def cog_unload(self):
        self.cleaner.cancel()

    @commands.dm_only()
    @commands.command()
    async def report(self, ctx):
        """This reports something to a server's staff channel.

        This requires a server's `staffchannel` to be configured.

        No arguments."""
        guilds = [guild for guild in self.bot.guilds if guild.get_member(ctx.author.id)]
        if not guilds:
            return await ctx.reply(
                content="You aren't in any servers with me in them.",
                mention_author=False,
            )
        for guild in guilds:
            if not self.bot.pull_channel(
                guild, get_config(guild.id, "staff", "staffchannel")
            ):
                guilds.remove(guild)
        if not guilds:
            return await ctx.reply(
                content="No servers we share have configured their Staff channels.",
                mention_author=False,
            )
        content = "Select a guild to report to. Send the number only."
        for idx, guild in enumerate(guilds):
            content += f"\n`{idx+1}` **{guild.name}**"

        message = await ctx.send(content=content)

        def messagecheck(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in ["👍", "👎"]

        try:
            response = await self.bot.wait_for(
                "message", timeout=60, check=messagecheck
            )
        except asyncio.TimeoutError:
            return await message.edit(
                content=random_msg("warn_timedout"),
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        if not response.content.isdigit() or 0 > int(response.content) >= len(guilds):
            return await message.edit(
                content="Index provided not valid.",
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        guild = guilds[int(response.content) - 1]
        channel = self.bot.pull_channel(
            guild, get_config(guild.id, "staff", "staffchannel")
        )
        await message.edit(
            content=f"**Guild:** {guild.name}",
            delete_after=5,
            allowed_mentions=discord.AllowedMentions(replied_user=False),
        )
        message = await ctx.send(
            content="**Please send the content of your report.** Max 4000 characters."
        )
        try:
            response = await self.bot.wait_for(
                "message", timeout=600, check=messagecheck
            )
        except asyncio.TimeoutError:
            return await message.edit(
                content=random_msg("warn_timedout"),
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        if len(response.content) > 4000:
            return await message.edit(
                content="Report too long. Shorten it and try again.",
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        report = response.content
        await message.edit(
            content=f"Got it.",
            delete_after=5,
            allowed_mentions=discord.AllowedMentions(replied_user=False),
        )
        message = await ctx.send(
            content="**Would you like to remain anonymous?**\nNote that for abuse purposes, your ID will be temporarily retained for three days regardless.\nThis ID will **not** be checked by either the Staff team or the bot owner unless necessary."
        )
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            return await message.edit(
                content=random_msg("warn_timedout"),
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        anon = False
        if str(reaction.emoji) == "👍":
            anon = True
        await message.edit(
            content=f"Got it. You will{'' if anon else ' not'} remain anonymous",
            delete_after=5,
            allowed_mentions=discord.AllowedMentions(replied_user=False),
        )
        ping = False
        staff_roles = [
            self.bot.pull_role(guild, get_config(guild.id, "staff", "modrole")),
            self.bot.pull_role(guild, get_config(guild.id, "staff", "adminrole")),
        ]
        if any(staff_roles):
            staff_role = next(
                staff_role for staff_role in staff_roles if staff_role is not None
            )
            message = await ctx.send(
                content="**Would you like ping the Staff?**\nPlease use this for urgent matters!"
            )
            await message.add_reaction("👍")
            await message.add_reaction("👎")
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=30.0, check=reactioncheck
                )
            except asyncio.TimeoutError:
                return await message.edit(
                    content=random_msg("warn_timedout"),
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )
            if str(reaction.emoji) == "👍":
                ping = True
            await message.edit(
                content=f"Got it. I will{'' if ping else ' not'} ping the Staff.",
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        embed = stock_embed(self.bot)
        embed.title = "⚠️ New report!"
        embed.description = "```" + report + "```"
        if not anon:
            member = guild.get_member(ctx.author.id)
            embed.set_author(name=member, icon_url=member.display_avatar.url)
            embed.color = member.color
        else:
            embed.set_author(
                name="Anonymous", icon_url=self.bot.user.display_avatar.url
            )
        message = await ctx.send(
            content=f"Is this report correct?{' I will ping the Staff as well.' if ping else ''}",
            embed=embed,
        )
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=120.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            return await message.edit(
                content=random_msg("warn_timedout"),
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        if str(reaction.emoji) == "👎":
            return await message.edit(
                content="Aborted!",
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        reportlog = get_guildfile(guild.id, "reportlog")
        reportlog[int(datetime.datetime.now().timestamp())] = ctx.author.id
        set_guildfile(guild.id, "reportlog", json.dumps(reportlog))
        await channel.send(content=staff_role.mention if ping else "", embed=embed)
        await message.delete()
        return await ctx.send(
            content=f"Your report has been{' anonymously' if anon else ''} sent."
        )

    @commands.guild_only()
    @commands.command()
    async def reprot(self, ctx):
        return await ctx.send(
            content="This incident has been reproted to the proper authorities. Thank you for your tmie."
        )

    @tasks.loop(time=datetime.time(hour=0))
    async def cleaner(self):
        # water go down the hole x2
        for g in self.bot.guilds:
            reportlog = get_guildfile(g.id, "reportlog")
            cleanlog = {}
            for instance, user in reportlog.items():
                if int(datetime.datetime.now().timestamp()) - 259200 > int(instance):
                    cleanlog[instance] = user
        set_guildfile(g.id, "reportlog", json.dumps(cleanlog))


async def setup(bot):
    await bot.add_cog(ModReport(bot))
