import re
import config
import discord
import datetime
import asyncio
import deepl
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.sv_config import get_config


class Messagespam(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channelspam = {}

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def gather(self, ctx):
        if ctx.channel.id in self.prevmessages:
            lastmsg = self.prevmessages[ctx.channel.id]
            # Prepare embed msg
            embed = discord.Embed(
                color=ctx.author.color,
                description=lastmsg.content,
                timestamp=lastmsg.created_at,
            )
            embed.set_footer(
                text=f"Sniped by {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
            embed.set_author(
                name=f"💬 {lastmsg.author} said in #{lastmsg.channel.name}...",
                icon_url=lastmsg.author.display_avatar.url,
            )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                content="There is no message delete in the snipe cache for this channel.",
                mention_author=False,
            )

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

        if all(
            (
                message.content,
                message.content
                == self.channelspam[message.guild.id][message.channel.id][
                    "original_message"
                ],
            )
        ) or all(
            (
                not message.content,
                message.stickers,
                message.stickers[0].url
                == self.channelspam[message.guild.id][message.channel.id][
                    "original_message"
                ],
            )
        ):
            if (
                message.author.id
                in self.channelspam[message.guild.id][message.channel.id]["senders"]
            ):
                return
            self.channelspam[message.guild.id][message.channel.id]["senders"].append(
                message.author.id
            )
        else:
            self.channelspam[message.guild.id][message.channel.id] = {
                "original_message": message.content,
                "senders": [message.author.id],
            }

        if len(self.channelspam[message.guild.id][message.channel.id]["senders"]) >= 5:
            await message.channel.purge(
                limit=len(
                    self.channelspam[message.guild.id][message.channel.id]["senders"]
                )
            )
            await message.channel.send("Detected and purged message spam.")
            self.channelspam[message.guild.id][message.channel.id] = {
                "original_message": message.content,
                "senders": [message.author.id],
            }


async def setup(bot: Bot):
    await bot.add_cog(Messagespam(bot))
