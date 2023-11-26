import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context, Bot, BucketType
import asyncio


class mdthread(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.webhook_name = "Murder Drones Thread Webhook"

    @commands.cooldown(1, 300, BucketType.user)
    @commands.command()
    async def mdping(self, ctx: Context, *, content: str):
        if ctx.channel.id != 1093720104946126919:
            return

        reaction_message = await ctx.channel.fetch_message(1093790310938726451)
        reaction = [
            element
            for element in reaction_message.reactions
            if element.emoji.id == 906980837092909136
        ][0]

        mentions = []

        async for member in reaction.users():
            mentions.append(f"<@{member.id}>")

        def check(r, u):
            return u == ctx.author and str(r.emoji) == "✅"

        confirmmsg = await ctx.reply(
            content=f"You're about to mention {len(mentions)} member{'' if len(mentions) == 1 else 's'}. Are you sure you want to do this?",
            mention_author=False,
        )
        await confirmmsg.add_reaction("✅")

        try:
            r, u = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await self.cancel_message(ctx, confirmmsg)
        else:
            await self.send_message(ctx, f"{' '.join(mentions)} {content}", confirmmsg)

    async def send_message(
        self, ctx: Context, content: str, confirmsg: discord.Message
    ):
        webhooks = await ctx.guild.webhooks()
        webhook_results = [
            element
            for element in webhooks
            if element.name == self.webhook_name
            and element.channel_id == ctx.channel.parent_id
        ]

        webhook = (
            await ctx.channel.parent.create_webhook(name=self.webhook_name)
            if len(webhook_results) == 0
            else webhook_results[0]
        )
        await confirmsg.delete()
        await ctx.message.delete()

        await webhook.send(
            content=content,
            avatar_url=ctx.author.display_avatar.url,
            username=ctx.author.display_name,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=True, roles=False
            ),
            thread=ctx.channel,
        )

    async def cancel_message(self, ctx: Context, confirmmsg: discord.Message):
        await confirmmsg.edit(
            content="Your message has been cancelled.",
            delete_after=5,
        )
        await ctx.message.delete()
        self.mdping.reset_cooldown(ctx)


async def setup(bot: Bot):
    await bot.add_cog(mdthread(bot))
