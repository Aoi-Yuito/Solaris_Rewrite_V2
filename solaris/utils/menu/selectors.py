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
from datetime import timedelta
from asyncio import TimeoutError

from solaris import Config
from solaris.utils import chron


class Selector:
    def __init__(self, menu, selection, *, timeout=300.0, auto_exit=True, check=None):
        self.menu = menu
        self.timeout = timeout
        self.auto_exit = auto_exit
        self.check = check or self._default_check

        self._base_selection = selection

    @property
    def selection(self):
        return self._base_selection

    @selection.setter
    def selection(self, value):
        self._base_selection = value

    def _default_check(self, reaction):
        return (
            reaction.message_id == self.menu.message.id
            and reaction.user_id == self.menu.ctx.author.id
            and reaction.emoji_name in self.selection
        )

    async def _serve(self):
        await self.menu.message.remove_all_reactions()
        emoji = await self.menu.bot.rest.fetch_guild(Config.HUB_GUILD_ID)

        for e in self.selection:
            await self.menu.message.add_reaction(emoji.get_emoji(int(e)))

    async def response(self):
        await self._serve()

        def predicate(event: hikari.ReactionAddEvent) -> bool:
            return event.user_id == self.menu.ctx.author.id and event.message_id == self.menu.message.id

        try:
            reaction = await self.menu.bot.wait_for(hikari.ReactionAddEvent, timeout=self.timeout, predicate=predicate)
        except TimeoutError:
            await self.menu.timeout(chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            if (r := reaction.emoji_name) == "exit" and self.auto_exit:
                await self.menu.stop()
            else:
                return r
        

    def __repr__(self):
        return (
            f"<Selector"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" menu={self.menu!r}>"
        )


class NumericalSelector(Selector): #Exit emoji id 796315251360137276
    def __init__(self, menu, iterable, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(menu, ["796315251360137276"], timeout=timeout, auto_exit=auto_exit, check=check)

        self.iterable = iterable
        self.max_page = (len(iterable) // 9) + 1
        self.pages = [{} for i in range(self.max_page)]

        self._selection = []
        self._last_selection = []
        self._page = 0

        for i, obj in enumerate(iterable):
            self.pages[i // 9].update({f"option{(i % 9) + 1}": obj})

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        self._last_selection = self._selection
        self._selection = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = max(0, min(value, self.max_page - 1))

    @property
    def last_selection(self):
        return self._last_selection

    @property
    def page_info(self):
        return f"Page {self.page + 1:,} of {self.max_page:,}"

    @property
    async def table(self):
        emoji = await self.menu.bot.rest.fetch_guild(Config.HUB_GUILD_ID)
        return "\n".join(f"{emoji.get_emoji(k).mention} {v}" for k, v in self.pages[self.page].items())

    def set_selection(self):
        s = self._base_selection.copy()
        insert_point = 0

        if len(self.pages) > 1:
            if self.page != 0:
                s.insert(0, "830402884830494721") # PageBack emoji's ID 830402884830494721
                s.insert(0, "830402919110672416") # StepBack emoji's ID 830402919110672416
                insert_point += 2

            if self.page != self.max_page - 1:
                s.insert(insert_point, "830402938831634492") # StepNext emoji's ID 830402938831634492
                s.insert(insert_point, "830402902044442634") # PageNext emoji's ID 830402902044442634

        for i in range(len(self.pages[self.page])):
            s.insert(i + insert_point, f"option{i + 1}")

        self.selection = s

    async def response(self):
        self.set_selection()

        if self.selection != self.last_selection:
            await self._serve()
 
        def predicate(event: hikari.ReactionAddEvent) -> bool:
            return event.user_id == self.menu.ctx.author.id and event.message_id == self.menu.message.id

        try:
            reaction = await self.menu.bot.wait_for(hikari.ReactionAddEvent, timeout=self.timeout, predicate=predicate)
        except TimeoutError:
            await self.menu.timeout(chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            if (r := reaction.emoji_name) == "exit":
                if self.auto_exit:
                    await self.menu.stop()
                return
            elif r == "stepback":
                self.page = 0
            elif r == "pageback":
                self.page -= 1
            elif r == "pagenext":
                self.page += 1
            elif r == "stepnext":
                self.page = self.max_page
            else:
                return self.pages[self.page][r]

            await self.menu.switch(reaction.emoji_name, reaction.emoji_id)
            return await self.response()

    def __repr__(self):
        return (
            f"<NumericalSelector"
            f" page={self.page!r}"
            f" max_page={self.max_page!r}"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" menu={self.menu!r}>"
        )


class PageControls(Selector): #Exit emoji id 796315251360137276
    def __init__(self, menu, pagemaps, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(menu, ["796315251360137276"], timeout=timeout, auto_exit=auto_exit, check=check)

        self.pagemaps = pagemaps
        self.max_page = len(pagemaps)

        self._selection = []
        self._last_selection = []
        self._page = 0

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        self._last_selection = self._selection
        self._selection = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = max(0, min(value, self.max_page - 1))

    @property
    def last_selection(self):
        return self._last_selection

    @property
    def page_info(self):
        return f"Page {self.page + 1:,} of {self.max_page:,}"

    def set_selection(self):
        s = self._base_selection.copy()
        insert_point = 0

        if len(self.pagemaps) > 1:
            if self.page != 0:
                s.insert(0, "830402884830494721") # PageBack emoji's ID 830402884830494721
                s.insert(0, "830402919110672416") # StepBack emoji's ID 830402919110672416
                insert_point += 2

            if self.page != self.max_page - 1:
                s.insert(insert_point, "830402938831634492") # StepNext emoji's ID 830402938831634492
                s.insert(insert_point, "830402902044442634") # PageNext emoji's ID 830402902044442634

        self.selection = s

    async def response(self):
        self.set_selection()

        if self.selection != self.last_selection:
            await self._serve()

        def predicate(event: hikari.ReactionAddEvent) -> bool:
            return event.user_id == self.menu.ctx.author.id and event.message_id == self.menu.message.id

        try:
            reaction = await self.menu.bot.wait_for(hikari.ReactionAddEvent, timeout=self.timeout, predicate=predicate)
        except TimeoutError:
            await self.menu.timeout(chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            if (r := reaction.emoji_name) == "exit":
                if self.auto_exit:
                    await self.menu.stop()
                return
            elif r == "stepback":
                self.page = 0
            elif r == "pageback":
                self.page -= 1
            elif r == "pagenext":
                self.page += 1
            elif r == "stepnext":
                self.page = self.max_page

            await self.menu.switch(reaction.emoji_name, reaction.emoji_id)
            return await self.response()

    def __repr__(self):
        return (
            f"<NumericalSelector"
            f" page={self.page!r}"
            f" max_page={self.max_page!r}"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" menu={self.menu!r}>"
        )