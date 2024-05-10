from discord.ext import commands
from discord.ext.commands import Cog
import discord
import datetime
import asyncio
import json
from helpers.checks import ismod
from helpers.sv_config import get_config
from helpers.embeds import stock_embed, createdat_embed, author_embed
from helpers.datafiles import get_guildfile, set_guildfile


class ModRaidmode(Cog):
    """
    A tool to help moderators manage raids.
    """

    def __init__(self, bot):
        self.bot = bot
        self.raidmode = []

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def raidmode(self, ctx):
        """This sets raidmode for the server.

        Medium requires `raidrole` to be configured.

        No arguments."""
        raidmode = get_guildfile(ctx.guild.id, "raidmode")
        if "setting" not in raidmode:
            raidmode["setting"] = 0
        embed = stock_embed(self.bot)
        embed.title = "🎚️ Your raidmode setting..."
        embed.description = f"Use the reactions to set the level. It will be preserved between bot restarts."
        embed.color = discord.Color.red()
        author_embed(embed, ctx.author)
        allowed_mentions = discord.AllowedMentions(replied_user=False)

        def fieldadd():
            off = "🔲" if not raidmode["setting"] else "⬛"
            embed.add_field(
                name="⬜ Off",
                value=off + " Raidmode will be turned off.",
                inline=False,
            )

            low = "🔲" if raidmode["setting"] == 1 else "⬛"
            embed.add_field(
                name="🟩 Low",
                value=low + " Raidmode will post new users to the Staff channel.",
                inline=False,
            )

            med = "🔲" if raidmode["setting"] == 2 else "⬛"
            embed.add_field(
                name="🟨 Medium",
                value=med
                + " Raidmode will assign a role to new users and post them to the Staff channel.",
                inline=False,
            )

            high = "🔲" if raidmode["setting"] == 3 else "⬛"
            embed.add_field(
                name="🟥 High",
                value=high + " Raidmode will automatically kick new users.",
                inline=False,
            )

        reacts = (
            ["⬜", "🟩"]
            + [
                (
                    "🟨"
                    if self.bot.pull_role(
                        ctx.guild, get_config(ctx.guild.id, "staff", "raidrole")
                    )
                    else "🚫"
                )
            ]
            + ["🟥"]
        )
        fieldadd()
        configmsg = await ctx.reply(embed=embed, mention_author=False)
        for react in reacts:
            await configmsg.add_reaction(react)
        embed.color = discord.Color.green()
        await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in reacts

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            embed.color = discord.Color.default()
            for react in reacts:
                await configmsg.remove_reaction(react, ctx.bot.user)
            return await configmsg.edit(
                embed=embed,
                allowed_mentions=allowed_mentions,
            )
        else:
            if str(reaction) == "⬜":
                raidmode["setting"] = 0
            elif str(reaction) == "🟩":
                raidmode["setting"] = 1
            elif str(reaction) == "🟨":
                raidmode["setting"] = 2
            elif str(reaction) == "🟥":
                raidmode["setting"] = 3
            set_guildfile(ctx.guild.id, "raidmode", json.dumps(raidmode))
            embed.clear_fields()
            fieldadd()
            embed.color = discord.Color.gold()
            for react in reacts:
                await configmsg.remove_reaction(react, ctx.bot.user)
            await configmsg.edit(embed=embed, allowed_mentions=allowed_mentions)

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        staffchannel = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "staff", "staffchannel")
        )
        if not staffchannel:
            return
        raidmode = get_guildfile(member.guild.id, "raidmode")
        if "setting" not in raidmode:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.description = f"{member.mention} ({member.id})"
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=member, icon_url=member.display_avatar.url)
        createdat_embed(embed, member)

        async def messagewait():
            embed.add_field(
                name="🔍 First message:", value="Currently watching...", inline=False
            )
            callout = await staffchannel.send(embed=embed)

            def check(m):
                return (
                    m.author.id == member.id
                    and m.guild.id == member.guild.id
                    and not m.is_system()
                )

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
                    value=f"[Sent]({msg.jump_url}) in {msg.channel.mention} on <t:{int(msg.created_at.astimezone().timestamp())}:f> (<t:{int(msg.created_at.astimezone().timestamp())}:R>):\n```{msg.clean_content}```",
                    inline=False,
                )
            await callout.edit(embed=embed)

        if raidmode["setting"] == 3:
            embed.title = "👢 Kick"
            rmstr = "`🟥 High`"
            await member.kick(
                reason="Sangou's Raidmode is set to `🟥 High`. Try again later."
            )
        else:
            embed.title = "📥 User Joined"
        if raidmode["setting"] == 2:
            rmstr = "`🟨 Medium`"
            if self.bot.pull_role(
                member.guild, get_config(member.guild.id, "staff", "raidrole")
            ):
                await member.add_roles(
                    member.guild.get_role(
                        self.bot.pull_role(
                            member.guild,
                            get_config(member.guild.id, "staff", "raidrole"),
                        )
                    )
                )
        if raidmode["setting"] == 1:
            rmstr = "`🟩 Low`"
        if raidmode["setting"] == 0:
            ts = datetime.datetime.now(datetime.timezone.utc)
            cutoff_ts = ts - datetime.timedelta(hours=24)
            if not member.created_at >= cutoff_ts:
                return
            rmstr = "`⬜ Off`"
        embed.add_field(
            name="🚨 Raid mode...", value=f"is currently {rmstr}.", inline=True
        )
        if raidmode["setting"] < 3:
            await messagewait()


async def setup(bot):
    await bot.add_cog(ModRaidmode(bot))
