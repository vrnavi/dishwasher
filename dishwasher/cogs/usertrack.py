import config
import datetime
import discord
import json
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.usertrack import get_usertrack, fill_usertrack, set_usertrack


class usertrack(Cog):
    """
    Keeps tabs on users.
    """

    def __init__(self, bot):
        self.bot = bot
        self.interactivecache = {}
        self.toilet.start()

    def cog_unload(self):
        self.toilet.cancel()

    def new_track(self, member):
        usertracks, uid = fill_usertrack(member.guild.id, member.id)
        if "jointime" not in usertracks[uid] or not usertracks[uid]["jointime"]:
            usertracks[uid]["jointime"] = int(member.joined_at.timestamp())
        set_usertrack(member.guild.id, json.dumps(usertracks))

    @commands.guild_only()
    @commands.command()
    async def timespent(self, ctx, target: discord.Member = None):
        usertracks = get_usertrack(ctx.guild.id)
        if not target:
            target = ctx.author
        if str(target.id) not in usertracks:
            return await ctx.reply(
                content="User not presently tracked. Wait a day.", mention_author=False
            )

        return await ctx.reply(
            content=f"**{target}** was first seen <t:{usertracks[str(target.id)]['jointime']}:R> on <t:{usertracks[str(target.id)]['jointime']}:F>, and was seen chatting for `{usertracks[str(target.id)]['truedays']}` days.\n\n**This counter may be inaccurate.** It calculates join dates and chatting days from when it was first activated.",
            mention_author=False,
        )

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if member.bot:
            return
        self.new_track(member)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if member.bot:
            return
        self.new_track(member)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        ctx = await self.bot.get_context(message)
        if message.author.bot or not message.guild or ctx.valid:
            return
        if message.guild.id not in self.interactivecache:
            self.interactivecache[message.guild.id] = []
        if message.author.id not in self.interactivecache[message.guild.id]:
            self.interactivecache[message.guild.id].append(message.author.id)

    @tasks.loop(time=datetime.time(hour=0))
    async def toilet(self):
        # water go down the hole
        for g in self.interactivecache:
            usertracks = get_usertrack(g)
            for u in self.interactivecache[g]:
                usertracks, uid = fill_usertrack(g, u, usertracks)
                if not usertracks[uid]["jointime"]:
                    usertracks[uid]["jointime"] = int(
                        self.bot.get_guild(g).get_member(u).joined_at.timestamp()
                    )
                usertracks[uid]["truedays"] += 1
            set_usertrack(g, json.dumps(usertracks))


async def setup(bot):
    await bot.add_cog(usertrack(bot))
