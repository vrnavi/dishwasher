import asyncio
import traceback
import datetime
import discord
import time
import json
import math
import parsedatetime
from helpers.datafiles import get_guildfile, set_guildfile
from helpers.sv_config import get_config
from helpers.placeholders import random_msg
from discord.ext.commands import Cog


class Common(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.async_call_shell = self.async_call_shell
        self.bot.slice_message = self.slice_message
        self.bot.hex_to_int = self.hex_to_int
        self.bot.download_file = self.download_file
        self.bot.aiojson = self.aiojson
        self.bot.aioget = self.aioget
        self.bot.aiogetbytes = self.aiogetbytes
        self.bot.escape_message = self.escape_message
        self.bot.get_used_invites = self.get_used_invites
        self.bot.await_message = self.await_message
        self.bot.await_reaction = self.await_reaction
        self.bot.convert_temperature = self.convert_temperature
        self.bot.filesize = self.filesize
        self.bot.parse_time = self.parse_time
        self.bot.c_to_f = self.c_to_f
        self.bot.f_to_c = self.f_to_c
        self.bot.c_to_k = self.c_to_k
        self.bot.f_to_k = self.f_to_k
        self.bot.pull_role = self.pull_role
        self.bot.pull_channel = self.pull_channel
        self.bot.pull_category = self.pull_category
        self.bot.pacify_name = self.pacify_name

    def pull_role(self, guild, role):
        if isinstance(role, str):
            role = discord.utils.get(guild.roles, name=role)
        else:
            role = guild.get_role(role)
        return role

    def pull_channel(self, guild, channel):
        if isinstance(channel, str):
            channel = discord.utils.get(
                list(guild.text_channels)
                + list(guild.voice_channels)
                + list(guild.threads),
                name=channel,
            )
        else:
            channel = guild.get_channel_or_thread(channel)
        return channel

    def pull_category(self, guild, category):
        if isinstance(category, str):
            category = discord.utils.get(guild.categories, name=category)
        else:
            category = guild.get_channel(category)
            if category and type(category) != discord.CategoryChannel:
                category = None
        return category

    def pacify_name(self, name):
        return discord.utils.escape_markdown(name.replace("@", "@ "))

    def c_to_f(self, c):
        return 9.0 / 5.0 * c + 32

    def f_to_c(self, f):
        return 5.0 / 9.0 * (f - 32)

    def c_to_k(self, c):
        return c + 273.15

    def f_to_k(self, f):
        return 5.0 / 9.0 * (f + 459.67)

    def parse_time(self, delta_str):
        cal = parsedatetime.Calendar()
        time_struct, parse_status = cal.parse(delta_str)
        res_timestamp = math.floor(time.mktime(time_struct))
        return res_timestamp

    async def aioget(self, url):
        try:
            data = await self.bot.session.get(url)
            if data.status != 200:
                self.bot.log.error(f"HTTP Error {data.status} while getting {url}")
                return None
            text_data = await data.text()
            # self.bot.log.info(f"Data from {url}: {text_data}")
            return text_data
        except:
            self.bot.log.error(
                f"Error while getting {url} "
                f"on aiogetbytes: {traceback.format_exc()}"
            )
            raise ConnectionError

    async def aiogetbytes(self, url):
        try:
            data = await self.bot.session.get(url)
            if data.status != 200:
                self.bot.log.error(f"HTTP Error {data.status} while getting {url}")
                return None
            byte_data = await data.read()
            # self.bot.log.debug(f"Data from {url}: {byte_data}")
            return byte_data
        except:
            self.bot.log.error(
                f"Error while getting {url} "
                f"on aiogetbytes: {traceback.format_exc()}"
            )
            raise ConnectionError

    async def aiojson(self, url):
        try:
            data = await self.bot.session.get(url)
            if data.status != 200:
                self.bot.log.error(f"HTTP Error {data.status} while getting {url}")
                return None
            text_data = await data.text()
            # self.bot.log.info(f"Data from {url}: {text_data}")
            content_type = data.headers["Content-Type"]
            return await data.json(content_type=content_type)
        except:
            self.bot.log.error(
                f"Error while getting {url} "
                f"on aiogetbytes: {traceback.format_exc()}"
            )
            raise ConnectionError

    def hex_to_int(self, color_hex: str):
        """Turns a given hex color into an integer"""
        return int("0x" + color_hex.strip("#"), 16)

    def escape_message(self, text: str):
        """Escapes unfun stuff from messages"""
        return str(text).replace("@", "@ ").replace("<#", "# ")

    async def get_used_invites(self, member: discord.Member):
        """Handles the invite correlation stuff"""
        try:
            real_invites = await member.guild.invites()
        except:
            return "Unable: Missing Permissions."
        invites = get_guildfile(member.guild.id, "invites")

        # Add unknown active invites. Can happen if invite was manually created
        for invite in real_invites:
            if invite.id not in invites:
                invites[invite.id] = {
                    "uses": 0,
                    "url": invite.url,
                    "max_uses": invite.max_uses,
                    "code": invite.code,
                }

        probable_invites_used = []
        items_to_delete = []
        # Look for invites whose usage increased since last lookup
        for id, invite in invites.items():
            real_invite = next((x for x in real_invites if x.id == id), None)

            if not real_invite:
                # Invite does not exist anymore. Was either revoked manually
                # or the final use was used up
                probable_invites_used.append(invite)
                items_to_delete.append(id)
            elif invite["uses"] < real_invite.uses:
                probable_invites_used.append(invite)
                invite["uses"] = real_invite.uses

        # Delete used up invites
        for id in items_to_delete:
            del invites[id]

        # Save invites data.
        set_guildfile(member.guild.id, "invites", json.dumps(invites))

        # Prepare the invite correlation message
        if len(probable_invites_used) == 1:
            invite_used = probable_invites_used[0]["code"]
        elif len(probable_invites_used) == 0:
            invite_used = "Unknown"
        else:
            invite_used = "One of: "
            invite_used += ", ".join([x["code"] for x in probable_invites_used])

        return invite_used

    async def await_message(self, channel, author, timeout=60):
        """Nice wrapper for waiting for a message"""

        def check(m):
            return m.author.id == author.id and m.channel.id == channel.id

        try:
            message = await self.bot.wait_for("message", timeout=timeout, check=check)
        except asyncio.TimeoutError:
            return None
        return message

    async def await_reaction(self, message, author, reactions, timeout=60):
        """Nice wrapper for waiting for a reaction"""

        def check(r, u):
            return (
                u.id == author.id
                and r.message.id == message.id
                and str(r.emoji) in reactions
            )

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=timeout, check=check
            )
        except asyncio.TimeoutError:
            return None
        return reaction

    def convert_temperature(self, temp, inunit, outunit):
        """Converts from one temperature unit to another."""
        if inunit.lower() == "c":
            if outunit.lower() == "f":
                out = (temp * 9 / 5) + 32
            elif outunit.lower() == "k":
                out = temp + 273.15
        elif inunit.lower() == "f":
            if outunit.lower() == "c":
                out = (temp - 32) * 5 / 9
            elif outunit.lower() == "k":
                out = (temp - 32) * 5 / 9 + 273.15
        elif inunit.lower() == "k":
            if outunit.lower() == "f":
                out = (temp - 273.15) * 9 / 5 + 32
            elif outunit.lower() == "c":
                out = temp - 273.15
        return out

    # This function is based on https://stackoverflow.com/a/35435419/3286892
    # by link2110 (https://stackoverflow.com/users/5890923/link2110)
    # modified by Ave (https://github.com/aveao), licensed CC-BY-SA 3.0
    async def download_file(self, url, local_filename):
        file_resp = await self.bot.session.get(url)
        file = await file_resp.read()
        with open(local_filename, "wb") as f:
            f.write(file)

    # This one's based on https://stackoverflow.com/a/1094933
    def filesize(self, num):
        for unit in ("", "K", "M", "G", "T"):
            if abs(num) < 1024.0:
                return f"{num:3.2f} {unit}B"
            num /= 1024.0
        return f"{num:.2f} PB"

    # 2000 is maximum limit of discord
    def slice_message(self, text, size=2000, prefix="", suffix=""):
        """Slices a message into multiple messages"""
        fragment_list = []
        size_wo_fix = size - len(prefix) - len(suffix)
        while len(text) > size_wo_fix:
            fragment_list.append(f"{prefix}{text[:size_wo_fix]}{suffix}")
            text = text[size_wo_fix:]
        fragment_list.append(f"{prefix}{text}{suffix}")
        return fragment_list

    async def async_call_shell(
        self, shell_command: str, inc_stdout=True, inc_stderr=True
    ):
        pipe = asyncio.subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(
            str(shell_command), stdout=pipe, stderr=pipe
        )

        if not (inc_stdout or inc_stderr):
            return "??? you set both stdout and stderr to False????"

        proc_result = await proc.communicate()
        stdout_str = proc_result[0].decode("utf-8").strip()
        stderr_str = proc_result[1].decode("utf-8").strip()

        if inc_stdout and not inc_stderr:
            return stdout_str
        elif inc_stderr and not inc_stdout:
            return stderr_str

        if stdout_str and stderr_str:
            return f"stdout:\n\n{stdout_str}\n\n" f"======\n\nstderr:\n\n{stderr_str}"
        elif stdout_str:
            return f"stdout:\n\n{stdout_str}"
        elif stderr_str:
            return f"stderr:\n\n{stderr_str}"

        return "No output."


async def setup(bot):
    await bot.add_cog(Common(bot))
