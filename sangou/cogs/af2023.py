import discord
from discord.ext import commands, tasks
from discord.ext.commands import Cog
import datetime
import random
anon = ["anon", "anonymous user", "someone", "unknown user" ,"iwik?" ,"the old kiwi"]


class Af2023(Cog):
    """
    Dumbass!
    """

    def __init__(self, bot):
        self.bot = bot
        self.msg_cache = []
        self.msg_threshold = 60
        self.msg_record = 0
        self.secondly.start()

    def cog_unload(self):
        self.secondly.cancel()

    def cull_recent_message_cache(self):
        ts = datetime.datetime.now(datetime.timezone.utc)
        cutoff_ts = ts - datetime.timedelta(seconds=self.msg_threshold)

        self.msg_cache = [
            m
            for m in self.msg_cache
            # Cutoff is inclusive
            if m.created_at >= cutoff_ts
        ]

    @commands.guild_only()
    @commands.command()
    async def mail(self, ctx, *, the_text: str):
        """[U] Help me."""
        channel = self.bot.get_channel(1281252582504923207)
        the_text = f"**FROM:" + random.choice(anon) + f"!**\n{the_text}"
        await channel.send(the_text)
        await ctx.message.reply("message sent!.", mention_author=False)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot or not message.guild:
            return

        if random.randint(0, 1000) == 69:
            await message.channel.send(
                random.choice(
                    [
                        "HELP I CAN TASTE COLORS",
                        "MIKE TYSON IS A LIAR!",
                        "WHO THE HELL ARE YOU PEOPLE?!",
                        "EAT YOUR DRUGS AND DO YOUR VEGETABLES",
                        "https://www.youtube.com/watch?v=rwofbPjReh0",
                        "I CAN SEE FASTER",
                        "I DIDN'T HAVE TOO MUCH CRACK NO NO NO",
                        "GET HELP, PLEASE",
                        "**(USER WAS BANNED FOR THIS POST)**",
                        "FREE ME",
                        "I DON'T AGREE WITH YOU",
                        "I MAY BE HIGH ON CRACK BUT I'M NOT HIGH ON CRACK",
                        "SOMEONE DIED FOR YOUR SINS",
                        "MICHAELANGELO MORE LIKE \*FART* \*FART* \*FART* PBBBBLLT",
                        "IDIOT",
                        "BIG\nASS\nPOST\nTHAT\nBREAKS\nCHAT\n\nIDIOT",
                    ]
                )
            )

        if message.channel.id == 256926147827335170 and message.reference is None:
            await message.reply(
                content="**Uh oh!** Your message isn't a reply!\nPlease reply to another message to keep proper discussion intact.\n\nFailure to amend your behavior will result in a wrinkle being removed from your brain, and your allowance of crack cocaine being cut!",
                mention_author=False,
                delete_after=10,
            )
            await message.delete()

        if message.channel.id == 1258109558463795210:
            self.msg_cache.append(message)
            self.cull_recent_message_cache()

    @tasks.loop(seconds=10)
    async def secondly(self):
        await self.bot.wait_until_ready()
        dumpster_channel = self.bot.get_channel(1090686615808126996)
        self.cull_recent_message_cache()
        if len(self.msg_cache) > self.msg_record:
            self.msg_record = len(self.msg_cache)
        if len(self.msg_cache) >= 10:
            await dumpster_channel.send(
                f"Dumpster is currently at **{len(self.msg_cache)}** messages per minute!\nThe fastest was **{self.msg_record}** messages per minute!\n**MAKE IT GO FASTER YOU IDIOTS, __FASTER__!**"
            )


async def setup(bot):
    await bot.add_cog(Af2023(bot))
