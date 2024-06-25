# This Helper contains code from Archiver, which was made by Roadcrosser.
# 🖤 If by any chance you're reading, we all miss you.
# https://github.com/Roadcrosser/archiver
import discord
import json
import os
import httplib2
import re
import datetime
import asyncio
import textwrap
import zipfile
from io import BytesIO


async def log_channel(bot, channel, zip_files=False, start_ts=None, end_ts=None):
    st = ""

    if zip_files:
        b = BytesIO()
        z = zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED)
        zipped_count = 0

    async for m in channel.history(
        limit=None, before=end_ts, after=start_ts, oldest_first=True
    ):
        blank_content = True

        header = (
            m.author.name
            + (" [BOT] " if m.author.bot else " ")
            + m.created_at.astimezone().strftime("%Y/%m/%d %H:%M")
            + (
                " (edited " + m.edited_at.astimezone().strftime("%Y/%m/%d %H:%M") + ")"
                if m.edited_at
                else ""
            )
            + "\n"
        )
        if m.type == discord.MessageType.reply:
            rep = m.reference.resolved
            if isinstance(rep, discord.DeletedReferencedMessage):
                preheader = "Original message was deleted"
            elif not rep:
                preheader = "Message could not be loaded"
            else:
                preheader = (
                    "↗️ "
                    + ("[BOT] " if rep.author.bot else "")
                    + ("@" if rep.author in m.mentions else "")
                    + rep.author.name
                    + " "
                    + rep.clean_content[:50]
                    + ("..." if len(rep.clean_content) > 50 else "")
                    + "\n"
                )
        else:
            preheader = ""
        add = preheader + header
        if m.is_system():
            add += m.system_content
            if m.system_content:
                blank_content = False
        else:
            add += m.clean_content
            if m.clean_content:
                blank_content = False

        for a in m.attachments:
            if not blank_content:
                add += "\n"
            if zip_files:
                fn = f"{a.id}-{a.filename}"
                f = await a.read()
                z.writestr(fn, f)
                zipped_count += 1
                add += textify_attach((a.filename, fn))
            else:
                add += textify_attach((a.filename, None))
            blank_content = False

        for e in m.embeds:
            if e.type == "rich":
                if not blank_content:
                    add += "\n"
                add += textify_embed(e)
                blank_content = False

        if m.reactions:
            if not blank_content:
                add += "\n"
            add += " ".join(
                [f"[ {str(rea.emoji)} {rea.count} ]" for rea in m.reactions]
            )
            blank_content = False

        add += "\n\n"
        st = st + add

    if zip_files:
        if zipped_count:
            z.close()
            b.seek(0)
            return (st, b)
        else:
            return (st, None)


def textify_attach(files, limit=40):
    text_proc = ["📄 " + files[0]]
    if files[1]:
        text_proc += ["🗜️ " + files[1]]
    text_proc = [textwrap.wrap(t, width=limit) for t in text_proc]

    texts = []

    for tt in text_proc:
        if not tt:
            tt = [""]
        for t in tt:
            texts += [t + " " * (limit - len(t))]

    ret = "┌─" + "─" * limit + "─╮"

    for t in texts:
        ret += "\n" + "│ " + t + " │"

    ret += "\n" + "└─" + "─" * limit + "─╯"

    return ret


def textify_embed(embed, limit=40):
    text_proc = []
    author = ""
    if embed.author:
        author += embed.author.name
        if embed.author.url:
            author += " - " + embed.author.url
    if author:
        text_proc += [author, ""]
    title = ""
    if embed.title:
        title += embed.title
        if embed.url:
            title += " - "
    if embed.url:
        title += embed.url
    if title:
        text_proc += [title, ""]
    if embed.description:
        text_proc += [embed.description, ""]
    if embed.thumbnail:
        text_proc += ["Thumbnail: " + embed.thumbnail.url, ""]
    for f in embed.fields:
        text_proc += [
            f.name
            + (
                ":"
                if not f.name.endswith(("!", ")", "}", "-", ":", ".", "?", "%", "$"))
                else ""
            ),
            *f.value.split("\n"),
            "",
        ]
    if embed.image:
        text_proc += ["Image: " + embed.image.url, ""]
    if embed.footer:
        if embed.timestamp:
            inp = (
                embed.footer.text
                + " | "
                + "{:%m/%d/%Y %H:%M}".format(embed.timestamp.astimezone())
            )
            text_proc += [inp, ""]
        else:
            text_proc += [embed.footer.text, ""]

    text_proc = [textwrap.wrap(t, width=limit) for t in text_proc]

    texts = []

    for tt in text_proc:
        if not tt:
            tt = [""]
        for t in tt:
            texts += [t + " " * (limit - len(t))]

    ret = "╓─" + "─" * limit + "─╮"

    for t in texts[:-1]:
        ret += "\n" + "║ " + t + " │"

    ret += "\n" + "╙─" + "─" * limit + "─╯"

    return ret


async def get_members(bot, message, args):
    user = []
    if args:
        user = message.guild.get_member_named(args)
        if not user:
            user = []
            arg_split = args.split()
            for a in arg_split:
                try:
                    a = int(a.strip("<@!#>"))
                except:
                    continue
                u = message.guild.get_member(a)
                if not u:
                    try:
                        u = await bot.fetch_user(a)
                    except:
                        pass
                if u:
                    user += [u]
        else:
            user = [user]

    return (user, None)
