import discord
from discord.ext import commands
from discord.ext.commands import Cog


class Explains(Cog):
    """
    Commands for easily explaining certain things.
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx):
        """[U] Staff defined tags."""
        return await ctx.send("Staff tag list coming soonTM")

    @tag.command(aliases=["memechannel", "wherememes", "memes", "whypay"])
    async def dumpster(self, ctx):
        """Explains Dumpster."""
        return await ctx.send(
            "**Where can I meme?/Why do I have to pay for memes?/You paywalled your meme channel!**\nA while ago, there was a channel for memes called Dumpster. It was removed due to misuse. In an effort to revive the channel, and curbstomp misuse in the process, all users of Dumpster are required to donate to charity *once*. To do so, see the <#1104519693026476173>.\nYou can also donate to the Staff team through Server Subscriptions, but the charity donation is preferred.\n\n**Please keep memes out of this server. <#256926147827335170> and <#256970699581685761> are NOT substitute meme channels.**"
        )

    @tag.command(aliases=["pluralkit"])
    async def plurality(self, ctx):
        """Explains PluralKit and bot webhooks."""
        return await ctx.send(
            '**What is PluralKit?/Why are there people chatting as bots?**\nPluralKit, specifically, allows plural users (see <https://pluralpedia.org/w/Plurality> for more information!) to chat without breaking the no-alting rule.\n\n**All plural users are valid. Please do not treat them as "wow! how do I chat like a bot???".**'
        )

    @tag.command(aliases=["matrix", "revolt"])
    async def forwarders(self, ctx):
        """Explains the alternative chat forwarders."""
        return await ctx.send(
            "**Why are there people chatting as bots?/Why are people chatting off platform?**\nThe OneShot Discord has two different chats attached to it.\n- Matrix (see <https://matrix.org/>), bridged to <#256970699581685761>, is open to all and is available in the channel topic.\n- Revolt (see <https://revolt.chat/>) is private *for now*, is available in all channels, and will eventually be open as a mirror for the OneShot Discord."
        )

    @tag.command(aliases=["embeds", "howpostembeds", "embed", "emoji"])
    async def journal(self, ctx):
        """Explains Strange Journal and Camera."""
        await ctx.send(
            '**How do I post embeds/use emoji/stickers/reactions?**\nTo do any of the following:\n- Post embeds.\n- React to messages.\n- Post emoji.\n- Post stickers.\n- Speak in voice channels.\n\nYou need the Strange Journal role. <#256926147827335170> specifically requires the Camera role to post embeds.\nTo learn how to get these roles, read <#989959374900449380> thoroughly.\n\n**Do __not__ "spoonfeed" any user the command for them (e.g. "just use X command!)". Doing so may result in a warning.**'
        )

    @tag.command(aliases=["readcontrols", "beforeask"])
    async def controls(self, ctx):
        """Tells someone to read controls."""
        await ctx.send(
            "**Whatever your question is, READ <#989959374900449380> FIRST!**\nYou are asking a question that is already answered in the information channel.\nYour question will not be answered until you read the information channel and attempt to find the answer for yourself.\nIf you are still having trouble, only then you may ask on where to find the answer."
        )

    @tag.command(aliases=["nogifs"])
    async def tenor(self, ctx):
        """Explains why Tenor is banned."""
        await ctx.send(
            "**Why can't I use tenor GIFs?**\nTenor GIFs are banned from this server due to spam and misuse.\nYou are welcome to upload your own GIFs though, if they are relevant."
        )

    @tag.command(aliases=["howappeal", "howtoappeal"])
    async def appeal(self, ctx):
        """Explains how to appeal."""
        await ctx.send(
            "**To appeal a ban, use the following link.**\nhttps://os.sysware.plus/appeal\n\nThis link can also be found on the pinned Steam Discussions post, and on the external site at https://os.sysware.plus"
        )


async def setup(bot):
    await bot.add_cog(Explains(bot))
