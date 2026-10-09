# Nexus Mods listing

Nexus can't be filled in automatically, so this is everything to paste into
https://www.nexusmods.com/borderlands2/mods/add . Attach `cutscene_skip.sdkmod` from the GitHub
release as the main file. For a Pre-Sequel listing the same text goes on The Pre-Sequel's own
Nexus page, https://www.nexusmods.com/borderlandsthepresequel/mods/add .

## Fields

- **Name:** Cutscene Skip (BL2 & TPS)
- **Summary (one line):** Skips cutscenes in BL2 and TPS (TPS untested): turn on Always Skip
  Cutscenes, or bind a key and press it during one. In-game cutscenes and the DLC intro videos.
- **Category:** Gameplay (Nexus calls it "Gameplay Effects and Changes" on some games), or
  Utilities
- **Version:** match the release tag, e.g. `0.1`
- **Language:** English
- **Requirements:** add `PythonSDK (willow2-mod-manager)` with the link
  https://github.com/bl-sdk/willow2-mod-manager/releases/latest
- **Permissions:** your call. The source is public on GitHub, so "open source, credit
  appreciated" fits.
- **Tags:** Quality of Life, Cutscenes, Utility
- **Source:** https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk

## Description (BBCode)

Nexus descriptions are BBCode. Paste this as-is:

```
[size=5][b]Cutscene Skip (BL2 & TPS)[/b][/size]

A PythonSDK mod for Borderlands 2 and Borderlands: The Pre-Sequel that skips cutscenes. The Pre-Sequel side should work (both games share the code the mod hooks into) but hasn't been tested yet.

Neither game lets you skip its cutscenes: boss intros, title cards, Jack's monologues, the DLC intro videos and the endings play out every time, on every character. This mod ends them. An in-game cutscene is jumped straight to its last frame, so anything it was going to do (open a door, spawn the boss, hand you the mission) still happens; full-screen videos are stopped before they start.

[size=4][b]Options[/b][/size]

[list]
[*][b]Always Skip Cutscenes[/b] - every in-game cutscene is skipped as soon as it starts, and the full-screen videos (DLC intros, endings, Sanctuary title cards) don't play at all
[*][b]Skip Cutscene[/b] - a key, unbound until you set it; press it during an in-game cutscene to skip it. It can't interrupt a video (the game draws nothing else while one plays), so use Always Skip Cutscenes for those
[/list]

Dialogue started together with a cutscene may keep playing after the skip. In co-op only the host can skip in-game cutscenes. Loading screens are untouched.

[size=4][b]Installation[/b][/size]

This is an SDK mod, not a BLCMM text mod. If you've never used one:

[list=1]
[*]Install the PythonSDK: follow [url=https://bl-sdk.github.io/willow2-mod-db/]the official guide[/url] (install the Visual C++ Redistributable, extract the SDK zip into your game folder, and on Linux/Steam Deck add the launch options it lists). You're done when a [b]MODS[/b] entry appears on the main menu.
[*]Drop [b]cutscene_skip.sdkmod[/b] into your [b]sdk_mods[/b] folder.
[*]Restart the game, open [b]MODS[/b], enable Cutscene Skip, and turn on Always Skip Cutscenes or bind the Skip Cutscene key.
[/list]

A step-by-step version with troubleshooting is in the [url=https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk#installation]README on GitHub[/url].

[size=4][b]Credits[/b][/size]

No code from other mods is included, but this one builds on what they figured out:

[list]
[*]apple1417 and the bl-sdk contributors, for the [url=https://github.com/bl-sdk/willow2-mod-manager]PythonSDK[/url] this runs on, keybinds included.
[*]FromDarkHell's Cutscene Disabler text mods for [url=https://github.com/BLCM/BLCMods/blob/master/Borderlands%202%20mods/FromDarkHell/Quality%20of%20Life/CutsceneDisabler.txt]Borderlands 2[/url] and [url=https://github.com/BLCM/BLCMods/blob/master/Pre%20Sequel%20Mods/FromDarkHell/Quality%20of%20Life/CutsceneDisabler.txt]The Pre-Sequel[/url], which showed how the games' level scripts run each cutscene, and that a skip has to let the cutscene's own follow-up steps run.
[*]ZooLSmith's [url=https://github.com/ZooLSmith/helios-tracker]Helios Tracker[/url] research notes, for how the games play full-screen videos and switch the player into cutscene mode.
[/list]

[size=4][b]Notes[/b][/size]

[list]
[*]Source code and issue tracker: [url=https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk]GitHub[/url]
[*]This mod was made with AI (Claude Code). The code and docs were written with it, under my direction.
[*]New mod, not everything is tested yet. If something looks off, leave a comment here or open an issue on GitHub; the [Cutscene Skip] lines from Binaries\Win32\Plugins\unrealsdk.log are the most useful thing to include. Pre-Sequel reports are especially welcome.
[/list]
```

## Before posting

- Play it first (`docs/testing.md`), then cut a release so the download exists
  (`docs/development.md`, "Cutting a release").
- Take two or three screenshots: the options menu with the toggle and the key, and a boss fight
  that would normally open with a cutscene. Nexus listings without images get skipped.
- Nexus has its own changelog tab; paste the entries from `src/cutscene_skip/Readme.md`.
