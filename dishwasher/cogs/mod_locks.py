from discord.ext import commands
from discord.ext.commands import Cog
import discord
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class ModLocks(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snapshots = {}

    async def set_sendmessage(
        self, channel: discord.TextChannel, role, allow_send, issuer
    ):
        try:
            roleobj = channel.guild.get_role(role)
            overrides = channel.overwrites_for(roleobj)
            overrides.send_messages = allow_send
            await channel.set_permissions(
                roleobj, overwrite=overrides, reason=str(issuer)
            )
        except:
            pass

    async def unlock_for_staff(self, channel: discord.TextChannel, issuer):
        await self.set_sendmessage(
            channel,
            get_config(channel.guild.id, "staff", "staffrole"),
            True,
            issuer,
        )

    async def unlock_for_bots(self, channel: discord.TextChannel, issuer):
        await self.set_sendmessage(
            channel,
            get_config(channel.guild.id, "staff", "botrole"),
            True,
            issuer,
        )

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["lockdown"])
    async def lock(self, ctx, soft: bool = False, channel: discord.TextChannel = None):
        """[S] Prevents people from speaking in a channel.

        Defaults to current channel."""
        if not channel:
            channel = ctx.channel
        mlog = get_config(ctx.guild.id, "logging", "modlog")
        staff_role_id = get_config(ctx.guild.id, "staff", "staffrole")
        bot_role_id = get_config(ctx.guild.id, "staf", "botrole")

        # Take a snapshot of current channel state before making any changes
        if ctx.guild.id not in self.snapshots:
            self.snapshots[ctx.guild.id] = {}
        if channel.id in self.snapshots[ctx.guild.id]:
            return await ctx.reply(
                content="This channel is already locked.", mention_author=False
            )
        self.snapshots[ctx.guild.id][channel.id] = channel.overwrites

        roles = []
        if not channel.permissions_for(ctx.guild.default_role).read_messages:
            for role, overwrite in list(channel.overwrites.items()):
                if channel.permissions_for(role).read_messages:
                    roles.append(r.id)
        elif not channel.permissions_for(ctx.guild.default_role).send_messages:
            for role, overwrite in list(channel.overwrites.items()):
                if (
                    channel.permissions_for(role).send_messages
                    and channel.permissions_for(role).read_messages
                ):
                    roles.append(r.id)
        else:
            roles.append(ctx.guild.default_role.id)
            for r in channel.changed_roles:
                if (
                    not channel.permissions_for(r).send_messages
                    or not channel.permissions_for(r).read_messages
                ):
                    continue
                roles.append(r.id)

        if staff_role_id in roles:
            roles.remove(staff_role_id)
        if bot_role_id in roles:
            roles.remove(bot_role_id)

        for role in roles:
            await self.set_sendmessage(channel, role, False, ctx.author)

        await self.unlock_for_staff(channel, ctx.author)
        await self.unlock_for_bots(channel, ctx.author)

        public_msg = "🔒 Channel locked down. "
        if not soft:
            public_msg += (
                "Only Staff may speak. "
                '**Do not** bring the topic to other channels or risk action taken. This includes "What happened?" messages.'
            )

        await ctx.reply(public_msg, mention_author=False)
        if mlog:
            msg = f"🔒 **Lockdown**: {ctx.channel.mention} by {ctx.author}"
            mlog = await self.bot.fetch_channel(mlog)
            await mlog.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """[S] Unlocks speaking in current channel."""
        if not channel:
            channel = ctx.channel
        mlog = get_config(ctx.guild.id, "logging", "modlog")

        # Restore from snapshot state.
        overwrites = self.snapshots[ctx.guild.id][channel.id]
        try:
            del self.snapshots[ctx.guild.id][channel.id]
        except:
            return await ctx.reply(
                content="This channel is not already locked.", mention_author=False
            )
        for o, p in channel.overwrites.items():
            try:
                if o in overwrites:
                    await channel.set_permissions(o, overwrite=overwrites[o])
                else:
                    await channel.set_permissions(o, overwrite=None)
            except:
                continue

        await ctx.reply("🔓 Channel unlocked.", mention_author=False)
        if mlog:
            msg = f"🔓 **Unlock**: {ctx.channel.mention} by {ctx.author}"
            mlog = await self.bot.fetch_channel(mlog)
            await mlog.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def lockout(self, ctx, target: discord.Member):
        if target == ctx.author:
            return await ctx.reply(
                random_self_msg(ctx.author.name), mention_author=False
            )
        elif target == self.bot.user:
            return await ctx.reply(
                random_bot_msg(ctx.author.name), mention_author=False
            )
        elif self.bot.check_if_target_is_staff(target):
            return await ctx.reply(
                "I cannot lockout Staff members.", mention_author=False
            )

        await ctx.channel.set_permissions(target, send_messages=False)
        await ctx.reply(content=f"{target} has been locked out.", mention_author=False)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def unlockout(self, ctx, target: discord.Member):
        if target == ctx.author:
            return await ctx.reply(
                random_self_msg(ctx.author.name), mention_author=False
            )
        elif target == self.bot.user:
            return await ctx.reply(
                random_bot_msg(ctx.author.name), mention_author=False
            )
        elif self.bot.check_if_target_is_staff(target):
            return await ctx.reply(
                "I cannot unlockout Staff members.", mention_author=False
            )

        await ctx.channel.set_permissions(target, overwrite=None)
        await ctx.reply(
            content=f"{target} has been unlocked out.", mention_author=False
        )


async def setup(bot):
    await bot.add_cog(ModLocks(bot))
