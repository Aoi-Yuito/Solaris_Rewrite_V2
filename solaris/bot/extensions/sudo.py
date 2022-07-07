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

import io
import os
import textwrap
import traceback
from time import time
from datetime import datetime
from contextlib import redirect_stdout

import hikari
import lightbulb
from lightbulb import commands

from solaris.utils import DEFAULT_EMBED_COLOUR


def clean_code(code):
    if code.startswith('```') and code.endswith('```'):
        return '\n'.join(code.split('\n')[1:-1])
    return code.strip('`\n')


sudo = lightbulb.plugins.Plugin(
    name="Sudo",
    description=None,
    include_datastore=True
)


@sudo.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    if not sudo.bot.ready.booted:
        sudo.bot.ready.up(sudo)

    sudo.d.configurable: bool = False
    sudo.d.image = None


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option(name="extension", description="Name of the ext to load.", type=str)
@lightbulb.command(name="load", aliases=["lext"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def load_extension(ctx: lightbulb.context.base.Context) -> None:
    try:
        ctx.bot.load_extensions(f"solaris.bot.extensions.{ctx.options.extension}")
        await ctx.respond(f"{ctx.bot.tick} `{ctx.options.extension}` loaded successfully.")
    except Exception:
        await ctx.respond(f"```py\n{traceback.format_exc()}\n```")
        await ctx.respond(f"{ctx.bot.cross} couldn't load the specified extension.")


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option(name="extension", description="Name of the ext to unload.", type=str)
@lightbulb.command(name="unload", aliases=["ulext"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def unload_extension(ctx: lightbulb.context.base.Context) -> None:
    try:
        ctx.bot.unload_extensions(f"solaris.bot.extensions.{ctx.options.extension}")
        await ctx.respond(f"{ctx.bot.tick} `{ctx.options.extension}` unloaded successfully.")
    except Exception:
        await ctx.respond(f"```py\n{traceback.format_exc()}\n```")
        await ctx.respond(f"{ctx.bot.cross} couldn't unloaded the specified extension.")


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option(name="extension", description="Name of the ext to reload.", type=str)
@lightbulb.command(name="reload", aliases=["rlext"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def reload_extension(ctx: lightbulb.context.base.Context) -> None:
    try:
        ctx.bot.reload_extensions(f'solaris.bot.extensions.{ctx.options.extension}')
        await ctx.respond(f"{ctx.bot.tick} `{ctx.options.extension}` reloaded successfully.")
    except Exception:
        await ctx.respond(f'```py\n{traceback.format_exc()}\n```')
        await ctx.respond(f"{ctx.bot.cross} couldn't reloaded the specified extension.")


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command(name="bot_restart", aliases=["rst"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def bot_restart_command(ctx: lightbulb.context.base.Context) -> None:
    await ctx.bot.close()
    os.system("python -m solaris")


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command(name="shutdown", aliases=["sd"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def shutdown_command(ctx: lightbulb.context.base.Context) -> None:
    await ctx.bot.close()


@sudo.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option(name="code", description="The Code to execute.", type=str, modifier=lightbulb.commands.base.OptionModifier.CONSUME_REST)
@lightbulb.command(name="eval", aliases=["ev"], description=None, hidden=True)
@lightbulb.implements(commands.prefix.PrefixCommand)
async def eval_command(ctx: lightbulb.context.base.Context) -> None:
    s = time()
    
    env = {
        'ctx': ctx,
        'bot': ctx.bot,
        'guild': ctx.get_guild(),
        'channel': ctx.get_channel(),
        'author': ctx.author,
        #'message': ctx.get_message(),
        '_': sudo.d.last_eval_result
    }
    env.update(globals())

    code = clean_code(ctx.options.code)
    buffer = io.StringIO()

    to_compile = f'async def foo():\n{textwrap.indent(code, " ")}'

    try:
        exec(to_compile, env)

    except Exception as e:
        
        embed = hikari.Embed(
            title="Compilation Results",
            description=f"**Program Output**\n```py\n{e.__class__.__name__}: {e}\n```",
            colour=DEFAULT_EMBED_COLOUR,
            timestamp=datetime.now().astimezone()
        )
        embed.set_thumbnail(
            "https://cdn.discordapp.com/attachments/991572493267636275/991590206258040872/python_logo.png"
        )
        embed.set_footer(
            text=f"Invoked by {ctx.author.username}",
            icon=ctx.author.avatar_url
        )
        return await ctx.respond(embed=embed)

    foo = env['foo']
    try:
        with redirect_stdout(buffer):
            ret = await foo()
    except Exception:
        value = buffer.getvalue()

        embed = hikari.Embed(
            title="Compilation Results",
            description=f"**Program Output**\n```py\n{value}{traceback.format_exc()}\n```",
            colour=DEFAULT_EMBED_COLOUR,
            timestamp=datetime.now().astimezone()
        )
        embed.set_thumbnail(
            "https://cdn.discordapp.com/attachments/991572493267636275/991590206258040872/python_logo.png"
        )
        embed.set_footer(
            text=f"Invoked by {ctx.author.username}",
            icon=ctx.author.avatar_url
        )
        await ctx.respond(embed=embed)
        
    else:
        value = buffer.getvalue()

        if ret is None:
            if value is not None:
                e = time()
                exc_time = f"{(e-s)*1_000:,.0f}"
                
                embed = hikari.Embed(
                    title="Compilation Results",
                    description=f"**Program Output**\n```py\n{value}\n```\n**Execution Time**\n*{exc_time} ms*",
                    colour=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.now().astimezone()
                )
                embed.set_thumbnail(
                    "https://cdn.discordapp.com/attachments/991572493267636275/991590206258040872/python_logo.png"
                )
                embed.set_footer(
                    text=f"Invoked by {ctx.author.username}",
                    icon=ctx.author.avatar_url
                )
                await ctx.respond(embed=embed)
                
            else:
                e = time()
                exc_time = f"{(e-s)*1_000:,.0f}"
                sudo.d.last_result = ret
                
                embed = hikari.Embed(
                    title="Compilation Results",
                    description=f"**Program Output**\n```py\n{value}{ret}\n```\n**Execution Time**\n*{exc_time} ms*",
                    colour=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.now().astimezone()
                )
                embed.set_thumbnail(
                    "https://cdn.discordapp.com/attachments/991572493267636275/991590206258040872/python_logo.png"
                )
                embed.set_footer(
                    text=f"Invoked by {ctx.author.username}",
                    icon=ctx.author.avatar_url
                )
                await ctx.respond(embed=embed)


def load(bot) -> None:
    bot.add_plugin(sudo)

def unload(bot) -> None:
    bot.remove_plugin(sudo)
