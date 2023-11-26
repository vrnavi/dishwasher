import config
from helpers.sv_config import get_config


def check_if_staff(ctx):
    if ctx.author.id in config.bot_managers:
        return True
    if ctx.author.id == ctx.bot.user.id:
        return True
    if not ctx.guild:
        return False
    return any(
        (
            any(
                r.id == get_config(ctx.guild.id, "staff", "staffrole")
                for r in ctx.author.roles
            ),
            any(m == ctx.author.id for m in config.bot_managers),
            ctx.author.guild_permissions.manage_guild,
        )
    )


def check_if_bot_manager(ctx):
    return any(m == ctx.author.id for m in config.bot_managers + [ctx.bot.user.id])
