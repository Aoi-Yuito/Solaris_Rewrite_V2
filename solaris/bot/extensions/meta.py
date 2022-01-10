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

import math
import psutil
import datetime as dt
import typing as t
from os import name
from platform import python_version
from time import time

from solaris.utils import (
    INFO_ICON,
    LOADING_ICON,
    SUCCESS_ICON,
    SUPPORT_GUILD_INVITE_LINK,
    checks,
    chron,
    converters,
    menu,
    string,
)
from solaris.utils.modules import deactivate


def get_emoji_limit(arg):
    return int(((1+(sqrt_5:=math.sqrt(5)))**(n:=arg+2)-(1-sqrt_5)**n)/(2**n*sqrt_5)*50)


def get_bitrate_limit(value):
    if value == 0:
        return 96
    elif value == 1:
        return 128
    elif value == 2:
        return 256
    elif value == 3:
        return 384


def get_filesie_limit(value):
    if value == 0:
        return 8
    elif value == 1:
        return 8
    elif value == 2:
        return 50
    elif value == 3:
        return 100


def get_member(ctx):
    try:
        m = ctx.bot.cache.get_member(ctx.guild_id, ctx.options.target.id)
    except:
        m = None
    if m is not None:
        return m
    else:
        return ctx.options.target


def online_member_counter(member):
    try:
        if member.visible_status == hikari.Status.ONLINE:
            return True
    except AttributeError:
        return False


def idle_member_counter(member):
    try:
        if member.visible_status == hikari.Status.IDLE:
            return True
    except AttributeError:
        return False


def dnd_member_counter(member):
    try:
        if member.visible_status == hikari.Status.DO_NOT_DISTURB:
            return True
    except AttributeError:
        return False


def offline_member_counter(member):
    try:
        if member.visible_status == hikari.Status.ONLINE:
            return False
    except AttributeError:
        return True


def activity_type_checker(ctx, user):
    try:
        return str(ctx.bot.cache.get_presence(ctx.guild_id, user.id).activities[0].type)
    except AttributeError:
        return "-"


def activity_state_checker(ctx, user):
    try:
        return str(ctx.bot.cache.get_presence(ctx.guild_id, user.id).activities[0].state)
    except AttributeError:
        return "-"


def category_channel_counter(ctx, channel):
    if ctx.bot.cache.get_guild_channel(channel).type == hikari.ChannelType.GUILD_CATEGORY:
        return True
    else:
        return False


def text_channel_counter(channel):
    if isinstance(channel, hikari.GuildTextChannel):
        return True
    else:
        return False


def voice_channel_counter(channel):
    if isinstance(channel, hikari.GuildVoiceChannel):
        return True
    else:
        return False


def stage_channel_counter(channel):
    if isinstance(channel, hikari.GuildStageChannel):
        return True
    else:
        return False


def news_channel_counter(channel):
    if isinstance(channel, hikari.GuildNewsChannel):
        return True
    else:
        return False


def store_channel_counter(channel):
    if isinstance(channel, hikari.GuildStoreChannel):
        return True
    else:
        False


def channel_access_checker(ctx, channel, user):
    perm = lightbulb.utils.permissions_in(
        channel,
        ctx.bot.cache.get_member(
            ctx.get_guild().id,
            user
        ),
        True
    )

    if perm.VIEW_CHANNEL:
        return True
    else:
        return False


def same_role_checker(ctx, role, guild, member):
    m = ctx.bot.cache.get_member(guild, member)
    if role in m.role_ids:
        return True
    else:
        False


def all_channel_under_category(ctx, channel, category_id):
    channel = ctx.bot.cache.get_guild_channel(channel)
    if channel.parent_id == category_id:
        return True
    else:
        False


def all_text_channel_under_category(ctx, channel, category_id):
    channel = ctx.bot.cache.get_guild_channel(channel)
    if isinstance(channel, hikari.GuildTextChannel):
        if channel.parent_id == category_id:
            return True
    else:
        return False


def all_news_channel_under_category(ctx, channel, category_id):
    channel = ctx.bot.cache.get_guild_channel(channel)
    if isinstance(channel, hikari.GuildNewsChannel):
        if channel.parent_id == category_id:
            return True
    else:
        return False


def all_store_channel_under_category(ctx, channel, category_id):
    channel = ctx.bot.cache.get_guild_channel(channel)
    if isinstance(channel, hikari.GuildStoreChannel):
        if channel.parent_id == category_id:
            return True
    else:
        return False


def all_voice_channel_under_category(ctx, channel, category_id):
    channel = ctx.bot.cache.get_guild_channel(channel)
    if isinstance(channel, hikari.GuildVoiceChannel):
        if channel.parent_id == category_id:
            return True
    else:
        return False


def all_stage_channel_under_category(ctx, channel, category_id):
    channel = ctx.bot.cache.get_guild_channel(channel)
    if isinstance(channel, hikari.GuildStageChannel):
        if channel.parent_id == category_id:
            return True
    else:
        return False


