import json
from typing import Dict
import discord
import config
from discord.ext.commands import Cog
from helpers.sv_config import get_config
from helpers.embeds import stock_embed


class Nopolls(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_socket_raw_receive(self, msg):
        msg_json = json.loads(msg)
        opcode = msg_json["op"]
        event = msg_json["t"]
        payload = msg_json["d"]

        if (
            opcode != 0
            or event != "MESSAGE_CREATE"
            or "poll" not in payload
            or "guild_id" not in payload
            or not payload["poll"]
            or not payload["guild_id"]
        ):
            return

        guild = self.bot.get_guild(int(payload["guild_id"]))
        channel = guild.get_channel_or_thread(int(payload["channel_id"]))
        author = guild.get_member(int(payload["author"]["id"]))
        message = channel.get_partial_message(int(payload["id"]))

        # Ignore unconfigured guilds is leeching off of burstreacts for now
        if not get_config(guild.id, "reaction", "burstreactsenable"):
            return

        await message.delete()

        mlog = self.bot.pull_channel(guild, get_config(guild.id, "logging", "modlog"))
        if not mlog:
            return

        # Send information to log channel
        embed = stock_embed(self.bot)
        embed.title = "🗑️ Autoremoved a Poll"
        embed.description = (
            f"`{author}`'s poll was removed. [{message.channel.mention}]"
        )
        embed.color = 0xEA50BA
        embed.set_author(
            name=self.bot.escape_message(author),
            icon_url=author.display_avatar.url,
        )

        await mlog.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Nopolls(bot))
