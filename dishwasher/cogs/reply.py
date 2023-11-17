import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import config
import datetime
import asyncio
from helpers.datafiles import get_guildfile, get_userfile
from helpers.checks import check_if_staff
from helpers.sv_config import get_config
from helpers.datafiles import get_userfile, fill_profile, set_userfile
from helpers.embeds import stock_embed, author_embed


class Reply(Cog):
    """
    A cog that stops people from ping replying people who don't want to be.
    """

    def __init__(self, bot):
        self.bot = bot
        self.usercounts = {}
        self.counttimer.start()
        self.last_eval_result = None
        self.previous_eval_code = None

    def cog_unload(self):
        self.counttimer.cancel()

    async def handle_message_with_reference(self, message):
        try:
            reference_message = await message.channel.fetch_message(
                message.reference.message_id
            )
            reference_author = reference_message.author
        except discord.errors.NotFound:
            # Assume original message doesn't exist, or is/was ephemeral.
            return

        if (
            message.author.bot
            or not message.guild
            or not message.guild.get_member(reference_author.id)
            or reference_author.id == message.author.id
            or not get_config(message.guild.id, "noreply", "enable")
            or reference_author.get_role(
                get_config(message.guild.id, "noreply", "noreply_role")
            )
            is None
        ):
            return

        staff_role = get_config(message.guild.id, "staff", "staff_role")
        if staff_role and message.author.get_role(staff_role):
            return

        if reference_author in message.mentions:
            if message.author.id not in self.usercounts:
                self.usercounts[message.author.id] = 0
                usertracks = get_guildfile(message.guild.id, "usertrack")
                if (
                    str(message.author.id) not in usertracks
                    or usertracks[str(message.author.id)]["truedays"] < 14
                ):
                    return await message.reply(
                        content="**Do not reply ping users who do not wish to be pinged.**\nAs you are new, this first time will not be a violation.",
                        file=discord.File("assets/noreply.png"),
                        mention_author=True,
                    )

            self.usercounts[message.author.id] += 1
            counts = [
                "0️⃣",
                "1️⃣",
                "2️⃣",
                "3️⃣",
                "4️⃣",
                "5️⃣",
                "6️⃣",
                "7️⃣",
                "8️⃣",
                "9️⃣",
                "🔟",
            ]

            if self.usercounts[message.author.id] == 5:
                await message.reply(
                    content=f"{message.guild.get_role(staff_role).mention} | {message.author.mention} reached `5` reply ping violations.",
                    mention_author=False,
                )
                self.usercounts[message.author.id] = 0
                return

            try:
                await message.add_reaction("🗞️")
                await message.add_reaction(counts[self.usercounts[message.author.id]])
                await message.add_reaction("🛑")
            except discord.errors.Forbidden:
                if message.channel.permissions_for(message.guild.me).add_reactions:
                    await message.reply(
                        content=f"**Congratulations, {message.author.mention}, you absolute dumbass.**\nAs your reward for blocking me to disrupt my function, here is a time out, just for you.",
                        mention_author=True,
                    )
                    await message.author.timeout(datetime.timedelta(minutes=10))
                    return
            except discord.errors.NotFound:
                return await message.reply(
                    content=f"Immediately deleting your message won't hide you from your sin, {message.author.mention}. You have `{self.usercounts[message.author.id]}` violation(s).",
                    mention_author=True,
                )

            def check(r, u):
                return (
                    u.id == reference_author.id
                    and str(r.emoji) == "🛑"
                    and r.message.id == message.id
                )

            try:
                await self.bot.wait_for("reaction_add", timeout=15.0, check=check)
            except asyncio.TimeoutError:
                await message.clear_reaction("🛑")
            except discord.errors.NotFound:
                pass
            else:
                self.usercounts[message.author.id] -= 1
                try:
                    await message.clear_reaction("🗞️")
                    await message.clear_reaction(
                        counts[self.usercounts[message.author.id] + 1]
                    )
                    await message.clear_reaction("🛑")
                    await message.add_reaction("👍")
                    await message.add_reaction(
                        counts[self.usercounts[message.author.id]]
                    )
                    await asyncio.sleep(5)
                    await message.clear_reaction("👍")
                    await message.clear_reaction(
                        counts[self.usercounts[message.author.id]]
                    )
                except discord.errors.NotFound:
                    return await message.reply(
                        content=f"Come on, I'm trying to put reactions here. Let me do so instead of immediately deleting your message, thanks?",
                        mention_author=True,
                    )
            return

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def reset(self, ctx, target: discord.Member):
        if target.id not in self.usercounts or self.usercounts[target.id] == 0:
            return await ctx.reply(
                content="This user doesn't have any reply ping violations.",
                mention_author=False,
            )
        else:
            self.usercounts[target.id] = 0
            return await ctx.reply(
                content="This user's reply ping counter has been reset.",
                mention_author=False,
            )

    @commands.command()
    async def replyconfig(self, ctx):
        profile = fill_profile(ctx.author.id)
        embed = stock_embed(self.bot)
        embed.title = "🏓 Your reply preference..."
        embed.description = (
            f"Use `{ctx.prefix}replyconfig [setting]` to change your preference."
        )
        embed.color = discord.color.red()
        author_embed(embed, ctx.author)
        allowed_mentions = discord.AllowedMentions(replied_user=False)

        def fieldadd():
            unconfigured = "🔘" if not profile["replypref"] else "⚫"
            embed.add_field(
                name="🤷 Unconfigured",
                value=unconfigured + " Indicates that you have no current preference.",
                inline=False,
            )

            pleaseping = "🔘" if profile["replypref"] == "pleasereplyping" else "⚫"
            embed.add_field(
                name="<:pleasereplyping:1171017026274340904> Please Reply Ping",
                value=pleaseping
                + " Indicates that you would like to be pinged in replies.",
                inline=False,
            )

            waitbeforeping = (
                "🔘" if profile["replypref"] == "waitbeforereplyping" else "⚫"
            )
            embed.add_field(
                name="<:waitbeforereplyping:1171017084222832671> Wait Before Reply Ping",
                value=waitbeforeping
                + " Indicates that you would only like to be pinged after some time has passed.",
                inline=False,
            )

            noping = "🔘" if profile["replypref"] == "noreplyping" else "⚫"
            embed.add_field(
                name="<:noreplyping:1171016972222332959> No Reply Ping",
                value=noping
                + " Indicates that you do not wish to be reply pinged whatsoever.",
                inline=False,
            )

        fieldadd()

        reacts = [
            "🤷",
            "<:pleasereplyping:1171017026274340904>",
            "<:waitbeforereplyping:1171017084222832671>",
            "<:noreplyping:1171016972222332959>",
        ]
        configmsg = await ctx.reply(embed=embed, mention_author=False)
        for react in reacts:
            await configmsg.add_reaction(react)
        embed.color = discord.color.green()
        await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in reacts

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            embed.color = discord.color.default()
            for react in reacts:
                await configmsg.remove_reaction(react, ctx.bot.user)
            return await configmsg.edit(
                embed=embed,
                allowed_mentions=allowed_mentions,
            )
        else:
            if str(reaction) == reacts[0]:
                profile["replypref"] = None
            elif str(reaction) == reacts[1]:
                profile["replypref"] = "pleasereplyping"
            elif str(reaction) == reacts[2]:
                profile["replypref"] = "waitbeforereplyping"
            elif str(reaction) == reacts[3]:
                profile["replypref"] = "noreplyping"
            set_userfile(ctx.author.id, "profile", json.dumps(profile))
            embed.clear_fields()
            fieldadd()
            embed.color = discord.color.gold()
            for react in reacts:
                await configmsg.remove_reaction(react, ctx.bot.user)
            await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if message.reference and message.type == discord.MessageType.reply:
            await self.handle_message_with_reference(message)

    @tasks.loop(hours=24)
    async def counttimer(self):
        await self.bot.wait_until_ready()
        self.usercounts = {}


async def setup(bot):
    await bot.add_cog(Reply(bot))
