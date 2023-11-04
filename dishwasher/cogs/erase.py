import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import random
import asyncio
import zipfile
from helpers.sv_config import get_config
from helpers.datafiles import get_guildfile, set_guildfile


class Erase(Cog):
    """
    For when you want to be forgotten.
    """

    def __init__(self, bot):
        self.bot = bot
        self.verifycode = format(random.getrandbits(128), "x")[:10]

    async def cog_load(self):
        await self.process_erased()

    def add_erased(self, guild, user, keywords, channels):
        erasequeue = get_guildfile(ctx.guild.id, "erasures")
        erasequeue[user.id] = {
            "keywords": keywords,
            "channels": channels,
            "completed": [],
        }
        set_guildfile(ctx.guild.id, "erasures", json.dumps(erasequeue))

    async def process_erased(self):
        await self.bot.wait_until_ready()
        api_url = "https://litterbox.catbox.moe/resources/internals/api.php"
        # Main loop.
        while True:
            # Guild loop.
            for g in self.bot.guilds:
                erasequeue = get_guildfile(g.id, "erasures")
                if not erasequeue:
                    await asyncio.sleep(60)
                    continue
                # User loop.
                for userid, params in erasequeue.items():
                    user = self.bot.fetch_user(userid)
                    batchzip = None
                    if params["channels"]:
                        channels = []
                        # Fill list of channels to run through.
                        for channel in params["channels"]:
                            if channel in params["completed"]:
                                continue
                            try:
                                channels.append(await g.fetch_channel(channel))
                            except:
                                # Assume channel already deleted.
                                erasequeue["userid"]["channels"].append(channel)
                                set_guildfile(g.id, "erasures", json.dumps(erasequeue))
                                continue

                        # Keyword setup.
                        if params["keywords"]:

                            def messagecheck(m):
                                return m.author.id == user.id and any(
                                    [
                                        keyword in m.content
                                        for keyword in params["keywords"]
                                    ]
                                )

                        else:

                            def messagecheck(m):
                                return m.author.id == user.id

                        # Actual processing of channels.
                        for channel in channels:
                            async for message in channel.history(oldest_first=True):
                                if message.author.id != user.id:
                                    continue
                                if message.attachments:
                                    for attachment in message.attachments:
                                        if (
                                            os.path.getsize("erasedbatch.zip")
                                            + attachment.size
                                            >= 524288000
                                        ):
                                            batchzip.close()
                                            with open(
                                                "erasedbatch.zip", "rb"
                                            ) as batchfile:
                                                formdata = aiohttp.FormData()
                                                formdata.add_field(
                                                    "reqtype", "fileupload"
                                                )
                                                formdata.add_field("time", "72h")
                                                formdata.add_field(
                                                    "fileToUpload", batchfile
                                                )
                                                async with self.bot.session.post(
                                                    api_url, data=formdata
                                                ) as response:
                                                    url = await response.text()
                                            await user.send(
                                                f"A batch of erased files from `{g.name}` has been uploaded.\nPlease download it within 72 hours.\n{url}"
                                            )
                                            os.remove("erasedbatch.zip")
                                            batchzip = zipfile.ZipFile(
                                                "erasedbatch.zip",
                                                mode="w",
                                                compression=zipfile.ZIP_LZMA,
                                            )
                                        batchzip.write(
                                            await attachment.read(), attachment.filename
                                        )
                                try:
                                    await message.delete()
                                except:
                                    continue
                            erasequeue["userid"]["completed"].append(channel.id)
                            set_guildfile(g.id, "erasures", json.dumps(erasequeue))
                    if batchzip:
                        batchzip.close()
                    if os.path.exists("erasedbatch.zip"):
                        with open("erasedbatch.zip", "rb") as batchfile:
                            formdata = aiohttp.FormData()
                            formdata.add_field("reqtype", "fileupload")
                            formdata.add_field("time", "72h")
                            formdata.add_field("fileToUpload", batchfile)
                            async with self.bot.session.post(
                                api_url, data=formdata
                            ) as response:
                                url = await response.text()
                        await user.send(
                            f"The final batch of erased files from `{g.name}` has been uploaded.\nPlease download it within 72 hours.\n{url}"
                        )
                        os.remove("erasedbatch.zip")
                    await user.send(
                        "All messages that could be deleted have been deleted."
                    )
                    del erasequeue["userid"]
                    set_guildfile(g.id, "erasures", json.dumps(erasequeue))

    @commands.guild_only()
    @commands.command()
    async def erase(self, ctx, verify=None):
        erasequeue = get_guildfile(ctx.guild.id, "erasures")
        if str(ctx.author.id) in erasequeue:
            return await ctx.reply(
                content=f"You have already requested to delete your messages from `{ctx.guild.name}`.",
                mention_author=False,
            )
        if not verify:
            return await ctx.reply(
                content=f"**THIS IS A VERY DESTRUCTIVE AND IRREVERSIBLE ACTION!**\nThe `erase` command will systematically and painstakingly wipe your post history from the current server, leaving **NOTHING** behind!\nWhile this is proceeding, you may be DMed zip files containing files and images uploaded to this server.\nI __strongly__ recommend you request your Data Package first by going to the following location on your client:\n- `Settings`\n- `Privacy & Safety`\n- `Request all of my data`\nWait for it to arrive before proceeding.\n\nIf you are SURE that you want to do this, rerun this command with the following code: `{self.verifycode}`",
                delete_after=60,
            )
        if verify != self.verifycode:
            return await ctx.reply("You specified an incorrect verification code.")
        else:
            self.verifycode = format(random.getrandbits(128), "x")[:10]

            def messagecheck(m):
                return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

            keywordask = await ctx.reply(
                content='If you would like to delete messages by certain keywords, enter them now, separated by spaces.\nIf you would like to purge everything, simply reply "all".',
                mention_author=False,
            )

            try:
                keywordmsg = await self.bot.wait_for(
                    "message", timeout=300.0, check=messagecheck
                )
            except asyncio.TimeoutError:
                return await keywordask.edit(
                    content="Operation timed out.",
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )

            if keywordmsg.content.split()[0] == "all":
                keywords = []
            else:
                keywords = keywordmsg.content.split()

            await keywordask.edit(
                content=f"Set keywords include: `{str(keywords)}`.",
                delete_after=10,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )

            channelask = await ctx.reply(
                content='If you would like to delete messages from certain channels, enter them now (channel IDs only), separated by spaces.\nIf you would like to purge everything, simply reply "all".',
                mention_author=False,
            )

            try:
                channelmsg = await self.bot.wait_for(
                    "message", timeout=300.0, check=messagecheck
                )
            except asyncio.TimeoutError:
                return await channelask.edit(
                    content="Operation timed out.",
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )

            if channelmsg.content.split()[0] == "all":
                channels = []
            else:
                channels = channelmsg.content.split()
                for channel in channels:
                    try:
                        await ctx.guild.fetch_channel(channel)
                    except:
                        return await ctx.reply(
                            content="One or more of your channel IDs didn't align with any channel on this server.\nPlease run the command again.",
                            mention_author=False,
                        )

            await channelask.edit(
                content=f"Set channels include: `{str(channels)}`.",
                delete_after=10,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )

            await ctx.reply(
                content="You will receive a DM as a test.",
                delete_after=5,
                mention_author=False,
            )
            try:
                await ctx.author.send(
                    content="This ia test, please ignore this message.", delete_after=5
                )
            except:
                return await ctx.reply(
                    content="You were unable to be DMed. Fix your DM settings with me, and then try again.",
                    mention_author=False,
                )

            self.add_erased(ctx.guild, ctx.author, keywords, channels)
            return await ctx.reply(
                content=f"You have requested to delete your messages from `{ctx.guild.name}`. This __cannot__ be undone.\nIt may take a while for the process to begin.",
                mention_author=False,
            )


async def setup(bot):
    await bot.add_cog(Erase(bot))
