# This Cog contains code from Arbitlog, which was made by Roadcrosser.
# https://github.com/Roadcrosser/archiver
import discord
import json
import os
import httplib2
import re
import datetime
import asyncio
import zipfile
import textwrap

from io import BytesIO

from discord.ext import commands
from discord.ext.commands import Cog
from helpers.checks import check_if_staff


class Arbitlog(Cog):
    def __init__(self, bot):
        self.bot = bot

    def textify_embed(self, embed, limit=40, padding=0, pad_first_line=True):
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
                    if not f.name.endswith(
                        ("!", ")", "}", "-", ":", ".", "?", "%", "$")
                    )
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

    async def log_whole_channel(self, channel, zip_files=False):
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
                add += (
                    " " * (padding * (not blank_content)) + "Attachment: " + a.filename
                )
                if zip_files:
                    fn = "{}-{}-{}".format(m.id, a.id, a.filename)
                    async with self.bot.session.get(a.url) as r:
                        f = await r.read()

                    z.writestr(fn, f)
                    add += " (Saved as {})".format(fn)
                    zipped_count += 1

                blank_content = False

            for e in m.embeds:
                if e.type == "rich":
                    if not blank_content:
                        add += "\n"
                    add += self.textify_embed(
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

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def arbitlog(self, ctx, *, args=""):
        channels = args.split()
        to_log = []
        for ch in channels:
            ch = ctx.guild.get_channel_or_thread(int(ch.strip("<#>")))
            if ch:
                if type(ch) == discord.CategoryChannel:
                    to_log += ch.channels
                else:
                    to_log += [ch]
        channels = to_log
        await ctx.channel.send(f"Logging: {' '.join([c.mention for c in channels])}")
        async with ctx.channel.typing():
            for ch in channels:
                out = await self.log_whole_channel(ch, zip_files=True)
                zipped_files = out[1]
                out = out[0]

                f = BytesIO()
                f.write(out.encode("utf-8"))
                f.seek(0)

                fn = "#{}-{}-{}".format(
                    ch.name, ch.id, int(ctx.message.created_at.timestamp())
                )

                reply = "Saved to disk as `{}.txt`.\n".format(fn)

                if zipped_files:
                    if not os.path.isdir("arbitlogs"):
                        os.mkdir("arbitlogs")

                    with open("arbitlogs/" + fn + ".zip", "wb+") as o:
                        o.write(zipped_files.getvalue())
                    reply += (
                        "Also saved files to disk as `{}.zip` ({:,.2f} MB).".format(
                            fn, int(len(zipped_files.getvalue()) / (1024 * 1024))
                        )
                    )

                with open("arbitlogs/" + fn + ".txt", "wb+") as o:
                    o.write(f.read())

                await ctx.channel.send(reply)

            return True


async def setup(bot):
    await bot.add_cog(Arbitlog(bot))
