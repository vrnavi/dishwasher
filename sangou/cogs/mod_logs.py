import discord
from discord.ext import commands
from discord.ext.commands import Cog
import json
from datetime import datetime, timezone
from helpers.checks import ismod, isadmin
from helpers.datafiles import get_guildfile, set_guildfile
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed, sympage


class ModLogs(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_embeds(self, sid: int, user, own: bool = False):
        uid = str(user.id)
        userlog = get_guildfile(sid, "userlog")
        events = ["notes", "tosses", "warns", "kicks", "bans"]

        if uid not in userlog:
            # Nonexist
            embed = stock_embed(self.bot)
            embed.title = "📇 About that log..."
            embed.description = (
                "> "
                + ("This user isn't" if not own else "You aren't")
                + " in the system!"
            )
            return [embed]
        elif not userlog[uid]:
            # Empty
            embed = stock_embed(self.bot)
            embed.title = "📇 About that log..."
            embed.description = (
                "> " + ("This user's" if not own else "Your") + " logs are empty!"
            )
            return [embed]

        embeds = []

        def dayrange(timestamps):
            if not timestamps:
                return 0
            return round((sorted(timestamps)[-1] - sorted(timestamps)[0]) / 86400)

        # Summary
        embed = stock_embed(self.bot)
        author_embed(embed, user)
        embed.title = "📇 Log summary..."

        for index, event in enumerate(events):
            if index < 2 and own:
                continue
            days = dayrange([instance["timestamp"] for instance in userlog[uid][event]])
            embed.add_field(
                name=["📝 Notes", "🚷 Tosses", "⚠️ Warnings", "👢 Kicks", "⛔ Bans"][
                    index
                ],
                value=f"`{len(userlog[uid][event])}` in `{days}` day"
                + ("s" if days != 1 else "")
                + ".",
                inline=True,
            )

        if not own:
            embed.description = (
                "User "
                + ("**is**" if userlog[uid]["watch"]["state"] else "is **not**")
                + " under watch."
            )
            timestamps = []
            for event in events:
                for instance in userlog[uid][event]:
                    timestamps.append(instance["timestamp"])
            days = dayrange(timestamps)
            embed.add_field(
                name="🗃️ Total",
                value=f"`{len(timestamps)}` in `{days}` day"
                + ("s" if days != 1 else "")
                + ".",
                inline=True,
            )
        embeds.append(embed)

        # Individual
        for index, event in enumerate(events):
            embed = stock_embed(self.bot)
            author_embed(embed, user)
            embed.title = (
                ["📝", "🚷", "⚠️", "👢", "⛔"][index]
                + " Recorded "
                + events[index]
                + "..."
            )
            if not userlog[uid][event]:
                embed.description = "> This section is empty!"
                embeds.append(embed)
                continue
            for idx, evn in enumerate(userlog[uid][event]):
                if event == "tosses":
                    lastline = f"__Incident:__ {evn['post_link']}"
                else:
                    lastline = f"__Reason:__ {evn['reason']}"
                embed.add_field(
                    name=["Note", "Toss", "Warning", "Kick", "Ban"][index]
                    + f" {idx+1}",
                    value=f"<t:{evn['timestamp']}:R> on <t:{evn['timestamp']}:f>\n"
                    + f"__Issuer:__ <@{evn['issuer_id']}> ({evn['issuer_id']})\n"
                    + lastline,
                    inline=False,
                )
            embeds.append(embed)

        return embeds

    @commands.bot_has_permissions(
        embed_links=True, add_reactions=True, manage_messages=True
    )
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(name="logs")
    async def logs_cmd(self, ctx, target: discord.User):
        """This shows the user`logs` for a user.

        Use the reactions to view different parts of the log.

        - `target`
        The user to get logs for."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
        embeds = self.get_log_embeds(ctx.guild.id, target, False)
        if len(embeds) == 1:
            return await ctx.reply(embed=embeds[0], mention_author=False)

        await sympage(self.bot, ctx, embeds, ["📇", "📝", "🚷", "⚠️", "👢", "⛔"])

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command(aliases=["listnotes", "usernotes"])
    async def notes(self, ctx, target: discord.User):
        """This shows the notes for a user.

        Useful if you need to see someone's notes quickly.

        - `target`
        The user to get notes for."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
        embeds = self.get_log_embeds(ctx.guild.id, target, False)
        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            await ctx.send(embed=embeds[1])

    @commands.guild_only()
    @commands.command()
    async def mylogs(self, ctx, eventtype=None):
        """This shows your logs.

        For privacy reasons, it won't show Notes, Tosses,
        or total events done on you. By default, shows a summary.

        - `eventtype`
        Whether you want warns, kicks, or bans. Optional."""
        embeds = self.get_log_embeds(ctx.guild.id, ctx.author, True)
        if len(embeds) == 1:
            return await ctx.author.send(embed=embeds[0])
        if not eventtype:
            embeds[0].color = ctx.author.color
            await ctx.author.send(
                content=f"You can use `{ctx.prefix}mylogs warns/kicks/bans` to see specific logs.",
                embed=embeds[0],
            )
            await ctx.message.add_reaction("📨")
            await ctx.reply(
                content="I've DMed your log summary for privacy.", mention_author=False
            )
        elif eventtype == "warns":
            embeds[3].color = ctx.author.color
            await ctx.author.send(embed=embeds[3])
            await ctx.message.add_reaction("📨")
            await ctx.reply(
                content="I've DMed your warnings for privacy.", mention_author=False
            )
        elif eventtype == "kicks":
            embeds[4].color = ctx.author.color
            await ctx.author.send(embed=embeds[4])
            await ctx.message.add_reaction("📨")
            await ctx.reply(
                content="I've DMed your kicks for privacy.", mention_author=False
            )
        elif eventtype == "bans":
            embeds[5].color = ctx.author.color
            await ctx.author.send(embed=embeds[5])
            await ctx.message.add_reaction("📨")
            await ctx.reply(
                content="I've DMed your bans for privacy.", mention_author=False
            )
        else:
            await ctx.reply(
                content="You need to specify either `warns`, `kicks`, or `bans`, not something else!",
                mention_author=False,
            )

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def clearevents(self, ctx, target: discord.User, eventtype):
        """This clears events for a user.

        Useful if you need to give a user a clean slate.

        - `target`
        The user to get notes for.
        - `eventtype`
        The type of event to clear."""
        types = ["notes", "tosses", "warns", "kicks", "bans"]
        eventtype = eventtype.lower()

        if eventtype not in types:
            return await ctx.reply(
                content=f"{eventtype} is not a valid event type.", mention_author=False
            )
        userlog = get_guildfile(ctx.guild.id, "userlog")
        if str(target.id) not in userlog:
            return await ctx.reply(
                content=f"{target.mention} has no logs!", mention_author=False
            )
        elif not userlog[str(target.id)][eventtype]:
            return await ctx.reply(
                content=f"{target.mention} has no {eventtype}!", mention_author=False
            )

        userlog[str(target.id)][eventtype] = []
        set_guildfile(ctx.guild.id, "userlog", json.dumps(userlog))
        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        await ctx.reply(
            content=f"I've cleared all of {target}'s {eventtype}.", mention_author=False
        )

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        msg = (
            f"🗑 **Cleared {eventtype}**: {ctx.author.mention} cleared"
            f" all {eventtype} events of {target.mention} | "
            f"{safe_name}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        await mlog.send(msg)

    @commands.check(isadmin)
    @commands.guild_only()
    @commands.command()
    async def delevent(self, ctx, target: discord.User, eventtype, index: int):
        """This deletes an event for a user.

        Not much more to this. There's no undo.

        - `target`
        The user to delete an event for.
        - `eventtype`
        The type of event to delete.
        - `index`
        The index of the event."""
        types = ["notes", "tosses", "warns", "kicks", "bans"]
        eventtype = eventtype.lower()

        if eventtype not in types:
            return await ctx.reply(
                content=f"{eventtype} is not a valid event type.", mention_author=False
            )
        userlog = get_guildfile(ctx.guild.id, "userlog")
        if str(target.id) not in userlog:
            return await ctx.reply(
                content=f"{target.mention} has no logs!", mention_author=False
            )
        elif not userlog[str(target.id)][eventtype]:
            return await ctx.reply(
                content=f"{target.mention} has no {event}!", mention_author=False
            )
        elif not 1 <= index <= len(userlog[str(target.id)][eventtype]):
            return await ctx.reply(
                content=f"Your index is out of bounds!", mention_author=False
            )

        del userlog[str(target.id)][eventtype][index - 1]
        set_guildfile(ctx.guild.id, "userlog", json.dumps(userlog))
        await ctx.reply(content=f"I've deleted that event.", mention_author=False)

        mlog = self.bot.pull_channel(
            ctx.guild, get_config(ctx.guild.id, "logging", "modlog")
        )
        if not mlog:
            return

        msg = (
            f"🗑 **Deleted {eventtype}**: "
            f"{ctx.author.mention} removed "
            f"{eventtype} {index} from {target.mention} | {safe_name}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        await mlog.send(msg)


async def setup(bot):
    await bot.add_cog(ModLogs(bot))
