from typing import NewType

from bottles.backend.logger import Logger # pyright: reportMissingImports=false
from bottles.backend.wine.catalogs import win_versions
from bottles.backend.wine.reg import Reg
from bottles.backend.wine.wineboot import WineBoot

logging = Logger()

# Define custom types for better understanding of the code
BottleConfig = NewType('BottleConfig', dict)


class RegKeys:
    
    def __init__(self, config: BottleConfig):
        self.config = config
        self.reg = Reg(self.config)

    def set_windows(self, version: str):
        '''
        Change Windows version in a bottle from the given
        configuration.
        ----------
        supported versions:
            - win10 (Microsoft Windows 10)
            - win81 (Microsoft Windows 8.1)
            - win8 (Microsoft Windows 8)
            - win7 (Microsoft Windows 7)
            - win2008r2 (Microsoft Windows 2008 R1)
            - win2008 (Microsoft Windows 2008)
            - winxp (Microsoft Windows XP)
        ------
        raises: ValueError
            If the given version is invalid.
        '''
        if version not in win_versions:
            raise ValueError("Given version is not supported.")
            
        if version == "winxp" and self.config.get("Arch") == "win64":
            version = "winxp64"

        wineboot = WineBoot(self.config)
        del_keys = {
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion": [
                "SubVersionNumber", "VersionNumber"
            ],
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion": [
                "CSDVersion", "CurrentBuildNumber", "CurrentVersion"
            ],
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ProductOptions": "ProductType",
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ServiceCurrent": "OS",
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows": "CSDVersion",
            "HKEY_CURRENT_USER\\Software\\Wine": "Version"
        }
        for d in del_keys:
            _val = del_keys.get(d)
            if isinstance(_val, list):
                for v in _val:
                    self.reg.remove(d, v)
            else:
                self.reg.remove(d, _val)
            
        bundle = {
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion": [
                {
                    "value": "CSDVersion",
                    "data": win_versions.get(version)["CSDVersion"]
                },
                {
                    "value": "CurrentBuild",
                    "data": win_versions.get(version)["CurrentBuild"]
                },
                {
                    "value": "CurrentBuildNumber",
                    "data": win_versions.get(version)["CurrentBuildNumber"]
                },
                {
                    "value": "CurrentVersion",
                    "data": win_versions.get(version)["CurrentVersion"]
                },
                {
                    "value": "ProductName",
                    "data": win_versions.get(version)["ProductName"]
                },
                {
                    "value": "CurrentMinorVersionNumber",
                    "data": win_versions.get(version)["CurrentMinorVersionNumber"],
                    "keyType": "dword"
                },
                {
                    "value": "CurrentMajorVersionNumber",
                    "data": win_versions.get(version)["CurrentMajorVersionNumber"],
                    "keyType": "dword"
                },
            ],
            "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows": [
                {
                    "value": "CSDVersion",
                    "data": win_versions.get(version)["CSDVersionHex"],
                    "keyType": "dword"
                }
            ]
        }

        if self.config.get("Arch") == "win64":
            bundle["HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\Microsoft\\Windows NT\\CurrentVersion"] = [
                {
                    "value": "CSDVersion",
                    "data": win_versions.get(version)["CSDVersion"]
                },
                {
                    "value": "CurrentBuild",
                    "data": win_versions.get(version)["CurrentBuild"]
                },
                {
                    "value": "CurrentBuildNumber",
                    "data": win_versions.get(version)["CurrentBuildNumber"]
                },
                {
                    "value": "CurrentVersion",
                    "data": win_versions.get(version)["CurrentVersion"]
                },
                {
                    "value": "ProductName",
                    "data": win_versions.get(version)["ProductName"]
                },
                {
                    "value": "CurrentMinorVersionNumber",
                    "data": win_versions.get(version)["CurrentMinorVersionNumber"],
                    "keyType": "dword"
                },
                {
                    "value": "CurrentMajorVersionNumber",
                    "data": win_versions.get(version)["CurrentMajorVersionNumber"],
                    "keyType": "dword"
                }
            ]

        if "ProductType" in win_versions.get(version):
            '''windows xp 32 doesn't have ProductOptions/ProductType key'''
            bundle["HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ProductOptions"] = [
                {
                    "value": "ProductType",
                    "data": win_versions.get(version)["ProductType"]
                }
            ]

        self.reg.import_bundle(bundle)

        wineboot.restart()
        wineboot.update()
    
    def set_app_default(self, version: str, executable: str):
        '''
        Change default Windows version per application in a bottle
        from the given configuration.
        '''
        if version not in win_versions:
            raise ValueError("Given version is not supported.")
            
        if version == "winxp" and self.config.get("Arch") == "win64":
            version = "winxp64"
            
        self.reg.add(
            key=f"HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\{executable}",
            value="Version",
            data=version
        )

    def toggle_virtual_desktop(self, state: bool, resolution: str = "800x600"):
        '''
        This function toggles the virtual desktop for a bottle, updating
        the Desktops registry key.
        '''
        wineboot = WineBoot(self.config)

        if state:
            self.reg.add(
                key="HKEY_CURRENT_USER\\Software\\Wine\\Explorer",
                value="Desktop",
                data="Default"
            )
            self.reg.add(
                key="HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops",
                value="Default",
                data=resolution
            )
        else:
            self.reg.remove(
                key="HKEY_CURRENT_USER\\Software\\Wine\\Explorer",
                value="Desktop"
            )
        wineboot.update()

    def apply_cmd_settings(self, scheme:dict={}):
        '''
        Change settings for the wine command line in a bottle.
        This method can also be used to apply the default settings, part
        of the Bottles experience, these are meant to improve the
        readability and usability.
        '''
        self.reg.import_bundle({
            "HKEY_CURRENT_USER\\Console\\C:_windows_system32_wineconsole.exe": [
                {"value": "ColorTable00", "data": "2368548"},
                {"value": "CursorSize","data": "25" },
                {"value": "CursorVisible","data": "1" },
                {"value": "EditionMode","data": "0" },
                {"value": "FaceName","data": "Monospace", "keyType": "dword"},
                {"value": "FontPitchFamily","data": "1" },
                {"value": "FontSize","data": "1248584" },
                {"value": "FontWeight","data": "400" },
                {"value": "HistoryBufferSize","data": "50" },
                {"value": "HistoryNoDup","data": "0" },
                {"value": "InsertMode","data": "1" },
                {"value": "MenuMask","data": "0" },
                {"value": "PopupColors","data": "245" },
                {"value": "QuickEdit","data": "1" },
                {"value": "ScreenBufferSize","data": "9830480" },
                {"value": "ScreenColors","data": "11" },
                {"value": "WindowSize","data": "1638480"
                }
            ]
        })
