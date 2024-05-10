import discord
from discord.ext import commands
from helpers.sv_config import get_config, get_raw_config


def isbot(ctx):
    return ctx.author.id == ctx.bot.user.id


async def ismanager(ctx, layered=False):
    if isbot(ctx):
        return True

    if layered:
        return ctx.author.id in ctx.bot.owner_ids

    return await commands.is_owner().predicate(ctx)


def isoverride(ctx):
    config = get_raw_config(ctx.guild.id)
    if not config["overrides"]:
        return (False, False)
    role = None
    for override in config["overrides"]:
        if ctx.bot.get_command(override["command"]) == ctx.command:
            for role in override["roles"]:
                if isinstance(role, str):
                    role = discord.utils.get(ctx.guild.roles, name=role)
                    if role:
                        role = role.id
                if ctx.author.get_role(role):
                    return (override["restrict"], True)
    return (override["restrict"], False)


async def isowner(ctx, layered=False):
    if not layered:
        if await ismanager(ctx, True):
            return True
        if isoverride(ctx)[0]:
            return isoverride(ctx)[1]
        elif isoverride(ctx)[1]:
            return True

    return ctx.guild.owner.id == ctx.author.id


async def isadmin(ctx, layered=False):
    if not layered:
        if await ismanager(ctx, True):
            return True
        if isoverride(ctx)[0]:
            return isoverride(ctx)[1]
        elif isoverride(ctx)[1]:
            return True
    if await isowner(ctx, True):
        return True
    if not get_config(ctx.guild.id, "staff", "adminrole"):
        return False

    if layered:
        return (
            ctx.guild.get_role(get_config(ctx.guild.id, "staff", "adminrole"))
            in ctx.author.roles
        )

    return await commands.has_role(
        get_config(ctx.guild.id, "staff", "adminrole")
    ).predicate(ctx)


async def ismod(ctx):
    if await ismanager(ctx, True):
        return True
    if isoverride(ctx)[0]:
        return isoverride(ctx)[1]
    elif isoverride(ctx)[1]:
        return True
    if await isadmin(ctx, True):
        return True
    if not get_config(ctx.guild.id, "staff", "modrole"):
        return False

    return await commands.has_role(
        get_config(ctx.guild.id, "staff", "modrole")
    ).predicate(ctx)
