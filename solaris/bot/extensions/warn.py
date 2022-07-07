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

import time
import typing as t
from string import ascii_lowercase

import hikari
import lightbulb
from lightbulb import commands

from solaris.utils import checks, chron, string

MODULE_NAME = "warn"

MIN_POINTS = 1
MAX_POINTS = 20
MAX_WARNTYPE_LENGTH = 25
MAX_WARNTYPES = 25


warn = lightbulb.plugins.Plugin(
    name="Warn",
    description="A system to serve official warnings to members.",
    include_datastore=True
)


@warn.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not warn.bot.ready.booted:
        warn.bot.ready.up(warn)

    warn.d.configurable: bool = True
    warn.d.image = "https://cdn.discordapp.com/attachments/991572493267636275/991586267630403604/siren.png"


@warn.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="warn", description="Warns one or more members in your server. Use the command for information on available subcommands.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def warn_group(ctx: lightbulb.context.base.Context):
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Warn",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991586267630403604/siren.png",
            description="There are a few different warning methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help warn {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )


@warn_group.child()
#@checks.bot_has_booted()
#@checks.bot_is_ready()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="comment", description="Name of the tag to create.", type=str, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST, required=False)
@lightbulb.option(name="points_override", description="Name of the tag to create.", type=int, required=False)
@lightbulb.option(name="warn_type", description="Name of the tag to create.", type=str)
@lightbulb.option(name="targets", description="Name of the tag to create.", type=hikari.Member, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="add", description="Warns one or more members in your server.")
#@checks.module_has_initialised(MODULE_NAME)
#@checks.author_can_warn()
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warn_add_command(ctx: lightbulb.context.base.Context) -> None:
    if not ctx.options.targets:
        return await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")

    if any(c not in ascii_lowercase for c in  ctx.options.warn_type):
        return await ctx.respond(f"{ctx.bot.cross} Warn type identifiers can only contain lower case letters.")

    if (ctx.options.points_override is not None) and (not MIN_POINTS <= ctx.options.points_override <= MAX_POINTS):
        return await ctx.respond(
            f"{ctx.bot.cross} The specified points override must be between {MIN_POINTS} and {MAX_POINTS} inclusive."
        )

    if (ctx.options.comment is not None) and len(ctx.options.comment) > 256:
        return await ctx.respond(f"{ctx.bot.cross} The comment must not exceed 256 characters in length.")

    type_map = {
        ctx.options.warn_type: ctx.options.points
        for ctx.options.warn_type, ctx.options.points in await ctx.bot.db.records(
            "SELECT WarnType, Points FROM warntypes WHERE GuildID = ?", ctx.get_guild().id
        )
    }

    if ctx.options.warn_type not in type_map.keys():
        return await ctx.respond(f"{ctx.bot.cross} That warn type does not exist.")

    for target in ctx.options.targets:
        if target.is_bot:
            await ctx.respond(f"{ctx.bot.info} Skipping {target.username} as bots can not be warned.")
            continue

        await ctx.bot.db.execute(
            "INSERT INTO warns (WarnID, GuildID, UserID, ModID, WarnType, Points, Comment) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ctx.bot.generate_id(),
            ctx.get_guild().id,
            target.id,
            ctx.author.id,
            ctx.options.warn_type,
            ctx.options.points_override or type_map[ctx.options.warn_type],
            ctx.options.comment,
        )

        records = await ctx.bot.db.records(
            "SELECT WarnType, Points FROM warns WHERE GuildID = ? AND UserID = ?", ctx.get_guild().id, target.id
        )
        max_points, max_strikes = (
            await ctx.bot.db.record("SELECT MaxPoints, MaxStrikes FROM warn WHERE GuildID = ?", ctx.get_guild().id)
            or [None] * 2
        )

        if (wc := [r[0] for r in records].count(ctx.options.warn_type)) >= (max_strikes or 3):
            # Account for unbans.
            await target.ban(reason=f"Received {string.ordinal(wc)} warning for {ctx.options.warn_type}.")
            return await ctx.respond(
                f"{ctx.bot.info} {target.username} was banned because they received a {string.ordinal(wc)} warning for the same offence."
            )

        points = sum(r[1] for r in records)

        if points >= (max_points or 12):
            await target.ban(reason=f"Received equal to or more than the maximum allowed number of points.")
            return await ctx.respond(
                f"{ctx.bot.info} {target.username} was banned because they received equal to or more than the maximum allowed number of points."
            )

        await ctx.respond(
            f"{target.mention}, you have been warned for {ctx.options.warn_type} for the {string.ordinal(wc)} of {max_strikes or 3} times. You now have {points} of your allowed {max_points or 12} points."
        )



