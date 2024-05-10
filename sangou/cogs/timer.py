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
from helpers.checks import ismanager
from helpers.placeholders import game_type, game_names


class Timer(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.minutely.start()
        self.hourly.start()
        self.daily.start()

    def cog_unload(self):
        self.minutely.cancel()
        self.hourly.cancel()
        self.daily.cancel()

    @commands.check(ismanager)
    @commands.command()
    async def listjobs(self, ctx):
        """This lists timed jobs.

        I really need to revamp this system.

        No arguments."""
        ctab = get_botfile("timers")
        embed = discord.Embed(title=f"Active jobs")
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

    @commands.check(ismanager)
    @commands.command(aliases=["removejob"])
    async def deletejob(self, ctx, timestamp: str, job_type: str, job_name: str):
        """This deletes a timed job.

        I really need to revamp this system.

        - `timestamp`
        The timestamp of the job.
        - `job_type`
        The type of the job.
        - `job_name`
        The name of the job. A userid."""
        delete_job(timestamp, job_type, job_name)
        await ctx.send(f"{ctx.author.mention}: Deleted!")

    async def do_jobs(self, ctab, jobtype, timestamp):
        log_channel = self.bot.get_channel(self.bot.config.logchannel)
        for job_name in ctab[jobtype][timestamp]:
            try:
                job_details = ctab[jobtype][timestamp][job_name]
                if jobtype == "unban":
                    target_user = await self.bot.fetch_user(job_name)
                    target_guild = self.bot.get_guild(job_details["guild"])
                    delete_job(timestamp, jobtype, job_name)
                    await target_guild.unban(target_user, reason="Timed ban expired.")
                elif jobtype == "remind":
                    text = job_details["text"]
                    original_timestamp = job_details["added"]
                    target = await self.bot.fetch_user(int(job_name))
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

    @tasks.loop(minutes=1)
    async def minutely(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(self.bot.config.logchannel)
        try:
            ctab = get_botfile("timers")
            timestamp = time.time()
            for jobtype in ctab:
                for jobtimestamp in ctab[jobtype]:
                    if timestamp > int(jobtimestamp):
                        await self.do_jobs(ctab, jobtype, jobtimestamp)
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-minutely has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(hours=1)
    async def hourly(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(self.bot.config.logchannel)
        try:
            # Change playing status.
            activity = discord.Activity(name=random.choice(game_names), type=game_type)
            await self.bot.change_presence(activity=activity)
        except:
            # Don't kill cronjobs if something goes wrong.
            await log_channel.send(
                f"Cron-hourly has errored: ```{traceback.format_exc()}```"
            )

    @tasks.loop(hours=24)
    async def daily(self):
        await self.bot.wait_until_ready()
        log_channel = self.bot.get_channel(self.bot.config.logchannel)
        try:
            shutil.make_archive("data_backup", "zip", "data")
            for m in self.bot.config.managers:
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
    await bot.add_cog(Timer(bot))
