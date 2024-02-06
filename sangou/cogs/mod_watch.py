import discord
import datetime
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import ismod
from helpers.datafiles import watch_userlog, get_guildfile
from helpers.placeholders import random_msg, create_log_embed
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, createdat_embed, joinedat_embed


class ModWatch(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.nocfgmsg = "Watching isn't set up for this server."

    def enabled(self, g):
        return self.bot.pull_channel(g, get_config(g.id, "staff", "watchchannel"))

    @commands.bot_has_guild_permissions(embed_links=True, create_public_threads=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def watch(self, ctx, target: discord.User):
        """This puts a user under watch.

        Please refer to the watching section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-watching-system/).

        - `target`
        The target to watch."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.bot.check_if_target_is_staff(target):
                return await ctx.send("I cannot watch Staff members.")

        trackerlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "staff", "watchchannel")
        )
        trackerthread = await trackerlog.create_thread(name=f"{target.name} Watchlog")
        embed = stock_embed(self.bot)
        embed.color = target.color
        embed.title = "🔍 User on watch..."
        embed.description = f"ID: `{target.id}`\n**Thread:** {trackerthread.mention}\n**Last Update:** `???`"
        embed.set_author(
            name=f"{target}",
            icon_url=target.display_avatar.url,
        )
        trackermsg = await trackerlog.send(embed=embed)
        watch_userlog(
            ctx.guild.id, target.id, ctx.author, True, trackerthread.id, trackermsg.id
        )
        await ctx.reply(
            content=f"**User is now on watch.**\nRelay thread available at {trackerthread.mention}.",
            mention_author=False,
        )

    @commands.bot_has_guild_permissions(embed_links=True, manage_threads=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def unwatch(self, ctx, target: discord.User):
        """This removes a user under watch.

        Please refer to the watching section of the [documentation](https://3gou.0ccu.lt/as-a-moderator/the-watching-system/).

        - `target`
        The target to unwatch."""
        if not self.enabled(ctx.guild):
            return await ctx.reply(self.nocfgmsg, mention_author=False)
        if target == ctx.author:
            return await ctx.send(
                random_msg("warn_targetself", authorname=ctx.author.name)
            )
        elif target == self.bot.user:
            return await ctx.send(
                random_msg("warn_targetbot", authorname=ctx.author.name)
            )
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
            if self.bot.check_if_target_is_staff(target):
                return await ctx.send("I cannot unwatch Staff members.")

        userlog = get_guildfile(ctx.guild.id, "userlog")
        if userlog[str(target.id)]["watch"]["state"]:
            trackerthread = await self.bot.fetch_channel(
                userlog[str(target.id)]["watch"]["thread"]
            )
            await trackerthread.edit(archived=True)
            trackerlog = self.bot.pull_channel(
                ctx.guild, get_config(ctx.guild.id, "staff", "watchchannel")
            )
            trackermsg = await trackerlog.fetch_message(
                userlog[str(target.id)]["watch"]["message"]
            )
            await trackermsg.delete()
            watch_userlog(ctx.guild.id, target.id, ctx.author, False)
            await ctx.reply("User is now not on watch.", mention_author=False)
        else:
            return await ctx.reply(
                content="User isn't on watch...", mention_author=False
            )

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if not message.content or not message.guild or not self.enabled(message.guild):
            return
        userlog = get_guildfile(message.guild.id, "userlog")
        try:
            if userlog[str(message.author.id)]["watch"]["state"]:
                trackerthread = await self.bot.fetch_channel(
                    userlog[str(message.author.id)]["watch"]["thread"]
                )
                trackerchannel = self.bot.pull_channel(
                    message.guild, get_config(message.guild.id, "staff", "watchchannel")
                )
                trackermsg = await trackerchannel.fetch_message(
                    userlog[str(message.author.id)]["watch"]["message"]
                )

                threadembed = stock_embed(self.bot)
                threadembed.color = message.author.color
                threadembed.description = message.content
                threadembed.set_author(
                    name=f"💬 {message.author} said in #{message.channel.name}...",
                    icon_url=message.author.display_avatar.url,
                    url=message.jump_url,
                )
                await trackerthread.send(embed=threadembed)

                msgembed = stock_embed(self.bot)
                msgembed.color = message.author.color
                msgembed.title = "🔍 User on watch..."
                msgembed.description = f"**ID:** `{message.author.id}`\n**Thread:** {trackerthread.mention}\n**Last Update:** <t:{int(message.created_at.timestamp())}:f>"
                msgembed.set_author(
                    name=f"{self.bot.escape_message(message.author)}",
                    icon_url=message.author.display_avatar.url,
                )
                await trackermsg.edit(content=None, embed=msgembed)
        except KeyError:
            return

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild):
            return
        userlog = get_guildfile(member.guild.id, "userlog")
        try:
            if userlog[str(member.id)]["watch"]["state"]:
                trackerthread = await self.bot.fetch_channel(
                    userlog[str(member.id)]["watch"]["thread"]
                )
                trackerchannel = self.bot.pull_channel(
                    member.guild, get_config(member.guild.id, "staff", "watchchannel")
                )
                trackermsg = await trackerchannel.fetch_message(
                    userlog[str(member.id)]["watch"]["message"]
                )
                invite_used = await self.bot.get_used_invites(member)

                threadembed = stock_embed(self.bot)
                threadembed.color = discord.Color.lighter_gray()
                threadembed.title = "📥 User Joined"
                threadembed.description = f"{member.mention} ({member.id})"
                threadembed.set_thumbnail(url=member.display_avatar.url)
                threadembed.set_author(
                    name=member,
                    icon_url=member.display_avatar.url,
                )
                createdat_embed(threadembed, member)
                threadembed.add_field(
                    name="📨 Invite used:", value=invite_used, inline=True
                )
                await trackerthread.send(embed=threadembed)

                msgembed = stock_embed(self.bot)
                msgembed.title = "🔍 User on watch..."
                msgembed.description = f"**ID:** `{member.id}`\n**Thread:** {trackerthread.mention}\n**Last Update:** <t:{int(datetime.datetime.now().timestamp())}:f>"
                msgembed.set_author(
                    name=f"{self.bot.escape_message(member)}",
                    icon_url=member.display_avatar.url,
                )
                await trackermsg.edit(content=None, embed=msgembed)
        except KeyError:
            return

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if not self.enabled(member.guild):
            return
        userlog = get_guildfile(member.guild.id, "userlog")
        try:
            if userlog[str(member.id)]["watch"]["state"]:
                trackerthread = await self.bot.fetch_channel(
                    userlog[str(member.id)]["watch"]["thread"]
                )
                trackerchannel = self.bot.pull_channel(
                    member.guild, get_config(member.guild.id, "staff", "watchchannel")
                )
                trackermsg = await trackerchannel.fetch_message(
                    userlog[str(member.id)]["watch"]["message"]
                )

                threadembed = stock_embed(self.bot)
                threadembed.color = discord.Color.darker_gray()
                threadembed.title = "📥 User Left"
                threadembed.description = f"{member.mention} ({member.id})"
                threadembed.set_thumbnail(url=member.display_avatar.url)
                threadembed.set_author(
                    name=member,
                    icon_url=member.display_avatar.url,
                )
                createdat_embed(threadembed, member)
                joinedat_embed(threadembed, member)
                await trackerthread.send(embed=threadembed)

                msgembed = stock_embed(self.bot)
                msgembed.title = "🔍 User on watch..."
                msgembed.description = f"**ID:** `{member.id}`\n**Thread:** {trackerthread.mention}\n**Last Update:** <t:{int(datetime.datetime.now().timestamp())}:f>"
                msgembed.set_author(
                    name=f"{self.bot.escape_message(member)}",
                    icon_url=member.display_avatar.url,
                )
                await trackermsg.edit(content=None, embed=msgembed)
        except KeyError:
            return


async def setup(bot):
    await bot.add_cog(ModWatch(bot))
