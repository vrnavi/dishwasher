import time
import discord
import os
import io
import asyncio
import matplotlib
import matplotlib.pyplot as plt
import typing
import random
import platform
from datetime import datetime, timezone
from discord.ext import commands
from discord.ext.commands import Cog
import aiohttp
import re as ren
import html
import json


class Basic(Cog):
    def __init__(self, bot):
        self.bot = bot
        matplotlib.use("agg")

    def pacify_name(self, name):
        return discord.utils.escape_markdown(name.replace("@", "@ "))

    @commands.command()
    async def hello(self, ctx):
        """[U] Says hello!"""
        await ctx.send(
            f"Hello {ctx.author.display_name}! Have you drank your Soylent Green today?"
        )

    @commands.command(aliases=["whatsmyip", "myip"])
    async def whatismyip(self, ctx):
        """[U] It just tells you 'your' IP."""
        await ctx.send(
            f"**Your IP is:** {random.choice(range(1,256))}.{random.choice(range(1,256))}.{random.choice(range(1,256))}.{random.choice(range(1,256))}"
        )

    @commands.command(aliases=["whatsmyid", "myid"])
    async def whatismyid(self, ctx):
        """[U] It just tells you your ID."""
        await ctx.send(str(ctx.author.id))

    @commands.command()
    async def clapifier(self, ctx, *, content):
        """[U] don't 👏 call 👏 yourself 👏 a 👏 pansexual 👏 if 👏 you've 👏 never 👏 deepthroated 👏 a 👏 pan 👏"""
        await ctx.send(
            content=f" {random.choice(['👏', '👏🏻', '👏🏼', '👏🏽', '👏🏾', '👏🏿'])} ".join(
                content.split()
            )
        )

    @commands.command(aliases=["yt"])
    async def youtube(self, ctx, *, arg: str):
        """[U] Returns the first video in a YouTube search."""
        try:
            html = await self.bot.aioget(
                f"https://www.youtube.com/results?search_query={arg}"
            )
        except:
            await ctx.reply(content="HTML error.", mention_author=False)
        allowed_mentions = discord.AllowedMentions(replied_user=False)
        navigation_reactions = ["⏹", "⬅️", "➡"]
        idx = 0

        def content():
            return ren.findall(r"watch\?v=(\S{11})", html)[idx + 1]

        holder = await ctx.reply(
            content=f"https://www.youtube.com/watch?v={content()}", mention_author=False
        )
        for e in navigation_reactions:
            await holder.add_reaction(e)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in navigation_reactions

        while True:
            try:
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=30.0, check=reactioncheck
                )
            except asyncio.TimeoutError:
                for react in navigation_reactions:
                    await holder.remove_reaction(react, ctx.bot.user)
                return
            if str(reaction) == "⏹":
                return await holder.delete()
            if str(reaction) == "⬅️":
                if idx != 0:
                    idx -= 1
                try:
                    await holder.remove_reaction("⬅️", ctx.author)
                except:
                    pass
            elif str(reaction) == "➡":
                if idx != 10:
                    idx += 1
                try:
                    await holder.remove_reaction("➡", ctx.author)
                except:
                    pass
            await holder.edit(
                content=f"https://www.youtube.com/watch?v={content()}",
                allowed_mentions=allowed_mentions,
            )

    @commands.command()
    async def trivia(self, ctx):
        """[U] A quick trivia game."""
        try:
            question = await self.bot.aiojson("https://opentdb.com/api.php?amount=1")
            if question["response_code"] != 0:
                return await ctx.reply(content="API error.", mention_author=False)

            answericons = ["🇦", "🇧", "🇨", "🇩"]
            answers = [question["results"][0]["correct_answer"]] + question["results"][
                0
            ]["incorrect_answers"]
            random.shuffle(answers)
            postpreamble = (
                "⬛⬜⬛⬜ **TRIVIA** ⬛⬜⬛⬜\n"
                + f"> `Category:` {question['results'][0]['category']}\n"
                + f"> `Difficulty:` {question['results'][0]['difficulty'].title()}\n\n"
                + f"💬 {html.unescape(question['results'][0]['question'])}\n"
            )
            postanswers = "\n".join(
                [
                    answericons[idx] + " " + html.unescape(answer)
                    for idx, answer in enumerate(answers)
                ]
            )
            posttimer = f"\n\n⏱️ The timer runs out <t:{int(datetime.now().timestamp())) + 62}:R>!"
            post = postpreamble + postanswers + posttimer
            msg = await ctx.reply(content=post, mention_author=False)

            for idx in range(len(answers)):
                await msg.add_reaction(answericons[idx])

            await asyncio.sleep(60)

            postanswers = "\n".join(
                [
                    "> " + answericons[idx] + " " + html.unescape(answer)
                    if answer == question["results"][0]["correct_answer"]
                    else answericons[idx] + " " + html.unescape(answer)
                    for idx, answer in enumerate(answers)
                ]
            )
            posttimer = (
                f"\n\n⏱️ The timer ran out <t:{int(datetime.now().timestamp())}:R>!"
            )
            post = postpreamble + postanswers + posttimer
            allowed_mentions = discord.AllowedMentions(replied_user=False)
            await msg.edit(content=post, allowed_mentions=allowed_mentions)
        except:
            await ctx.send("Unspecified error.")

    @commands.command()
    async def hug(self, ctx):
        """[U] Gives you a hug."""
        await ctx.send(f"I am incapable of hugs, but... \*hugs*")

    @commands.command()
    async def choose(self, ctx, *options):
        """[U] Chooses something for you."""
        return await ctx.send(f"You should `{random.choice(options)}`!")

    @commands.command()
    async def roll(self, ctx, dice=None):
        """[U] Rolls the dice!"""
        if dice:
            try:
                amount, faces = [int(arg) for arg in dice.split("d")]
            except:
                return await ctx.reply(
                    content="Invalid input. Try `1d6` or `3d20`.", mention_author=False
                )
            if amount <= 0:
                return await ctx.reply(
                    content="You roll a `nothing`. Good job, idiot.",
                    mention_author=False,
                )
            elif faces <= 1:
                return await ctx.reply(
                    content="The die fizzles out of existence for not being possible. Way to go.",
                    mention_author=False,
                )
        else:
            faces = 6
            amount = 1
        rolls = []
        for roll in range(amount):
            rolls.append(random.randrange(faces) + 1)
        if amount > 1:
            return await ctx.reply(
                content="You rolled: `"
                + ", ".join([str(roll) for roll in rolls])
                + "` totalling **"
                + str(sum(rolls))
                + "**.",
                mention_author=False,
            )
        else:
            return await ctx.reply(
                content=f"You rolled a `{sum(rolls)}`.", mention_author=False
            )

    @commands.command()
    async def baguette(self, ctx):
        """[U] hon hon hon baguette"""
        await ctx.send(f"🥖")

    @commands.command()
    async def kill(self, ctx, the_text: str):
        """[U] Kills someone."""
        await ctx.send(f"{the_text} got stuck in the Dishwasher.")

    @commands.command(aliases=["timer"])
    async def eggtimer(self, ctx, minutes: int = 5):
        """[S] Posts a timer."""
        if minutes >= 60:
            return await ctx.reply(
                "I'm not making a timer longer than an hour.", mention_author=False
            )
        time = minutes * 60
        await ctx.message.add_reaction("⏳")
        await asyncio.sleep(time)
        msg = await ctx.channel.send(content=ctx.author.mention)
        await msg.edit(content="⌛", delete_after=5)

    @commands.group(invoke_without_command=True)
    async def avy(self, ctx, target: discord.User = None):
        """[U] Gets a user's avy."""
        if target is not None:
            if ctx.guild and ctx.guild.get_member(target.id):
                target = ctx.guild.get_member(target.id)
        else:
            target = ctx.author
        await ctx.send(content=target.display_avatar.url)

    @avy.command(name="server")
    async def _server(self, ctx, target: discord.Guild = None):
        """[U] Gets a server's avy."""
        if target is None:
            target = ctx.guild
        return await ctx.send(content=target.icon.url)

    @commands.command(aliases=["bigtimerush"])
    async def btr(self, ctx):
        await ctx.send(files=[discord.File("assets/bigtimerush.mp3")])

    @commands.command()
    async def install(self, ctx):
        """[U] Teaches you how to install a Dishwasher."""
        await ctx.send(
            f"Here's how to install a dishwasher:\n<https://www.whirlpool.com/blog/kitchen/how-to-install-a-dishwasher.html>\n\nWhile you're at it, consider protecting your dishwasher:\n<https://www.2-10.com/homeowners-warranty/dishwasher/>\n\nRemember, the more time you spend with your dishwasher instead of the kitchen sink, __the better__."
        )

    @commands.command(name="hex")
    async def _hex(self, ctx, num: int):
        """[U] Converts base 10 to 16."""
        hex_val = hex(num).upper().replace("0X", "0x")
        await ctx.reply(content=f"{hex_val}", mention_author=False)

    @commands.command(aliases=["catbox", "imgur"])
    async def rehost(self, ctx, links=None):
        """[U] Uploads a file to catbox.moe."""
        api_url = "https://catbox.moe/user/api.php"
        if not ctx.message.attachments and not links:
            return await ctx.reply(
                content="You need to supply a file or a file link to rehost.",
                mention_author=False,
            )
        links = links.split() if links else []
        for r in [f.url for f in ctx.message.attachments] + links:
            formdata = aiohttp.FormData()
            formdata.add_field("reqtype", "urlupload")
            if self.bot.config.catbox_key:
                formdata.add_field("userhash", self.bot.config.catbox_key)
            formdata.add_field("url", r)
            async with self.bot.session.post(api_url, data=formdata) as response:
                output = await response.text()
                await ctx.reply(content=output, mention_author=False)

    @commands.command(name="dec")
    async def _dec(self, ctx, num):
        """[U] Converts base 16 to 10."""
        await ctx.reply(content=f"{int(num, 16)}", mention_author=False)

    @commands.guild_only()
    @commands.command()
    async def membercount(self, ctx):
        """[U] Prints the member count of the server."""
        await ctx.reply(
            f"{ctx.guild.name} has {ctx.guild.member_count} members.",
            mention_author=False,
        )

    @commands.command()
    async def about(self, ctx):
        """[U] Shows a quick embed with bot info."""
        embed = discord.Embed(
            title=self.bot.user.name,
            url=self.bot.config.source_url,
            description=self.bot.config.long_desc,
            color=ctx.guild.me.color if ctx.guild else self.bot.user.color,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(
            name=f"📊 Usage",
            value=f"**Guilds:** {len(self.bot.guilds)}\n**Users:** {len(self.bot.users)}",
            inline=True,
        )
        embed.add_field(
            name=f"⏱️ Uptime",
            value=f"{self.bot.user.name} started on <t:{self.bot.start_timestamp}:F>, or <t:{self.bot.start_timestamp}:R>.",
            inline=True,
        )
        embed.add_field(
            name=f"📡 Unit",
            value=f"Running {platform.python_implementation()} {platform.python_version()} on {platform.platform(aliased=True, terse=True)} {platform.architecture()[0]}.",
            inline=True,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="server", aliases=["invite"])
    async def hostserver(self, ctx):
        """[U] Gives an invite to the host server."""
        await ctx.author.send(
            content="Here is an invite to my host server.\nhttps://discord.gg/"
            + "p"
            + "3"
            + "M"
            + "v"
            + "p"
            + "S"
            + "v"
            + "X"
            + "r"
            + "m"
        )
        if ctx.guild:
            await ctx.reply(
                content="As to not be rude, I have DMed the server link to you.",
                mention_author=False,
            )

    @commands.command(aliases=["commands"])
    async def help(self, ctx):
        """Posts a help command."""
        await ctx.reply(
            "[Press F1 For] HELP\nhttps://kitchen.0ccu.lt/",
            mention_author=False,
        )

    @commands.command(aliases=["showcolor"])
    async def color(self, ctx, color):
        """Shows a color in chat."""
        if color[0] == "#":
            color = color[1:]

        def hex_check(color):
            try:
                int(color, 16)
                return True
            except ValueError:
                return False

        if hex_check(color) and len(color) == 6:
            await ctx.reply(
                f"https://singlecolorimage.com/get/{color}/128x128",
                mention_author=False,
            )
        else:
            await ctx.reply(
                "Please provide a valid hexadecimal color.", mention_author=False
            )
            return

    @commands.command(aliases=["p"])
    async def ping(self, ctx):
        """[U] Shows ping values to discord.

        RTT = Round-trip time, time taken to send a message to discord
        GW = Gateway Ping"""
        before = time.monotonic()
        tmp = await ctx.reply("⌛", mention_author=False)
        after = time.monotonic()
        rtt_ms = (after - before) * 1000
        gw_ms = self.bot.latency * 1000

        message_text = f":ping_pong:\nrtt: `{rtt_ms:.1f}ms`\ngw: `{gw_ms:.1f}ms`"
        self.bot.log.info(message_text)
        await tmp.edit(content=message_text)

    @commands.guild_only()
    @commands.command()
    async def poll(self, ctx, poll_title: str, *options: str):
        poll_emoji = [
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
        optionlines = ""
        if not options:
            return await ctx.reply(
                content="**No options specified.** Add some and try again.",
                mention_author=False,
            )
        elif len(options) > 10:
            return await ctx.reply(
                content="**Too many options.** Remove some and try again.",
                mention_author=False,
            )
        for i, l in enumerate(options):
            optionlines = f"{optionlines}\n`#{i+1}:` {l}"
        poll = await ctx.reply(
            content=f"**{poll_title}**{optionlines}", mention_author=False
        )
        for n in range(len(options)):
            await poll.add_reaction(poll_emoji[n])

    @commands.cooldown(1, 5, type=commands.BucketType.default)
    @commands.guild_only()
    @commands.command(aliases=["loadingbar"])
    async def progressbar(self, ctx):
        """[U] Creates a progress bar of the current year."""
        async with ctx.channel.typing():
            start = datetime(datetime.now().year, 1, 1)
            end = datetime(datetime.now().year + 1, 1, 1)
            total = end - start
            current = datetime.now() - start
            percentage = (current / total) * 100

            plt.figure().set_figheight(0.5)
            plt.margins(x=0, y=0)
            plt.tight_layout(pad=0)
            plt.axis("off")

            plt.barh(0, percentage, color="#43b581")
            plt.barh(0, 100 - percentage, left=percentage, color="#747f8d")

            plt.margins(x=0, y=0)
            plt.tight_layout(pad=0)
            plt.axis("off")

            plt.savefig(f"{ctx.guild.id}-progressbar.png")

            plt.close()
        await ctx.reply(
            content=f"**{datetime.now().year}** is **{percentage}**% complete.",
            file=discord.File(f"{ctx.guild.id}-progressbar.png"),
            mention_author=False,
        )
        os.remove(f"{ctx.guild.id}-progressbar.png")

    @commands.cooldown(1, 5, type=commands.BucketType.default)
    @commands.guild_only()
    @commands.command()
    async def joingraph(self, ctx):
        """[U] Shows the graph of users that joined."""
        async with ctx.channel.typing():
            rawjoins = [m.joined_at.date() for m in ctx.guild.members]
            joindates = sorted(list(dict.fromkeys(rawjoins)))
            joincounts = []
            for i, d in enumerate(joindates):
                if i != 0:
                    joincounts.append(joincounts[i - 1] + rawjoins.count(d))
                else:
                    joincounts.append(rawjoins.count(d))
            plt.plot(joindates, joincounts)
            plt.savefig(f"{ctx.guild.id}-joingraph.png", bbox_inches="tight")
            plt.close()
        await ctx.reply(
            file=discord.File(f"{ctx.guild.id}-joingraph.png"), mention_author=False
        )
        os.remove(f"{ctx.guild.id}-joingraph.png")

    @commands.guild_only()
    @commands.command(aliases=["joinscore"])
    async def joinorder(self, ctx, target: typing.Union[discord.Member, int] = None):
        """[U] Shows the joinorder of a user."""
        members = sorted(ctx.guild.members, key=lambda v: v.joined_at)
        if not target:
            memberidx = members.index(ctx.author) + 1
        elif type(target) == discord.Member:
            memberidx = members.index(target) + 1
        else:
            memberidx = target
        message = ""
        for idx, m in enumerate(members):
            if memberidx - 6 <= idx <= memberidx + 4:
                user = self.pacify_name(str(m))
                message = (
                    f"{message}\n`{idx+1}` **{user}**"
                    if memberidx == idx + 1
                    else f"{message}\n`{idx+1}` {user}"
                )
        await ctx.reply(content=message, mention_author=False)

    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def info(self, ctx, *, target: discord.User = None):
        """[S] Gets full user info."""
        if not target:
            target = ctx.author

        if not ctx.guild.get_member(target.id):
            # Memberless code.
            color = discord.Color.lighter_gray()
            nickname = ""
        else:
            # Member code.
            target = ctx.guild.get_member(target.id)
            color = target.color
            nickname = f"\n**Nickname:** `{ctx.guild.get_member(target.id).nick}`"

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
            value=f"<t:{int(target.created_at.astimezone().timestamp())}:f>\n<t:{int(target.created_at.astimezone().timestamp())}:R>",
            inline=True,
        )
        if ctx.guild.get_member(target.id):
            embed.add_field(
                name="⏱️ Account joined:",
                value=f"<t:{int(target.joined_at.astimezone().timestamp())}:f>\n<t:{int(target.joined_at.astimezone().timestamp())}:R>",
                inline=True,
            )
            embed.add_field(
                name="🗃️ Joinscore:",
                value=f"`{sorted(ctx.guild.members, key=lambda v: v.joined_at).index(target)+1}` of `{len(ctx.guild.members)}`",
                inline=True,
            )
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
            if len(target.roles) > 1:
                for index, role in enumerate(target.roles):
                    if role.name == "@everyone":
                        continue
                    roles.append("<@&" + str(role.id) + ">")
                    rolelist = ",".join(reversed(roles))
            else:
                rolelist = "None"
            embed.add_field(name=f"🎨 Roles:", value=f"{rolelist}", inline=False)

        await ctx.reply(embed=embed, mention_author=False)

    @info.command()
    async def role(self, ctx, *, role: discord.Role = None):
        """[S] Gets full role info."""
        if role == None:
            role = ctx.guild.default_role

        embed = discord.Embed(
            color=role.color,
            title=f"Info for role @{role}{' [MANAGED]' if role.managed else ''}",
            description=f"**ID:** `{role.id}`\n**Color:** `{str(role.color)}`",
            timestamp=datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(name=role.guild.name, icon_url=role.guild.icon.url)
        embed.set_thumbnail(url=(role.icon.url if role.icon else None))
        embed.add_field(
            name="⏰ Role created:",
            value=f"<t:{int(role.created_at.astimezone().timestamp())}:f>\n<t:{int(role.created_at.astimezone().timestamp())}:R>",
            inline=True,
        )
        embed.add_field(
            name="👥 Role members:",
            value=f"`{len(role.members)}`",
            inline=True,
        )
        embed.add_field(
            name="🚩 Role flags:",
            value=f"**Hoisted:** {str(role.hoist)}\n**Mentionable:** {str(role.mentionable)}",
            inline=True,
        )
        await ctx.reply(embed=embed, mention_author=False)

    @info.command(aliases=["guild"])
    async def server(self, ctx, *, server: discord.Guild = None):
        """[S] Gets full server info."""
        if server == None:
            server = ctx.guild

        serverdesc = "*" + server.description + "*" if server.description else ""
        embed = discord.Embed(
            color=server.me.color,
            title=f"Info for server {server}",
            description=f"{serverdesc}\n**ID:** `{server.id}`\n**Owner:** {server.owner.mention}",
            timestamp=datetime.now(),
        )
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.display_avatar)
        embed.set_author(name=server.name, icon_url=server.icon.url)
        embed.set_thumbnail(url=(server.icon.url if server.icon else None))
        embed.add_field(
            name="⏰ Server created:",
            value=f"<t:{int(server.created_at.astimezone().timestamp())}:f>\n<t:{int(server.created_at.astimezone().timestamp())}:R>",
            inline=True,
        )
        embed.add_field(
            name="👥 Server members:",
            value=f"`{server.member_count}`",
            inline=True,
        )
        embed.add_field(
            name="#️⃣ Counters:",
            value=f"**Text Channels:** {len(server.text_channels)}\n**Voice Channels:** {len(server.voice_channels)}\n**Forum Channels:** {len(server.forums)}\n**Roles:** {len(server.roles)}\n**Emoji:** {len(server.emojis)}\n**Stickers:** {len(server.stickers)}\n**Boosters:** {len(server.premium_subscribers)}",
            inline=False,
        )

        if server.banner:
            embed.set_image(url=server.banner.url)

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot):
    await bot.add_cog(Basic(bot))
