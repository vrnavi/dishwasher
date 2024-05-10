import re
import discord
import datetime
import asyncio
import deepl
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.sv_config import get_config


class Messagespam(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channelspam = {}

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.content
            and not message.stickers
            or message.author.bot
            or not message.guild
            or message.guild.id != 256926147827335170
        ):
            return

        if message.guild.id not in self.channelspam:
            self.channelspam[message.guild.id] = {}

        if message.channel.id not in self.channelspam[message.guild.id]:
            self.channelspam[message.guild.id][message.channel.id] = {
                "original_message": message.content,
                "senders": [message.author.id],
            }
            return

        if (
            message.content
            and message.content
            != self.channelspam[message.guild.id][message.channel.id][
                "original_message"
            ]
            or message.stickers
            and message.stickers[0].url
            != self.channelspam[message.guild.id][message.channel.id][
                "original_message"
            ]
        ):
            self.channelspam[message.guild.id][message.channel.id] = {
                "original_message": message.content,
                "senders": [message.author.id],
            }
            return

        if (
            message.author.id
            in self.channelspam[message.guild.id][message.channel.id]["senders"]
        ):
            return
        self.channelspam[message.guild.id][message.channel.id]["senders"].append(
            message.author.id
        )

        if len(self.channelspam[message.guild.id][message.channel.id]["senders"]) >= 5:
            await message.channel.purge(
                limit=len(
                    self.channelspam[message.guild.id][message.channel.id]["senders"]
                )
            )
            await message.channel.send(
                "Detected and purged message spam.\n**Offending users:**\n"
                + "\n".join(
                    [
                        str(await self.bot.fetch_user(x))
                        for x in self.channelspam[message.guild.id][message.channel.id][
                            "senders"
                        ]
                    ]
                )
            )
            self.channelspam[message.guild.id][message.channel.id] = {
                "original_message": message.content,
                "senders": [message.author.id],
            }


async def setup(bot: Bot):
    await bot.add_cog(Messagespam(bot))