class DetailedServerInfoMenu(menu.MultiPageMenu):
    def __init__(meta, ctx, table):
        pagemaps = []
        base_pm = {
            "header": "Information",
            "title": f"Detailed server information for {ctx.get_guild().name}",
            "thumbnail": ctx.get_guild().icon_url,
        }

        for key, value in table.items():
            pm = base_pm.copy()
            pm.update({"description": f"Showing {key} information.", "fields": value})
            pagemaps.append(pm)

        super().__init__(ctx, pagemaps, timeout=120.0)


class LeavingMenu(menu.SelectionMenu):
    def __init__(meta, ctx):
        pagemap = {
            "header": "Leave Wizard",
            "title": "Leaving already?",
            "description": (
                "If you remove Solaris from your server, all server information Solaris has stored, as well as any roles and channels Solaris has created, will be deleted."
                f"If you are having issues with Solaris, consider joining the support server to try and find a resolution - select {ctx.bot.info} to get an invite link.\n\n"
                "Are you sure you want to remove Solaris from your server?"
            ),
            "thumbnail": ctx.bot.get_me().avatar_url,
        }
        super().__init__(ctx, ["832160810738253834", "832160894079074335", "796345797112365107"], pagemap, timeout=120.0)

    async def start(meta):
        r = await super().start()

        if r == "confirm":
            pagemap = {
                "header": "Leave Wizard",
                "description": "Please wait... This should only take a few seconds.",
                "thumbnail": LOADING_ICON,
            }
            await meta.switch(pagemap, remove_all_reactions=True)
            await meta.leave()
        elif r == "cancel":
            await meta.stop()
        elif r == "info":
            pagemap = {
                "header": "Leave Wizard",
                "title": "Let's get to the bottom of this!",
                "description": f"Click [here]({SUPPORT_GUILD_INVITE_LINK}) to join the support server.",
                "thumbnail": INFO_ICON,
            }
            await meta.switch(pagemap, remove_all_reactions=True)

    async def leave(meta):
        dlc_id, dar_id = (
            await meta.bot.db.record(
                "SELECT DefaultLogChannelID, DefaultAdminRoleID FROM system WHERE GuildID = ?", meta.ctx.get_guild().id
            )
            or [None] * 2
        )

        await deactivate.everything(meta.ctx)

        perm = lightbulb.utils.permissions_for(
            ctx.bot.cache.get_member(
                ctx.get_guild().id,
                841547626772168704
            )
        )

        if perm.MANAGE_ROLES and (dar := meta.ctx.get_guild().get_role(dar_id)) is not None:
            await dar.delete(reason="Solaris is leaving the server.")

        if (
            perm.MANAGE_CHANNELS
            and (dlc := meta.ctx.get_guild().get_channel(dlc_id)) is not None
        ):
            await dlc.delete(reason="Solaris is leaving the server.")

        pagemap = {
            "header": "Leave Wizard",
            "title": "Sorry to see you go!",
            "description": (
                f"If you ever wish to reinvite Solaris, you can do so by clicking [here]({self.bot.admin_invite}) (recommended permissions), or [here]({self.bot.non_admin_invite}) (minimum required permissions).\n\n"
                "The Solaris team wish you and your server all the best."
            ),
        }
        await meta.switch(pagemap)
        await meta.bot.rest.leave_guild(ctx.get_guild().id)


meta = lightbulb.plugins.Plugin(
    name="Meta",
    description="Commands for retrieving information regarding Solaris, from invitation links to detailed bot statistics.",
    include_datastore=True
)


@meta.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    if not meta.bot.ready.booted:
        meta.d.developer = (await meta.bot.rest.fetch_application()).owner
        #meta.d.developer = await meta.bot.grab_user(714022418200657971)
        meta.d.artist = await meta.bot.grab_user(714022418200657971)
        meta.d.testers = [
            (await meta.bot.grab_user(id_))
            for id_ in (
                733297588241170472,
                713882503114653746,
                735125848499421243,
                763794369714454538,
                792606073860128769,
            )
        ]
        meta.d.support_guild = await meta.bot.rest.fetch_guild(774530528623067157)
        meta.d.helper_role = meta.bot.cache.get_role(786614866739068938)

        meta.bot.ready.up(meta)

    meta.d.configurable: bool = False
    meta.d.image = "https://cdn.discordapp.com/attachments/803218459160608777/925288082754908161/meta.png"


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="about", aliases=["credits"], description="View info regarding those behind Solaris' development. This includes the developer and the testers.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def about_command(ctx: lightbulb.context.base.Context):
    prefix = await ctx.bot.prefix(ctx.get_guild().id)
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            title="About Solaris",
            description=f"Use `{prefix}botinfo` for detailed statistics.",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                ("Developer", meta.d.developer.mention, False),
                ("Avatar Designer", meta.d.artist.mention, False),
                ("Testers", string.list_of([t.mention for t in meta.d.testers]), False),
            ),
        )
    )


