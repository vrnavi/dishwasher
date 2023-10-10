import config
import time
import discord
import traceback
import random
import shutil
import os
from datetime import datetime, timezone
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.datafiles import get_botfile, delete_job
from helpers.checks import check_if_staff


class Dishtimer(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.minutely.start()
        self.hourly.start()
        self.daily.start()

    def cog_unload(self):
        self.minutely.cancel()
        self.hourly.cancel()
        self.daily.cancel()

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def listjobs(self, ctx):
        """[S] Lists timed Dishtimer jobs."""
        ctab = get_botfile("dishtimers")
        embed = discord.Embed(title=f"Active Dishtimer jobs")
        for jobtype in ctab:
            for jobtimestamp in ctab[jobtype]:
                for job_name in ctab[jobtype][jobtimestamp]:
                    job_details = repr(ctab[jobtype][jobtimestamp][job_name])
                    embed.add_field(
                        name=f"{jobtype} for {job_name}",
                        value=f"Executes on <t:{jobtimestamp}:F>.\nJSON data: {job_details}",
                        inline=False,
                    )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["removejob"])
    async def deletejob(self, ctx, timestamp: str, job_type: str, job_name: str):
        """[S] Removes a timed Dishtimer job.

        You'll need to supply:
        - timestamp (like 1545981602)
        - job type (like "unban")
        - job name (userid, like 420332322307571713)

        You can get all 3 from listjobs command."""
        delete_job(timestamp, job_type, job_name)
        await ctx.send(f"{ctx.author.mention}: Deleted!")

    async def do_jobs(self, ctab, jobtype, timestamp):
        log_channel = self.bot.get_channel(config.bot_logchannel)
        for job_name in ctab[jobtype][timestamp]:
            try:
                job_details = ctab[jobtype][timestamp][job_name]
                if jobtype == "unban":
                    target_user = await self.bot.fetch_user(job_name)
                    target_guild = self.bot.get_guild(job_details["guild"])
                    delete_job(timestamp, jobtype, job_name)
                    await target_guild.unban(
                        target_user, reason="Dishtimer: Timed ban expired."
                    )
                elif jobtype == "remind":
                    text = job_details["text"]
                    added_on = job_details["added"]
                    target = await self.bot.fetch_user(int(job_name))
                    original_timestamp = (
                        datetime.strptime(added_on, "%Y-%m-%d %H:%M:%S")
                        .replace(tzinfo=timezone.utc)
                        .astimezone()
                        .strftime("%s")
                    )
                    if target:
                        embed = discord.Embed(
                            title="⏰ Reminder",
                            description=f"You asked to be reminded <t:{original_timestamp}:R> on <t:{original_timestamp}:f>.",
                            timestamp=datetime.now(),
                        )
                        embed.set_footer(
                            text=self.bot.user.name, icon_url=self.bot.user.avatar.url
                        )
                        embed.add_field(
                            name="📝 Contents",
                            value=f"{text}",
                            inline=False,
                        )
                        await target.send(embed=embed)
                    delete_job(timestamp, jobtype, job_name)
            except:
                # Don't kill cronjobs if something goes wrong.
                delete_job(timestamp, jobtype, job_name)
                await log_channel.send(
                    "Crondo has errored, job deleted: ```"
                    f"{traceback.format_exc()}```"
                )

    async def clean_channel(self, channel_id):
        log_channel = self.bot.get_channel(config.bot_logchannel)
        channel = self.bot.get_channel(channel_id)
        try:
            done_cleaning = False
            count = 0
            while not done_cleaning:
                purge_res = await channel.purge(limit=100)
                count += len(purge_res)
                if len(purge_res) != 100:
                    done_cleaning = True
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cronclean has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(minutes=1)
    async def minutely(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(config.bot_logchannel)
        try:
            ctab = get_botfile("dishtimers")
            timestamp = time.time()
            for jobtype in ctab:
                for jobtimestamp in ctab[jobtype]:
                    if timestamp > int(jobtimestamp):
                        await self.do_jobs(ctab, jobtype, jobtimestamp)

            # Handle clean channels
            for clean_channel in config.minutely_clean_channels:
                await self.clean_channel(clean_channel)
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-minutely has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(hours=1)
    async def hourly(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(config.bot_logchannel)
        try:
            # Handle clean channels
            for clean_channel in config.hourly_clean_channels:
                await self.clean_channel(clean_channel)
            # Change playing status.
            activity = discord.Activity(
                name=random.choice(config.game_names), type=config.game_type
            )
            await self.bot.change_presence(activity=activity)
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-hourly has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(hours=24)
    async def daily(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(config.bot_logchannel)
        try:
            shutil.make_archive("data_backup", "zip", "data")
            for m in config.bot_managers:
                await self.bot.get_user(m).send(
                    content="Daily backups:",
                    file=discord.File("data_backup.zip"),
                )
            os.remove("data_backup.zip")
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-daily has errored: ```{traceback.format_exc()}```"
            )


async def setup(bot):
    await bot.add_cog(Dishtimer(bot))
