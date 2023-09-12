from discord.ext import commands
from discord.ext.commands import Cog
import config
import discord
import datetime
import asyncio
from helpers.checks import check_if_staff
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, createdat_embed


class ModObserve(Cog):
    """
    A tool to help moderators keep track of potential problem users.
    """

    def __init__(self, bot):
        self.bot = bot
        self.raidmode = []

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def raidmode(self, message, args=""):
        if not args:
            if message.guild.id in self.raidmode:
                await message.reply(
                    "Raid mode is currently `🟢 ON`.", mention_author=False
                )
            else:
                await message.reply(
                    "Raid mode is currently `🔴 OFF`.", mention_author=False
                )
            return
        if args == "on":
            if message.guild.id not in self.raidmode:
                self.raidmode.append(message.guild.id)
                await message.reply("Raid mode is now `🟢 ON`.", mention_author=False)
            else:
                await message.reply(
                    "Raid mode is already `🟢 ON`!", mention_author=False
                )
            return
        if args == "off":
            if message.guild.id in self.raidmode:
                self.raidmode.remove(message.guild.id)
                await message.reply("Raid mode is now `🔴 OFF`.", mention_author=False)
            else:
                await message.reply(
                    "Raid mode is already  `🔴 OFF`!", mention_author=False
                )
            return
        else:
            await message.reply(
                "Incorrect arguments. Use `on` or `off`.", mention_author=False
            )
            return

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if not get_config(member.guild.id, "staff", "staff_channel"):
            return
        ts = datetime.datetime.now(datetime.timezone.utc)
        cutoff_ts = ts - datetime.timedelta(hours=24)
        if member.created_at >= cutoff_ts or member.guild.id in self.raidmode:
            embed = stock_embed(self.bot)
            embed.color = discord.Color.lighter_gray()
            embed.title = "📥 User Joined"
            embed.description = f"{member.mention} ({member.id})"
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_author(name=member, icon_url=member.display_avatar.url)
            createdat_embed(embed, member)

            if member.guild.id in self.raidmode:
                rmstr = "`🟢 ON`"
            else:
                rmstr = "`🔴 OFF`"
            embed.add_field(
                name="🚨 Raid mode...", value=f"is currently {rmstr}.", inline=True
            )
            embed.add_field(
                name="🔍 First message:", value="Currently watching...", inline=False
            )
            callout = await member.guild.get_channel(
                get_config(member.guild.id, "staff", "staff_channel")
            ).send(embed=embed)

            def check(m):
                return m.author.id == member.id and m.guild.id == member.guild

            try:
                msg = await self.bot.wait_for("message", timeout=7200, check=check)
            except asyncio.TimeoutError:
                embed.set_field_at(
                    index=2,
                    name="🔍 First message:",
                    value=f"This user did not send a message within `2 hours`.",
                    inline=False,
                )
            else:
                embed.set_field_at(
                    index=2,
                    name="🔍 First message:",
                    value=f"[Sent]({msg.jump_url}) in {msg.channel.mention} on <t:{msg.created_at.astimezone().strftime('%s')}:f> (<t:{msg.created_at.astimezone().strftime('%s')}:R>):\n```{msg.clean_content}```",
                    inline=False,
                )
            await callout.edit(embed=embed)


async def setup(bot):
    await bot.add_cog(ModObserve(bot))
