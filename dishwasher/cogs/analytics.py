import discord
from discord.ext.commands import Cog
from discord.ext import commands, tasks
import json
import re
import config
import datetime
import asyncio
import hashlib
import time
from helpers.checks import check_if_staff
from helpers.sv_config import get_config


class Analytics(Cog):
    """
    I need to know. I NEED to know!
    """

    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Analytics(bot))
