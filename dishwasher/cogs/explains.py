import discord
from discord.ext import commands
from discord.ext.commands import Cog


class Explains(Cog):
    """
    Commands for easily explaining certain things.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True, aliases=["memechannel", "wherememes", "memes"])
    async def dumpster(self, ctx):
        """Explains Dumpster."""
        return
        # await ctx.send(
        #    "**Where can I meme?/Why is there no meme channel?**\nA while ago, there was a channel for memes called Dumpster. It was removed due to misuse. Dumpster has not, is not, and will never be a core part of this server, and it is not coming back.\n\n**Please keep memes out of this server. <#256926147827335170> and <#256970699581685761> are NOT substitute meme channels.**"
        # )

    @commands.command(
        hidden=True, aliases=["embeds", "howpostembeds", "embed", "emoji"]
    )
    async def journal(self, ctx):
        """Explains Strange Journal and Camera."""
        await ctx.send(
            '**How do I post embeds/use emoji/stickers/reactions?**\nTo do any of the following:\n- Post embeds.\n- React to messages.\n- Post emoji.\n- Post stickers.\n- Speak in voice channels.\n\nYou need the Strange Journal role. <#256926147827335170> specifically requires the Camera role to post embeds.\nTo learn how to get these roles, read <#989959374900449380> thoroughly.\n\n**Do __not__ "spoonfeed" any user the command for them (e.g. "just use X command!)". Doing so may result in a warning.**'
        )

    @commands.command(hidden=True, aliases=["readcontrols", "beforeask"])
    async def controls(self, ctx):
        """Tells someone to read controls."""
        await ctx.send(
            "**Whatever your question is, READ <#989959374900449380> FIRST!**\nYou are asking a question that is already answered in the information channel.\nYour question will not be answered until you read the information channel and attempt to find the answer for yourself.\nIf you are still having trouble, only then you may ask on where to find the answer."
        )

    @commands.command(hidden=True, aliases=["nogifs"])
    async def tenor(self, ctx):
        """Explains why Tenor is banned."""
        await ctx.send(
            "**Why can't I use tenor GIFs?**\nTenor GIFs are banned from this server due to spam and misuse.\nYou are welcome to upload your own GIFs though, if they are relevant."
        )

    @commands.command(hidden=True, aliases=["howappeal", "howtoappeal"])
    async def appeal(self, ctx):
        """Explains how to appeal."""
        await ctx.send(
            "**To appeal a ban, use the following link.**\nhttp://os.whistler.page/appeal\n\nThis link can also be found on the pinned Steam Discussions post, and on the external site at https://os.whistler.page."
        )


async def setup(bot):
    await bot.add_cog(Explains(bot))
