import discord
from discord.ext import commands
from discord.ext.commands import Cog
import json
from datetime import datetime, timezone
from helpers.checks import check_if_staff
from helpers.datafiles import userlog_event_types, get_guildfile, set_guildfile
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed, sympage


class ModLogs(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_embeds(self, sid: int, user, own: bool = False):
        uid = str(user.id)
        userlog = get_guildfile(sid, "userlog")
        events = ["notes", "tosses", "warns", "kicks", "bans"]

        # Nonexist
        if uid not in userlog:
            embed = stock_embed(self.bot)
            embed.title = "📇 About that log..."
            embed.description = (
                "> "
                + ("This user isn't" if not own else "You aren't")
                + " in the system!"
            )
            return [embed]

        # Empty
        if not userlog[uid]:
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
                name=["📝 Notes", "🚷 Tosses", "⚠️ Warnings", "👢 Kicks", "⛔ Bans"][index],
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
                ["📝", "🚷", "⚠️", "👢", "⛔"][index] + " Recorded " + events[index] + "..."
            )
            if not userlog[uid][event]:
                embed.description = "> This section is empty!"
                embeds.append(embed)
                continue
            for idx, evn in enumerate(userlog[uid][event]):
                embed.add_field(
                    name=["Note", "Toss", "Warning", "Kick", "Ban"][index]
                    + f" {idx+1}",
                    value=f"<t:{evn['timestamp']}:R> on <t:{evn['timestamp']}:f>\n"
                    + f"__Issuer:__ <@{evn['issuer_id']}> ({evn['issuer_id']})\n"
                    + f"__Reason:__ {evn['reason']}",
                    inline=False,
                )
            embeds.append(embed)

        return embeds

    def get_log_embed(self, sid: int, user, event):
        uid = str(user.id)
        userlog = get_guildfile(sid, "userlog")
        embed = stock_embed(self.bot)
        index = ["notes", "tosses", "warns", "kicks", "bans"].index(event)
        author_embed(embed, user)

        # Nonexist
        if uid not in userlog:
            embed.title = "📇 About that log..."
            embed.description = (
                "> "
                + ("This user isn't" if not own else "You aren't")
                + " in the system!"
            )
            return embed

        # Empty
        if not userlog[uid]:
            embed.title = "📇 About that log..."
            embed.description = (
                "> " + ("This user's" if not own else "Your") + " logs are empty!"
            )
            return embed

        # Individual
        embed.title = (
            ["📝", "🚷", "⚠️", "👢", "⛔"][index] + " Recorded " + event + "..."
        )
        if not userlog[uid][event]:
            embed.description = "> This section is empty!"
        else:
            for idx, evn in enumerate(userlog[uid][event]):
                embed.add_field(
                    name=["Note", "Toss", "Warning", "Kick", "Ban"][index]
                    + f" {idx+1}",
                    value=f"<t:{evn['timestamp']}:R> on <t:{evn['timestamp']}:f>\n"
                    + f"__Issuer:__ <@{evn['issuer_id']}> ({evn['issuer_id']})\n"
                    + f"__Reason:__ {evn['reason']}",
                    inline=False,
                )
        return embed

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(name="logs")
    async def logs_cmd(self, ctx, target: discord.User):
        """[S] The full User Logs command."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
        embeds = self.get_log_embeds(ctx.guild.id, target, False)
        if len(embeds) == 1:
            return await ctx.reply(embed=embeds[0], mention_author=False)

        await sympage(self.bot, ctx, embeds, ["📇", "📝", "🚷", "⚠️", "👢", "⛔"])

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["listnotes", "usernotes"])
    async def notes(self, ctx, target: discord.User):
        """[S] Lists notes for a user."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
        embed = self.get_log_embed(ctx.guild.id, target, event="notes")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command()
    async def mylogs(self, ctx, eventtype=None):
        """[U] Lists your Log events."""
        embeds = self.get_log_embeds(ctx.guild.id, ctx.author, True)
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

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def clearevents(self, ctx, target: discord.User, eventtype):
        """[S] Clears all events of given type for a user."""
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
        if not userlog[str(target.id)][eventtype]:
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

        mlog = get_config(ctx.guild.id, "logging", "modlog")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)
        msg = (
            f"🗑 **Cleared {eventtype}**: {ctx.author.mention} cleared"
            f" all {eventtype} events of {target.mention} | "
            f"{safe_name}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        await mlog.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def delevent(self, ctx, target: discord.User, eventtype, index: int):
        """[S] Removes a specific event from a user."""
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
        if not userlog[str(target.id)][eventtype]:
            return await ctx.reply(
                content=f"{target.mention} has no {event}!", mention_author=False
            )
        if not 1 <= index <= len(userlog[str(target.id)[eventtype]]):
            return await ctx.reply(
                content=f"Your index is out of bounds!", mention_author=False
            )
        del userlog[str(target.id)][eventtype][index - 1]
        set_guildfile(ctx.guild.id, "userlog", json.dumps(userlog))
        await ctx.reply(content=f"I've deleted that event.", mention_author=False)

        mlog = get_config(ctx.guild.id, "logging", "modlog")
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)
        msg = (
            f"🗑 **Deleted {eventtype}**: "
            f"{ctx.author.mention} removed "
            f"{eventtype} {index} from {target.mention} | {safe_name}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        await mlog.send(msg)


async def setup(bot):
    await bot.add_cog(ModLogs(bot))
