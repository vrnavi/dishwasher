import discord
from discord.ext.commands import Cog
import json
import re
import datetime
import os
from helpers.datafiles import add_userlog, get_guildfile
from helpers.sv_config import get_config
from helpers.embeds import (
    stock_embed,
    slice_embed,
    mod_embed,
    author_embed,
    createdat_embed,
    joinedat_embed,
)


class Logs2(Cog):
    """
    An advanced logging mechanism, which logs. Logs many changes.
    """

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()

        ulog = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "logging", "userlog")
        )
        if not ulog:
            return

        invite_used = await self.bot.get_used_invites(member)

        embeds = []
        embed = stock_embed(self.bot)
        embed.color = discord.Color.lighter_gray()
        embed.title = "📥 User Joined"
        embed.description = f"{member.mention} ({member.id})"
        author_embed(embed, member, True)
        createdat_embed(embed, member)
        embed.add_field(name="📨 Invite used:", value=invite_used, inline=True)

        embeds.append(embed)

        warns = get_guildfile(member.guild.id, "userlog")
        try:
            if warns[str(member.id)]["warns"]:
                embed = stock_embed(self.bot)
                embed.color = discord.Color.red()
                embed.title = "⚠️ This user has warnings!"
                for idx, warn in enumerate(warns[str(member.id)]["warns"]):
                    timestamp = warn["timestamp"]
                    embed.add_field(
                        name=f"Warn {idx + 1}: <t:{timestamp}:f> (<t:{timestamp}:R>)",
                        value=f"__Issuer:__ <@{warn['issuer_id']}> ({warn['issuer_id']})\n"
                        f"\n__Reason:__ {warn['reason']}",
                        inline=False,
                    )
                embeds.append(embed)
        except KeyError:  # if the user is not in the file
            pass

        await ulog.send(embeds=embeds)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        await self.bot.wait_until_ready()
        if (
            after.author.bot
            or not after.guild
            or before.clean_content == after.clean_content
        ):
            return

        ulog = self.bot.pull_channel(
            after.guild, get_config(after.guild.id, "logging", "userlog")
        )
        if not ulog:
            return

        if not after.edited_at:
            # TODO: implement logging for embeds being suppressed
            # this is just a catch-all in case it's a message flag
            # being changed or something (crossposted, embed suppressed,
            # w/e else
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.light_gray()
        embed.title = "📝 Message Edit"
        embed.description = f"{after.author.mention} ({after.author.id}) in {after.channel.mention} [[Jump]({after.jump_url})]"
        author_embed(embed, after.author)

        slice_embed(
            embed,
            before.clean_content,
            f"❌ Before on <t:{int(before.created_at.astimezone().timestamp())}:f>",
        )
        slice_embed(
            embed,
            after.clean_content,
            f"⭕ After on <t:{int(after.edited_at.astimezone().timestamp())}:f>",
        )

        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot or not message.guild:
            return

        ulog = self.bot.pull_channel(
            message.guild, get_config(message.guild.id, "logging", "userlog")
        )
        if not ulog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.dark_gray()
        embed.title = "🗑️ Message Delete"
        embed.description = f"{message.author.mention} ({message.author.id}) in {message.channel.mention}"
        author_embed(embed, message.author)

        slice_embed(
            embed,
            message.clean_content,
            f"🧾 Sent on <t:{int(message.created_at.astimezone().timestamp())}:f>:",
        )

        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()

        ulog = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "logging", "userlog")
        )
        mlog = self.bot.pull_channel(
            member.guild, get_config(member.guild.id, "logging", "modlog")
        )
        if not ulog and not mlog:
            return

        try:
            await member.guild.fetch_ban(member)
            return
        except discord.NotFound:
            pass
        except discord.Forbidden:
            # Put in a "no permissions to check why!" disclaimer
            return

        alog = [
            entry
            async for entry in member.guild.audit_logs(
                limit=1, action=discord.AuditLogAction.kick
            )
        ]
        if alog and alog[0].target.id == member.id:
            cutoff_ts = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(seconds=5)
            if not alog[0].created_at <= cutoff_ts:
                if alog[0].user.id != self.bot.user.id:
                    add_userlog(
                        member.guild.id,
                        member.id,
                        alog[0].user,
                        "Kicked by external method.",
                        "kicks",
                    )
                    if not mlog:
                        return

                    user = member
                    staff = alog[0].user
                    reason = alog[0].reason

                    embed = stock_embed(self.bot)
                    embed.color = discord.Color.from_str("#FFFF00")
                    embed.title = "👢 Kick"
                    embed.description = f"{user.mention} was kicked by {staff.mention} [External Method]"
                    mod_embed(embed, user, staff, reason)

                    await mlog.send(embed=embed)
                return

        if not ulog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.darker_gray()
        embed.title = "📥 User Left"
        embed.description = f"{member.mention} ({member.id})"
        author_embed(embed, member, True)
        createdat_embed(embed, member)
        joinedat_embed(embed, member)

        await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_ban(self, guild, member):
        await self.bot.wait_until_ready()

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            )
        ]
        if alog[0].user.id == self.bot.user.id or alog[0].target.id != member.id:
            return

        add_userlog(
            guild.id,
            member.id,
            alog[0].user,
            "Banned by external method.",
            "bans",
        )

        mlog = self.bot.pull_channel(guild, get_config(guild.id, "logging", "modlog"))
        if not mlog:
            return

        user = member
        staff = alog[0].user
        reason = alog[0].reason

        embed = stock_embed(self.bot)
        embed.color = discord.Color.from_str("#FF0000")
        embed.title = "⛔ Ban"
        embed.description = (
            f"{user.mention} was banned by {staff.mention} [External Method]"
        )
        mod_embed(embed, user, staff, reason)

        await mlog.send(embed=embed)

    @Cog.listener()
    async def on_member_unban(self, guild, user):
        await self.bot.wait_until_ready()

        mlog = self.bot.pull_channel(guild, get_config(guild.id, "logging", "modlog"))
        if not mlog:
            return

        alog = [
            entry
            async for entry in guild.audit_logs(
                limit=1, action=discord.AuditLogAction.unban
            )
        ]
        if alog[0].user.id == self.bot.user.id:
            return

        user = user
        staff = alog[0].user
        reason = alog[0].reason

        embed = stock_embed(self.bot)
        embed.color = discord.Color.from_str("#00FF00")
        embed.title = "🎁 Unban"
        embed.description = (
            f"{user.mention} was unbanned by {staff.mention} [External Method]"
        )
        mod_embed(embed, user, staff, reason)

        await mlog.send(embed=embed)

    @Cog.listener()
    async def on_user_update(self, user_before, user_after):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            ulog = self.bot.pull_channel(
                guild, get_config(guild.id, "logging", "userlog")
            )
            member = guild.get_member(user_after.id)
            if not ulog or not member:
                continue

            embed = stock_embed(self.bot)
            embed.color = member.color
            embed.title = "ℹ️ Member Update"
            embed.description = f"{member.mention} ({member.id})"
            author_embed(embed, member)

            # Usernames
            if str(user_before) != str(user_after):
                embed.add_field(
                    name="📝 Username Change",
                    value=f"❌ {user_before}\n⬇️\n⭕ {user_after}",
                    inline=False,
                )

            # Display Names
            if user_before.global_name != user_after.global_name:
                embed.add_field(
                    name="🪪 Display Name Change",
                    value=f"❌ {user_before.global_name}\n⬇️\n⭕ {user_after.global_name}",
                    inline=False,
                )

            if embed.fields:
                await ulog.send(embed=embed)

    @Cog.listener()
    async def on_member_update(self, member_before, member_after):
        await self.bot.wait_until_ready()

        ulog = self.bot.pull_channel(
            member_after.guild, get_config(member_after.guild.id, "logging", "userlog")
        )
        if not ulog:
            return

        embed = stock_embed(self.bot)
        embed.color = member_after.color
        embed.title = "ℹ️ Member Update"
        embed.description = f"{member_after.mention} ({member_after.id})"
        author_embed(embed, member_after)

        # Roles
        if member_before.roles != member_after.roles:
            roles = []
            for role in member_after.guild.roles:
                if role == member_after.guild.default_role:
                    continue
                if not member_after.guild.get_role(role.id):
                    # Role was deleted.
                    return
                if role in member_before.roles and role in member_after.roles:
                    roles.append(role.mention)
                elif role in member_before.roles and role not in member_after.roles:
                    roles.append("> ~~" + role.mention + "~~")
                elif role not in member_before.roles and role in member_after.roles:
                    roles.append("> " + role.mention)
                else:
                    continue

            embed.add_field(
                name="🎨 Role Change",
                value="\n".join(reversed(roles)),
                inline=False,
            )

        # Nicknames
        if member_before.nick != member_after.nick:
            if not member_before.nick:
                fname = "🏷 Nickname Added"
            elif not member_after.nick:
                fname = "🏷 Nickname Removed"
            else:
                fname = "🏷 Nickname Changed"
            embed.add_field(
                name=fname,
                value=f"❌ {member_before.nick}\n⬇️\n⭕ {member_after.nick}",
                inline=False,
            )

        if embed.fields:
            await ulog.send(embed=embed)

    @Cog.listener()
    async def on_guild_update(self, guild_before, guild_after):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            guild_after, get_config(guild_after.id, "logging", "serverlog")
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.from_str("#FFCC00")
        embed.title = "🏡 Server Update"
        embed.description = (
            f"{guild_after.name} with `{guild_after.member_count}` members."
        )
        author_embed(embed, guild_after)

        # Server Names
        if guild_before.name != guild_after.name:
            embed.add_field(
                name="📝 Name Change",
                value=f"❌ {guild_before.name}\n⬇️\n⭕ {guild_after.name}",
                inline=False,
            )

        # Server Banners
        try:
            if guild_before.banner.url != guild_after.banner.url:
                if guild_after.banner:
                    text = "The new banner is below."
                    embed.set_image(url=guild_after.banner.url)
                else:
                    text = "The banner was removed."
                embed.add_field(
                    name="🎨 Banner Change",
                    value=text,
                    inline=False,
                )
        except:
            pass

        if embed.fields:
            await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            channel.guild, get_config(channel.guild.id, "logging", "serverlog")
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.from_str("#00FFFF")
        embed.title = "🏠 Channel Created"
        embed.description = f"`{str(channel.category)}/`#{channel.name} ({channel.id}) [{channel.mention}]"
        author_embed(embed, channel.guild)

        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            channel.guild, get_config(channel.guild.id, "logging", "serverlog")
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.from_str("#FF00FF")
        embed.title = "🏚️ Channel Deleted"
        embed.description = f"`{str(channel.category)}/`#{channel.name} ({channel.id})"
        author_embed(embed, channel.guild)

        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_channel_update(self, channel_before, channel_after):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            channel_after.guild,
            get_config(channel_after.guild.id, "logging", "serverlog"),
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = discord.Color.from_str("#FFFF00")
        embed.title = "🏘️ Channel Update"
        embed.description = (
            f"{channel_after.name} ({channel_after.id}) [{channel_after.mention}]"
        )
        author_embed(embed, channel_after.guild)

        # Names
        if channel_before.name != channel_after.name:
            embed.add_field(
                name="📝 Name Change",
                value=f"❌ {channel_before.name}\n⬇️\n⭕ {channel_after.name}",
                inline=False,
            )

        # Topics
        try:
            if channel_before.topic != channel_after.topic:
                slice_embed(
                    embed, "❌ ```" + channel_before.topic + "```", "✍️ Topic Change"
                )
                slice_embed(embed, "⭕ ```" + channel_after.topic + "```", "⬇️")
        except:
            pass

        # NSFW
        if channel_before.nsfw != channel_after.nsfw:
            embed.add_field(
                name="🔞 NSFW Change",
                value=f"❌ {channel_before.nsfw}\n⬇️\n⭕ {channel_after.nsfw}",
                inline=False,
            )

        # News
        try:
            if channel_before.is_news() != channel_after.is_news():
                embed.add_field(
                    name="📣 News Change",
                    value=f"❌ {channel_before.is_news()}\n⬇️\n⭕ {channel_after.is_news()}",
                    inline=False,
                )
        except:
            pass

        # Bitrate
        try:
            if channel_before.bitrate != channel_after.bitrate:
                embed.add_field(
                    name="🔊 Bitrate Change",
                    value=f"❌ {channel_before.bitrate}\n⬇️\n⭕ {channel_after.bitrate}",
                    inline=False,
                )
        except:
            pass

        # User Limit
        try:
            if channel_before.user_limit != channel_after.user_limit:
                embed.add_field(
                    name="👥 User Limit Change",
                    value=f"❌ {channel_before.user_limit}\n⬇️\n⭕ {channel_after.user_limit}",
                    inline=False,
                )
        except:
            pass

        # Slowmode
        try:
            if channel_before.slowmode_delay != channel_after.slowmode_delay:
                embed.add_field(
                    name="⏱️ Slowmode Change",
                    value=f"❌ {channel_before.slowmode_delay}\n⬇️\n⭕ {channel_after.slowmode_delay}",
                    inline=False,
                )
        except:
            pass

        # Thread Default Archive
        try:
            if (
                channel_before.default_auto_archive_duration
                != channel_after.default_auto_archive_duration
            ):
                embed.add_field(
                    name="⏲️ Thread Default Archive Change",
                    value=f"❌ {channel_before.default_auto_archive_duration}\n⬇️\n⭕ {channel_after.default_auto_archive_duration}",
                    inline=False,
                )
        except:
            pass

        # Thread Default Slowmode
        try:
            if (
                channel_before.default_thread_slowmode_delay
                != channel_after.default_thread_slowmode_delay
            ):
                embed.add_field(
                    name="⏱️ Thread Default Slowmode Change",
                    value=f"❌ {channel_before.default_thread_slowmode_delay}\n⬇️\n⭕ {channel_after.default_thread_slowmode_delay}",
                    inline=False,
                )
        except:
            pass

        # Forum Default Reaction Emoji
        try:
            if (
                channel_before.default_reaction_emoji
                != channel_after.default_reaction_emoji
            ):
                embed.add_field(
                    name="👍 Forum Default Emoji Change",
                    value=f"❌ {channel_before.default_reaction_emoji}\n⬇️\n⭕ {channel_after.default_reaction_emoji}",
                    inline=False,
                )
        except:
            pass

        # Forum Default Sort Order
        try:
            if channel_before.default_sort_order != channel_after.default_sort_order:
                embed.add_field(
                    name="🗂️ Forum Default Sort Order Change",
                    value=f"❌ {channel_before.default_sort_order}\n⬇️\n⭕ {channel_after.default_sort_order}",
                    inline=False,
                )
        except:
            pass

        # Forum Default Layout
        try:
            if channel_before.default_layout != channel_after.default_layout:
                embed.add_field(
                    name="🗒️ Forum Default Layout Change",
                    value=f"❌ {channel_before.default_layout}\n⬇️\n⭕ {channel_after.default_layout}",
                    inline=False,
                )
        except:
            pass

        # Permissions
        if channel_before.overwrites != channel_after.overwrites:
            output = []
            for entry in list(channel_before.overwrites.items()):
                if entry[0] not in channel_after.overwrites:
                    output.append(f"- {entry[0]}")
                for perm, value in dict(entry[1]).items():
                    if value != dict(channel_after.overwrites_for(entry[0]))[perm]:
                        if entry[0] in channel_after.overwrites:
                            output.append(f"{entry[0]}")
                        output.append(
                            f"{perm}\n- {value}\n+ {dict(channel_after.overwrites_for(entry[0]))[perm]}"
                        )
            for entry in list(channel_after.overwrites.items()):
                if entry[0] in channel_before.overwrites:
                    continue
                output.append(f"+ {entry[0]}")
                for perm, value in dict(entry[1]).items():
                    if value != dict(channel_before.overwrites_for(entry[0]))[perm]:
                        output.append(
                            f"{perm}\n- {dict(channel_before.overwrites_for(entry[0]))[perm]}\n+ {value}"
                        )

            embed.add_field(
                name="🔒 Permission Change",
                value="```diff\n" + "\n".join(output) + "```",
                inline=False,
            )

        if embed.fields:
            await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_create(self, role):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            role.guild, get_config(role.guild.id, "logging", "serverlog")
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = role.color
        embed.title = "🏷️ Role Created"
        embed.description = f"{role.name} ({role.id}) [<@&{role.id}>]"
        embed.set_author(
            name=role.guild.name,
            icon_url=role.guild.icon.url,
        )
        author_embed(embed, role.guild)

        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_delete(self, role):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            role.guild, get_config(role.guild.id, "logging", "serverlog")
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = role.color
        embed.title = "🔥 Role Deleted"
        embed.description = f"{role} ({role.id}) [{role.mention}]"
        embed.set_author(
            name=role.guild.name,
            icon_url=role.guild.icon.url,
        )

        await slog.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_update(self, role_before, role_after):
        await self.bot.wait_until_ready()

        slog = self.bot.pull_channel(
            role_after.guild, get_config(role_after.guild.id, "logging", "serverlog")
        )
        if not slog:
            return

        embed = stock_embed(self.bot)
        embed.color = role_after.color
        embed.title = "🖋️ Role Update"
        embed.description = f"{role_after} ({role_after.id}) [{role_after.mention}]"
        embed.set_author(
            name=role_after.guild.name,
            icon_url=role_after.guild.icon.url,
        )

        # Names
        if role_before.name != role_after.name:
            embed.add_field(
                name="📝 Name Change",
                value=f"❌ {role_before}\n⬇️\n⭕ {role_after}",
                inline=False,
            )

        # Colors
        if role_before.color != role_after.color:
            embed.add_field(
                name="🌈 Color Change",
                value=f"❌ {str(role_before.color)}\n⬇️\n⭕ {str(role_after.color)}",
                inline=False,
            )

        # Icons
        try:
            if role_before.icon != role_after.icon:
                if role_after.icon:
                    text = "The new icon is to the side."
                    embed.set_thumbnail(url=role_after.icon.url)
                else:
                    text = "The icon was removed."
                embed.add_field(
                    name="ℹ️ Icon Change",
                    value=text,
                    inline=False,
                )
        except:
            pass

        # Hoists
        if role_before.hoist != role_after.hoist:
            embed.add_field(
                name="🆙 Hoist Change",
                value=f"❌ {str(role_before.hoist)}\n⬇️\n⭕ {str(role_after.hoist)}",
                inline=False,
            )

        # Mentions
        if role_before.mentionable != role_after.mentionable:
            embed.add_field(
                name="1️⃣ Mentionable Change",
                value=f"❌ {str(role_before.mentionable)}\n⬇️\n⭕ {str(role_after.mentionable)}",
                inline=False,
            )

        # Managed
        if role_before.managed != role_after.managed:
            embed.add_field(
                name="🔧 Management Change",
                value=f"❌ {str(role_before.managed)}\n⬇️\n⭕ {str(role_after.managed)}",
                inline=False,
            )

        # Tags
        try:
            if role_before.tags != role_after.tags:
                if role_before.tags.is_bot_managed != role_after.tags.is_bot_managed:
                    embed.add_field(
                        name="🤖 Bot Manager Change",
                        value=f"❌ {str(role_before.tags.bot_id)}\n⬇️\n⭕ {str(role_after.tags.bot_id)}",
                        inline=False,
                    )
                if (
                    role_before.tags.is_guild_connection
                    != role_after.tags.is_guild_connection
                ):
                    embed.add_field(
                        name="🔗 Linked Role Change",
                        value=f"❌ {role_before.tags.is_guild_connection()}\n⬇️\n⭕ {role_after.tags.is_guild_connection()}",
                        inline=False,
                    )
                if (
                    role_before.tags.is_available_for_purchase
                    != role_after.tags.is_available_for_purchase
                ):
                    embed.add_field(
                        name="💰 Pay For Role Change",
                        value=f"❌ {role_before.tags.subscription_listing_id}\n⬇️\n⭕ {role_after.tags.subscription_listing_id()}",
                        inline=False,
                    )
                if (
                    role_before.tags.is_integration()
                    != role_after.tags.is_integration()
                ):
                    embed.add_field(
                        name="🤝 Integration Change",
                        value=f"❌ {ole_before.tags.integration_id}\n⬇️\n⭕ {role_after.tags.integration_id}",
                        inline=False,
                    )
        except:
            pass

        # Permissions
        if role_before.permissions != role_after.permissions:
            output = []
            for perm, value in dict(discord.Permissions()).items():
                if (
                    dict(role_before.permissions)[perm]
                    != dict(role_after.permissions)[perm]
                ):
                    output.append(
                        f"{perm}\n- {dict(role_before.permissions)[perm]}\n+ {dict(role_after.permissions)[perm]}"
                    )

            embed.add_field(
                name="🔒 Permission Change",
                value="```diff\n" + "\n".join(output) + "```",
                inline=False,
            )

        if embed.fields:
            await slog.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logs2(bot))
