import discord
import json
import os
import httplib2
import re
import datetime
import config
import asyncio
import textwrap
import zipfile
from io import BytesIO


async def log_whole_channel(bot, channel, zip_files=False):
    st = ""

    if zip_files:
        b = BytesIO()
        z = zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED)
        zipped_count = 0

    async for m in channel.history(limit=None):
        blank_content = True
        ts = "{:%Y-%m-%d %H:%M} ".format(m.created_at)
        padding = len(ts) + len(m.author.name) + 2
        add = ts
        if m.type == discord.MessageType.default:
            add += "{0.author.name}: {0.clean_content}".format(m)
            if m.clean_content:
                blank_content = False
        else:
            add += m.system_content

        for a in m.attachments:
            if not blank_content:
                add += "\n"
            add += " " * (padding * (not blank_content)) + "Attachment: " + a.filename
            if zip_files:
                fn = "{}-{}-{}".format(m.id, a.id, a.filename)
                async with bot.session.get(a.url) as r:
                    f = await r.read()

                z.writestr(fn, f)
                add += " (Saved as {})".format(fn)
                zipped_count += 1

            blank_content = False

        for e in m.embeds:
            if e.type == "rich":
                if not blank_content:
                    add += "\n"
                add += textify_embed(
                    e, limit=40, padding=padding, pad_first_line=not blank_content
                )
                blank_content = False

        if m.reactions:
            if not blank_content:
                add += "\n"
            add += " " * (padding * (not blank_content))
            add += " ".join(
                ["[{} {}]".format(str(r.emoji), r.count) for r in m.reactions]
            )
            blank_content = False

        add += "\n"
        st = add + st

    ret = st
    if zip_files:
        if zipped_count:
            z.writestr("log.txt", st)
            b.seek(0)
            ret = (ret, b)
        else:
            ret = (ret, None)

    return ret


def textify_embed(embed, limit=40, padding=0, pad_first_line=True):
    text_proc = []
    title = ""
    if embed.title:
        title += embed.title
        if embed.url:
            title += " - "
    if embed.url:
        title += embed.url
    if not title and embed.author:
        title = embed.author.name
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
        text_proc += [embed.footer.text, ""]

    text_proc = [textwrap.wrap(t, width=limit) for t in text_proc]

    texts = []

    for tt in text_proc:
        if not tt:
            tt = [""]
        for t in tt:
            texts += [t + " " * (limit - len(t))]

    ret = " " * (padding * pad_first_line) + "╓─" + "─" * limit + "─╮"

    for t in texts[:-1]:
        ret += "\n" + " " * padding + "║ " + t + " │"

    ret += "\n" + " " * padding + "╙─" + "─" * limit + "─╯"

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
