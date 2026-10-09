# Cutscene Skip (BL2 & TPS)

> This mod was made with AI (Claude Code). The code and docs were written with it,
> under my direction.

An SDK mod for Borderlands 2 and Borderlands: The Pre-Sequel that skips cutscenes. Turn on one
setting and every cutscene is skipped the moment it starts, or bind a key and skip the one that
is playing. The Pre-Sequel side should work (both games share the code the mod hooks into) but
hasn't been tested yet.

**[Download the latest release](https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk/releases/latest)**,
drop `cutscene_skip.sdkmod` into your `sdk_mods` folder, restart the game. First time using SDK
mods? See [Installation](#installation).

Neither game lets you skip its cutscenes: boss intros, title cards, Jack's monologues, the DLC
intro videos and the endings all play out every time, on every character. This mod ends them.
An in-game cutscene is jumped straight to its last frame, so anything the cutscene was going to
do (open a door, spawn the boss, hand you the mission) still happens; full-screen videos are
stopped before they start.

This is a new mod and I haven't been able to test everything, so if something looks off, leave a
comment or [open an issue](https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk/issues).
Even a one-liner about what you were doing helps. The mod writes a line to the console and to
`<game>\Binaries\Win32\Plugins\unrealsdk.log` for everything it does, starting with
`[Cutscene Skip]`; those lines are the most useful thing you can send.

## Options

- **Always Skip Cutscenes** (on/off, starts off) - every in-game cutscene is skipped as soon as it
  starts, and full-screen videos (the DLC intros, the endings, the Sanctuary title cards) don't
  play at all. Loading screens are left alone.
- **Skip Cutscene** (key, unbound until you set it) - press it during an in-game cutscene to skip
  it. It can't interrupt a full-screen video: the game draws nothing else while one plays, so
  nothing can react to a key. Use Always Skip Cutscenes for those.

Both settings are under the mod's entry in the `MODS` menu and are saved when you leave the
options screen.

Things to know:

- Dialogue that was started together with a cutscene may keep playing after the skip; it is
  triggered separately from the cutscene itself.
- In co-op only the host can skip in-game cutscenes (the host runs them, and the other players
  see what the host sees). Videos are skipped on whoever has Always Skip Cutscenes on.
- If a cutscene refuses to end, the log gets a `please report this` line. Send it along with what
  you were doing.

## Installation

This is an SDK mod, not a BLCMM text mod, so it needs the PythonSDK installed once. The same SDK
and the same mod file work for Borderlands 2 and The Pre-Sequel; install them into whichever game
you want, or both. If you have never used SDK mods, follow all three parts in order.

### 1. Install the PythonSDK (once)

These steps are condensed from the official guide at https://bl-sdk.github.io/willow2-mod-db/ ,
which is the place to look if anything here is out of date.

1. Install the latest [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x86.exe)
   (x86, since both games are 32-bit).
2. Download `willow2-sdk.zip` from the latest release at
   https://github.com/bl-sdk/willow2-mod-manager/releases/latest . Do not download the
   "Source code" links.
3. Find the game folder. On Steam, right-click the game, `Manage` > `Browse local files`. Typical
   paths: `C:\Program Files (x86)\Steam\steamapps\common\Borderlands 2` and
   `C:\Program Files (x86)\Steam\steamapps\common\BorderlandsPreSequel`; on Epic, Borderlands 2
   is at `C:\Program Files\Epic Games\Borderlands 2`.
4. Extract the zip directly into that game folder so its contents merge with what is there. Say yes
   to overwriting. You should now have `<game>\sdk_mods` and
   `<game>\Binaries\Win32\Plugins\unrealsdk.dll`.
5. **Linux / Steam Deck only:** in Steam, open the game's `Properties`, force a specific Proton
   version under `Compatibility` (recent Proton GE builds work best), then under `General` set the
   launch options to:
   ```
   WINEDLLOVERRIDES="ddraw=n,b" %command% -pf_tricks=vcrun2022
   ```
6. Start the game. A new `MODS` entry on the main menu means the SDK is installed.

### 2. Install this mod

1. Get `cutscene_skip.sdkmod` from this repository's
   [Releases](https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk/releases) page. If
   there is no release yet, see [Building from source](#building-from-source) below.
2. Drop the `.sdkmod` file straight into `<game>\sdk_mods`. (If you instead have the folder
   `cutscene_skip`, put that folder in `sdk_mods` so that `sdk_mods\cutscene_skip\__init__.py`
   exists; avoid ending up with the folder nested inside another copy of itself.)
3. Restart the game. Mods only load on startup.

### 3. Enable and configure

1. From the main menu open `MODS`, select `Cutscene Skip`, and enable it. New mods start disabled.
2. Open its options. Turn on `Always Skip Cutscenes`, or bind `Skip Cutscene` to a key under
   `Keybinds`, or both. The settings are saved when you leave the options screen and persist
   between sessions.

### Requirements

- Borderlands 2 or Borderlands: The Pre-Sequel (the Windows builds; on Linux they run through
  Proton as above). All DLC is fine but not required.
- PythonSDK / Willow2 Mod Manager v3.8 or newer.
- Microsoft Visual C++ Redistributable (x86).
- No other mods are required.

### Troubleshooting

- **No `MODS` entry on the main menu:** check that `<game>\sdk_mods` exists (the zip was extracted
  one folder too deep or too shallow if not), then reinstall the Visual C++ Redistributable.
- **Game crashes on launch after installing the SDK:** install the latest Visual C++
  Redistributable. On Proton, `-pf_tricks=vcrun2022` in the launch options does this; failing that,
  run `protontricks 49520 vcrun2022` for Borderlands 2 or `protontricks 261640 vcrun2022` for
  The Pre-Sequel.
- **The mod isn't in the list:** make sure the file is `sdk_mods\cutscene_skip.sdkmod` or the
  folder is `sdk_mods\cutscene_skip\`, then restart the game. Errors while loading mods are
  written to `<game>\Binaries\Win32\Plugins\unrealsdk.log`.
- **A cutscene played anyway:** open the log and look for `[Cutscene Skip]` lines from that
  moment. `cutscene started` followed by `skipped` means the mod worked and what you saw was the
  dialogue or the fade; no lines at all means the mod never saw the cutscene; a `please report
  this` line means it saw it and couldn't end it. Any of those is worth an issue.
- **Want to see it working:** open the console (press the tilde key twice) after a cutscene and
  look for `[Cutscene Skip] skipped ...`.
- **More help:** the SDK's [Modding Support Discord](https://discord.gg/bXeqV8Ef9R).

### Building from source

```sh
cd src && zip -r ../cutscene_skip.sdkmod cutscene_skip -x '*__pycache__*'
```

## For modders

The mod's source is `src/cutscene_skip/`. Notes on the SDK, how the games run cutscenes, the
hooks used, prior art and the dev loop are in [docs/](docs/), starting with
[docs/development.md](docs/development.md).

## Credits

No code from other mods is included, but this one builds on what they figured out:

- apple1417 and the bl-sdk contributors, for the
  [PythonSDK](https://github.com/bl-sdk/willow2-mod-manager) this runs on, keybinds included.
- FromDarkHell's Cutscene Disabler text mods for
  [Borderlands 2](https://github.com/BLCM/BLCMods/blob/master/Borderlands%202%20mods/FromDarkHell/Quality%20of%20Life/CutsceneDisabler.txt)
  and [The Pre-Sequel](https://github.com/BLCM/BLCMods/blob/master/Pre%20Sequel%20Mods/FromDarkHell/Quality%20of%20Life/CutsceneDisabler.txt),
  which showed how the games' level scripts run each cutscene, and that a skip has to let the
  cutscene's own follow-up steps run.
- ZooLSmith's [Helios Tracker](https://github.com/ZooLSmith/helios-tracker) research notes, for
  how the games play full-screen videos and switch the player into cutscene mode.

## Changelog

See [src/cutscene_skip/Readme.md](src/cutscene_skip/Readme.md).