@warn_group.child()
#@checks.author_can_warn()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.option(name="warn_id", description="Id of the warn issue.", type=str)
@lightbulb.command(name="remove", aliases=["rm"], description="Removes a warning.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warn_remove_command(ctx: lightbulb.context.base.Context) -> None:
    modified = await ctx.bot.db.execute("DELETE FROM warns WHERE WarnID = ?", ctx.options.warn_id)

    if not modified:
        return await ctx.respond(f"{ctx.bot.cross} That warn ID is not valid.")

    await ctx.respond(f"{ctx.bot.tick} Warn {ctx.options.warn_id} removed.")



@warn_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
#@commands.has_permissions(administrator=True)
@lightbulb.option(name="target", description="Target for resetting warn.", type=hikari.Member)
@lightbulb.command(name="reset", description="Resets a member's warnings.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warn_reset_command(ctx: lightbulb.context.base.Context) -> None:
    modified = await ctx.bot.db.execute(
        "DELETE FROM warns WHERE GuildID = ? AND UserID = ?", ctx.get_guild().id, ctx.options.target.id
    )

    if not modified:
        return await ctx.respond(f"{ctx.bot.cross} That member does not have any warns.")

    await ctx.respond(f"{ctx.bot.tick} Warnings for {ctx.options.target.username} resetted.")



@warn_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.option(name="target", description="Target for resetting warn.", type=hikari.Member, required=False)
@lightbulb.command(name="list", description="Lists a member's warnings.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warn_list_command(ctx: lightbulb.context.base.Context) -> None:
    target = ctx.options.target or ctx.author

    if isinstance(target, str):
        return await ctx.respond(
            f"{ctx.bot.cross} Blue Brain was unable to identify a member with the information provided."
        )

    records = await ctx.bot.db.records(
        "SELECT WarnID, ModID, WarnTime, WarnType, Points, Comment FROM warns WHERE GuildID = ? AND UserID = ? ORDER BY WarnTime DESC",
        ctx.get_guild().id,
        target.id,
    )
    points = sum(record[4] for record in records)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Warn",
            title=f"Warn information for {target.username}",
            description=f"{points} point(s) accumulated. Showing {min(len(records), 10)} of {len(records)} warning(s).",
            #colour=target.get_top_role().color,
            thumbnail=target.avatar_url,
            fields=(
                (
                    f"Warn ID: {record[0]}",
                    f"**{record[3]}**: {record[5] or 'No additional comment was made.'} ({record[4]} point(s))\n"
                    f"{getattr(ctx.get_guild().get_member(record[1]), 'mention', 'Unknown')} - {chron.short_date_and_time(chron.from_iso(record[2]))}",
                    False,
                )
                for record in records[-10:]
            ),
        )
    )



@warn.command()
#@checks.author_can_configure()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.command(name="warntype", description="Manages warn types. Use the command for information on available subcommands.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def warntype_group(ctx: lightbulb.context.base.Context) -> None:
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="WarnType",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991586166052749332/mobile.png",
            description="There are a few different commands you can use to manage warn types.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help warntype {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )



@warntype_group.child()
#@checks.author_can_configure()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.option(name="points", description="Strike points for the warntype.", type=int)
@lightbulb.option(name="warn_type", description="Type of the warn.", type=str)
@lightbulb.command(name="new", description="Creates a new warn type.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warntype_new_command(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.warn_type):
        return await ctx.respond(f"{ctx.bot.cross} Warn type identifiers can only contain lower case letters.")

    if len(ctx.options.warn_type) > MAX_WARNTYPE_LENGTH:
        return await ctx.respond(
            f"{ctx.bot.cross} Warn type identifiers must not exceed {MAX_WARNTYPE_LENGTH} characters in length."
        )

    if not MIN_POINTS <= ctx.options.points <= MAX_POINTS:
        return await ctx.respond(
            f"{ctx.bot.cross} The number of points for this warn type must be between {MIN_POINTS} and {MAX_POINTS} inclusive."
        )

    warn_types = await ctx.bot.db.column("SELECT WarnType FROM warntypes WHERE GuildID = ?", ctx.get_guild().id)

    if len(warn_types) == MAX_WARNTYPES:
        return await ctx.respond(f"{ctx.bot.cross} You can only set up to {MAX_WARNTYPES} warn types.")

    if ctx.options.warn_type in warn_types:
        prefix = await ctx.bot.prefix(ctx.get_guild().id)
        return await ctx.respond(
            f"{ctx.bot.cross} That warn type already exists. You can use `{prefix}warntype edit {warn_type}`"
        )

    await ctx.bot.db.execute(
        "INSERT INTO warntypes (GuildID, WarnType, Points) VALUES (?, ?, ?)", ctx.get_guild().id, ctx.options.warn_type, ctx.options.points
    )
    await ctx.respond(
        f'{ctx.bot.tick} The warn type "{ctx.options.warn_type}" has been created, and is worth {ctx.options.points} point(s).'
    )



@warntype_group.child()
#@checks.author_can_configure()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.option(name="new_name", description="New name of the warntype.", type=str, required=False)
@lightbulb.option(name="new_points", description="New strike points for the warntype.", type=int, required=False)
@lightbulb.option(name="warn_type", description="Name of the warntype", type=str)
@lightbulb.command(name="edit", description="Edits an existing warn type.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warntype_edit_command(ctx: lightbulb.context.base.Context) -> None:
    if ctx.options.new_points is None and ctx.options.new_name is None:
        await ctx.respond(f"{ctx.bot.cross} Nothing to modify.")

    if ctx.options.new_points is not None:
        if not MIN_POINTS <= ctx.options.new_points <= MAX_POINTS:
            return await ctx.respond(
                f"{ctx.bot.cross} The number of points for this warn type must be between {MIN_POINTS} and {MAX_POINTS} inclusive."
            )

    if ctx.options.new_name is not None:
        if any(c not in ascii_lowercase for c in ctx.options.new_name):
            return await ctx.respond(f"{ctx.bot.cross} Warn type identifiers can only contain lower case letters.")

        if ctx.options.new_name == ctx.options.warn_type:
            return await ctx.respond(f'{ctx.bot.cross} That warn type "{ctx.options.new_name}" already exists.')

        warn_types = await ctx.bot.db.column("SELECT WarnType FROM warntypes WHERE GuildID = ?", ctx.get_guild().id)

        if ctx.options.warn_type not in warn_types:
            return await ctx.respond(f'{ctx.bot.cross} The warn type "{ctx.options.warn_type}" does not exist.')

        if ctx.options.new_name in warn_types:
            return await ctx.respond(f'{ctx.bot.cross} That warn type "{ctx.options.new_name}" already exists.')

    if ctx.options.new_name and ctx.options.new_points:
        retro = await ctx.bot.db.record("SELECT RetroUpdates FROM warn WHERE GuildID = ?", ctx.get_guild().id)
        if retro:
            default = await ctx.bot.db.field(
                "SELECT Points FROM warntypes WHERE GuildID = ? AND WarnType = ?", ctx.get_guild().id, ctx.options.warn_type
            )
            await ctx.bot.db.execute(
                "UPDATE warns SET WarnType = ?, Points = ? WHERE GuildID = ? AND WarnType = ? AND Points = ?",
                ctx.options.new_name,
                ctx.options.new_points,
                ctx.get_guild().id,
                ctx.options.warn_type,
                default,
            )
            await ctx.respond(f'{ctx.bot.tick} The warn type "{ctx.options.warn_type}" has been renamed to "{ctx.options.new_name}" and it is now worth {ctx.options.new_points} point(s).') 
        else:
            await ctx.bot.db.execute(
                "UPDATE warns SET WarnType = ?, Points = ? WHERE GuildID = ? AND WarnType = ?",
                ctx.options.new_name,
                ctx.options.new_points,
                ctx.get_guild().id,
                ctx.options.warn_type,
            )
            await ctx.respond(f'{ctx.bot.tick} The warn type "{ctx.options.warn_type}" has been renamed to "{ctx.options.new_name}" and it is now worth {ctx.options.new_points} point(s).')
    elif ctx.options.new_name:
        await ctx.bot.db.execute(
            "UPDATE warntypes SET WarnType = ? WHERE GuildID = ? AND WarnType = ?",
            ctx.options.new_name,
            ctx.get_guild().id,
            ctx.options.warn_type,
        )
        await ctx.bot.db.execute(
            "UPDATE warns SET WarnType = ? WHERE GuildID = ? AND WarnType = ?", ctx.options.new_name, ctx.get_guild().id, ctx.options.warn_type
        )
        await ctx.respond(f'{ctx.bot.tick} The warn type "{ctx.options.warn_type}" has been renamed to "{ctx.options.new_name}".')         
    elif ctx.options.new_points:
        if await ctx.bot.db.field("SELECT RetroUpdates FROM warn WHERE GuildID = ?", ctx.get_guild().id):
            default = await ctx.bot.db.field(
                "SELECT Points FROM warntypes WHERE GuildID = ? AND WarnType = ?", ctx.get_guild().id, ctx.options.warn_type
            )
            await ctx.bot.db.execute(
                "UPDATE warns SET Points = ? WHERE GuildID = ? AND WarnType = ? AND Points = ?",
                ctx.options.new_points,
                ctx.get_guild().id,
                ctx.options.warn_type,
                default,
            )
        await ctx.bot.db.execute(
            "UPDATE warntypes SET Points = ? WHERE GuildID = ? AND WarnType = ?",
            ctx.options.new_points,
            ctx.get_guild().id,
            ctx.options.warn_type,
        )
        await ctx.respond(f'{ctx.bot.tick} The warn type "{ctx.options.warn_type}" is now worth {ctx.options.new_points} point(s).')



@warntype_group.child()
#@checks.author_can_configure()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.option(name="warn_type", description="Name of the warntype", type=str)
@lightbulb.command(name="delete", aliases=["del"], description="Deletes a warn type.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warntype_delete_command(ctx: lightbulb.context.base.Context) -> None:
    if any(c not in ascii_lowercase for c in ctx.options.warn_type):
        return await ctx.respond("{ctx.bot.cross} Warn types can only contain lower case letters.")

    modified = await ctx.bot.db.execute(
        "DELETE FROM warntypes WHERE GuildID = ? AND WarnType = ?", ctx.get_guild().id, ctx.options.warn_type
    )

    if not modified:
        return await ctx.respond(f"{ctx.bot.cross} That warn type does not exist.")

    await ctx.bot.db.execute("DELETE FROM warns WHERE GuildID = ? AND WarnType = ?", ctx.get_guild().id, ctx.options.warn_type)
    await ctx.respond(f'{ctx.bot.tick} Warn type "{ctx.options.warn_type}" deleted.')



@warntype_group.child()
#@checks.author_can_warn()
@lightbulb.add_checks(lightbulb.guild_only)
#@checks.module_has_initialised(MODULE_NAME)
@lightbulb.command(name="list", description="Lists the server's warn types.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def warntype_list_command(ctx: lightbulb.context.base.Context) -> None:
    records = await ctx.bot.db.records("SELECT WarnType, Points FROM warntypes WHERE GuildID = ?", ctx.get_guild().id)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Warn",
            title="Warn types",
            description=f"Using {len(records)} of this server's allowed {MAX_WARNTYPES} warn types.",
            thumbnail=ctx.get_guild().icon_url,
            fields=((warn_type, f"{points} point(s)", True) for warn_type, points in records),
        )
    )



def load(bot) -> None:
    bot.add_plugin(warn)

def unload(bot) -> None:
    bot.remove_plugin(warn)
