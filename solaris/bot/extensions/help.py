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
import datetime as dt

from collections import defaultdict

from solaris.utils import checks, chron, converters, menu, modules, string


class HelpMenu(menu.MultiPageMenu):
    def __init__(bot_help, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


class ConfigHelpMenu(menu.NumberedSelectionMenu):
    def __init__(bot_help, ctx):
        pagemap = {
            "header": "Help",
            "title": "Configuration help",
            "description": "Select the module you want to configure.",
            "thumbnail": ctx.bot.get_me().avatar_url,
        }
        super().__init__(
            ctx,
            [ctx.bot.get_plugin(extension.title()).name.lower() for extension in ctx.bot._extensions if ctx.bot.get_plugin(extension.title()).d.configurable is True],
            pagemap,
        )

    async def start(bot_help):
        if (r := await super().start()) is not None:
            await bot_help.display_help(r)

    async def display_help(bot_help, module):
        prefix = await bot_help.bot.prefix(bot_help.ctx.get_guild().id)

        await bot_help.message.remove_all_reactions()
        await bot_help.message.edit(
            embed=bot_help.bot.embed.build(
                ctx=bot_help.ctx,
                header="Help",
                title=f"Configuration help for {module}",
                description=(
                    list(filter(lambda c: bot_help.bot.get_plugin(c.title()).name.lower() == module, bot_help.bot._extensions)).pop().__doc__
                ),
                thumbnail=bot_help.bot.get_me().avatar_url,
                fields=(
                    (
                        (doc := func.__doc__.split("\n", maxsplit=1))[0],
                        f"{doc[1]}\n`{prefix}config {module} {name[len(module)+2:]}`",
                        False,
                    )
                    for name, func in filter(lambda f: module in f[0], modules.config.__dict__.items())
                    if not name.startswith("_")
                ),
            )
        )


bot_help = lightbulb.plugins.Plugin(
    name="Help",
    description="Assistance with using a configuring Solaris.",
    include_datastore=True
)


@bot_help.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    if not bot_help.bot.ready.booted:
        bot_help.bot.ready.up(bot_help)

    bot_help.d.configurable: bool = False
    bot_help.d.image = "https://cdn.discordapp.com/attachments/803218459160608777/925288131811504158/help.png"


async def basic_syntax(ctx, cmd, prefix):
    try:
        await cmd.evaluate_checks(ctx)
        return f"{prefix}{cmd.name}" if cmd.parent is None else f"  ↳ {cmd.name}"
    except lightbulb.errors.CheckFailure:
        return f"{prefix}{cmd.name} (✗)" if cmd.parent is None else f"  ↳ {cmd.name} (✗)"


def full_syntax(ctx, cmd, prefix):
    invokations = "|".join([cmd.name, *cmd.aliases])
    if (p := cmd.parent) is None:
        return f"```{prefix}{invokations} {cmd.signature}```"
    else:
        p_invokations = "|".join([p.name, *p.aliases])
        return f"```{prefix}{p_invokations} {invokations} {cmd.signature}```"


async def required_permissions(ctx, cmd):
    try:
        await cmd.evaluate_checks(ctx)
        return "Yes"
    except lightbulb.errors.MissingRequiredPermission as exc:
        mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
        return f"No - You are missing the {mp} permission(s)"
    except lightbulb.errors.BotMissingRequiredPermission as exc:
        mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
        return f"No - Solaris is missing the {mp} permission(s)"
    #except checks.AuthorCanNotConfigure:
    #    return "No - You are not able to configure Solaris"
    except lightbulb.errors.CommandInvocationError:
        return "No - Solaris is not configured properly"


async def get_command_mapping(bot_help, ctx):
    mapping = defaultdict(list)
    plugins = []

    for extension in bot_help.bot._extensions:
        if (bot_help.bot.get_plugin(extension.title()).d.image) is not None:
            for cmd in bot_help.bot.get_plugin(extension.title()).all_commands:
                if (bot_help.bot.get_plugin(extension.title()).d.image) is not None:
                    try:
                        for i in cmd.subcommands.values():
                            break
                        mapping[extension].append(cmd)
                        for c in cmd.subcommands.values():
                            mapping[extension].append(c)
                    except AttributeError:
                        mapping[extension].append(cmd)

    return mapping


async def get_cooldown(ctx, cmd):
    try:
        await cmd.evaluate_cooldowns(ctx)
        return "No"
    except lightbulb.errors.CommandIsOnCooldown as exc:
        return exc.retry_after


async def convert(ctx, arg):
    try:
        for cmd in ctx.bot.get_prefix_command(arg).subcommands.values():
            if arg == f"{cmd.parent.name} {cmd.name}":
                return cmd
        else:
            if (c := ctx.bot.get_prefix_command(arg)) is not None:
                return c
    except AttributeError:
        if (c := ctx.bot.get_prefix_command(arg)) is not None:
            return c
    else:
        raise hikari.NotFoundError



@bot_help.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="cmd", description="Name of the command to view.", type=str, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST, required=False)
@lightbulb.command(name="help", description="Help with anything Solaris. Passing a command name through will show help with that specific command")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def help_command(ctx: lightbulb.context.base.Context)-> None:
    prefix = await ctx.bot.prefix(ctx.get_guild().id)

    if isinstance(ctx.options.cmd, lightbulb.commands.Command):
        await ctx.respond(f"{ctx.bot.cross} Solaris has no commands or aliases with that name.")

    elif isinstance(ctx.options.cmd, str):
        if ctx.options.cmd == "config":
            await ConfigHelpMenu(ctx).start()
        else:
            cmd = await convert(ctx, ctx.options.cmd)
            await ctx.respond(
                embed=ctx.bot.embed.build(
                    ctx=ctx,
                    header="Help",
                    description=f"{cmd.description}",
                    thumbnail=ctx.bot.get_me().avatar_url,
                    fields=(
                        ("Syntax (<required> • [optional])", full_syntax(ctx, cmd, prefix), False),
                        (
                            "On cooldown?",
                            f"Yes, for {chron.long_delta(dt.timedelta(seconds=s))}."
                            if (s := (await get_cooldown(ctx, cmd)))
                            else "No",
                            False,
                        ),
                        ("Can be run?", (await required_permissions(ctx, cmd)), False),
                        (
                            "Parent",
                            full_syntax(ctx, p, prefix) if (p := cmd.parent) is not None else "None",
                            False,
                        ),
                    ),
                )
            )

    else:
        pagemaps = []

        for extension, cmds in (await get_command_mapping(bot_help, ctx)).items():
            pagemaps.append(
                {
                    "header": "Help",
                    "title": f"The `{ctx.bot.get_plugin(extension.title()).name}` module",
                    "description": f"{ctx.bot.get_plugin(extension.title()).description}\n\nUse `{prefix}help [command]` for more detailed help on a command. You can not run commands with `(✗)` next to them.",
                    #"thumbnail": ctx.bot.get_me().avatar_url,
                    "thumbnail": ctx.bot.get_plugin(extension.title()).d.image,
                    "fields": (
                            (
                            f"{len(cmds)} command(s)",
                            "```{}```".format(
                                "\n".join([await basic_syntax(ctx, cmd, prefix) for cmd in cmds])
                            ),
                            False,
                        ),
                    ),
                }
            )

        await HelpMenu(ctx, pagemaps).start()

            


def load(bot) -> None:
    bot.add_plugin(bot_help)

def unload(bot) -> None:
    bot.remove_plugin(bot_help)
