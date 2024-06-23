import re
import discord
import datetime
import asyncio
import deepl
import googletrans
from discord.ext.commands import Cog, Context, Bot
from discord.ext import commands
from helpers.checks import ismod
from helpers.sv_config import get_config


class Messagescan(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_re = re.compile(
            r"https://(?:canary\.|ptb\.)?discord\.com/channels/[0-9]+/[0-9]+/[0-9]+",
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
            "🇧🇬": {"name": "Bulgarian", "deeplcode": "BG", "gtcode": "bg"},
            "🇨🇿": {"name": "Czech", "deeplcode": "CS", "gtcode": "cs"},
            "🇩🇰": {"name": "Danish", "deeplcode": "DA", "gtcode": "da"},
            "🇩🇪": {"name": "German", "deeplcode": "DE", "gtcode": "de"},
            "🇬🇷": {"name": "Greek", "deeplcode": "EL", "gtcode": "el"},
            "🇬🇧": {"name": "British English", "deeplcode": "EN-GB", "gtcode": "en"},
            "🇺🇸": {"name": "American English", "deeplcode": "EN-US", "gtcode": "en"},
            "🇪🇸": {"name": "Spanish", "deeplcode": "ES", "gtcode": "es"},
            "🇪🇪": {"name": "Estonian", "deeplcode": "ET", "gtcode": "et"},
            "🇫🇮": {"name": "Finnish", "deeplcode": "FI", "gtcode": "fi"},
            "🇫🇷": {"name": "French", "deeplcode": "FR", "gtcode": "fr"},
            "🇭🇺": {"name": "Hungarian", "deeplcode": "HU", "gtcode": "hu"},
            "🇮🇩": {"name": "Indonesian", "deeplcode": "ID", "gtcode": "id"},
            "🇮🇹": {"name": "Italian", "deeplcode": "IT", "gtcode": "it"},
            "🇯🇵": {"name": "Japanese", "deeplcode": "JA", "gtcode": "ja"},
            "🇰🇷": {"name": "Korean", "deeplcode": "KO", "gtcode": "ko"},
            "🇱🇹": {"name": "Lithuanian", "deeplcode": "LT", "gtcode": "lt"},
            "🇱🇻": {"name": "Latvian", "deeplcode": "LV", "gtcode": "lv"},
            "🇳🇴": {"name": "Norwegian", "deeplcode": "NB", "gtcode": "no"},
            "🇳🇱": {"name": "Dutch", "deeplcode": "NL", "gtcode": "nl"},
            "🇵🇱": {"name": "Polish", "deeplcode": "PL", "gtcode": "pl"},
            "🇧🇷": {"name": "Brazilian Portugese", "deeplcode": "PT-BR", "gtcode": "pt"},
            "🇵🇹": {"name": "Portugese", "deeplcode": "PT-PT", "gtcode": "pt"},
            "🇷🇴": {"name": "Romanian", "deeplcode": "RO", "gtcode": "ro"},
            "🇷🇺": {"name": "Russian", "deeplcode": "RU", "gtcode": "ru"},
            "🇸🇰": {"name": "Slovak", "deeplcode": "SK", "gtcode": "sk"},
            "🇸🇮": {"name": "Slovenian", "deeplcode": "SL", "gtcode": "sl"},
            "🇸🇪": {"name": "Swedish", "deeplcode": "SV", "gtcode": "sv"},
            "🇹🇷": {"name": "Turkish", "deeplcode": "TR", "gtcode": "tr"},
            "🇺🇦": {"name": "Ukrainian", "deeplcode": "UK", "gtcode": "uk"},
            "🇨🇳": {"name": "Simplified Chinese", "deeplcode": "ZH", "gtcode": "zh-cn"},
        }

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def snipe(self, ctx):
        """This shows the last deleted message in a channel.

        It will *only* be the last deleted message.
        Hope you have logs if you wanted older!

        No arguments."""
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

    @commands.bot_has_permissions(embed_links=True)
    @commands.check(ismod)
    @commands.guild_only()
    @commands.command()
    async def snipf(self, ctx):
        """This shows the last edited message in a channel.

        It will *only* be the last edited message.
        Hope you have logs if you wanted older!

        No arguments."""
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
                split_before_msg = self.bot.slice_message(
                    lastbeforemsg.clean_content, size=1024, prefix=">>> "
                )
                embed.add_field(
                    name=f"❌ Before on <t:{int(lastbeforemsg.created_at.astimezone().timestamp())}:f>",
                    value=f"**Message was too long to post!** Split into fragments below.",
                    inline=False,
                )
                ctr = 1
                for p in split_before_msg:
                    embed.add_field(
                        name=f"🧩 Fragment {ctr}",
                        value=p,
                        inline=True,
                    )
                    ctr = ctr + 1
            else:
                embed.add_field(
                    name=f"❌ Before on <t:{int(lastbeforemsg.created_at.astimezone().timestamp())}:f>",
                    value=f">>> {lastbeforemsg.clean_content}",
                    inline=False,
                )
            if len(lastaftermsg.clean_content) > 1024:
                split_after_msg = self.bot.slice_message(
                    lastaftermsg.clean_content, size=1024, prefix=">>> "
                )
                embed.add_field(
                    name=f"⭕ After on <t:{int(lastaftermsg.edited_at.astimezone().timestamp())}:f>",
                    value=f"**Message was too long to post!** Split into fragments below.",
                    inline=False,
                )
                ctr = 1
                for p in split_after_msg:
                    embed.add_field(
                        name=f"🧩 Fragment {ctr}",
                        value=p,
                        inline=True,
                    )
                    ctr = ctr + 1
            else:
                embed.add_field(
                    name=f"⭕ After on <t:{int(lastaftermsg.edited_at.astimezone().timestamp())}:f>",
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
        """This shows the DeepL free tier usage pool.

        There's not much more to this.

        No arguments."""
        translation = deepl.Translator(
            self.bot.config.deepl_key, send_platform_info=False
        )
        usage = translation.get_usage()

        await ctx.send(
            content=f"**DeepL limit counter:**\n**Characters:** `{usage.character.count}/{usage.character.limit}`\n**Documents:** `{usage.document.count}/{usage.document.limit}`"
        )

    @commands.bot_has_guild_permissions(add_reactions=True, manage_messages=True)
    @commands.command()
    async def timebomb(self, ctx, minutes: float = 5, message: discord.Message = None):
        """This sets a timebomb for a message.

        You can also react with a bomb emoji.
        Doing so will set a five minute itmer.
        Put a message link to do this to a specific message,
        or don't and it will use your last message.

        - `minutes`
        The amount of minutes to wait. Optional.
        - `message`
        The message to timebomb. Optional."""
        if not message:
            skiponce = True
            async for message in ctx.channel.history(limit=200):
                if message.author.id != ctx.author.id:
                    continue
                if not skiponce:
                    break
                skiponce = False
        await message.add_reaction("💣")
        await message.add_reaction("⏲️")
        await asyncio.sleep(minutes * 60)
        await message.add_reaction("💥")
        await asyncio.sleep(1)
        await message.delete()

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        ctx = await self.bot.get_context(message)
        if (
            not message.content
            or ctx.valid
            or message.author.bot
            or not message.guild
            or not message.channel.permissions_for(message.author).embed_links
            or not get_config(message.guild.id, "reaction", "embedenable")
        ):
            return

        msglinks = self.link_re.findall(message.content)
        tiktoklinks = self.tiktoklink_re.findall(message.content)
        if not any((msglinks, tiktoklinks)):
            return

        for link in msglinks + tiktoklinks:
            parts = message.content.split(link)
            if parts[0].count("||") % 2 and parts[1].count("||") % 2:
                try:
                    msglinks.remove(link)
                except:
                    tiktoklinks.remove(link)
            elif parts[0].count("<") % 2 and parts[1].count(">") % 2:
                try:
                    msglinks.remove(link)
                except:
                    tiktoklinks.remove(link)

        ttlinks = ""
        embeds = None

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

                if rcvchannel.is_nsfw() and not message.channel.is_nsfw():
                    continue

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
                        embed.description = "> " + "\n> ".join(
                            rcvmessage.clean_content.split("\n")
                        )
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
                if (
                    rcvmessage.attachments
                    and rcvmessage.attachments[0].content_type[:6] == "image/"
                ):
                    if rcvmessage.attachments[0].is_spoiler():
                        embed.set_image(url="https://files.catbox.moe/ja0foc.png")
                    else:
                        embed.set_image(url=rcvmessage.attachments[0].url)
                    if len(rcvmessage.attachments) > 1:
                        if not embed.description:
                            embed.description = ""
                        embed.description += f"\n\n🖼️ __Original post has `{len(rcvmessage.attachments)}` images.__"
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
            if tiktoklinks:
                ctr = 0
                while not message.embeds:
                    if ctr == 50:
                        break
                    await asyncio.sleep(0.1)
                    ctr += 1
            await message.edit(suppress=True)

        def deletecheck(m):
            return m.id == message.id

        if any((ttlinks, embeds)):
            reply = await message.reply(
                content=ttlinks, embeds=embeds, mention_author=False
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
        if all((user.bot, user.id != self.bot.user.id)) or reaction.count != 1:
            return

        # Translation
        if (
            str(reaction) in self.langs
            and reaction.message.content
            and reaction.message.channel.permissions_for(user).send_messages
            and get_config(reaction.message.guild.id, "reaction", "translateenable")
        ):
            # DeepL
            dloutput = None
            if self.bot.config.deepl_key:
                deepltranslation = deepl.Translator(
                    self.bot.config.deepl_key, send_platform_info=False
                )
                usage = deepltranslation.get_usage()
                if usage.character.valid:
                    dloutput = deepltranslation.translate_text(
                        reaction.message.clean_content,
                        target_lang=self.langs[str(reaction)]["deeplcode"],
                    )

                    if dloutput.detected_source_lang == "EN":
                        dloutflag = "🇺🇸"
                        dloutname = "English"
                    elif dloutput.detected_source_lang == "PT":
                        dloutflag = "🇵🇹"
                        dloutname = "Portuguese"
                    else:
                        for v in self.langs:
                            if (
                                self.langs[v]["deeplcode"]
                                == dloutput.detected_source_lang
                            ):
                                dloutflag = v
                                dloutname = self.langs[v]["name"]

            # Google Translate
            try:
                googletranslation = googletrans.Translator()
                gtoutput = googletranslation.translate(
                    reaction.message.clean_content,
                    dest=self.langs[str(reaction)]["gtcode"],
                )

                if gtoutput.src == "en":
                    gtoutflag = "🇺🇸"
                    gtoutname = "English"
                elif gtoutput.src == "pt":
                    gtoutflag = "🇵🇹"
                    gtoutname = "Portuguese"
                else:
                    for v in self.langs:
                        if self.langs[v]["gtcode"] == gtoutput.src:
                            gtoutflag = v
                            gtoutname = self.langs[v]["name"]
            except:
                gtoutput = None

            if not dloutput and not gtoutput:
                return await reaction.message.reply(
                    content="Unable to translate message: neither DeepL or Google Translate responded.",
                    mention_author=False,
                )

            reacts = ["🚫" if not dloutput else "<:deepl:1177134874021347378>"] + [
                "🚫" if not gtoutput else "<:googletrans:1177134340778500146>"
            ]
            state = 0 if dloutput else 1

            def content():
                outflag = dloutflag if not state else gtoutflag
                outname = dloutname if not state else gtoutname
                method = "DeepL" if not state else "Google"
                embed.description = dloutput.text if not state else gtoutput.text
                embed.set_footer(
                    text=f"{method} Translated from {outflag} {outname} by {user}",
                    icon_url=user.display_avatar.url,
                )

            embed = discord.Embed(
                color=reaction.message.author.color,
                timestamp=reaction.message.created_at,
            )
            content()
            embed.set_author(
                name=f"💬 {reaction.message.author} said in #{reaction.message.channel.name}...",
                icon_url=reaction.message.author.display_avatar.url,
                url=reaction.message.jump_url,
            )
            allowed_mentions = discord.AllowedMentions(replied_user=False)
            # Use a single image from post for now.
            if (
                reaction.message.attachments
                and reaction.message.attachments[0].content_type[:6] == "image/"
            ):
                embed.set_image(url=reaction.message.attachments[0].url)
            elif reaction.message.embeds and reaction.message.embeds[0].image:
                embed.set_image(url=reaction.message.embeds[0].image.url)
            holder = await reaction.message.reply(embed=embed, mention_author=False)
            for e in reacts:
                await holder.add_reaction(e)

            def reactioncheck(r, u):
                return u.id == user.id and str(r.emoji) in reacts

            while True:
                try:
                    reaction, user = await self.bot.wait_for(
                        "reaction_add", timeout=30.0, check=reactioncheck
                    )
                except asyncio.TimeoutError:
                    for react in reacts:
                        await holder.remove_reaction(react, self.bot.user)
                    return
                if str(reaction) == "<:deepl:1177134874021347378>":
                    if state != 0:
                        state = 0
                    try:
                        await holder.remove_reaction(
                            "<:deepl:1177134874021347378>", user
                        )
                    except:
                        pass
                elif str(reaction) == "<:googletrans:1177134340778500146>":
                    if state != 1:
                        state = 1
                    try:
                        await holder.remove_reaction(
                            "<:googletrans:1177134340778500146>", user
                        )
                    except:
                        pass
                content()
                await holder.edit(embed=embed, allowed_mentions=allowed_mentions)

        # Timebomb
        if (
            str(reaction) == "💣"
            and reaction.message.author.id == user.id
            and reaction.message.guild
            and reaction.message.channel.permissions_for(
                reaction.message.guild.me
            ).manage_messages
        ):
            await reaction.message.add_reaction("⏲️")
            await asyncio.sleep(300)
            await reaction.message.add_reaction("💥")
            await asyncio.sleep(1)
            await reaction.message.delete()


async def setup(bot: Bot):
    await bot.add_cog(Messagescan(bot))
