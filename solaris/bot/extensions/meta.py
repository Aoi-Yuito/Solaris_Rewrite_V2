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

from time import time
from solaris.utils import checks


meta = lightbulb.plugins.Plugin(
    name="Meta",
    description="Commands for retrieving information regarding Solaris, from invitation links to detailed bot statistics.",
    include_datastore=True
)


@meta.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not meta.bot.ready.booted:
        meta.bot.ready.up(meta)

    meta.d.configurable: bool = False


#@checks.bot_has_booted()
#@checks.bot_is_ready()
@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="ping", description="Ping Command")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def ping_command(ctx: lightbulb.context.base.Context):
    lat = meta.bot.heartbeat_latency * 1_000
    s = time()
    pm = await ctx.respond(f"{meta.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: - ms.")
    e = time()
    await pm.edit(
        content=f"{meta.bot.info} Pong! DWSP latency: {lat:,.0f} ms. Response time: {(e-s)*1_000:,.0f} ms."
    )


#@checks.bot_has_booted()
#@checks.bot_is_ready()
@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="source", aliases=["src"], description="Source")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def source_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                (
                    "Available under the GPLv3 license",
                    "Click [here](https://github.com/parafoxia/Solaris) to view.",
                    False,
                ),
            ),
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="h", description="get help text")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def h_command(ctx: lightbulb.context.base.Context):
    """get help text"""
        #await ctx.send_help(ctx.command)  
        #help_text = lightbulb.get_help_text(self.h_command)
        #await ctx.respond(help_text)
        
        #from bluebrain.utils.modules import retrieve
        #await ctx.respond((await retrieve.log_channel(ctx.bot, ctx.get_guild().id)))
        
        #bot = await self.bot.rest.fetch_member(ctx.get_guild().id, 841547626772168704)
        #perm = lightbulb.utils.permissions_for(bot)
        #print(perm.ADMINISTRATOR)

        #async with ctx.get_channel().trigger_typing():
        #    msg = await ctx.respond("test")
        #    emoji = []
        #    emoji.append(ctx.bot.cache.get_emoji(832160810738253834))
        #    emoji.append(ctx.bot.cache.get_emoji(832160894079074335))   
        #    for em in emoji:
        #await msg.add_reaction(em)

        #perm = lightbulb.utils.permissions_in(
        #    ctx.get_channel(),
        #    await ctx.bot.rest.fetch_member(
        #        ctx.get_guild().id,
        #        841547626772168704
        #    ),
        #    True
        #)
        #if not perm:
        #    print(perm.SEND_MESSAGES)

        #perm = lightbulb.utils.permissions_for(
        #    await ctx.bot.rest.fetch_member(
        #        ctx.get_guild().id,
        #        841547626772168704
        #    )
        #)
        #print(perm)
        #for ext in self.bot._extensions:
        #    await ctx.respond(self.bot.get_plugin(ext.title()))
    await ctx.respond(ctx.get_guild().id)



def load(bot):
    bot.add_plugin(meta)

def unload(bot):
    bot.remove_plugin(meta)
