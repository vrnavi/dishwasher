# This cog handles errors.

# Imports.
import discord
import sys
import traceback
from discord.ext import commands
from discord.ext.commands import Cog
from helpers.embeds import stock_embed, slice_embed
from helpers.placeholders import random_msg


class errors(Cog):
    def __init__(self, bot):
        self.bot = bot

    # Responsible for actually DMing the errors.
    async def throw_error(self, err, func, err_type):
        embed = stock_embed(self.bot)
        err_tb = "\n".join(traceback.format_exception(*err))

        if err_type == 0:
            embed.color = discord.Color.from_str("#FF0000")
            embed.title = "🔥 Code Error"
            embed.description = f"In `{func}`!"
            self.bot.log.error(f"Code error in {func}!\n{err_tb}")
        elif err_type == 1:
            embed.color = discord.Color.from_str("#FFFF00")
            embed.title = "⚠️ Code Error"
            embed.description = f"In command `{func}`!"
            self.bot.log.error(f"Code error in command {func}!\n{err_tb}")

        slice_embed(embed, err_tb, "🔍 Traceback", "```", "```")

        for m in self.bot.config.managers:
            await self.bot.get_user(m).send(embed=embed)

    # Testing command.
    @commands.command()
    async def breakcommand(self, ctx):
        if ctx.author.id != 120698901236809728:
            return
        test = 1 + "a"

    # Receives command errors.
    @Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(
            error, commands.CommandInvokeError
        ) and "Cannot send messages to this user" not in str(error):
            err = (
                type(error.__cause__),
                error.__cause__,
                error.__cause__.__traceback__,
            )
            self.bot.errors.append((err, ctx, ()))
            await self.throw_error(err, ctx.command, 1)
            return await ctx.send(random_msg("err_generic"))

        self.bot.log.error(
            f"An error occurred with `{ctx.command}` from "
            f"{ctx.message.author} ({ctx.message.author.id}):\n"
            f"{type(error)}: {error}"
        )

        if isinstance(
            error, commands.CommandInvokeError
        ) and "Cannot send messages to this user" in str(error):
            return await ctx.send(random_msg("err_dmfail"))
        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(random_msg("err_serversonly"))
        elif isinstance(error, commands.PrivateMessageOnly):
            return await ctx.send(random_msg("err_dmsonly"))
        elif (
            isinstance(error, commands.InvalidEndOfQuotedStringError)
            or isinstance(error, commands.ExpectedClosingQuoteError)
            or isinstance(error, commands.UnexpectedQuoteError)
        ):
            return await ctx.send(random_msg("err_quotes"))
        elif isinstance(error, commands.MissingRole):
            return await ctx.send(
                random_msg("err_role") + f"```{error.missing_role}```"
            )
        elif isinstance(error, commands.BotMissingPermissions):
            roles_needed = "\n+ ".join(error.missing_permissions)
            return await ctx.send(
                random_msg("err_perms") + f"```diff\n+ {roles_needed}```"
            )
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(
                random_msg("err_cooldown") + f"{error.retry_after:.1f} seconds."
            )
        elif isinstance(error, commands.CheckFailure):
            return await ctx.send(random_msg("err_checkfail"))
        elif isinstance(error, commands.MissingRequiredAttachment):
            return await ctx.send(random_msg("err_noattachment"))
        elif isinstance(error, commands.UserNotFound):
            return await ctx.send(random_msg("err_usernotfound"))
        elif isinstance(error, commands.MemberNotFound):
            return await ctx.send(random_msg("err_membernotfound"))

        help_text = (
            f"Usage of this command is: ```{ctx.prefix}{ctx.command.qualified_name} "
            f"{ctx.command.signature}```\nPlease see `{ctx.prefix}help"
            f"` for more info."
        )

        if isinstance(error, commands.BadArgument):
            return await ctx.send(f"You gave incorrect arguments. {help_text}")
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"You gave incomplete arguments. {help_text}")

    # Receives code errors.
    @Cog.listener()
    async def on_error(self, event_method, *args, **kwargs):
        err = sys.exc_info()

        ctx = None
        if args:
            for arg in args:
                if type(arg) == discord.Message:
                    ctx = await self.bot.get_context(arg)

        self.bot.errors.append((err, ctx, (args, kwargs)))
        await self.throw_error(err, ctx if ctx else event_method, 0)


async def setup(bot):
    await bot.add_cog(errors(bot))
