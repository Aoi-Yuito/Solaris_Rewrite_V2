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

import re
import aiohttp
from io import BytesIO

import hikari
import lightbulb
from lightbulb import commands

import datetime as dt

from solaris.utils import chron
from solaris.utils import checks

from solaris.bot.extensions.meta import all_channel_under_category


LINK_REGEX = re.compile(
    r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()!@:%_\+.~#?&\/\/=]*)"
)
INVITE_REGEX = re.compile(r"(?:https?://)?discord(?:app)?\.(?:com/invite|gg)/[a-zA-Z0-9]+/?")


UNHOIST_PATTERN = "".join(chr(i) for i in [*range(0x20, 0x30), *range(0x3A, 0x41), *range(0x5B, 0x61)])
STRICT_UNHOIST_PATTERN = "".join(chr(i) for i in [*range(0x20, 0x41), *range(0x5B, 0x61)])


def is_url(string: str, *, fullmatch: bool = True) -> bool:
    if fullmatch and LINK_REGEX.fullmatch(string):
        return True
    elif not fullmatch and LINK_REGEX.match(string):
        return True

    return False


def is_invite(string: str, *, fullmatch: bool = True) -> bool:
    if fullmatch and INVITE_REGEX.fullmatch(string):
        return True
    elif not fullmatch and INVITE_REGEX.match(string):
        return True

    return False


mod = lightbulb.plugins.Plugin(
    name="Mod",
    description="Basic moderation actions designed to help you keep your server clean and safe.",
    include_datastore=True
)


@mod.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not mod.bot.ready.booted:
        mod.bot.ready.up(mod)

    mod.d.configurable: bool = False
    mod.d.image = "https://cdn.discordapp.com/attachments/991572493267636275/991578577776689212/mod.png"