##############
@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="support", aliases=["sos"], description="Provides an invite link to Solaris' support server.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def support_command(ctx: lightbulb.context.base.Context):
    online = []
    for m in meta.d.support_guild.get_members():
        try:
            if not (ctx.bot.cache.get_member(meta.d.support_guild.id, m)).is_bot:
                if ctx.bot.cache.get_presence(meta.d.support_guild.id, m).visible_status == hikari.Status.ONLINE:
                    online.append(m)
        except AttributeError:
            pass

    #online = [m for m in meta.d.support_guild.get_members() if not (await ctx.bot.grab_user(m)).is_bot and (ctx.bot.cache.get_presence(meta.d.support_guild.id, m)).visible_status == hikari.Status.ONLINE]
    helpers = [
        m for m in meta.d.support_guild.get_members() if not (ctx.bot.cache.get_member(meta.d.support_guild.id, m)).is_bot and (ctx.bot.cache.get_member(meta.d.support_guild.id, m)).get_top_role().position == meta.d.helper_role.position
    ]
    online_helpers = set(online) & set(helpers)

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description=f"Click [here]({SUPPORT_GUILD_INVITE_LINK}) to join the support server.",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                ("Online / members", f"{len(online):,} / {len(meta.d.support_guild.get_members()):,}", True),
                ("Online / helpers", f"{len(online_helpers):,} / {len(helpers):,}", True),
                ("Developer", str(ctx.bot.cache.get_presence(meta.d.support_guild.id, meta.d.developer.id).visible_status).title(), True),
            ),
        )
    )
###############


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="invite", aliases=["join"], description="Provides the links necessary to invite Solaris to other servers.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def invite_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                (
                    "Primary link",
                    f"To invite Solaris with administrator privileges, click [here]({ctx.bot.admin_invite}).",
                    False,
                ),
                (
                    "Secondary",
                    f"To invite Solaris without administrator privileges, click [here]({ctx.bot.non_admin_invite}) (you may need to grant Solaris some extra permissions in order to use some modules).",
                    False,
                ),
                ("Servers", f"{ctx.bot.guild_count:,}", True),
                ("Users", f"{ctx.bot.user_count:,}", True),
                ("Get started", "`>>setup`", True),
            ),
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="source", aliases=["src"], description="Provides a link to Solaris' source code.")
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
@lightbulb.command(name="issue", aliases=["bugreport", "reportbug", "featurerequest", "requestfeature"], description="Provides a link to open an issue on the Solaris repo.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def issue_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description="If you have discovered a bug not already known or want a feature not requested, open an issue using the green button in the top right of the window.",
            thumbnail=ctx.bot.get_me().avatar_url,
            fields=(
                (
                    "View all known bugs",
                    "Click [here](https://github.com/parafoxia/Solaris/issues?q=is%3Aissue+is%3Aopen+label%3Abug).",
                    False,
                ),
                (
                    "View all planned features",
                    "Click [here](https://github.com/parafoxia/Solaris/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement).",
                    False,
                ),
            ),
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="version", description="The version to view.", required=False)
@lightbulb.command(name="changelog", aliases=["release"], description="Provides a link to view the changelog for the given version.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def changelog_command(ctx: lightbulb.context.base.Context):
    url = (
        "https://github.com/parafoxia/Solaris/releases"
        if not ctx.options.version
        else f"https://github.com/parafoxia/Solaris/releases/tag/v{ctx.options.version}"
    )
    version_info = f"version {ctx.options.version}" if ctx.options.version else "all versions"
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description=f"Click [here]({url}) to information on {version_info}.",
            thumbnail=ctx.bot.get_me().avatar_url,
        )
    )


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


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.UserBucket(300, 1))
@lightbulb.command(name="botinfo", aliases=["bi", "botstats", "stats", "bs"], description="Displays statistical information on Solaris.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def botinfo_command(ctx: lightbulb.context.base.Context):
    with (proc := psutil.Process()).oneshot():
        prefix = await ctx.bot.prefix(ctx.get_guild().id)
        uptime = time() - proc.create_time()
        cpu_times = proc.cpu_times()
        total_memory = psutil.virtual_memory().total / (1024 ** 2)
        memory_percent = proc.memory_percent()
        memory_usage = total_memory * (memory_percent / 100)

        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title="Bot information",
                description=f"Solaris was developed by {(await ctx.bot.rest.fetch_application()).owner.mention}. Use `{prefix}about` for more information.",
                thumbnail=ctx.bot.get_me().avatar_url,
                fields=(
                    ("Bot version", f"{ctx.bot.version}", True),
                    ("Python version", f"{python_version()}", True),
                    ("discord.py version", f"{hikari.__version__}", True),
                    ("Uptime", chron.short_delta(dt.timedelta(seconds=uptime)), True),
                    (
                        "CPU time",
                        chron.short_delta(
                            dt.timedelta(seconds=cpu_times.system + cpu_times.user), milliseconds=True
                        ),
                        True,
                    ),
                    (
                        "Memory usage",
                        f"{memory_usage:,.3f} / {total_memory:,.0f} MiB ({memory_percent:.0f}%)",
                        True,
                    ),
                    ("Servers", f"{ctx.bot.guild_count:,}", True),
                    ("Users", f"{ctx.bot.user_count:,}", True),
                    ("Commands", f"{ctx.bot.command_count:,}", True),
                    ("Code", f"{ctx.bot.loc.code:,} lines", True),
                    ("Comments", f"{ctx.bot.loc.docs:,} lines", True),
                    ("Blank", f"{ctx.bot.loc.empty:,} lines", True),
                    (
                        "Database calls since uptime",
                        f"{ctx.bot.db._calls:,} ({ctx.bot.db._calls/uptime:,.3f} per second)",
                        True,
                    ),
                ),
            )
        )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the User to View.", type=hikari.User, required=False)
