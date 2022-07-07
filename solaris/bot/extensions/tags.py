# Solaris - A Discord bot designed to make your server a safer and better place.
# Copyright (C) 2020  Ethan Henderson

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Ethan Henderson
# parafoxia@carberra.xyz

import hikari
import lightbulb
from lightbulb import commands

import typing as t
from string import ascii_lowercase

from solaris.utils import menu, checks, markdown, converters

#MAX_TAGS = 35
MAX_TAGNAME_LENGTH = 25


class HelpMenu(menu.MultiPageMenu):
    def __init__(tag, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


tag = lightbulb.plugins.Plugin(
    name="Tags",
    description="Commands for creating tags.",
    include_datastore=True
)


@tag.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    if not tag.bot.ready.booted:
        tag.bot.ready.up(tag)

    tag.d.configurable: bool = False
    tag.d.image = "https://cdn.discordapp.com/attachments/991572493267636275/991586086906237048/tags.png"


@tag.command()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="tag_name", description="Name of the tag to fetch.", type=str)
@lightbulb.command(name="tag", description="Shows the content of an existing tag.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def tag_command(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.tag_name):
        return await ctx.respond(f"{ctx.bot.cross} Tag identifiers can only contain lower case letters.")

    tag_names= await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)

    cache = []

    if ctx.options.tag_name not in tag_names:
        await ctx.respond(f'{ctx.bot.cross} The Tag `{ctx.options.tag_name}` does not exist.')
        for x in range(len(tag_names)):
            if tag_names[x][0] == ctx.options.tag_name[0]:
                cache.append(tag_names[x])
        await ctx.respond("Did you mean..." + '\n'.join(cache) + " ?")

    else:
        content, tag_id = await ctx.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, ctx.options.tag_name)
        await ctx.respond(content)


@tag.command()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="tags", description="Commands to create tags in the server.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def tags_group(ctx: lightbulb.context.base.Context) -> None:
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Tags",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991586109073137664/tag2.png",
            description="There are a few different tag methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help tags {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="content", description="Content of the tag to create.", type=str, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="tag_name", description="Name of the tag to create.", type=str)