@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.KICK_MEMBERS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.KICK_MEMBERS))
@lightbulb.option(name="reason", description="Reason for the kick.", type=str, required=False, default="No reason provided.", modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="Members to be kicked", type=hikari.Member, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="kick", description="Kicks one or more members from your server.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def kick_command(ctx: lightbulb.context.base.Context):
    targets = ctx.options.targets
    reason = ctx.options.reason
    if not targets:
        await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")
    else:
        count = 0

        async with ctx.get_channel().trigger_typing():
            for target in targets:
                try:
                    await target.kick(reason=f"{reason} - Actioned by {ctx.author.username}")
                    count += 1
                except hikari.ForbiddenError:
                    await ctx.respond(
                        f"{ctx.bot.cross} Failed to kick {target.username} as their permission set is superior to Solaris'."
                    )

            if count > 0:
                await ctx.respond(f"{ctx.bot.tick} {count:,} member(s) were kicked.")
            else:
                await ctx.respond(f"{ctx.bot.info} No members were kicked.")

@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.BAN_MEMBERS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.BAN_MEMBERS))
@lightbulb.option(name="reason", description="Reason of the ban", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="delete_message_days", description="Number of days to delete the message", type=int, default=1, required=False)
@lightbulb.option(name="targets", description="Members or Users to ban", type=hikari.User, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="ban", description="Bans one or more members from your server.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def ban_command(ctx: lightbulb.context.base.Context):
    # NOTE: This is here to get mypy to shut up. Need to look at typehints for this.
    reason = ctx.options.reason
    targets = ctx.options.targets
    delete_message_days = ctx.options.delete_message_days or 1

    if not targets:
        await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")
    elif not 0 <= delete_message_days <= 7:
        await ctx.respond(
            f"{ctx.bot.cross} The number of days to delete is outside valid bounds - it should be between 0 and 7 inclusive."
        )
    else:
        count = 0

        async with ctx.get_channel().trigger_typing():
            for target in targets:
                try:
                    banned_user = await ctx.bot.rest.fetch_ban(ctx.guild_id, target.id)
                    if banned_user:
                        await ctx.respond(f"{ctx.bot.info} {target.username} is already banned from this server, so skipping {target.username}...")
                        continue
                        
                except hikari.NotFoundError:
                    await ctx.get_guild().ban(
                        target,
                        delete_message_days=delete_message_days,
                        reason=(
                            (f"{reason}" if target.id in [m for m in ctx.get_guild().get_members()] else f"{reason} (Hackban)")
                            + f" - Actioned by {ctx.author.username}"
                        ),
                    )
                    count += 1
                    
                except hikari.ForbiddenError:
                    await ctx.respond(
                        f"{ctx.bot.cross} Failed to ban {target.username} as their permission set is superior to Solaris'."
                    )

            if count > 0:
                await ctx.respond(f"{ctx.bot.tick} {count:,} member(s) were banned.")
            else:
                await ctx.respond(f"{ctx.bot.info} No members were banned.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.BAN_MEMBERS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.BAN_MEMBERS))
@lightbulb.option(name="reason", description="Reason for the unban", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="IDs of the Users to unban", type=int, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="unban", description="Unbans one or more users from your server.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def unban_command(ctx: lightbulb.context.base.Context):
    reason = ctx.options.reason
    targets = ctx.options.targets

    if not targets:
        await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")
    else:
        count = 0

        async with ctx.get_channel().trigger_typing():
            for target in targets:
                await ctx.get_guild().unban(target, reason=f"{reason} - Actioned by {ctx.author.username}")
                count += 1

            if count > 0:
                await ctx.respond(f"{ctx.bot.tick} {count:,} user(s) were unbanned.")
            else:
                await ctx.respond(f"{ctx.bot.cross} No users were unbanned.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.BAN_MEMBERS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.BAN_MEMBERS))
@lightbulb.option(name="reason", description="Reason of the ban", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="delete_message_days", description="Number of days to delete the message", type=int, default=1, required=False)
@lightbulb.option(name="targets", description="Members or Users to ban", type=hikari.User, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="softban", aliases=["sban"], description="Bans one or more members from your server.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def softban_command(ctx: lightbulb.context.base.Context):
    # NOTE: This is here to get mypy to shut up. Need to look at typehints for this.
    reason = ctx.options.reason
    targets = ctx.options.targets
    delete_message_days = ctx.options.delete_message_days or 1

    if not targets:
        await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")
    elif not 0 <= delete_message_days <= 7:
        await ctx.respond(
            f"{ctx.bot.cross} The number of days to delete is outside valid bounds - it should be between 0 and 7 inclusive."
        )
    else:
        count = 0

        async with ctx.get_channel().trigger_typing():
            for target in targets:
                try:
                    banned_user = await ctx.bot.rest.fetch_ban(ctx.guild_id, target.id)
                    if banned_user:
                        await ctx.respond(f"{ctx.bot.info} {target.username} is already banned from this server, so skipping {target.username}...")
                        continue
                        
                except hikari.NotFoundError:
                    await ctx.get_guild().ban(
                        target,
                        delete_message_days=delete_message_days,
                        reason=(
                            (f"{reason}" if target.id in [m for m in ctx.get_guild().get_members()] else f"{reason} (Softban)")
                            + f" - Actioned by {ctx.author.username}"
                        ),
                    )
                    
                except hikari.ForbiddenError:
                    await ctx.respond(
                        f"{ctx.bot.cross} Failed to ban {target.username} as their permission set is superior to Solaris'."
                    )

                await ctx.get_guild().unban(target, reason=f"{reason} - Actioned by {ctx.author.username}")
                count += 1

            if count > 0:
                await ctx.respond(f"{ctx.bot.tick} {count:,} member(s) were softbanned.")
            else:
                await ctx.respond(f"{ctx.bot.info} No members were softbanned.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="clear", aliases=["clr"], description="Clears up to 100 messages from a channel. Use the command for information on available subcommands.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def clear_group(ctx: lightbulb.context.base.Context):
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Clear",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991580004137844766/broom.png",
            description="There are a few different clear methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help clear {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )


@clear_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="targets", description="The User Objects or IDs", type=hikari.Member, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="scan", description="The number of messages to clear", type=int, required=True)
@lightbulb.command(name="message", aliases=["m"], description="Clears up to 100 messages from a channel.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def clear_message_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.scan <= 100:
        await ctx.respond(
            f"{ctx.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
        )
        assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
        return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
    
    else:
        async with ctx.get_channel().trigger_typing():
            channel = ctx.get_channel()
            predicates = [
                # Ignore deferred typing indicator so it doesn't get deleted lmfao
                lambda message: not (hikari.MessageFlag.LOADING & message.flags)
            ]

            if ctx.options.targets:
                predicates.extend([(lambda m: m.author.id == t.id) for t in ctx.options.targets])
            
                messages = (
                    await ctx.bot.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )
            
                if messages:
                    try:
                        await ctx.bot.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        )
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )
                        
            else:
                messages = (
                    await ctx.bot.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .limit(ctx.options.scan + 1)
                )

                if messages:
                    try:
                        await ctx.bot.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        )


@clear_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="regex_expression", description="The regex expression for the message", type=str, required=True, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The User Objects or IDs", type=hikari.Member, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="scan", description="The number of messages to clear", type=int, required=True)
@lightbulb.command(name="regex", aliases=["r"], description="Only delete messages that match with the regular expression.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def clear_regex_message_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.scan <= 100:
        await ctx.respond(
            f"{ctx.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
        )
        assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
        return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
    
    else:
        async with ctx.get_channel().trigger_typing():
            channel = ctx.get_channel()
            predicates = [
                # Ignore deferred typing indicator so it doesn't get deleted lmfao
                lambda message: not (hikari.MessageFlag.LOADING & message.flags)
            ]

            if ctx.options.targets:
                predicates.extend([(lambda m: m.author.id == t.id) for t in ctx.options.targets])
                
                try:
                    regex = re.compile(ctx.options.regex_expression)
                
                except re.error as error:
                    await ctx.respond(f"{ctx.bot.cross} Invalid regex passed. Failed parsing regex: ```{str(error)}```")
                    assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
                    return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
        
                else:
                    predicates.append(lambda message, regex=regex: regex.match(message.content) if message.content else False)

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        ) 
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )
            else:

                try:
                    regex = re.compile(ctx.options.regex_expression)
                
                except re.error as error:
                    await ctx.respond(f"{ctx.bot.cross} Invalid regex passed. Failed parsing regex: ```{str(error)}```")
                    assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
                    return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
        
                else:
                    predicates.append(lambda message, regex=regex: regex.match(message.content) if message.content else False)

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        ) 
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )


