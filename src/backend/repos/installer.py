# installer.py
#
# Copyright 2020 brombinmirko <send@mirko.pm>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from typing import Union
from bottles.backend.repos.repo import Repo  # pyright: reportMissingImports=false


class InstallerRepo(Repo):
    name = "installers"

    def get(self, name: str, plain: bool = False) -> Union[str, dict, bool]:
        if name in self.catalog:
            entry = self.catalog[name]
            url = f"{self.url}/{entry['Category']}/{name}.yml"
            return self.get_manifest(url, plain)
        return False
    
    def get_review(self, name: str) -> Union[str, bool]:
        if name in self.catalog:
            return self.get_manifest(f"{self.url}/Reviews/{name}.md", plain=True)
        return False
    
    def get_icon(self, name: str) -> Union[str, bool]:
        if name in self.catalog:
            entry = self.catalog[name]
            executable = entry.get("Executable", {})
            icon = executable.get("icon")
            if icon:
                return f"{self.url}/data/{name}/{icon}"
        return False
                