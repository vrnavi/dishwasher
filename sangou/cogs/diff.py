import io
import discord
import requests
from diff_match_patch import diff_match_patch
from discord.ext import commands
from discord.ext.commands import Cog


class Diff(Cog):

    @commands.cooldown(1, 5, type=commands.BucketType.default)
    @commands.command()
    async def diff(self, ctx: commands.Context, old: str = None, new: str = None):
        is_file = False
        # Checks if the user has uploaded 2 files - does something else in this case!
        if len(ctx.message.attachments) >= 2 and (old is None and new is None):
            if (
                ctx.message.attachments[0].size > 5000000
                or ctx.message.attachments[0].size > 5000000
            ):
                return await ctx.reply(
                    content="Maximum filesize is `5 MB`.", mention_author=False
                )
            is_file = (
                True  # This will make it return a file at the end, instead of text.
            )

            # Let's get an attachment
            old_attachment = requests.get(ctx.message.attachments[0].url)
            new_attachment = requests.get(ctx.message.attachments[1].url)
            try:
                old = old_attachment.content.decode("UTF-8")
                new = new_attachment.content.decode("UTF-8")
            except UnicodeDecodeError:
                await ctx.send(
                    "I was unable to read these files! Please make sure you upload valid files encoded with UTF-8!"
                )
                return
        # Compares the first string against the second string. This requires users to surround the strings with "" "" / etc

        init_text = "```diff\n"
        text = ""
        dmp = diff_match_patch()
        line_diff = dmp.diff_main(old, new)
        prev_value = 0
        differences = 0
        removals = 0
        additions = 0

        dmp.diff_cleanupSemantic(line_diff)

        for line in line_diff:
            if line[0] == 0:
                value = line[1]
                if prev_value != 0:
                    text += "\n"
                text += f"{value}"
            elif line[0] == 1:
                value = line[1]
                value = value.strip().replace("\n", "\n+ ")
                text += f"\n+ {value.strip()}"
                differences += 1
                additions += 1
            elif line[0] == -1:
                value = line[1]
                value = value.strip().replace("\n", "\n- ")
                text += f"\n- {value.strip()}"
                differences += 1
                removals += 1
            prev_value = line[0]
        end_text = "```"
        info_text = f"Found {differences} Differences. ({additions} Additions, {removals} Removals)\n"

        total_length = len(text) + len(info_text) + len(init_text) + len(end_text)

        if total_length > 2000 or is_file:
            bb = io.BytesIO(f"{info_text}{text}".encode("utf-8"))
            file = discord.File(bb)
            file.filename = "differences.txt"
            if not is_file:
                message = "The differences were too long to display over Discord! Please see attached text file."
            else:
                message = "File changes have been dumped into the attached file."
            await ctx.send(message, file=file)
        else:
            await ctx.send(f"{info_text}{init_text}{text}{end_text}")


async def setup(bot):
    await bot.add_cog(Diff(bot))
