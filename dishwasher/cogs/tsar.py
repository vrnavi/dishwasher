import config
import datetime
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.checks import check_if_bot_manager
from helpers.usertrack import get_usertrack, fill_usertrack, set_usertrack


class TSAR(Cog):
    """
    TSAR BOMBA! True. Self. Assignable. Roles.
    """

    def __init__(self, bot):
        self.bot = bot
        self.interactivecache = {}
        self.toilet.start()

    def cog_unload(self):
        self.toilet.cancel()

    def new_track(member):
        usertracks, uid = fill_usertrack(member.guild.id, member.id)
        if "jointime" not in usertracks[uid] or not usertracks[uid]["jointime"]:
            usertracks[uid]["jointime"] = int(member.joined_at.timestamp())
        set_usertrack(member.guild.id, json.dumps(usertracks))

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if member.bot:
            return
        new_track(member)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if member.bot:
            return
        new_track(member)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot or not message.guild:
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
    await bot.add_cog(TSAR(bot))
