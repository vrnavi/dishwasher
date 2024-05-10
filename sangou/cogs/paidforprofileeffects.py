import json
from typing import Dict
import discord
import random
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.sv_config import get_config
from helpers.embeds import stock_embed


class AvyDecorations(Cog):
    def __init__(self, bot: commands.Bot):
        """
        Laughs at you if you have profile effects.
        """
        self.bot = bot

    async def profile_check(self, payload: Dict):
        """The funny handler."""
        channel_id = payload["channel_id"]
        user_id = payload["author"]["id"]
        message_id = payload["id"]
        decoration_hash = payload["author"].get("avatar_decoration_data", None)

        guild_id = None
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if channel.id == int(channel_id):
                    guild_id = guild.id

        if (
            not decoration_hash
            or not guild_id
            or decoration_hash["sku_id"]
            in ("1144058522808614923", "1144058844004233369", "1144059132517826601")
        ):
            return

        # Ignore not configured guilds
        if not get_config(guild_id, "reaction", "paidforprofileeffectsenable"):
            return

        guild = self.bot.get_guild(int(guild_id))
        channel = guild.get_channel_or_thread(int(channel_id))
        author = guild.get_member(int(user_id))
        message = channel.get_partial_message(int(message_id))

        # Laugh
        if random.randint(1, 100) <= 5:
            await message.reply(
                file=discord.File("assets/congratulations.png"), mention_author=False
            )

    @commands.Cog.listener()
    async def on_socket_raw_receive(self, msg: str):
        """Raw gateway socket events receiver."""
        msg_json = json.loads(msg)
        opcode = msg_json["op"]
        event = msg_json["t"]
        data = msg_json["d"]

        if opcode == 0:
            if event == "MESSAGE_CREATE":
                await self.profile_check(data)


async def setup(bot: commands.Bot):
    await bot.add_cog(AvyDecorations(bot))
