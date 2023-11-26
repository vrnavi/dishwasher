import discord
from discord.ext.commands import Cog
import json
import re
import io
import config
from datetime import datetime
from datetime import timezone
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class AutoApps(Cog):
    """
    Automatic application responses with per-guild variance.
    """

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        if (
            message.guild
            and get_config(message.guild.id, "autoapp", "enable")
            and message.channel.id
            == get_config(message.guild.id, "autoapp", "autoapp_channel")
            and message.author.id
            == get_config(message.guild.id, "autoapp", "autoapp_id")
        ):
            staledays = (
                get_config(message.guild.id, "autoapp", "autoapp_staledays") * 86400
            )
            staff_role = message.guild.get_role(
                get_config(message.guild.id, "staff", "staff_role")
            )
            if staff_role:
                minreq = int(len(staff_role.members) / 2 // 1 + 1)

            # Guild specific code.
            custom_msg = None
            custom_threadname = None
            if message.guild.id == 256926147827335170:
                if not message.embeds:
                    return
                user = await self.bot.fetch_user(message.embeds[0].fields[3].value)
                custom_msg = (
                    "\n"
                    + f"Until it can be coded to automatically appear here, use `pws logs {user.id}`.\nRemember to post ban context if available (ban record, modmail logs, etc.)."
                    + "\n"
                )
            else:
                user = message.author

            await message.add_reaction("✅")
            await message.add_reaction("❎")
            await message.add_reaction("✳️")
            if custom_threadname:
                threadname = custom_threadname
            else:
                threadname = (
                    str(user)
                    + "'s "
                    + get_config(message.guild.id, "autoapp", "autoapp_name")
                )
            appthread = await message.create_thread(
                name=threadname,
                reason=f"Automatic Applications by {self.bot.user.name}.",
            )
            msg = f"Vote using reactions. Use this thread for discussion.\n`✅ = Yes`\n`❎ = No`\n`✳️ = Abstain`\n\n"
            if custom_msg:
                msg += custom_msg + "\n\n"
            elif get_config(message.guild.id, "autoapp", "autoapp_msg"):
                msg += get_config(message.guild.id, "autoapp", "autoapp_msg") + "\n\n"
            if staff_role:
                msg += f"There are currently `{int(len(staff_role.members))}` Staff members at this time.\nVoting should end once one option reaches `{minreq}` votes."
            if staledays:
                msg += f"\n\nThis {get_config(message.guild.id, 'autoapp', 'autoapp_name')} will turn stale on <t:{int(datetime.now(timezone.utc).timestamp())+staledays}:f>, or <t:{int(datetime.now(timezone.utc).timestamp())+staledays}:R>."
            await appthread.send(content=msg)


async def setup(bot):
    await bot.add_cog(AutoApps(bot))
