import asyncio
import discord
import datetime


def slice_embed(embed, text, name, prefix="", suffix=""):
    fragment_list = []
    size_wo_fix = 1020 - len(prefix) - len(suffix)
    while len(text) > size_wo_fix:
        fragment_list.append(f"{prefix}{text[:size_wo_fix]}{suffix}")
        text = text[size_wo_fix:]
    fragment_list.append(f"{prefix}{text}{suffix}")

    if len(fragment_list) == 1:
        embed.add_field(
            name=name,
            value=f">>> {fragment_list[0]}",
            inline=False,
        )
        return

    embed.add_field(
        name=name,
        value="**Too long to post!** Split into fragments below.",
        inline=False,
    )
    for i, c in enumerate(fragment_list):
        embed.add_field(
            name=f"🧩 Fragment {i+1}",
            value=f">>> {c}",
            inline=False,
        )
    return


def author_embed(embed, obj, thumbnail=False):
    if type(obj).__name__ == "Guild":
        embed.set_author(
            name=obj.name,
            icon_url=obj.icon.url,
        )
        if thumbnail:
            embed.set_thumbnail(url=obj.display_avatar.url)

    elif type(obj).__name__ == "Member" or type(obj).__name__ == "User":
        embed.set_author(
            name=obj.global_name + f" [{obj}]" if obj.global_name else str(obj),
            icon_url=obj.display_avatar.url,
        )
        if thumbnail:
            embed.set_thumbnail(url=obj.display_avatar.url)


def mod_embed(embed, target, staff, reason=None):
    def username_system(user):
        def pacify_name(name):
            return discord.utils.escape_markdown(name.replace("@", "@ "))

        formatted = (
            pacify_name(user.global_name) + f" [{pacify_name(str(user))}]"
            if user.global_name
            else pacify_name(str(user))
        ) + f" ({str(user.id)})"

        return formatted

    embed.set_author(
        name=target,
        icon_url=target.display_avatar.url,
    )
    embed.add_field(
        name=f"👤 User",
        value=username_system(target),
        inline=True,
    )
    embed.add_field(
        name=f"🛠️ Staff",
        value=username_system(staff),
        inline=True,
    )
    if reason:
        embed.add_field(name=f"📝 Reason", value=reason, inline=False)


def createdat_embed(embed, member):
    embed.add_field(
        name="⏰ Account Created",
        value=f"<t:{int(member.created_at.astimezone().timestamp())}:f>\n<t:{int(member.created_at.astimezone().timestamp())}:R>",
        inline=True,
    )


def joinedat_embed(embed, member):
    embed.add_field(
        name="⏱️ Account Joined",
        value=f"<t:{int(member.joined_at.astimezone().timestamp())}:f>\n<t:{int(member.joined_at.astimezone().timestamp())}:R>",
        inline=True,
    )


def stock_embed(bot):
    embed = discord.Embed(timestamp=datetime.datetime.now())
    embed.set_footer(text=bot.user.name, icon_url=bot.user.display_avatar)
    return embed


def quote_embed(bot, qmsg, omsg, label="Quoted"):
    embed = stock_embed(bot)
    embed.color = qmsg.author.color
    embed.timestamp = qmsg.created_at
    if qmsg.clean_content:
        limit = 500
        if len(qmsg.clean_content) <= limit or '"' + omsg.jump_url + '"' in omsg:
            embed.description = "> " + "\n> ".join(qmsg.clean_content.split("\n"))
        else:
            embed.description = (
                "> "
                + "\n> ".join(qmsg.clean_content[:limit].split("\n"))
                + "...\n\n"
                + f'**Message is over {limit} long.**\nUse `"LINK"` to show full message.'
            )
    embed.set_footer(
        text=f"{label} by {omsg.author}",
        icon_url=omsg.author.display_avatar.url,
    )
    embed.set_author(
        name=f"💬 {qmsg.author} said in #{qmsg.channel.name}...",
        icon_url=qmsg.author.display_avatar.url,
        url=qmsg.jump_url,
    )
    if qmsg.attachments and qmsg.attachments[0].content_type[:6] == "image/":
        if qmsg.attachments[0].is_spoiler():
            embed.set_image(url="https://files.catbox.moe/tpgdvl.png")
        else:
            embed.set_image(url=qmsg.attachments[0].url)
            if len(qmsg.attachments) > 1:
                if not embed.description:
                    embed.description = ""
                embed.description += (
                    f"\n\n🖼️ __Original post has `{len(qmsg.attachments)}` images.__"
                )
    elif qmsg.embeds and qmsg.embeds[0].image:
        embed.set_image(url=qmsg.embeds[0].image.url)
    elif qmsg.stickers:
        embed.set_image(url=qmsg.stickers[0].url)
    return embed


async def sympage(bot, ctx, embeds, symbols):
    index = 0

    embeds[index].color = discord.Color.red()
    message = await ctx.reply(embed=embeds[index], mention_author=False)
    allowed_mentions = discord.AllowedMentions(replied_user=False)
    for symbol in symbols:
        await message.add_reaction(symbol)

    def reactioncheck(r, u):
        return (
            u.id == ctx.author.id
            and str(r.emoji) in symbols
            and r.message.id == message.id
        )

    async def close():
        for symbol in symbols:
            await message.remove_reaction(symbol, ctx.bot.user)
        embeds[index].color = discord.Color.default()
        await message.edit(embed=embeds[index], allowed_mentions=allowed_mentions)

    embeds[index].color = discord.Color.green()
    await message.edit(embed=embeds[index], allowed_mentions=allowed_mentions)

    while True:
        try:
            reaction, user = await bot.wait_for(
                "reaction_add", timeout=30.0, check=reactioncheck
            )
        except asyncio.TimeoutError:
            return await close()
        else:
            try:
                await message.remove_reaction(reaction, ctx.author)
            except:
                pass
            index = symbols.index(reaction.emoji)
            embeds[index].color = discord.Color.green()
            await message.edit(embed=embeds[index], allowed_mentions=allowed_mentions)