@clear_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="targets", description="The User Objects or IDs", type=hikari.Member, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="scan", description="The number of messages to clear", type=int, required=True)
@lightbulb.command(name="embed", aliases=["e"], description="Only delete messages that contain embeds.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def clear_embed_message_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.scan <= 100:
        await ctx.respond(
            f"{ctx.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
        )
        assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
        return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
    
    else:
        async with ctx.get_channel().trigger_typing():
            channel = ctx.get_channel()
            predicates = [
                # Ignore deferred typing indicator so it doesn't get deleted lmfao
                lambda message: not (hikari.MessageFlag.LOADING & message.flags)
            ]

            if ctx.options.targets:
                predicates.extend([(lambda m: m.author.id == t.id) for t in ctx.options.targets])
                predicates.append(lambda message: bool(message.embeds))

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        )     
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )
            else:
                predicates.append(lambda message: bool(message.embeds))
                
                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        ) 
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )


@clear_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="targets", description="The User Objects or IDs", type=hikari.Member, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="scan", description="The number of messages to clear", type=int, required=True)
@lightbulb.command(name="links", aliases=["l"], description="Only delete messages that contain links.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def clear_link_message_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.scan <= 100:
        await ctx.respond(
            f"{ctx.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
        )
        assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
        return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
    
    else:
        async with ctx.get_channel().trigger_typing():
            channel = ctx.get_channel()
            predicates = [
                # Ignore deferred typing indicator so it doesn't get deleted lmfao
                lambda message: not (hikari.MessageFlag.LOADING & message.flags)
            ]

            if ctx.options.targets:
                predicates.extend([(lambda m: m.author.id == t.id) for t in ctx.options.targets])
                predicates.append(lambda message: is_url(message.content, fullmatch=False) if message.content else False)

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        )       
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )
            else:
                predicates.append(lambda message: is_url(message.content, fullmatch=False) if message.content else False)
                
                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        ) 
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )


@clear_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="targets", description="The User Objects or IDs", type=hikari.Member, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="scan", description="The number of messages to clear", type=int, required=True)
@lightbulb.command(name="invites", aliases=["i"], description="Only delete messages that contain Discord invites.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def clear_invite_message_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.scan <= 100:
        await ctx.respond(
            f"{ctx.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
        )
        assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
        return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
    
    else:
        async with ctx.get_channel().trigger_typing():
            channel = ctx.get_channel()
            predicates = [
                # Ignore deferred typing indicator so it doesn't get deleted lmfao
                lambda message: not (hikari.MessageFlag.LOADING & message.flags)
            ]

            if ctx.options.targets:
                predicates.extend([(lambda m: m.author.id == t.id) for t in ctx.options.targets])
                predicates.append(lambda message: is_invite(message.content, fullmatch=False) if message.content else False)

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        )   
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )
            else:
                predicates.append(lambda message: is_invite(message.content, fullmatch=False) if message.content else False)

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        ) 
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )


@clear_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="targets", description="The User Objects or IDs", type=hikari.Member, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="scan", description="The number of messages to clear", type=int, required=True)
@lightbulb.command(name="attachments", aliases=["a"], description="Only delete messages that contain files & images.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def clear_attachment_message_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.scan <= 100:
        await ctx.respond(
            f"{ctx.bot.cross} The number of messages to clear is outside valid bounds - it should be between 1 and 100 inclusive."
        )
        assert ctx.invoked is not None and ctx.invoked.cooldown_manager is not None
        return await ctx.invoked.cooldown_manager.reset_cooldown(ctx)
    
    else:
        async with ctx.get_channel().trigger_typing():
            channel = ctx.get_channel()
            predicates = [
                # Ignore deferred typing indicator so it doesn't get deleted lmfao
                lambda message: not (hikari.MessageFlag.LOADING & message.flags)
            ]

            if ctx.options.targets:
                predicates.extend([(lambda m: m.author.id == t.id) for t in ctx.options.targets])
                predicates.append(lambda message: bool(message.attachments))

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        )     
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )
            else:
                predicates.append(lambda message: bool(message.attachments))

                messages = (
                    await ctx.app.rest.fetch_messages(channel)
                    .take_until(lambda m: (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)) > m.created_at)
                    .filter(*predicates)
                    .limit(ctx.options.scan)
                )

                if messages:
                    try:
                        await ctx.app.rest.delete_messages(channel, messages)
                        await ctx.respond(
                            f"{ctx.bot.tick} {len(messages):,} message(s) were deleted.", delete_after=5,
                        )
                    except hikari.BulkDeleteError as error:
                        await ctx.respond(
                            f"{ctx.bot.info} Only **{len(error.messages_deleted)}/{len(messages)}** message(s) were deleted due to an error.", delete_after=5,
                        ) 
                else:
                    await ctx.respond(
                        f"{ctx.bot.cross} No messages matched the specified criteria from the past two weeks!", delete_after=5,
                    )


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.option(name="reason", description="Reason for the clean", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The channel to clean", type=hikari.GuildChannel, required=True)
@lightbulb.command(name="clearchannel", aliases=["clrch"], description="Clears an entire channel of messages.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def clearchannel_command(ctx: lightbulb.context.base.Context):
    reason = ctx.options.reason
    target = ctx.options.target
    ctx_is_target = ctx.get_channel() == target

    async with ctx.get_channel().trigger_typing():
        print(target.permission_overwrites)
        if isinstance(target, hikari.GuildTextChannel):
            await ctx.get_guild().create_text_channel(
                name=target.name,
                topic=target.topic,
                nsfw=target.is_nsfw,
                rate_limit_per_user=target.rate_limit_per_user,
                #permission_overwrites=target.permission_overwrites,
                category=target.parent_id,
                reason=f"{reason} - Actioned by {ctx.author.username}"
            )

        elif isinstance(target, hikari.GuildNewsChannel):
            await ctx.get_guild().create_news_channel(
                name=target.name,
                topic=target.topic,
                nsfw=target.is_nsfw,
                rate_limit_per_user=target.rate_limit_per_user,
                #permission_overwrites=target.permission_overwrites,
                category=target.parent_id,
                reason=f"{reason} - Actioned by {ctx.author.username}"
            )

        elif isinstance(target, hikari.GuildVoiceChannel):
            await ctx.get_guild().create_voice_channel(
                name=target.name,
                user_limit=target.user_limit,
                bitrate=target.bitrate,
                video_quality_mode=target.video_quality_mode,
                #permission_overwrites=target.permission_overwrites,
                region=target.region,
                category=target.parent_id,
                reason=f"{reason} - Actioned by {ctx.author.username}"
            )
        await target.delete()

        if not ctx_is_target:
            await ctx.respond(f"{ctx.bot.tick} Channel cleared.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="timeout", aliases=["to"], description="Timeout a user. Use the command for information on available subcommands.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def timeout_group(ctx: lightbulb.context.base.Context):
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Timeout",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991580653185417246/stopwatch.png",
            description="There are a few different timeout methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help timeout {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )


@timeout_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.option(name="reason", description="Reason for the timeout.", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The Members to set a timeout.", type=hikari.Member, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="duration", description="The duration(Days) to time the user out for", type=int, required=True)
@lightbulb.command(name="add", description="Timeout Member command, supports durations longer than 28 days.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def timeout_add_command(ctx: lightbulb.context.base.Context):
    if not 0 < ctx.options.duration <= 28:
        await ctx.respond(
            f"{ctx.bot.cross} The duration to set the timeout is outside valid bounds - it should be between 1 and 28 inclusive."
        )

    count = 0
    today = dt.datetime.now(dt.timezone.utc)

    async with ctx.get_channel().trigger_typing():
        for target in ctx.options.targets:
            if target.communication_disabled_until() is not None:
                await ctx.respond(f"{ctx.bot.info} {target.mention} is already under a timeout, so skipping {target.mention}...")
                continue
            elif target.communication_disabled_until() is None:
                try:
                    await target.edit(
                        communication_disabled_until=today + dt.timedelta(days=ctx.options.duration),
                        reason=f"{ctx.options.reason} - Actioned by {ctx.author.username}"
                    )
                    count += 1
                except hikari.NotFoundError:
                    pass

        if count > 0:
            await ctx.respond(f"{ctx.bot.tick} Timeout is not set to `{ctx.options.duration}` day(s) for {count:,} member(s).")
        else:
            await ctx.respond(f"{ctx.bot.info} No members were set to timeout.")


@timeout_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.option(name="reason", description="Reason for the timeout.", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The Members to remove a timeout.", type=hikari.Member, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="remove", description="Timeout remove command, removes a timeout from members.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def timeout_remove_command(ctx: lightbulb.context.base.Context):
    count = 0

    async with ctx.get_channel().trigger_typing():
        for target in ctx.options.targets:
            if target.communication_disabled_until() is not None:
                try:
                    await target.edit(
                        communication_disabled_until=None,
                        reason=f"{ctx.options.reason} - Actioned by {ctx.author.username}"
                    )
                    count += 1
                except hikari.NotFoundError:
                    pass
                
            elif target.communication_disabled_until() is None:
                await ctx.respond(f"{ctx.bot.info} {target.mention} is not under any timeout, so skipping {target.mention}...")
                continue

        if count > 0:
            await ctx.respond(f"{ctx.bot.tick} Timeout removed from {count:,} member(s).")
        else:
            await ctx.respond(f"{ctx.bot.info} No members were removed from timeout.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.option(name="targets", description="The Channels to set slowmode.", type=hikari.GuildTextChannel, required=False, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.option(name="interval", description="The slowmode interval in seconds, use 0 to disable it.", type=int, required=True)
@lightbulb.command(name="slowmode", description="Set slowmode interval for channels.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def slowmode_command(ctx: lightbulb.context.base.Context):
    if not 0 <= ctx.options.interval <= 21600:
        await ctx.respond(
            f"{ctx.bot.cross} The interval to set slowmode is outside valid bounds - it should be between 0 and 21600 inclusive."
        )

    count = 0

    if ctx.options.targets:
        async with ctx.get_channel().trigger_typing():
            for target in ctx.options.targets:
                try:
                    await target.edit(rate_limit_per_user=ctx.options.interval)
                    count += 1
                except hikari.NotFoundError:
                    pass

            if count > 0:
                await ctx.respond(f"{ctx.bot.tick} Slowmode is now set to 1 message per `{ctx.options.interval}` seconds for `{count:,}` channel(s).")
            else:
                await ctx.respond(f"{ctx.bot.info} No channels were slowmoded.")
    else:
        async with ctx.get_channel().trigger_typing():
            await ctx.get_channel().edit(rate_limit_per_user=ctx.options.interval)
            await ctx.respond(f"{ctx.bot.tick} Slowmode is now set to 1 message per `{ctx.options.interval}` seconds for this channel.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="create", aliases=["crt", "mk"], description="Creates new items in singular or batches. Use the command for information on available subcommands.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def create_group(ctx: lightbulb.context.base.Context):
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="create",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991584795572306020/add-image.png",
            description="There are a few different creation methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help create {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )


@create_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_cooldown(300, 2, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="reason", description="Reason for the emoji create action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="link", description="The specified emoji to create from the given link", type=str, required=True)
@lightbulb.option(name="name", description="The name of the emoji.", type=str, required=True)
@lightbulb.command(name="emoji", aliases=["emote", "e"], description="Creates the specified emoji from the given link.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def create_emoji_command(ctx: lightbulb.context.base.Context):
    async with aiohttp.ClientSession() as session:
        async with session.get(ctx.options.link) as r:
            try:
                if r.status in range(200, 299):
                    img = BytesIO(await r.read())
                    byte = img.getvalue()
                    emoji = await ctx.bot.rest.create_emoji(guild=ctx.guild_id, name=ctx.options.name, image=byte, reason=ctx.options.reason)
                    await ctx.respond(f"{ctx.bot.tick} Successfully created emoji: {emoji.mention}")
                else:
                    await ctx.respond(f"{ctx.bot.cross} Error when making request | Response: `{r.status}`.")
            except hikari.BadRequestError:
                await ctx.respond(f"{ctx.bot.cross} The file size was larger than 256kb, so it can't be added to your server.")


@create_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_cooldown(300, 2, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="reason", description="Reason for the sticker create action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="link", description="The specified sticker to create from the given link", type=str, required=True)
@lightbulb.option(name="tag", description="The tag of the sticker.", type=str, required=True)
@lightbulb.option(name="name", description="The name of the sticker.", type=str, required=True)
@lightbulb.command(name="sticker", aliases=["st"], description="Creates the specified sticker from the given link.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def create_emoji_command(ctx: lightbulb.context.base.Context):
    async with aiohttp.ClientSession() as session:
        async with session.get(ctx.options.link) as r:
            try:
                if r.status in range(200, 299):
                    img = BytesIO(await r.read())
                    byte = img.getvalue()
                    sticker = await ctx.get_guild().create_sticker(name=ctx.options.name, tag=ctx.options.tag, image=byte, reason=ctx.options.reason)
                    await ctx.respond(f"{ctx.bot.tick} Successfully created sticker")
                else:
                    await ctx.respond(f"{ctx.bot.cross} Error when making request | Response: `{r.status}`.")
            except hikari.BadRequestError:
                await ctx.respond(f"{ctx.bot.cross} The file size was larger than 512kb, so it can't be added to your server.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.option(name="nickname", description="The name to set nickname", type=str, required=True, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The Member to set nickname", type=hikari.Member, required=True)
@lightbulb.command(name="setnickname", aliases=["setnick"], description="Sets a member's nickname.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def setnickname_command(ctx: lightbulb.context.base.Context):
    nickname = ctx.options.nickname
    target = ctx.options.target or ctx.bot.cache.get_member(ctx.guild_id , ctx.author.id)

    if len(nickname) > 32:
        await ctx.respond(f"{ctx.bot.cross} Nicknames can not be more than 32 characters in length.")
    elif not isinstance(target, hikari.Member):
        await ctx.respond(
            f"{ctx.bot.cross} Solaris was unable to identify a server member with the information provided."
        )
    else:
        try:
            await target.edit(nick=nickname)
            await ctx.respond(f"{ctx.bot.tick} Nickname changed.")
        except hikari.ForbiddenError:
            await ctx.respond(
                f"{ctx.bot.cross} Failed to change {target.display_name}'s nickname as their permission set is superior to Solaris'."
            )


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.option(name="reason", description="Reason for the clear nickname action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The Members to clear their nickname", type=hikari.Member, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="clearnickname", aliases=["clrnick"], description="Clears one or more members' nicknames.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def clearnickname_command(ctx: lightbulb.context.base.Context):
    count = 0
    reason = ctx.options.reason
    targets = ctx.options.targets

    async with ctx.get_channel().trigger_typing():
        for target in targets:
            try:
                await target.edit(nick=None, reason=f"{reason} - Actioned by {ctx.author.username}")
                count += 1
            except hikari.ForbiddenError:
                await ctx.respond(
                    f"{ctx.bot.cross} Failed to clear {target.display_name}'s nickname as their permission set is superior to Solaris'."
                )

        if count > 0:
            await ctx.respond(f"{ctx.bot.tick} Cleared {count:,} member(s)' nicknames.")
        else:
            await ctx.respond(f"{ctx.bot.info} No members' nicknames were changed.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.buckets.GuildBucket(3600, 1))
@lightbulb.option(name="strict", description="Whether to change it strictly or not", type=bool, default=False, required=False)
@lightbulb.command(name="unhoistnicknames", description="Unhoists the nicknames of all members.")
@lightbulb.implements(commands.prefix.PrefixCommand)
async def unhoistnicknames_command(ctx: lightbulb.context.base.Context):
    count = 0
    strict = ctx.options.strict

    async with ctx.get_channel().trigger_typing():
        for member in ctx.get_guild().get_members():
            try:
                match = re.match(
                    rf"[{STRICT_UNHOIST_PATTERN if strict else UNHOIST_PATTERN}]+", ctx.bot.cache.get_member(ctx.guild_id, member).display_name
                )
                if match is not None:
                    await ctx.bot.cache.get_member(ctx.guild_id, member).edit(
                        nick=ctx.bot.cache.get_member(ctx.guild_id, member).display_name.replace(match.group(), "", 1),
                        reason=f"Unhoisted. - Actioned by {ctx.author.username}",
                    )
                    count += 1
            except hikari.ForbiddenError:
                pass

        await ctx.respond(f"{ctx.bot.tick} Unhoisted {count:,} nicknames.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="delete", aliases=["del", "rm"], description="Deletes items in singular or batches. Use the command for information on available subcommands.")
@lightbulb.implements(commands.prefix.PrefixCommandGroup)
async def delete_group(ctx: lightbulb.context.base.Context):
    cmds = []
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds_list = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)
    for cmd in cmds_list:
        if cmd not in cmds:
            cmds.append(cmd)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Delete",
            thumbnail="https://cdn.discordapp.com/attachments/991572493267636275/991585028528148530/delete.png",
            description="There are a few different deletion methods you can use.",
            fields=(
                *(
                    (
                        cmd.name.title(),
                        f"{cmd.description} For more infomation, use `{prefix}help delete {cmd.name}`",
                        False,
                    )
                    for cmd in cmds
                ),
            ),
        )
    )


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.buckets.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The channel to delete", type=hikari.GuildChannel, required=True)
@lightbulb.command(name="channel", description="Deletes the specified channel.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_channel_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target
    #reason = ctx.options.reason
    ctx_is_target = ctx.get_channel() == target

    async with ctx.get_channel().trigger_typing():
        await target.delete()
        #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}")

        if not ctx_is_target:
            await ctx.respond(f"{ctx.bot.tick} Channel deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.buckets.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete channels action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The channels to delete", type=hikari.GuildChannel, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="channels", description="Deletes one or more channels.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_channels_command(ctx: lightbulb.context.base.Context):
    #reason = ctx.options.reason
    targets = ctx.options.targets

    if not targets:
        await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")
    else:
        ctx_in_targets = ctx.get_channel() in targets
        count = 0

        async with ctx.get_channel().trigger_typing():
            for target in targets:
                await target.delete()
                #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}")
                count += 1

        if not ctx_in_targets:
            await ctx.respond(f"{ctx.bot.tick} {count:,} channel(s) were deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.buckets.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete category action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The category to delete", type=hikari.GuildCategory, required=True)
@lightbulb.command(name="category", description="Deletes the specified category along with all channels within it.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_category_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target
    #reason = ctx.options.reason
    all_channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)
    category_channels = [c for c in all_channels if all_channel_under_category(ctx, c, target.id) is True]
    ctx_in_targets = ctx.get_channel().id in category_channels

    async with ctx.get_channel().trigger_typing():
        for tc in all_channels:
            if ctx.bot.cache.get_guild_channel(tc).parent_id == target.id:
                await ctx.bot.cache.get_guild_channel(tc).delete()
            #await ctx.bot.cache.get_guild_channel(tc).delete(reason=f"{reason} - Actioned by {ctx.author.username}")
                await target.delete()
        #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}")

        if not ctx_in_targets:
            await ctx.respond(f"{ctx.bot.tick} Category deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(300, 1, lightbulb.buckets.GuildBucket)
#@lightbulb.option(name="reason", description="Reason for the delete role action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The role to delete", type=hikari.Role, required=True)
@lightbulb.command(name="role", description="Deletes the specified role.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_role_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target
    #reason = ctx.options.reason

    async with ctx.get_channel().trigger_typing():
        await ctx.bot.rest.delete_role(ctx.guild_id, target.id)
        #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}")

        await ctx.respond(f"{ctx.bot.tick} Role deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.buckets.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete roles action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The roles to delete", type=hikari.Role, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="roles", description="Deletes one or more roles.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_roles_command(ctx: lightbulb.context.base.Context):
    #reason = ctx.options.reason
    targets = ctx.options.targets

    if not targets:
        await ctx.respond(f"{ctx.bot.cross} No valid targets were passed.")
    else:
        count = 0

        async with ctx.get_channel().trigger_typing():
            for target in targets:
                await ctx.bot.rest.delete_role(ctx.guild_id, target.id)
                #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}")
                count += 1

        await ctx.respond(f"{ctx.bot.tick} `{count:,}` role(s) were deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(300, 2, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="reason", description="Reason for the delete emoji action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The emoji to delete", type=hikari.Emoji, required=True)
@lightbulb.command(name="emoji", aliases=["emote", "e"], description="Deletes the specified emoji.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_emoji_command(ctx: lightbulb.context.base.Context):
    async with ctx.get_channel().trigger_typing():
        await ctx.bot.rest.delete_emoji(guild=ctx.guild_id, emoji=ctx.options.target, reason=f"{ctx.options.reason} - Actioned by {ctx.author.username}")
        await ctx.respond(f"{ctx.bot.tick} Successfully deleted the Emoji.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(300, 2, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="reason", description="Reason for the delete emojis action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The emojis to delete", type=hikari.Emoji, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="emojis", aliases=["emotes"], description="Deletes the specified emojis.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_emojis_command(ctx: lightbulb.context.base.Context):
    count = 0
    async with ctx.get_channel().trigger_typing():
        for target in ctx.options.targets:
            await ctx.bot.rest.delete_emoji(guild=ctx.guild_id, emoji=target, reason=f"{ctx.options.reason} - Actioned by {ctx.author.username}")
            count += 1
        await ctx.respond(f"{ctx.bot.tick} `{count:,}` emoji(s) were deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(300, 2, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="reason", description="Reason for the delete sticker action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="ID", description="The sticker ID to delete", type=int, required=True)
@lightbulb.command(name="sticker", aliases=["st"], description="Deletes the specified sticker.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_sticker_command(ctx: lightbulb.context.base.Context):
    target = await ctx.bot.rest.fetch_sticker(ctx.options.ID)
    async with ctx.get_channel().trigger_typing():
        await ctx.get_guild().delete_sticker(sticker=target, reason=f"{ctx.options.reason} - Actioned by {ctx.author.username}")
        await ctx.respond(f"{ctx.bot.tick} Successfully deleted the sticker.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(300, 2, lightbulb.buckets.GuildBucket)
@lightbulb.option(name="reason", description="Reason for the delete stickers action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="IDs", description="The sticker IDs to delete", type=int, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="stickers", description="Deletes the specified stickers.")
@lightbulb.implements(commands.prefix.PrefixSubCommand)
async def delete_stickers_command(ctx: lightbulb.context.base.Context):
    count = 0
    async with ctx.get_channel().trigger_typing():
        for sticker in ctx.options.IDs:
            target = await ctx.bot.rest.fetch_sticker(sticker)
            await ctx.get_guild().delete_sticker(sticker=target, reason=f"{ctx.options.reason} - Actioned by {ctx.author.username}")
            count += 1
        await ctx.respond(f"{ctx.bot.tick} Successfully deleted the sticker.")


def load(bot) -> None:
    bot.add_plugin(mod)

def unload(bot) -> None:
    bot.remove_plugin(mod)