@lightbulb.command(name="new", description="Creates a new tag.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def tag_create(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.tag_name):
        return await ctx.respond(f"{ctx.bot.cross} Tag identifiers can only contain lower case letters.")

    if len(ctx.options.tag_name) > MAX_TAGNAME_LENGTH:
        return await ctx.respond(
            f"{ctx.bot.cross} Tag identifiers must not exceed `{MAX_TAGNAME_LENGTH}` characters in length."
        )

    tag_names = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)

    #if len(tag_names) == MAX_TAGS:
        #return await ctx.send(f"{self.bot.cross} You can only set up to {MAX_TAGS} warn types.")

    if ctx.options.tag_name in tag_names:
        prefix = await ctx.bot.prefix(ctx.get_guild().id)
        return await ctx.respond(
            f"{ctx.bot.cross} That tag already exists. You can use `{prefix}tag edit {ctx.options.tag_name}`"
        )

    await ctx.bot.db.execute(
        "INSERT INTO tags (GuildID, UserID, TagID, TagName, TagContent) VALUES (?, ?, ?, ?, ?)",
        ctx.get_guild().id,
        ctx.author.id,
        ctx.bot.generate_id(),
        ctx.options.tag_name.strip(),
        ctx.options.content.strip()
    )
    await ctx.respond(f'{ctx.bot.tick} The tag `{ctx.options.tag_name}` has been created.')


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="content", description="Content of the tag to create.", type=str, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="tag_name", description="Name of the tag to edit.", type=str)
@lightbulb.command(name="edit", description="Edits an existing tag.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def tag_edit(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.tag_name):
        return await ctx.repond(f"{ctx.bot.cross} Tag identifiers can only contain lower case letters.")

    user_id, tag_id = await ctx.bot.db.record("SELECT UserID, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, ctx.options.tag_name)

    if user_id != ctx.author.id:
        return await ctx.repond(f"{ctx.bot.cross} You can't edit others tags. You can only edit your own tags.")

    else:
        tag_content = await ctx.bot.db.column("SELECT TagContent FROM tags WHERE GuildID = ?", ctx.get_guild().id)
        tag_names = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)

        if ctx.options.tag_name not in tag_names:
            return await ctx.repond(f'{ctx.bot.cross} The tag `{ctx.options.tag_name}` does not exist.')

        if ctx.options.content in tag_content:
            return await ctx.repond(f'{ctx.bot.cross} That content already exists in this `{ctx.options.tag_name}` tag.')

        await ctx.bot.db.execute(
            "UPDATE tags SET TagContent = ? WHERE GuildID = ? AND TagName = ?",
            ctx.options.content,
            ctx.get_guild().id,
            ctx.options.tag_name,
        )

        await ctx.respond(
            f"{ctx.bot.tick} The `{ctx.options.tag_name}` tag's content has been updated."
        )


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="tag_name", description="Name of the tag to delete.", type=str)
@lightbulb.command(name="delete", description="Deletes an existing tag.", aliases=["del"])
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def tag_delete_command(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.tag_name):
        return await ctx.respond(f"{ctx.bot.cross} Tag identifiers can only contain lower case letters.")

    user_id, tag_id = await ctx.bot.db.record("SELECT UserID, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, ctx.options.tag_name)

    if user_id != ctx.author.id:
        return await ctx.respond(f"{ctx.bot.cross} You can't delete others tags. You can only delete your own tags.")

    modified = await ctx.bot.db.execute(
        "DELETE FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, ctx.options.tag_name
    )

    if not modified:
        return await ctx.respond(f"{ctx.bot.cross} That tag does not exist.")

    await ctx.respond(f'{ctx.bot.tick} Tag `{ctx.options.tag_name}` deleted.')


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="tag_name", description="Name of the tag to fetch info.", type=str)
@lightbulb.command(name = "info", description="Shows information about an existing tag.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def tag_info_command(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.tag_name):
        return await ctx.respond(f"{ctx.bot.cross} Tag identifiers can only contain lower case letters.")

    tag_names = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)

    if ctx.options.tag_name not in tag_names:
        return await ctx.respond(f'{ctx.bot.cross} The Tag `{ctx.options.tag_name}` does not exist.')

    user_id, tag_id, tag_time = await ctx.bot.db.record("SELECT UserID, TagID, TagTime FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, ctx.options.tag_name)

    user = await ctx.bot.rest.fetch_user(user_id)

    embed = hikari.Embed(title = 'Tag Info', colour = ctx.member.get_top_role().color, timestamp = ctx.message.created_at)
    embed.set_thumbnail(user.avatar_url)
    embed.add_field(name = "Owner", value = user.mention, inline = False)
    embed.add_field(name = "Tag Name", value = ctx.options.tag_name, inline = True)
    embed.add_field(name = "Tag ID", value = tag_id, inline = True)
    embed.add_field(name = "Created at", value = tag_time, inline = True)
    embed.set_footer(text = f"Requested by {ctx.author.username}", icon = ctx.author.avatar_url)

    await ctx.respond(embed = embed)


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target for to fetch info about tag.", type=hikari.Member, required=False)
@lightbulb.command(name = "all", description="Shows the tag list of a tag owner.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def member_tag_list_command(ctx: lightbulb.context.base.Context) -> None:
    target = ctx.options.target or ctx.author

    prefix = await ctx.bot.prefix(ctx.get_guild().id)
    all_tags = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)
    tag_names = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ? AND UserID = ?", ctx.get_guild().id, target.id)
    tag_all = await ctx.bot.db.records("SELECT Tagname, TagID FROM tags WHERE GuildID = ? AND UserID = ?", ctx.get_guild().id, target.id)
    if len(tag_names) == 0:
        if target == ctx.author:
            return await ctx.respond(f"{ctx.bot.cross} You don't have any tag list.")
        else:
            return await ctx.respond(f"{ctx.bot.cross} That member doesn't have any tag list.")

    user = await ctx.bot.grab_user(target.id)

    try:
        pagemaps = []

        for tag_name, tag_id in sorted(tag_all):
            content, tag_id = await ctx.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, tag_name)
            first_step = content
            pagemaps.append(
                {
                    "header": "Tags",
                    "title": f"All tags of this server for {user.username}",
                    "description": f"Using **{len(tag_names)}** of this server's {len(all_tags)} tags.",
                    "thumbnail": user.avatar_url,
                    "fields": (
                        (
                            tag_name,
                            "ID: " + tag_id + "\n\n**Content**" + "\n```\n" + ''.join(first_step.replace('<', '\\<')[0:350]) + "..." + "\n\n```\n***To see this tags whole content type `" + prefix + "tag " + tag_name + "`***",
                            False
                            ),
                        ),
                    }
                )

        await HelpMenu(ctx, pagemaps).start()

    except IndexError:
        await ctx.respond(
            embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Tags",
            title=f"All tags of this server for {self.user.username}",
            description=f"Using {len(tag_names)} of this server's {len(all_tags)} tags.",
            thumbnail=user.avatar_url,
            fields=((tag_name, f"ID: {tag_id}", True) for tag_name, tag_id in sorted(tag_all)),
        )
    )


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="tag_name", description="Name of the tag to send raw data of that tag.", type=str)
@lightbulb.command(name="raw", description="Gets the raw content of the tag. This is with markdown escaped. Useful for editing.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def raw_command(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.tag_name):
        return await ctx.respond(f"{ctx.bot.cross} Tag identifiers can only contain lower case letters.")

    tag_content = await ctx.bot.db.column("SELECT TagContent FROM tags WHERE GuildID = ?", ctx.get_guild().id)
    tag_names = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)

    if ctx.options.tag_name not in tag_names:
        return await ctx.respond(f'{ctx.bot.cross} The Tag `{ctx.options.tag_name}` does not exist.')

    content, tag_id = await ctx.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, ctx.options.tag_name)

    first_step = markdown.escape_markdown(content)
    await ctx.respond(first_step.replace('<', '\\<'))


