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

import hikari
import lightbulb
from lightbulb import commands

import datetime as dt

from solaris.utils import chron
from solaris.utils import checks

from solaris.bot.extensions.meta import all_channel_under_category


UNHOIST_PATTERN = "".join(chr(i) for i in [*range(0x20, 0x30), *range(0x3A, 0x41), *range(0x5B, 0x61)])
STRICT_UNHOIST_PATTERN = "".join(chr(i) for i in [*range(0x20, 0x41), *range(0x5B, 0x61)])


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
    mod.d.image = None

@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.KICK_MEMBERS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.KICK_MEMBERS))
@lightbulb.option(name="reason", description="Reason for the kick.", type=str, required=False, default="No reason provided.", modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="Members to be kicked", type=hikari.Member, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="kick", description="Kicks one or more members from your server.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
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
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
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
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
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
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.option(name="reason", description="Reason for the clean", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The channel to clean", type=hikari.GuildChannel, required=True)
@lightbulb.command(name="clearchannel", aliases=["clrch"], description="Clears an entire channel of messages.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def clearchannel_command(ctx: lightbulb.context.base.Context):
    reason = ctx.options.reason
    target = ctx.options.target
    ctx_is_target = ctx.get_channel() == target

    async with ctx.get_channel().trigger_typing():
        if isinstance(target, hikari.GuildTextChannel):
            await ctx.get_guild().create_text_channel(
                name=target.name,
                topic=target.topic,
                nsfw=True if target.is_nsfw is not None else False,
                rate_limit_per_user=target.rate_limit_per_user,
                #permission_overwrites=target.permission_overwrites,
                category=target.parent_id,
                reason=f"{reason} - Actioned by {ctx.author.username}"
            )

        elif isinstance(target, hikari.GuildNewsChannel):
            await ctx.get_guild().create_news_channel(
                name=target.name,
                topic=target.topic,
                nsfw=True if target.is_nsfw is not None else False,
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

        elif isinstance(target, hikari.GuildStageChannel):
            await ctx.get_guild().create_stage_channel(
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
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.option(name="reason", description="Reason for the mute", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The Member to mute", type=hikari.Member, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="mute", description="Mute Member command", hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def mute_command(ctx: lightbulb.context.base.Context):
    # TODO: Actually write this.
    await ctx.respond(f"{ctx.bot.info} Not implemented.")


@mod.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_NICKNAMES))
@lightbulb.option(name="nickname", description="The name to set nickname", type=str, required=True, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The Member to set nickname", type=hikari.Member, required=True)
@lightbulb.command(name="setnickname", aliases=["setnick"], description="Sets a member's nickname.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
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
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
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
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(3600, 1))
@lightbulb.option(name="strict", description="Whether to change it strictly or not", type=bool, default=False, required=False)
@lightbulb.command(name="unhoistnicknames", description="Unhoists the nicknames of all members.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
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
@lightbulb.implements(commands.prefix.PrefixCommandGroup, commands.slash.SlashCommandGroup)
async def delete_group(ctx: lightbulb.context.base.Context):
    prefix = await ctx.bot.prefix(ctx.guild_id)
    cmds = sorted(ctx.command.subcommands.values(), key=lambda c: c.name)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Delete",
            thumbnail=ctx.bot.get_me().avatar_url,
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
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The channel to delete", type=hikari.GuildChannel, required=True)
@lightbulb.command(name="channel", description="Deletes the specified channel.")
@lightbulb.implements(commands.prefix.PrefixSubCommand, commands.slash.SlashSubCommand)
async def delete_channel_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target
    #reason = ctx.options.reason
    ctx_is_target = ctx.get_channel() == target

    async with ctx.get_channel().trigger_typing():
        await target.delete()
        #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}") #ahh... there is no reason kwarg for it...

        if not ctx_is_target:
            await ctx.respond(f"{ctx.bot.tick} Channel deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete channels action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The channels to delete", type=hikari.GuildChannel, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="channels", description="Deletes one or more channels.")
@lightbulb.implements(commands.prefix.PrefixSubCommand, commands.slash.SlashSubCommand)
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
                #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}") #ahh... there is no reason kwarg for it...
                count += 1

        if not ctx_in_targets:
            await ctx.respond(f"{ctx.bot.tick} {count:,} channel(s) were deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_CHANNELS))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete category action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The category to delete", type=hikari.GuildCategory, required=True)
@lightbulb.command(name="category", description="Deletes the specified category along with all channels within it.")
@lightbulb.implements(commands.prefix.PrefixSubCommand, commands.slash.SlashSubCommand)
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
            #await ctx.bot.cache.get_guild_channel(tc).delete(reason=f"{reason} - Actioned by {ctx.author.username}") #ahh... there is no reason kwarg for it...
        await target.delete()
        #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}") #ahh... there is no reason kwarg for it...

        if not ctx_in_targets:
            await ctx.respond(f"{ctx.bot.tick} Category deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete role action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="target", description="The role to delete", type=hikari.Role, required=True)
@lightbulb.command(name="role", description="Deletes the specified role.")
@lightbulb.implements(commands.prefix.PrefixSubCommand, commands.slash.SlashSubCommand)
async def delete_role_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target
    #reason = ctx.options.reason

    async with ctx.get_channel().trigger_typing():
        await ctx.bot.rest.delete_role(ctx.guild_id, target.id)
        #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}") #ahh... there is no reason kwarg for it...

        await ctx.respond(f"{ctx.bot.tick} Role deleted.")


@delete_group.child()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.add_checks(lightbulb.bot_has_guild_permissions(hikari.Permissions.SEND_MESSAGES, hikari.Permissions.MANAGE_ROLES))
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
#@lightbulb.option(name="reason", description="Reason for the delete roles action", type=str, default="No reason provided.", required=False, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.option(name="targets", description="The roles to delete", type=hikari.Role, required=True, modifier=lightbulb.commands.base.OptionModifier.GREEDY)
@lightbulb.command(name="roles", description="Deletes one or more roles.")
@lightbulb.implements(commands.prefix.PrefixSubCommand, commands.slash.SlashSubCommand)
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
                #await target.delete(reason=f"{reason} - Actioned by {ctx.author.username}") #ahh... there is no reason kwarg for it...
                count += 1

        await ctx.respond(f"{ctx.bot.tick} {count:,} role(s) were deleted.")


def load(bot) -> None:
    bot.add_plugin(mod)

def unload(bot) -> None:
    bot.remove_plugin(mod)
