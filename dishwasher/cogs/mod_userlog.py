import discord
from discord.ext import commands
from discord.ext.commands import Cog
import json
from datetime import datetime, timezone
from helpers.checks import check_if_staff
from helpers.userlogs import get_userlog, set_userlog, userlog_event_types
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, author_embed


class ModUserlog(Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_userlog_embed_for_id(self, sid: int, user, own: bool = False, event=""):
        uid = str(user.id)
        userlog = get_userlog(sid)
        embed = stock_embed(self.bot)
        author_embed(embed, user)
        embed.title = f"📜 Recorded logs..."
        if uid not in userlog:
            embed.description = f"> Not in system."
            return embed

        wanted_events = ["warns", "kicks", "bans"]
        if not own:
            wanted_events = ["tosses"] + wanted_events
        if event and not isinstance(event, list):
            wanted_events = [event]

        for event_type in wanted_events:
            if event_type in userlog[uid] and userlog[uid][event_type]:
                event_name = userlog_event_types[event_type]
                contents = ""
                for idx, event in enumerate(userlog[uid][event_type]):
                    issuer = (
                        ""
                        if own
                        else f"__Issuer:__ <@{event['issuer_id']}> "
                        f"({event['issuer_id']})\n"
                    )
                    timestamp = datetime.strptime(
                        event["timestamp"], "%Y-%m-%d %H:%M:%S"
                    ).strftime("%s")
                    contents += (
                        f"\n`{event_name} {idx + 1}` <t:{timestamp}:R> on <t:{timestamp}:f>\n"
                        + issuer
                        + f"__Reason:__ {event['reason']}\n"
                    )
                if len(contents) != 0:
                    embed.add_field(
                        name=event_type.capitalize(),
                        value=contents,
                        inline=False,
                    )

        if not embed.fields:
            embed.color = discord.Color.green()
        else:
            embed.color = discord.Color.orange()

        if not own:
            if userlog[uid]["watch"]["state"]:
                watch_state = "is"
                embed.color = discord.Color.dark_red()
            else:
                watch_state = "is not"
            embed.description = f"🔎 *User **{watch_state}** under watch, and has `{len(userlog[uid]['notes'])}` note{'s' if len(userlog[uid]['notes']) != 1 else ''}.*"
        else:
            embed.description = f""

        if not embed.fields:
            embed.description += f"\n> No logs recorded."

        return embed

    def clear_event_from_id(self, sid: int, uid: str, event_type):
        userlog = get_userlog(sid)
        if uid not in userlog:
            return f"<@{uid}> has no {event_type}!"
        event_count = len(userlog[uid][event_type])
        if not event_count:
            return f"<@{uid}> has no {event_type}!"
        userlog[uid][event_type] = []
        set_userlog(sid, json.dumps(userlog))
        return f"<@{uid}> no longer has any {event_type}!"

    def delete_event_from_id(self, sid: int, uid: str, idx: int, event_type):
        userlog = get_userlog(sid)
        if uid not in userlog:
            return f"<@{uid}> has no {event_type}!"
        event_count = len(userlog[uid][event_type])
        if not event_count:
            return f"<@{uid}> has no {event_type}!"
        if idx > event_count:
            return "Index is higher than " f"count ({event_count})!"
        if idx < 1:
            return "Index is below 1!"
        event = userlog[uid][event_type][idx - 1]
        event_name = userlog_event_types[event_type]
        embed = discord.Embed(
            color=discord.Color.dark_red(),
            title=f"{event_name} {idx} on " f"{event['timestamp']}",
            description=f"Issuer: {event['issuer_name']}\n"
            f"Reason: {event['reason']}",
        )
        del userlog[uid][event_type][idx - 1]
        set_userlog(sid, json.dumps(userlog))
        return embed

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["events"])
    async def eventtypes(self, ctx):
        """[S] Lists available event types."""
        event_list = [f"{et} ({userlog_event_types[et]})" for et in userlog_event_types]
        event_text = "Available events:\n``` - " + "\n - ".join(event_list) + "```"
        await ctx.send(event_text)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(name="userlog", aliases=["logs"])
    async def userlog_cmd(self, ctx, target: discord.User, event=""):
        """[S] Lists userlog events for a user."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
        embed = self.get_userlog_embed_for_id(ctx.guild.id, target, event=event)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["listnotes", "usernotes"])
    async def notes(self, ctx, target: discord.User):
        """[S] Lists notes for a user."""
        if ctx.guild.get_member(target.id):
            target = ctx.guild.get_member(target.id)
        embed = self.get_userlog_embed_for_id(ctx.guild.id, target, event="notes")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(
        aliases=[
            "mywarns",
            "mylogs",
        ]
    )
    async def myuserlog(self, ctx):
        """[U] Lists your userlog events (warns, etc)."""
        embed = self.get_userlog_embed_for_id(ctx.guild.id, ctx.author, True)
        await ctx.author.send(embed=embed)
        await ctx.message.add_reaction("📨")
        await ctx.reply(
            content="For privacy, your logs have been DMed.", mention_author=False
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clearwarns"])
    async def clearevent(self, ctx, target: discord.User, event="warns"):
        """[S] Clears all events of given type for a user."""
        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        msg = self.clear_event_from_id(ctx.guild.id, str(target.id), event)
        safe_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, str(target)
        )
        await ctx.send(msg)
        msg = (
            f"🗑 **Cleared {event}**: {ctx.author.mention} cleared"
            f" all {event} events of {target.mention} | "
            f"{safe_name}"
            f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
        )
        if not mlog:
            return
        mlog = await self.bot.fetch_channel(mlog)
        await mlog.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["delwarn"])
    async def delevent(self, ctx, target: discord.User, idx: int, event="warns"):
        """[S] Removes a specific event from a user."""
        mlog = get_config(ctx.guild.id, "logs", "mlog_thread")
        del_event = self.delete_event_from_id(ctx.guild.id, str(target.id), idx, event)
        event_name = userlog_event_types[event].lower()
        # This is hell.
        if isinstance(del_event, discord.Embed):
            await ctx.send(f"{target.mention} has a {event_name} removed!")
            safe_name = await commands.clean_content(escape_markdown=True).convert(
                ctx, str(target)
            )
            msg = (
                f"🗑 **Deleted {event_name}**: "
                f"{ctx.author.mention} removed "
                f"{event_name} {idx} from {target.mention} | {safe_name}"
                f"\n🔗 __Jump__: <{ctx.message.jump_url}>"
            )
            if not mlog:
                return
            mlog = await self.bot.fetch_channel(mlog)
            await mlog.send(msg, embed=del_event)
        else:
            await ctx.send(del_event)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def fullinfo(self, ctx, *, target: discord.User = None):
        """[S] Gets full user info."""
        if not target:
            target = ctx.author

        embeds = []

        if not ctx.guild.get_member(target.id):
            # Memberless code.
            color = discord.Color.lighter_gray()
            nickname = ""
        else:
            # Member code.
            target = ctx.guild.get_member(target.id)
            color = target.color
            nickname = f"\n**Nickname:** `{target.nick}`"

        embed = discord.Embed(
            color=color,
            title=f"Info for {'user' if ctx.guild.get_member(target.id) else 'member'} {target}{' [BOT]' if target.bot else ''}",
            description=f"**ID:** `{target.id}`{nickname}",
            timestamp=datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(name=f"{target}", icon_url=f"{target.display_avatar.url}")
        embed.set_thumbnail(url=f"{target.display_avatar.url}")
        embed.add_field(
            name="⏰ Account created:",
            value=f"<t:{target.created_at.astimezone().strftime('%s')}:f>\n<t:{target.created_at.astimezone().strftime('%s')}:R>",
            inline=True,
        )
        if ctx.guild.get_member(target.id):
            embed.add_field(
                name="⏱️ Account joined:",
                value=f"<t:{target.joined_at.astimezone().strftime('%s')}:f>\n<t:{target.joined_at.astimezone().strftime('%s')}:R>",
                inline=True,
            )
            embed.add_field(
                name="🗃️ Joinscore:",
                value=f"`{sorted(ctx.guild.members, key=lambda v: v.joined_at).index(target)+1}` of `{len(ctx.guild.members)}`",
                inline=True,
            )
            emoji = ""
            details = ""
            try:
                emoji = f"{target.activity.emoji} " if target.activity.emoji else ""
            except:
                emoji = ""
            try:
                details = (
                    f"\n{target.activity.details}" if target.activity.details else ""
                )
            except:
                details = ""
            try:
                name = f"{target.activity.name}" if target.activity.name else ""
            except:
                name = ""
            if emoji or name or details:
                embed.add_field(
                    name="💭 Status:", value=f"{emoji}{name}{details}", inline=False
                )
            roles = []
            if target.roles:
                for index, role in enumerate(target.roles):
                    if role.name == "@everyone":
                        continue
                    roles.append("<@&" + str(role.id) + ">")
                    rolelist = ",".join(reversed(roles))
            else:
                rolelist = "None"
            embed.add_field(name=f"🎨 Roles:", value=f"{rolelist}", inline=False)
        embeds.append(embed)

        user_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, target.name
        )
        display_name = await commands.clean_content(escape_markdown=True).convert(
            ctx, target.display_name
        )

        event_types = ["warns", "bans", "kicks", "tosses", "notes"]
        embed = self.get_userlog_embed_for_id(ctx.guild.id, target, event=event_types)
        embeds.append(embed)

        await ctx.reply(embeds=embeds, mention_author=False)


async def setup(bot):
    await bot.add_cog(ModUserlog(bot))