@lightbulb.command(name="userinfo", aliases=["ui"], description="Displays information on a given user. If no user is provided, Solaris will display your information.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def userinfo_command(ctx: lightbulb.context.base.Context):
    target = get_member(ctx) or ctx.bot.cache.get_member(ctx.guild_id, ctx.author.id)

    if isinstance(target, hikari.Member):
        ps = target.premium_since.replace(tzinfo=None) if target.premium_since is not None else target.premium_since
        ngr = len([r for r in ctx.get_guild().get_roles()])

        perm = lightbulb.utils.permissions_for(
            ctx.bot.cache.get_member(
                ctx.get_guild().id,
                target.id
            )
        )

        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"User information for {target.username}",
                description=(
                    f"This member is also known as {target.display_name} in this server."
                    if target.nickname
                    else f"This member does not have a nickname in this server."
                ),
                colour=target.get_top_role().color,
                thumbnail=target.avatar_url,
                fields=(
                    ("ID", target.id, False),
                    ("Discriminator", target.discriminator, True),
                    ("Bot?", target.is_bot, True),
                    ("Admin?", "True" if perm.ADMINISTRATOR else "False", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Joined on", chron.long_date(target.joined_at), True),
                    ("Boosted on", chron.long_date(ps) if ps else "-", True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                    ("Member for", chron.short_delta(dt.datetime.utcnow() - target.joined_at.replace(tzinfo=None)), True),
                    ("Booster for", chron.short_delta(dt.datetime.utcnow() - ps) if ps else "-", True),
                    ("Status", str((ctx.bot.cache.get_presence(ctx.get_guild().id, target.id).visible_status)).title() if (ctx.bot.cache.get_presence(ctx.guild_id, target.id)) else "offline", True),
                    (
                        "Activity type",
                        activity_type_checker(ctx, target),
                        True,
                    ),
                    ("Activity State", activity_state_checker(ctx, target), True),
                    ("Nº of roles", f"{len([r for r in target.get_roles()])-1:,}", True),
                    ("Top role", target.get_top_role().mention, True),
                    ("Top role position", f"{string.ordinal(ngr - target.get_top_role().position)} / {ngr:,}", True),
                ),
            )
        )


    elif isinstance(target, hikari.User):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"User information for {target.username}",
                description="Showing reduced information as the given user is not in this server.",
                thumbnail=target.avatar_url,
                fields=(
                    ("ID", target.id, True),
                    ("Discriminator", target.discriminator, True),
                    ("Bot?", target.is_bot, True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                    ("\u200b", "\u200b", True),
                ),
            )
        )

    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a user with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="serverinfo", aliases=["si", "guildinfo", "gi"], description="Displays information on your server.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def serverinfo_command(ctx: lightbulb.context.base.Context):
    guild = ctx.get_guild()
    guild_owner = ctx.bot.cache.get_member(guild.id, guild.owner_id)

    perm = lightbulb.utils.permissions_for(
        ctx.bot.cache.get_member(
            guild.id,
            841547626772168704
        )
    )

    bot_count = len([m for m in guild.get_members() if ctx.bot.cache.get_member(guild.id, m).is_bot])
    human_count = guild.member_count - bot_count

    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            title=f"Server information for {guild.name}",
            thumbnail=guild.icon_url,
            colour=guild_owner.get_top_role().colour,
            fields=(
                ("ID", guild.id, False),
                ("Owner", guild_owner.mention, True),
                ("Region", guild.preferred_locale, True),
                ("Top role", ctx.bot.cache.get_role([r for r in guild.get_roles()][1]).mention, True),
                ("Members", f"{guild.member_count:,}", True),
                ("Humans / bots", f"{human_count:,} / {bot_count:,}", True),
                (
                    "Bans",
                    f"{len(await ctx.bot.rest.fetch_bans(guild.id)):,}" if perm.BAN_MEMBERS else "-",
                    True,
                ),
                ("Roles", f"{len([r for r in guild.get_roles()])-1:,}", True),
                ("Text channels", f"{len([c for c in guild.get_channels() if text_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                ("Voice channels", f"{len([c for c in guild.get_channels() if voice_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                ("Stage channels", f"{len([c for c in guild.get_channels() if stage_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                ("News channels", f"{len([c for c in guild.get_channels() if news_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                ("Store channels", f"{len([c for c in guild.get_channels() if store_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                (
                    "Invites",
                    f"{len(await ctx.bot.rest.fetch_guild_invites(guild.id)):,}" if perm.MANAGE_GUILD else "-",
                    True,
                ),
                ("Emojis", f"{len(guild.get_emojis()):,} / {get_emoji_limit(guild.premium_tier.value)*2:,}", True),
                ("Boosts", f"{guild.premium_subscription_count:,} (level {guild.premium_tier.value})", True),
                ("Newest member", ctx.bot.cache.get_member(guild.id, max(guild.get_members(), key=lambda m: ctx.bot.cache.get_member(guild.id, m).joined_at)).mention, True),
                ("Created on", chron.long_date(guild.created_at), True),
                ("Existed for", chron.short_delta(dt.datetime.utcnow() - guild.created_at.replace(tzinfo=None)), True),
                (
                    "Statuses",
                    (
                        f"🟢 {len([m for m in guild.get_members() if online_member_counter(ctx.bot.cache.get_presence(guild.id, m)) is True]):,} "
                        f"🟠 {len([m for m in guild.get_members() if idle_member_counter(ctx.bot.cache.get_presence(guild.id, m)) is True]):,} "
                        f"🔴 {len([m for m in guild.get_members() if dnd_member_counter(ctx.bot.cache.get_presence(guild.id, m)) is True]):,} "
                        f"⚪ {len([m for m in guild.get_members() if offline_member_counter(ctx.bot.cache.get_presence(guild.id, m)) is True]):,}"
                    ),
                    False,
                ),
            ),
        )
    )

@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the channel to View.", type=hikari.GuildChannel, required=False)
@lightbulb.command(name="channelinfo", aliases=["ci"], description="Displays information on a given channel.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def channelinfo_command(ctx: lightbulb.context.base.Context):
    guild = ctx.get_guild()
    target = ctx.options.target or ctx.get_channel()

    perm = lightbulb.utils.permissions_for(
        ctx.bot.cache.get_member(
            guild.id,
            841547626772168704
        )
    )

    if isinstance(target, hikari.GuildTextChannel):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Channel information for {target.name}",
                description="This channel is a text channel.",
                thumbnail=guild.icon_url,
                fields=(
                    ("ID", target.id, False),
                    ("NSFW?", "True" if target.is_nsfw is True else "False", True),
                    ("News?", isinstance(target, hikari.GuildNewsChannel), True),
                    ("Type", target.type, True),
                    ("Category", (ctx.bot.cache.get_guild_channel(target.parent_id)).name, True),
                    ("Position", f"{string.ordinal(target.position+1)} / {len([c for c in guild.get_channels()]):,}", True),
                    ("Allowed members", f"{len([m for m in guild.get_members() if channel_access_checker(ctx, target, m) is True]):,}", True),
                    ("Overwrites", f"{len(target.permission_overwrites)}", True),
                    (
                        "Invites",
                        f"{len([i for i in ctx.bot.cache.get_invites_view_for_channel(guild.id, target.id)]):,}" if perm.MANAGE_GUILD else "-",
                        True,
                    ),
                    ("Pins", f"{len(await target.fetch_pins())}", True),
                    ("Slowmode delay", target.rate_limit_per_user, True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                    ("Topic", "-" if target.topic is None else target.topic, False),
                ),
            )
        )

    elif isinstance(target, hikari.GuildNewsChannel):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Channel information for {target.name}",
                description="This channel is a news channel.",
                thumbnail=guild.icon_url,
                fields=(
                    ("ID", target.id, False),
                    ("NSFW?", "True" if target.is_nsfw is True else "False", True),
                    ("News?", isinstance(target, hikari.GuildNewsChannel), True),
                    ("Type", target.type, True),
                    ("Category", (ctx.bot.cache.get_guild_channel(target.parent_id)).name, True),
                    ("Position", f"{string.ordinal(target.position+1)} / {len([c for c in guild.get_channels()]):,}", True),
                    ("Allowed members", f"{len([m for m in guild.get_members() if channel_access_checker(ctx, target, m) is True]):,}", True),
                    ("Overwrites", f"{len(target.permission_overwrites)}", True),
                    (
                        "Invites",
                        f"{len([i for i in ctx.bot.cache.get_invites_view_for_channel(guild.id, target.id)]):,}" if perm.MANAGE_GUILD else "-",
                        True,
                    ),
                    ("Pins", f"{len(await target.fetch_pins())}", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                    ("Topic", "-" if target.topic is None else target.topic, False),
                ),
            )
        )

    elif isinstance(target, hikari.GuildStoreChannel):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Channel information for {target.name}",
                description="This channel is a store channel.",
                thumbnail=guild.icon_url,
                fields=(
                    ("ID", target.id, False),
                    ("NSFW?", "True" if target.is_nsfw is True else "False", True),
                    ("Type", target.type, True),
                    ("Category", (ctx.bot.cache.get_guild_channel(target.parent_id)).name, True),
                    ("Position", f"{string.ordinal(target.position+1)} / {len([c for c in guild.get_channels()]):,}", True),
                    ("Allowed members", f"{len([m for m in guild.get_members() if channel_access_checker(ctx, target, m) is True]):,}", True),
                    ("Overwrites", f"{len(target.permission_overwrites)}", True),
                    (
                        "Invites",
                        f"{len([i for i in ctx.bot.cache.get_invites_view_for_channel(guild.id, target.id)]):,}" if perm.MANAGE_GUILD else "-",
                        True,
                    ),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                ),
            )
        )

    elif isinstance(target, hikari.GuildVoiceChannel):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Channel information for {target.name}",
                description="This channel is a voice channel.",
                thumbnail=guild.icon_url,
                fields=(
                    ("ID", target.id, False),
                    ("Type", target.type, True),
                    ("Region", "-" if target.region is None else target.region, True),
                    ("Category", (ctx.bot.cache.get_guild_channel(target.parent_id)).name, True),
                    ("Bitrate", f"{target.bitrate//1000:,.0f} kbps", True),
                    ("User Limit", f"{target.user_limit:,}", True),
                    ("Video Quality Mode", target.video_quality_mode, True),
                    ("Position", f"{string.ordinal(target.position+1)} / {len([c for c in guild.get_channels() if voice_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                    ("Overwrites", f"{len(target.permission_overwrites)}", True),
                    (
                        "Invites",
                        f"{len([i for i in ctx.bot.cache.get_invites_view_for_channel(guild.id, target.id)]):,}" if perm.MANAGE_GUILD else "-",
                        True,
                    ),
                    ("Members joined", f"{len([m for m in ctx.bot.cache.get_voice_states_view_for_channel(guild.id, target.id)]):,} / {target.user_limit or '∞'}", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                ),
            )
        )

    elif isinstance(target, hikari.GuildStageChannel):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Channel information for {target.name}",
                description="This channel is a stage channel.",
                thumbnail=guild.icon_url,
                fields=(
                    ("ID", target.id, False),
                    ("Type", target.type, True),
                    ("Region", target.region, True),
                    ("Category", (ctx.bot.cache.get_guild_channel(target.parent_id)).name, True),
                    ("Bitrate", f"{target.bitrate//1000:,.0f} kbps", True),
                    ("User Limit", f"{target.user_limit:,}", True),
                    ("Position", f"{string.ordinal(target.position+1)} / {len([c for c in guild.get_channels() if voice_channel_counter(ctx.bot.cache.get_guild_channel(c)) is True]):,}", True),
                    ("Overwrites", f"{len(target.permission_overwrites)}", True),
                    (
                        "Invites",
                        f"{len([i for i in ctx.bot.cache.get_invites_view_for_channel(guild.id, target.id)]):,}" if perm.MANAGE_GUILD else "-",
                        True,
                    ),
                    ("Members joined", f"{len([m for m in ctx.bot.cache.get_voice_states_view_for_channel(guild.id, target.id)]):,} / {target.user_limit or '∞'}", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                ),
            )
        )

    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a channel with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the category to View.", type=hikari.GuildCategory, required=False)
@lightbulb.command(name="categoryinfo", aliases=["cti"], description="Displays information on a given category.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def categoryinfo_command(ctx: lightbulb.context.base.Context):
    guild = ctx.get_guild()
    target = ctx.options.target or ctx.bot.cache.get_guild_channel(ctx.get_channel().parent_id)
    all_channels = ctx.bot.cache.get_guild_channels_view_for_guild(guild.id)

    if isinstance(target, hikari.GuildCategory):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Category information for {target.name}",
                thumbnail=guild.icon_url,
                fields=(
                    ("ID", target.id, False),
                    ("NSFW?", "True" if target.is_nsfw is True else "False", True),
                    ("Type", target.type, True),
                    ("Position", f"{string.ordinal(target.position+1)} / {len([c for c in ctx.bot.cache.get_guild_channels_view_for_guild(guild.id) if category_channel_counter(ctx, c) is True]):,}", True),
                    ("All Channels", f"{len([c for c in all_channels if all_channel_under_category(ctx, c, target.id) is True]):,} / {len([ac for ac in guild.get_channels()]):,}", True),
                    ("Text Channels", f"{len([tc for tc in all_channels if all_text_channel_under_category(ctx, tc, target.id) is True]):,}", True),
                    ("News Channels", f"{len([tc for tc in all_channels if all_news_channel_under_category(ctx, tc, target.id) is True]):,}", True),
                    ("Store Channels", f"{len([tc for tc in all_channels if all_store_channel_under_category(ctx, tc, target.id) is True]):,}", True),
                    ("Voice Channels", f"{len([vc for vc in all_channels if all_voice_channel_under_category(ctx, vc, target.id) is True]):,}", True),
                    ("Stage Channels", f"{len([tc for tc in all_channels if all_stage_channel_under_category(ctx, tc, target.id) is True]):,}", True),
                    ("Overwrites", f"{len(target.permission_overwrites)}", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                ),
            )
        )

    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a category with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the role to View.", type=hikari.Role, required=False)
@lightbulb.command(name="roleinfo", aliases=["ri"], description="Displays information on a given role.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def roleinfo_command(ctx: lightbulb.context.base.Context):
    guild = ctx.get_guild()
    target = ctx.options.target or ctx.author.get_top_role()

    if isinstance(target, hikari.Role):
        ngr = len(guild.get_roles())

        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Role information for {target.name}",
                description=f"You currently{' ' if target.id in ctx.bot.cache.get_member(guild.id, ctx.author.id).role_ids else ' do not '}have this role.",
                thumbnail=guild.icon_url,
                colour=target.colour,
                fields=(
                    ("ID", target.id, False),
                    ("Hoisted?", target.is_hoisted, True),
                    ("Assignable?", not target.is_managed, True),
                    ("Mentionable?", target.is_mentionable, True),
                    ("Admin?", "True" if target.permissions.ADMINISTRATOR else "False", True),
                    ("Premium?", target.is_premium_subscriber_role, True),
                    ("Position", f"{string.ordinal(ngr - target.position)} / {ngr:,}", True),
                    ("Colour", f"{str(target.colour)}", True),
                    ("Unicode Emoji", "-" if target.unicode_emoji is None else  target.unicode_emoji, True),
                    ("Members", f"{len([m for m in guild.get_members() if same_role_checker(ctx, target.id, guild.id, m) is True]):,}", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                ),
            )
        )

    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a role with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the message to View.", type=hikari.Message, required=True)
@lightbulb.command(name="messageinfo", aliases=["mi"], description="Displays information on a given message.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def messageinfo_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target

    if isinstance(target, hikari.Message):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Message information",
                description=f"You can see the original message [here]({target.make_link(ctx.get_guild().id)}).",
                thumbnail=target.author.avatar_url,
                colour=ctx.bot.cache.get_member(ctx.get_guild().id, target.author.id).get_top_role().colour,
                fields=(
                    ("ID", target.id, False),
                    ("TTS?", str(target.is_tts), True),
                    ("Embedded?", bool(target.embeds), True),
                    ("Pinned?", str(target.is_pinned), True),
                    ("Author", target.author.mention, True),
                    ("Channel", ctx.bot.cache.get_guild_channel(target.channel_id).mention, True),
                    ("Reactions", f"{len([r.count for r in target.reactions]):,}", True),
                    ("Member mentions", f"{len(target.mentions.user_ids):,}", True),
                    ("Role mentions", f"{len(target.mentions.role_ids):,}", True),
                    ("Channels mentions", f"{len([c for c in target.mentions.channels_ids]):,}", True),
                    #("Flags", target.flags, True),
                    #("Components", len([c for c in target.components]), True),
                    #("Type", target.type, True),
                    #("Webhook ID", target.webhook_id, True),
                    ("Attachments", f"{len(target.attachments):,}", True),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                    ("Last edited on", chron.long_date(target.edited_timestamp) if target.edited_timestamp else chron.long_date(target.created_at), True),
                    (
                        "Content",
                        (target.content if len(target.content) <= 1024 else f"{target.content[:1021]}...") or "-",
                        False,
                    ),
                ),
            )
        )

    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a message with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the emoji to View.", type=hikari.Emoji, required=True)
@lightbulb.command(name="emojiinfo", aliases=["ei"], description="Displays information on a given emoji. This only works for custom emoji.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def emojiinfo_command(ctx: lightbulb.context.base.Context):
    perm = lightbulb.utils.permissions_for(
        ctx.bot.cache.get_member(
            ctx.get_guild().id,
            841547626772168704
        )
    )

    if isinstance(ctx.options.target, hikari.Emoji):
        emoji = ctx.options.target.parse(ctx.options.target.mention)
        target = await ctx.bot.rest.fetch_emoji(ctx.get_guild().id, emoji.id)
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                title=f"Emoji information for {target.name}",
                thumbnail=target.url,
                fields=(
                    ("ID", target.id, False),
                    ("Animated?", target.is_animated, True),
                    ("Managed?", target.is_managed, True),
                    ("Available?", target.is_available, True),
                    (
                        "Created by",
                        u.mention if (u := target.user) and perm.MANAGE_EMOJIS_AND_STICKERS is not None else "-",
                        True,
                    ),
                    ("Created on", chron.long_date(target.created_at), True),
                    ("Existed for", chron.short_delta(dt.datetime.utcnow() - target.created_at.replace(tzinfo=None)), True),
                ),
            )
        )

    else:
        await ctx.respond(
            f"{ctx.bot.cross} Solaris was unable to identify an emoji with the information provided. Are you sure it is a custom emoji?"
        )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="detailedserverinfo", aliases=["dsi", "detailedguildinfo", "dgi"], description="Displays more detailed information on your server.")
