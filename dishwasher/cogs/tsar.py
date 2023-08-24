import config
import datetime
import discord
import json
import asyncio
from discord.ext import commands, tasks
from discord.ext.commands import Cog
from helpers.checks import check_if_staff, check_if_bot_manager
from helpers.usertrack import get_usertrack, fill_usertrack, set_usertrack
from helpers.embeds import stock_embed
from helpers.sv_config import fill_config, set_config


class TSAR(Cog):
    """
    TSAR BOMBA! True. Self. Assignable. Roles.
    """

    def __init__(self, bot):
        self.bot = bot
        self.interactivecache = {}
        self.toilet.start()

    def cog_unload(self):
        self.toilet.cancel()

    def new_track(self, member):
        usertracks, uid = fill_usertrack(member.guild.id, member.id)
        if "jointime" not in usertracks[uid] or not usertracks[uid]["jointime"]:
            usertracks[uid]["jointime"] = int(member.joined_at.timestamp())
        set_usertrack(member.guild.id, json.dumps(usertracks))

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command()
    async def tsar(self, ctx):
        configs = fill_config(ctx.guild.id)

        navigation_reactions = ["⏹", "✨", "❌", "💣"]

        embed = stock_embed(self.bot)
        embed.title = "⚙️ TSAR Configuration Editor"
        embed.color = ctx.author.color
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        if not configs["tsar"]["roles"]:
            embed.add_field(
                name="Currently empty!",
                value="Click the sparkle icon to get started.",
                inline=False,
            )
        else:
            for name, tsar in list(configs["tsar"]["roles"].items()):
                embed.add_field(
                    name=name,
                    value=f"> **Role:** {ctx.guild.get_role(tsar['roleid']).mention}\n"
                    + f"> **Minimum Days:** `{tsar['mindays']}`\n"
                    + f"> **Forbidden Roles:** "
                    + ", ".join(
                        [
                            ctx.guild.get_role(int(s)).mention
                            for s in tsar["blacklisted"]
                        ]
                    )
                    if tsar["blacklisted"]
                    else "None"
                    + "\n"
                    + f"> **Required Roles: **"
                    + ", ".join(
                        [ctx.guild.get_role(int(s)).mention for s in tsar["required"]]
                    )
                    if tsar["required"]
                    else "None" + "\n",
                    inline=False,
                )
        configmsg = await ctx.reply(embed=embed, mention_author=False)
        for e in navigation_reactions:
            await configmsg.add_reaction(e)

        def reactioncheck(r, u):
            return u.id == ctx.author.id and str(r.emoji) in navigation_reactions

        def messagecheck(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            return await configmsg.edit(
                content="Operation timed out.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )

        async def waitformsg():
            try:
                message = await self.bot.wait_for(
                    "message", timeout=300.0, check=messagecheck
                )
            except asyncio.TimeoutError:
                await configsuppmsg.delete()
                return await configmsg.edit(
                    content="Operation timed out.",
                    embed=None,
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )
            return message

        if str(reaction) == "⏹":
            return await configmsg.edit(
                content="Operation cancelled.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        elif str(reaction) == "✨":
            if len(configs["tsar"]["roles"]) == 20:
                return await ctx.reply(
                    content="Unable to create new TSAR: Maximum of 20 TSARs reached.",
                    mention_author=False,
                )
            namemsg = await ctx.send(content="**Making new TSAR.**\nName of this TSAR?")
            nameresp = await waitformsg()
            await namemsg.edit(
                content=f"TSAR Name: `{nameresp.content}`", delete_after=5
            )
            IDmsg = await ctx.send(content="ID of the role to give?")
            IDresp = await waitformsg()
            await IDmsg.edit(content=f"Role ID: `{IDresp.content}`", delete_after=5)
            mindaysmsg = await ctx.send(content="Minimum days?")
            mindaysresp = await waitformsg()
            await mindaysmsg.edit(
                content=f"Minimum days: `{mindaysresp.content}`", delete_after=5
            )
            blacklistedrolesmsg = await ctx.send(
                content="Roles forbidden? (IDs separated by spaces, or none for none)"
            )
            blacklistedrolesresp = await waitformsg()
            await blacklistedrolesmsg.edit(
                content=f"Forbidden roles: `{blacklistedrolesresp.content}`",
                delete_after=5,
            )
            requiredrolesmsg = await ctx.send(
                content="Roles required? (IDs separated by spaces, or none for none)"
            )
            requiredrolesresp = await waitformsg()
            await requiredrolesmsg.edit(
                content=f"Required roles: `{requiredrolesresp.content}`", delete_after=5
            )
            configs["tsar"]["roles"][nameresp.content] = {
                "roleid": int(IDresp.content),
                "mindays": int(mindaysresp.content),
                "blacklisted": blacklistedrolesresp.content.split()
                if blacklistedrolesresp.content.lower() != "none"
                else None,
                "required": requiredrolesresp.content.split()
                if requiredrolesresp.content.lower() != "none"
                else None,
            }
            configs = set_config(
                ctx.guild.id, "tsar", "roles", configs["tsar"]["roles"]
            )
            return await configmsg.edit(
                content="TSAR list updated.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        elif str(reaction) == "❌":
            namemsg = await ctx.send(content="**Removing a TSAR.**\nName of this TSAR?")
            nameresp = await waitformsg()
            await namemsg.delete()
            del configs["tsar"]["roles"][nameresp.content]
            configs = set_config(
                ctx.guild.id, "tsar", "roles", configs["tsar"]["roles"]
            )
            return await configmsg.edit(
                content="TSAR list updated.",
                embed=None,
                delete_after=5,
                allowed_mentions=discord.AllowedMentions(replied_user=False),
            )
        elif str(reaction) == "💣":
            confirmmsg = await ctx.send(content="Nuke the **ENTIRE** TSAR list?")
            confirmresp = await waitformsg()
            await confirmmsg.delete()
            if confirmresp.content.lower() == "yes":
                configs["tsar"]["roles"] = {}
                configs = set_config(
                    ctx.guild.id, "tsar", "roles", configs["tsar"]["roles"]
                )
                return await configmsg.edit(
                    content="TSAR list nuked.",
                    embed=None,
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )
            else:
                return await configmsg.edit(
                    content="Aborted.",
                    embed=None,
                    delete_after=5,
                    allowed_mentions=discord.AllowedMentions(replied_user=False),
                )

    @Cog.listener()
    async def on_member_join(self, member):
        await self.bot.wait_until_ready()
        if member.bot:
            return
        self.new_track(member)

    @Cog.listener()
    async def on_member_remove(self, member):
        await self.bot.wait_until_ready()
        if member.bot:
            return
        self.new_track(member)

    @Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()
        if message.author.bot or not message.guild:
            return
        if message.guild.id not in self.interactivecache:
            self.interactivecache[message.guild.id] = []
        if message.author.id not in self.interactivecache[message.guild.id]:
            self.interactivecache[message.guild.id].append(message.author.id)

    @tasks.loop(time=datetime.time(hour=0))
    async def toilet(self):
        # water go down the hole
        for g in self.interactivecache:
            usertracks = get_usertrack(g)
            for u in self.interactivecache[g]:
                usertracks, uid = fill_usertrack(g, u, usertracks)
                if not usertracks[uid]["jointime"]:
                    usertracks[uid]["jointime"] = int(
                        self.bot.get_guild(g).get_member(u).joined_at.timestamp()
                    )
                usertracks[uid]["truedays"] += 1
            set_usertrack(g, json.dumps(usertracks))


async def setup(bot):
    await bot.add_cog(TSAR(bot))
