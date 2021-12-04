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

from solaris.utils import Search

import datetime
from operator import attrgetter
from typing import (
    Protocol, 
    Callable,
    TypeVar, 
    Iterable, 
    Optional, 
    Any, 
    SupportsInt,
    TYPE_CHECKING, 
    Union
)

#if TYPE_CHECKING:
#    import datetime
SupportsIntCast = Union[SupportsInt, str, bytes, bytearray]


DISCORD_EPOCH = 1420070400000
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)

class EqualityComparable:
    __slots__ = ()

    id: int

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id

    def __ne__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.id != self.id
        return True

class Hashable(EqualityComparable):
    __slots__ = ()

    def __hash__(self) -> int:
        return self.id >> 22

class Converter(Protocol[T_co]):

    async def convert(self, ctx: lightbulb.context.base.Context, argument: str) -> T_co:
        
        raise NotImplementedError('Derived classes need to implement this.')


def snowflake_time(id: int) -> datetime.datetime:
    timestamp = ((id >> 22) + DISCORD_EPOCH) / 1000
    return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)


class Object(Hashable):

    def __init__(self, id: SupportsIntCast):
        try:
            id = int(id)
        except ValueError:
            raise TypeError(f'id parameter must be convertable to int not {id.__class__!r}') from None
        else:
            self.id = id

    def __repr__(self) -> str:
        return f'<Object id={self.id!r}>'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the snowflake's creation time in UTC."""
        return snowflake_time(self.id)


def find(predicate: Callable[[T], Any], seq: Iterable[T]) -> Optional[T]:

    for element in seq:
        if predicate(element):
            return element
    return None

    
def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]:

    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace('__', '.'))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [(attrget(attr.replace('__', '.')), value) for attr, value in attrs.items()]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None



class User(Converter):
    async def convert(self, ctx, arg):
        if (user := await ctx.bot.grab_user(arg)) is None:
            raise hikari.NotFoundError
        return user


class Text_Channel(Converter):
    async def convert(self, ctx, arg):
        if (channel := await ctx.bot.grab_channel(arg)) is None:
            raise hikari.NotFoundError
        return channel


class Voice_Channel(Converter):
    async def convert(self, ctx, arg):
        if (channel := await ctx.bot.grab_channel(arg)) is None:
            raise hikari.NotFoundError
        return channel


class Guild(Converter):
    async def convert(self, ctx, arg):
        if (guild := await ctx.bot.grab_guild(arg)) is None:
            raise hikari.NotFoundError
        return guild


class Command(Converter):
    async def convert(self, ctx, arg):
        if (c := ctx.bot.get_command(arg)) is not None:
            return c
        else:
            # Check for subcommands.
            for cmd in ctx.bot.walk_commands():
                if arg == f"{cmd.parent.name} {cmd.name}":
                    return cmd
        raise hikari.NotFoundError


class SearchedMember(Converter):
    async def convert(self, ctx, arg):
        obj_list = []

        for m in ctx.get_guild().get_members():
            obj_list.append((await ctx.bot.rest.fetch_user(m)))

        async def grab_object(x):
            person = await ctx.bot.rest.fetch_user(x)
            return person.username

        if (
            member := get(
                obj_list,
                username=str(Search(arg, [(await grab_object(m)) for m in ctx.get_guild().get_members()]).best(min_accuracy=0.75)),
            )
        ) is None:
            raise hikari.NotFoundError


class BannedUser(Converter):
    async def convert(self, ctx, arg):
        if ctx.guild.me.guild_permissions.ban_members:
            if arg.isdigit():
                try:
                    return (await ctx.bot.rest.fetch_ban(guild=ctx.guild, user=Object(id=int(arg)))).user
                except hikari.NotFoundError:
                    raise hikari.BadRequestError

            banned = [e.user for e in await ctx.guild.bans()]
            if banned:
                if (user := find(lambda u: str(u) == arg, banned)) is not None:
                    return user
                else:
                    raise hikari.NotFoundError