@lightbulb.add_cooldown(callback=lambda _: lightbulb.GuildBucket(300, 1))
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def detailedserverinfo_command(ctx: lightbulb.context.base.Context):
    guild = ctx.get_guild()
    perm = lightbulb.utils.permissions_for(
        ctx.bot.cache.get_member(
            ctx.get_guild().id,
            841547626772168704
        )
    )

    table = {
        "overview": (
            ("ID", guild.id, False),
            ("Name", guild.name, True),
            ("Region", guild.preferred_locale, True),
            ("Inactive channel", ctx.bot.cache.get_guild_channel(guild.afk_channel_id) if guild.afk_channel_id is not None else "-", True),
            ("Inactive timeout", guild.afk_timeout, True),
            ("System messages channel", ctx.bot.cache.get_guild_channel(guild.system_channel_id).mention if guild.system_channel_id is not None else "-", True),
            ("Send welcome messages?", guild.system_channel_flags, True),
            ("Send boost messages?", guild.system_channel_flags, True),
            (
                "Default notifications",
                "Only @mentions" if guild.default_message_notifications.value else "All Messages",
                True,
            ),
            ("\u200b", "\u200b", True),
        ),
        "moderation": (
            ("Verficiation level", str(guild.verification_level).title(), False),
            (
                "Explicit media content filter",
                str(guild.explicit_content_filter).replace("_", " ").title(),
                False,
            ),
            ("2FA requirement for moderation?", bool(guild.mfa_level), False),
        ),
        "numerical": (
            ("Members", f"{guild.member_count:,}", True),
            ("Humans", f"{(hc := len([m for m in guild.get_members() if not ctx.bot.cache.get_member(guild.id, m).is_bot])):,}", True),
            ("Bots", f"{guild.member_count - hc:,}", True),
            ("Est. prune (1d)", f"{await ctx.bot.rest.estimate_guild_prune_count(guild=guild.id, days=1):,}", True),
            ("Est. prune (7d)", f"{await ctx.bot.rest.estimate_guild_prune_count(guild=guild.id, days=7):,}", True),
            ("Est. prune (30d)", f"{await ctx.bot.rest.estimate_guild_prune_count(guild=guild.id, days=30):,}", True),
            ("Roles", f"{len([r for r in guild.get_roles()]):,}", True),
            (
                "Members with top role",
                f"{len([m for m in guild.get_members() if [r for r in guild.get_roles()][1] in ctx.bot.cache.get_member(guild.id, m).role_ids]):,}",
                True,
            ),
            (
                "Bans",
                f"{len([b for b in await ctx.bot.rest.fetch_bans(guild.id)]) if perm.BAN_MEMBERS else None:,}",
                True,
            ),
            (
                "Invites",
                f"{len([i for i in await ctx.bot.rest.fetch_guild_invites(guild.id)]) if perm.MANAGE_GUILD else None:,}",
                True,
            ),
            (
                "Webhooks",
                f"{len([w for w in await ctx.bot.rest.fetch_guild_webhooks(guild.id)]) if perm.MANAGE_WEBHOOKS else None:,}",
                True,
            ),
            ("Emojis", f"{len([e for e in guild.get_emojis()]):,}", True),
            ("Bitrate limit", f"{get_bitrate_limit(guild.premium_tier.value)} kbps", True),
            ("Filesize limit", f"{get_filesie_limit(guild.premium_tier.value)} MB", True),
            ("Boosts", f"{guild.premium_subscription_count:,}", True),
            ("Boosters", f"{len([m for m in guild.get_members() if ctx.bot.cache.get_member(guild.id, m).premium_since is not None]):,}", True),
            ("\u200b", "\u200b", True),
            ("\u200b", "\u200b", True),
        ),
        # "miscellaneous": [
        # ]
    }

    await DetailedServerInfoMenu(ctx, table).start()


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.option(name="target", description="Target the user to View.", type=hikari.User, required=False)
@lightbulb.command(name="avatar", aliases=["profile", "pfp", "av"], description="Displays the avatar (profile picture) of a given user.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def avatar_command(ctx: lightbulb.context.base.Context):
    target = ctx.options.target or ctx.author

    if isinstance(target, hikari.Member) or isinstance(target, hikari.User):
        await ctx.respond(
            embed=ctx.bot.embed.build(
                ctx=ctx,
                header="Information",
                description=f"Displaying avatar for {target.username}.",
                image=target.avatar_url,
            )
        )
    else:
        await ctx.respond(f"{ctx.bot.cross} Solaris was unable to identify a user with the information provided.")


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="icon", description="Displays the icon of your server.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def icon_command(ctx: lightbulb.context.base.Context):
    await ctx.respond(
        embed=ctx.bot.embed.build(
            ctx=ctx,
            header="Information",
            description=f"Displaying icon for {ctx.get_guild().name}.",
            image=ctx.get_guild().icon_url,
        )
    )


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.command(name="leave", description="Utility to make Solaris clean up before leaving the server.")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
#@checks.author_can_configure()
async def leave_command(ctx: lightbulb.context.base.Context):
    await LeavingMenu(ctx).start()


@meta.command()
@lightbulb.add_checks(lightbulb.guild_only)
@lightbulb.add_cooldown(callback=lambda _: lightbulb.UserBucket(10, 1))
@lightbulb.command(name="h", description="get help text")
@lightbulb.implements(commands.prefix.PrefixCommand, commands.slash.SlashCommand)
async def h_command(ctx: lightbulb.context.base.Context):
    #perm = lightbulb.utils.permissions_for(
    #    ctx.bot.cache.get_member(
    #        ctx.get_guild().id,
    #        841547626772168704
    #    )
    #)
    #print(perm)
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
    #await ctx.respond(ctx.get_guild().id)
    #l = [m for m in ctx.get_guild().get_members()]
    #await ctx.respond(l)
    await ctx.respond(ctx.bot.cache.get_presence(ctx.get_guild().id, ctx.author.id).activities)
    await ctx.respond(ctx.bot.cache.get_presence(ctx.get_guild().id, ctx.author.id).activities[0].name)
    await ctx.respond(ctx.bot.cache.get_presence(ctx.get_guild().id, ctx.author.id).activities[0].type)
    await ctx.respond(ctx.bot.cache.get_presence(ctx.get_guild().id, ctx.author.id).activities[0].state)
    #p = []
    #for m in ctx.get_guild().get_members():
    #    p.append(ctx.bot.cache.get_presence(ctx.get_guild().id, m))
    #await ctx.respond(p)
    #r = []
    #for m in ctx.get_guild().get_members():
    #    r.append(ctx.bot.cache.get_member(ctx.get_guild().id, m).get_top_role().position)
    #await ctx.respond(r)



def load(bot):
    bot.add_plugin(meta)

def unload(bot):
    bot.remove_plugin(meta)
