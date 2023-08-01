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


class Messagescan(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_re = re.compile(
            r"https://(?:canary\.|ptb\.)?discord\.com/channels/[0-9]+/[0-9]+/[0-9]+",
            re.IGNORECASE,
        )
        self.twitterlink_re = re.compile(
            r"https://twitter\.com/[A-z0-9]+/status/[0-9]+",
            re.IGNORECASE,
        )
        self.tiktoklink_re = re.compile(
            r"https://(?:www\.)?tiktok\.com/@[A-z0-9]+/video/[0-9]+",
            re.IGNORECASE,
        )
        self.prevmessages = {}
        self.prevedit_before = {}
        self.prevedit_after = {}
        self.langs = {
            "🇧🇬": {"name": "Bulgarian", "code": "BG"},
            "🇨🇿": {"name": "Czech", "code": "CS"},
            "🇩🇰": {"name": "Danish", "code": "DA"},
            "🇩🇪": {"name": "German", "code": "DE"},
            "🇬🇷": {"name": "Greek", "code": "EL"},
            "🇬🇧": {"name": "British English", "code": "EN-GB"},
            "🇺🇸": {"name": "American English", "code": "EN-US"},
            "🇪🇸": {"name": "Spanish", "code": "ES"},
            "🇪🇪": {"name": "Estonian", "code": "ET"},
            "🇫🇮": {"name": "Finnish", "code": "FI"},
            "🇫🇷": {"name": "French", "code": "FR"},
            "🇭🇺": {"name": "Hungarian", "code": "HU"},
            "🇮🇩": {"name": "Indonesian", "code": "ID"},
            "🇮🇹": {"name": "Italian", "code": "IT"},
            "🇯🇵": {"name": "Japanese", "code": "JA"},
            "🇰🇷": {"name": "Korean", "code": "KO"},
            "🇱🇹": {"name": "Lithuanian", "code": "LT"},
            "🇱🇻": {"name": "Latvian", "code": "LV"},
            "🇳🇴": {"name": "Norwegian", "code": "NB"},
            "🇳🇱": {"name": "Dutch", "code": "NL"},
            "🇵🇱": {"name": "Polish", "code": "PL"},
            "🇧🇷": {"name": "Brazilian Portugese", "code": "PT-BR"},
            "🇵🇹": {"name": "Portugese", "code": "PT-PT"},
            "🇷🇴": {"name": "Romanian", "code": "RO"},
            "🇷🇺": {"name": "Russian", "code": "RU"},
            "🇸🇰": {"name": "Slovak", "code": "SK"},
            "🇸🇮": {"name": "Slovenian", "code": "SL"},
            "🇸🇪": {"name": "Swedish", "code": "SV"},
            "🇹🇷": {"name": "Turkish", "code": "TR"},
            "🇺🇦": {"name": "Ukrainian", "code": "UK"},
            "🇨🇳": {"name": "Simplified Chinese", "code": "ZH"},
        }

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def snipe(self, ctx):
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

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def snip(self, ctx):
        if ctx.channel.id in self.prevedit_before:
            lastbeforemsg = self.prevedit_before[ctx.channel.id]
            lastaftermsg = self.prevedit_after[ctx.channel.id]
            # Prepare embed msg
            embed = discord.Embed(
                color=ctx.author.color,
                timestamp=lastaftermsg.created_at,
            )
            embed.set_footer(
                text=f"Snipped by {ctx.author}",
                icon_url=ctx.author.display_avatar.url,
            )
            embed.set_author(
                name=f"💬 {lastaftermsg.author} said in #{lastaftermsg.channel.name}...",
                icon_url=lastaftermsg.author.display_avatar.url,
                url=lastaftermsg.jump_url,
            )
            # Split if too long.
            if len(lastbeforemsg.clean_content) > 1024:
                split_before_msg = list(
                    [
                        lastbeforemsg.clean_content[i : i + 1020]
                        for i in range(0, len(lastbeforemsg.clean_content), 1020)
                    ]
                )
                embed.add_field(
                    name=f"❌ Before on <t:{lastbeforemsg.created_at.astimezone().strftime('%s')}:f>",
                    value=f"**Message was too long to post!** Split into fragments below.",
                    inline=False,
                )
                ctr = 1
                for p in split_before_msg:
                    embed.add_field(
                        name=f"🧩 Fragment {ctr}",
                        value=f">>> {p}",
                        inline=True,
                    )
                    ctr = ctr + 1
            else:
                embed.add_field(
                    name=f"❌ Before on <t:{lastbeforemsg.created_at.astimezone().strftime('%s')}:f>",
                    value=f">>> {lastbeforemsg.clean_content}",
                    inline=False,
                )
            if len(lastaftermsg.clean_content) > 1024:
                split_after_msg = list(
                    [
                        lastaftermsg.clean_content[i : i + 1020]
                        for i in range(0, len(lastaftermsg.clean_content), 1020)
                    ]
                )
                embed.add_field(
                    name=f"⭕ After on <t:{lastaftermsg.edited_at.astimezone().strftime('%s')}:f>",
                    value=f"**Message was too long to post!** Split into fragments below.",
                    inline=False,
                )
                ctr = 1
                for p in split_after_msg:
                    embed.add_field(
                        name=f"🧩 Fragment {ctr}",
                        value=f">>> {p}",
                        inline=True,
                    )
                    ctr = ctr + 1
            else:
                embed.add_field(
                    name=f"⭕ After on <t:{lastaftermsg.edited_at.astimezone().strftime('%s')}:f>",
                    value=f">>> {lastaftermsg.clean_content}",
                    inline=False,
                )
            await ctx.reply(embed=embed, mention_author=False)
        else:
            await ctx.reply(
                content="There is no message edit in the snip cache for this channel.",
                mention_author=False,
            )

    @commands.command()
    async def usage(self, ctx):
        translation = deepl.Translator(config.deepl_key, send_platform_info=False)
        usage = translation.get_usage()

        await ctx.send(
            content=f"**DeepL limit counter:**\n**Characters:** `{usage.character.count}/{usage.character.limit}`\n**Documents:** `{usage.document.count}/{usage.document.limit}`"
        )

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if (
            not message.content
            or message.author.bot
            or not message.guild
            or not message.channel.permissions_for(message.author).embed_links
            or not get_config(message.guild.id, "misc", "embed_enable")
        ):
            return

        msglinks = self.link_re.findall(message.content)
        twitterlinks = self.twitterlink_re.findall(message.content)
        tiktoklinks = self.tiktoklink_re.findall(message.content)
        if not any((msglinks, twitterlinks, tiktoklinks)):
            return

        for link in msglinks + twitterlinks + tiktoklinks:
            parts = message.content.split(link)
            if parts[0].count("||") % 2 and parts[1].count("||") % 2:
                try:
                    msglinks.remove(link)
                except:
                    try:
                        twitterlinks.remove(link)
                    except:
                        tiktoklinks.remove(link)
            elif parts[0].count("<") % 2 and parts[1].count(">") % 2:
                try:
                    msglinks.remove(link)
                except:
                    try:
                        twitterlinks.remove(link)
                    except:
                        tiktoklinks.remove(link)

        twlinks = ""
        ttlinks = ""
        embeds = None

        if twitterlinks:
            twlinks = "\n".join(
                [t.replace("twitter", "vxtwitter") for t in twitterlinks]
            )

        if tiktoklinks:
            ttlinks = "\n".join([t.replace("tiktok", "vxtiktok") for t in tiktoklinks])

        if msglinks:
            embeds = []
            for m in msglinks:
                components = m.split("/")
                guildid = int(components[4])
                channelid = int(components[5])
                msgid = int(components[6])

                try:
                    rcvguild = self.bot.get_guild(guildid)
                    rcvchannel = rcvguild.get_channel_or_thread(channelid)
                    rcvmessage = await rcvchannel.fetch_message(msgid)
                except:
                    break

                # Prepare embed msg
                embed = discord.Embed(
                    color=rcvmessage.author.color,
                    timestamp=rcvmessage.created_at,
                )
                if rcvmessage.clean_content:
                    limit = 500
                    if (
                        len(rcvmessage.clean_content) <= limit
                        or message.content.split(m)[0][-1:] == '"'
                        and message.content.split(m)[1][:1] == '"'
                    ):
                        embed.description = f">>> {rcvmessage.clean_content}"
                    else:
                        embed.description = (
                            "> "
                            + "\n> ".join(rcvmessage.clean_content[:limit].split("\n"))
                            + "...\n\n"
                            + f'**Message is over {limit} long.**\nUse `"LINK"` to show full message.'
                        )
                embed.set_footer(
                    text=f"Quoted by {message.author}",
                    icon_url=message.author.display_avatar.url,
                )
                embed.set_author(
                    name=f"💬 {rcvmessage.author} said in #{rcvmessage.channel.name}...",
                    icon_url=rcvmessage.author.display_avatar.url,
                    url=rcvmessage.jump_url,
                )
                # Use a single image from post for now.
                if (
                    rcvmessage.attachments
                    and rcvmessage.attachments[0].content_type[:6] == "image/"
                ):
                    embed.set_image(url=rcvmessage.attachments[0].url)
                elif rcvmessage.embeds and rcvmessage.embeds[0].image:
                    embed.set_image(url=rcvmessage.embeds[0].image.url)
                elif rcvmessage.stickers:
                    embed.set_image(url=rcvmessage.stickers[0].url)
                embeds.append(embed)

        if (
            message.guild
            and message.channel.permissions_for(message.guild.me).manage_messages
        ):
            # Discord SUCKS!!
            if twitterlinks or tiktoklinks:
                ctr = 0
                while not message.embeds:
                    if ctr == 50:
                        break
                    await asyncio.sleep(0.1)
                    ctr += 1
            await message.edit(suppress=True)

        def deletecheck(m):
            return m.id == message.id

        if any((ttlinks, twlinks, embeds)):
            reply = await message.reply(
                content=twlinks + ttlinks, embeds=embeds, mention_author=False
            )
            try:
                await message.channel.fetch_message(message.id)
            except discord.NotFound:
                await reply.delete()
            try:
                await self.bot.wait_for(
                    "message_delete", timeout=600, check=deletecheck
                )
                await reply.delete()
            except:
                pass

    @Cog.listener()
    async def on_message_delete(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot or not message.guild:
            return

        self.prevmessages[message.channel.id] = message

    @Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        await self.bot.wait_until_ready()
        if message_after.author.bot or not message_after.guild:
            return

        self.prevedit_before[message_after.channel.id] = message_before
        self.prevedit_after[message_after.channel.id] = message_after

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        await self.bot.wait_until_ready()
        if (
            all((user.bot, user.id != self.bot.user.id))
            or str(reaction) not in self.langs
            or reaction.count != 1
            or not get_config(reaction.message.guild.id, "misc", "translate_enable")
        ):
            return

        translation = deepl.Translator(config.deepl_key, send_platform_info=False)
        usage = translation.get_usage()

        if usage.any_limit_reached:
            await reaction.message.reply(
                content="Unable to translate message: monthly limit reached.",
                mention_author=False,
            )
            return
        output = translation.translate_text(
            reaction.message.clean_content,
            target_lang=self.langs[str(reaction)]["code"],
        )
        if output.detected_source_lang == "EN":
            out_flag = "🇺🇸"
            out_name = "English"
        elif output.detected_source_lang == "PT":
            out_flag = "🇵🇹"
            out_name = "Portuguese"
        else:
            for v in self.langs:
                if self.langs[v]["code"] == output.detected_source_lang:
                    out_flag = v
                    out_name = self.langs[v]["name"]

        embed = discord.Embed(
            color=reaction.message.author.color,
            description=output.text,
            timestamp=reaction.message.created_at,
        )
        embed.set_footer(
            text=f"Translated from {out_flag} {out_name} by {user}",
            icon_url=user.display_avatar.url,
        )
        embed.set_author(
            name=f"💬 {reaction.message.author} said in #{reaction.message.channel.name}...",
            icon_url=reaction.message.author.display_avatar.url,
            url=reaction.message.jump_url,
        )
        # Use a single image from post for now.
        if (
            reaction.message.attachments
            and reaction.message.attachments[0].content_type[:6] == "image/"
        ):
            embed.set_image(url=reaction.message.attachments[0].url)
        elif reaction.message.embeds and reaction.message.embeds[0].image:
            embed.set_image(url=reaction.message.embeds[0].image.url)
        await reaction.message.reply(embed=embed, mention_author=False)


async def setup(bot: Bot):
    await bot.add_cog(Messagescan(bot))
