import json
from typing import Dict
import discord
import config
from discord.ext import commands
from helpers.sv_config import get_config
from helpers.embeds import stock_embed


class Nopolls(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def poll_check(self, payload):
        channel_id = payload["channel_id"]
        user_id = payload["author"]["id"]
        message_id = payload["id"]
        guild_id = payload.get("guild_id", None)
        poll = payload["poll"]

        # Ignore not super reactions or DM reaction add events
        if not poll or not guild_id:
            return

        # Ignore not configured guilds
        # leeching off of burstreacts for now
        if not get_config(guild_id, "reaction", "burstreactsenable"):
            return

        guild = self.bot.get_guild(int(guild_id))
        channel = guild.get_channel_or_thread(int(channel_id))
        author = guild.get_member(int(user_id))
        message = channel.get_partial_message(int(message_id))

        # Remove message
        await message.delete()

        mlog = self.bot.pull_channel(guild, get_config(guild.id, "logging", "modlog"))

        if not mlog:
            return

        # Send information to log channel
        embed = stock_embed(self.bot)
        embed.title = "🗑️ Autoremoved a Poll"
        embed.description = f"`{author}`'s poll was removed. [{message.channel.mention}]"
        embed.color = 0xEA50BA
        embed.set_author(
            name=self.bot.escape_message(author),
            icon_url=author.display_avatar.url,
        )

        await mlog.send(embed=embed)

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, msg: str):
        msg_json = json.loads(msg)
        opcode = msg_json["op"]
        event = msg_json["t"]
        data = msg_json["d"]

        if opcode == 0 and event == "MESSAGE_CREATE":
            await self.poll_check(data)


async def setup(bot):
    await bot.add_cog(Nopolls(bot))