@tags_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="list", description="Lists the server's tags.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def tags_list_command(ctx: lightbulb.context.base.Context) -> None:
    prefix = await ctx.bot.prefix(ctx.get_guild().id)
    tag_names = await ctx.bot.db.column("SELECT TagName FROM tags WHERE GuildID = ?", ctx.get_guild().id)
    records = await ctx.bot.db.records("SELECT TagName, TagID FROM tags WHERE GuildID = ?", ctx.get_guild().id)

    try:
        pagemaps = []

        for tag_name, tag_id in sorted(records):
            content, tag_id = await ctx.bot.db.record("SELECT TagContent, TagID FROM tags WHERE GuildID = ? AND TagName = ?", ctx.get_guild().id, tag_name)
            first_step = content
            pagemaps.append(
                {
                    "header": "Tags",
                    "title": f"All tags of this server",
                    "description": f"A total of **{len(tag_names)}** tags of this server.",
                    "thumbnail": ctx.get_guild().icon_url,
                    "fields": (
                        (
                            tag_name,
                            "ID: " + tag_id + "\n\n**Content**" + "\n```\n" + ''.join(first_step.replace('<', '\\<')[0:350]) + "..." + "\n\n```\n***To see this tags whole content type `" + prefix + "tag " + tag_name + "`***",
                            False
                            ),
                        ),
                    }
                )

        await HelpMenu(ctx, pagemaps).start()

    except IndexError:
        await ctx.respond(
            embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Tags",
            title="All tags of this server",
            description=f"A total of **{len(tag_names)}** tags of this server.",
            thumbnail=ctx.get_guild().icon_url,
            fields=((tag_name, f"ID: {tag_id}", True) for tag_name, tag_id in sorted(records)),
        )
    )


def load(bot) -> None:
    bot.add_plugin(tag)

def unload(bot) -> None:
    bot.remove_plugin(tag)
