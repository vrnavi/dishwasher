import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import datetime
import asyncio
from helpers.checks import ismod
from helpers.sv_config import get_config
from helpers.datafiles import get_file, fill_profile, set_file
from helpers.embeds import stock_embed, author_embed


class Reply(Cog):
    """
    A cog that stops people from ping replying people who don't want to be.
    """

    def __init__(self, bot):
        self.bot = bot
        self.violations = {}
        self.timers = {}
        self.counttimer.start()
        self.last_eval_result = None
        self.previous_eval_code = None

    def cog_unload(self):
        self.counttimer.cancel()

    def check_override(self, message):
        if not message.guild:
            return None
        setting_roles = [
            (self.bot.pull_role(message.guild, "Please Reply Ping"), "pleasereplyping"),
            (
                self.bot.pull_role(message.guild, "Wait Before Reply Ping"),
                "waitbeforereplyping",
            ),
            (self.bot.pull_role(message.guild, "No Reply Pings"), "noreplyping"),
        ]
        for role, identifier in setting_roles:
            if role == None:
                continue
            elif role in message.author.roles:
                return identifier
        return None

    async def add_violation(self, message):
        staff_roles = [
            self.bot.pull_role(
                message.guild, get_config(message.guild.id, "staff", "modrole")
            ),
            self.bot.pull_role(
                message.guild, get_config(message.guild.id, "staff", "adminrole")
            ),
        ]
        if not get_config(message.guild.id, "staff", "noreplythreshold"):
            return
        maximum = (
            10
            if get_config(message.guild.id, "staff", "noreplythreshold") > 10
            else get_config(message.guild.id, "staff", "noreplythreshold")
        )
        if (
            not maximum
            or not any(staff_roles)
            or any([staff_role in message.author.roles for staff_role in staff_roles])
            or self.bot.is_owner(message.author)
        ):
            return

        if message.guild.id not in self.violations:
            self.violations[message.guild.id] = {}
        if message.author.id not in self.violations[message.guild.id]:
            self.violations[message.guild.id][message.author.id] = 0
            usertracks = get_file("usertrack", f"servers/{message.guild.id}")
            if (
                str(message.author.id) not in usertracks
                or usertracks[str(message.author.id)]["truedays"] < 14
            ):
                return await message.reply(
                    content="**Do not reply ping users who do not wish to be pinged.**\n"
                    + "As this part of noreply is bugged, nothing will happen.",
                    file=discord.File("assets/noreply.png"),
                    mention_author=True,
                )

        self.violations[message.guild.id][message.author.id] += 1
        if self.violations[message.guild.id][message.author.id] == maximum:
            await message.reply(
                content=f"you wouldve reached the reply ping violation staff ping, but im kind enough to let you off with nothing",
                mention_author=False,
            )
            self.violations[message.guild.id][message.author.id] = 0
            return

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

        await message.add_reaction(
            counts[self.violations[message.guild.id][message.author.id]]
        )
        await message.add_reaction("🛑")

        reacted = self.bot.await_reaction(
            message, message.reference.resolved.author, ["🛑"], 120
        )
        if not reacted:
            return await message.clear_reaction("🛑")

        self.violations[message.guild.id][message.author.id] -= 1
        await message.clear_reaction("🛑")
        await message.clear_reaction(
            counts[self.violations[message.guild.id][message.author.id] + 1]
        )
        await message.add_reaction(
            counts[self.violations[message.guild.id][message.author.id]]
        )
        await message.add_reaction("👍")
        await asyncio.sleep(5)
        await message.clear_reaction("👍")
        await message.clear_reaction(
            counts[self.violations[message.guild.id][message.author.id]]
        )
        return

    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def reset(self, ctx, target: discord.Member):
        """This resets reply ping violations for a user.

        There's not much more to it.

        - `target`
        The target to reset violations for."""
        if (
            ctx.guild.id not in self.violations
            or target.id not in self.violations[message.guild.id]
            or self.violations[message.guild.id][message.author.id] == 0
        ):
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

    @commands.bot_has_permissions(embed_links=True)
    @commands.command()
    async def replyconfig(self, ctx):
        """This sets your reply ping preferences.

        Use the reactions to pick your setting.
        See the [documentation](https://3gou.0ccu.lt/as-a-user/reply-ping-preferences/) for more info.

        No arguments."""
        override = self.check_override(ctx.message)
        if override:
            return await ctx.reply(
                content="<:sangouspeak:1182927625161809931> You already have an indicator role, you don't need to set your preferences here.",
                mention_author=False,
            )

        profile = fill_profile(ctx.author.id)
        embed = stock_embed(self.bot)
        embed.title = "🏓 Your reply preference..."
        embed.color = discord.Color.red()
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
                name="<:yping:1266128081920331816> Please Reply Ping",
                value=pleaseping
                + " Indicates that you would like to be pinged in replies.",
                inline=False,
            )

            waitbeforeping = (
                "🔘" if profile["replypref"] == "waitbeforereplyping" else "⚫"
            )
            embed.add_field(
                name="<:mping:1266129731959656530> Wait Before Reply Ping",
                value=waitbeforeping
                + " Indicates that you would only like to be pinged after some time has passed.",
                inline=False,
            )

            noping = "🔘" if profile["replypref"] == "noreplyping" else "⚫"
            embed.add_field(
                name="<:nping:1266128115961167924> No Reply Ping",
                value=noping
                + " Indicates that you do not wish to be reply pinged whatsoever.",
                inline=False,
            )

        fieldadd()

        reacts = [
            "🤷",
            "<:yping:1266128081920331816>",
            "<:mping:1266129731959656530>",
            "<:nping:1266128115961167924>",
        ]
        configmsg = await ctx.reply(embed=embed, mention_author=False)
        for react in reacts:
            await configmsg.add_reaction(react)
        embed.color = discord.Color.green()
        await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in reacts

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            embed.color = discord.Color.default()
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
            set_file("profile", json.dumps(profile), f"users/{ctx.author.id}")
            embed.clear_fields()
            fieldadd()
            embed.color = discord.Color.gold()
            for react in reacts:
                await configmsg.remove_reaction(react, ctx.bot.user)
            await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if (
            message.author.bot
            or message.is_system()
            or not message.guild
            or not message.reference
            or message.type != discord.MessageType.reply
        ):
            return

        try:
            refmessage = await message.channel.fetch_message(
                message.reference.message_id
            )
            if (
                refmessage.author.id == message.author.id
                or not message.guild.get_member(refmessage.author.id)
            ):
                return
        except:
            return

        preference = self.check_override(refmessage)
        if not preference:
            preference = fill_profile(refmessage.author.id)["replypref"]
            if not preference:
                return

        async def wrap_violation(message):
            try:
                await self.add_violation(message)
                return
            except discord.errors.Forbidden:
                if not (
                    message.channel.permissions_for(message.guild.me).add_reactions
                    and message.channel.permissions_for(
                        message.guild.me
                    ).manage_messages
                    and message.channel.permissions_for(
                        message.guild.me
                    ).moderate_members
                ):
                    return

                await message.author.timeout(datetime.timedelta(minutes=10))
                return await message.reply(
                    content=f"**Congratulations, {message.author.mention}, you absolute IDIOT.**\nAs your reward for blocking me to disrupt my function, here is a time out, just for you. (hey draco here, i dont know how to disable this.)",
                    mention_author=True,
                )
            except discord.errors.NotFound:
                return await message.reply(
                    content=f"{message.author.mention} immediately deleted their own message.\n{message.author.display_name} now has `{self.violations[message.guild.id][message.author.id]}` violation(s).",
                    mention_author=True,
                )

        # If not reply pinged...
        if (
            preference == "pleasereplyping"
            and refmessage.author not in message.mentions
        ):
            await message.add_reaction("<:yping:1266128081920331816>")
            pokemsg = await message.reply(content=refmessage.author.mention)
            await self.bot.await_message(message.channel, refmessage.author, 86400)
            return await pokemsg.delete()

        # If reply pinged at all...
        elif preference == "noreplyping" and refmessage.author in message.mentions:
            await message.add_reaction("<:nping:1266128115961167924>")
            await wrap_violation(message)
            return

        # If reply pinged in a window of time...
        elif (
            preference == "waitbeforereplyping"
            and refmessage.author in message.mentions
        ):
            if message.guild.id not in self.timers:
                self.timers[message.guild.id] = {}
            self.timers[message.guild.id][refmessage.author.id] = int(
                refmessage.created_at.timestamp()
            )
            if (
                int(message.created_at.timestamp()) - 30
                <= self.timers[message.guild.id][refmessage.author.id]
            ):
                await message.add_reaction("<:mping:1266129731959656530>")
                await wrap_violation(message)
            return

    @tasks.loop(hours=24)
    async def counttimer(self):
        await self.bot.wait_until_ready()
        self.violations = {}


async def setup(bot):
    await bot.add_cog(Reply(bot))
