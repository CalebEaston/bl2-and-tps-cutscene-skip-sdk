# Cutscene Skip (BL2 / TPS PythonSDK mod)

A Borderlands 2 and Borderlands: The Pre-Sequel mod for the **new** PythonSDK stack
(willow2-mod-manager v3.8 / pyunrealsdk / `mods_base` 1.12 / `keybinds` 1.2, embedded Python
3.14; one SDK zip and one `.sdkmod` serve both games). The legacy PythonSDK (`Mods.ModMenu`,
`BL2MOD`) is archived and is NOT what this targets. Sibling project with the same conventions:
`../bl2-and-tps-enemy-and-item-scaling-sdk`. Neither game has been played with this mod yet
(v0.1, 2026-10-09).

## What the mod does

Exactly two settings (Caleb's spec):

| Setting | Kind | Effect |
|---|---|---|
| `Always Skip Cutscenes` | BoolOption, off | every in-engine cutscene is skipped as it starts; full-screen videos (Bink: DLC intros, endings, title cards) are stopped from starting |
| `Skip Cutscene` | keybind, unbound | skips the in-engine cutscene playing right now; can't interrupt a video (nothing ticks while one plays) |

No logging toggle: cutscenes are rare, so every detection, skip stage and result is logged with
the `[Cutscene Skip]` prefix (console and `<game>\Binaries\Win32\Plugins\unrealsdk.log`). The
log is Caleb's bug report: write log lines so they say which assumption broke.

Design and every verified fact: `docs/sdk-notes.md`. Short version: a cutscene is a Kismet
`SeqAct_Interp` (Matinee) whose `InterpData` has a director (camera) group; every Matinee node in
both games has a Gearbox-added `Last Frame` input (index 5) that jumps it to the end, gated by
`bFireEventsWhenJumpToLastFrame` / `bFireCompleteEventWhenJumpToLastFrame`, which the mod forces
True first because the level script waits on those outputs. The skip is staged (last frame ->
`pc.SkipMatinee()` -> `SetPosition(end)` -> `Stop()`), each stage checked 0.3 s later, so the first
playtest log says which one works. Videos are blocked in a PRE hook on `ClientPlayBinkMovie`.

Current priority: **get a working version in-game first, then patch**. Keep it simple; no
over-engineering for compatibility; change the game's own state rather than patching what is
displayed; keep diagnostics that log a "please report this" line rather than silent fixes.

## Layout

```
src/cutscene_skip/        the mod: __init__.py, pyproject.toml (mod metadata), Readme.md (changelog)
src/                      is the "mods folder" the game is pointed at; keep it to mod packages only
.willow2-mod-manager/     git submodule, pinned to the v3.8 release commit (9097107) for type-checking
docs/sdk-notes.md         reference: SDK facts, cutscene mechanics, prior art, design, open questions
docs/testing.md           playtest checklist for Caleb: plain in-game steps and log lines, nothing typed into
                          the console (he can't paste into it)
docs/testing-probes.md    developer version: console probes and what each would settle
docs/development.md       human-facing dev notes: layout, checks, running from checkout, releases
docs/nexus.md             ready-to-paste Nexus listing (Caleb posts it himself, when confident)
.github/workflows/        release.yml: a v* tag builds the .sdkmod and publishes a GitHub Release
pyproject.toml            pyright + ruff config only (copied from the bl-sdk repos)
```

The README is the player-facing page (AI disclosure first, download link, plain-language
options, install guide, no internals); developer material goes in `docs/`.

The folder name `cutscene_skip` is the Python module name, the settings file name
(`<game>/sdk_mods/settings/cutscene_skip.json`) and the required root folder of the `.sdkmod`.
Never put a `.` in it. Every non-dot subfolder of `src/` gets imported as a mod, so tests/docs/tools
go at the repo root, not under `src/`.

## Hard rules for the code

- `build_mod()` must be called at module level of `__init__.py` (it inspects the caller's frame to
  find the module and the sibling `pyproject.toml`). Name/author/version/description come from
  `pyproject.toml`; don't define `__version__`/`__author__` in code.
- Hook strings are `Package.Class:Function` (colon), on the class that declares or overrides the
  function in the running game: `Engine.PlayerController:NotifyDirectorControl` (WPC does not
  override it), `WillowGame.WillowPlayerController:PlayerTick` (WPC does). Callback is
  `(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction)`.
- `args` is a COPY for plain values; struct and array members are views. To change an argument:
  `with prevent_hooking_direct_calls(): func(new)` then `return Block`.
- Exceptions inside a hook are logged and the function runs anyway, so a broken hook looks like a
  no-op. Read the console/log when testing. Per-stage work in `_run_stage` catches its own
  exceptions so one failing method never blocks the next.
- Hooks and keybinds are inert until the mod is enabled. Never pass `immediately_enable=True`.
- Never change a Matinee from inside `NotifyDirectorControl` or any Kismet-driven hook: the
  notification is sent from inside the matinee's own update. Queue, then act from `PlayerTick`.
- Hold Unreal objects across frames only through `unrealsdk.unreal.WeakPointer`; clear every
  queue on `WillowClientDisableLoadingMovie` (map loaded).
- Options: pass `options=[...]` and `keybinds=[...]` explicitly (module-scan order is unstable).
  `on_change_*` callbacks receive the NEW value while `opt.value` is still the OLD one. Don't call
  `option.reset()` (added in mods_base 1.13; the game ships 1.12).
- Keybind: `@keybind("Skip Cutscene", None, description=...)` -> no-arg callback on IE_Pressed.
  The key is a UE key name string saved under `"keybinds"` in the settings file; `None` = unbound.
  Renaming the option or the keybind orphans its saved value; say so in the changelog.
- Labels at or under 25 characters (the mod menu truncates longer ones); plain words.
- The first 1024 bytes of `__init__.py` must not contain `from Mods.`, `from ..ModMenu import` or
  `BL2MOD):`, even in a comment, or the loader treats the mod as legacy.
- `project.version` must be dotted integers (`"0.1"`); anything else raises at import.
- Python file content stays ASCII (ruff RUF001/RUF003 flag en dashes and curly quotes). No `TODO`
  comments in code (ruff TD/FIX rules); put open items in `docs/sdk-notes.md`.
- Use `unrealsdk.logging.info/warning/error`, never `print`. `dev_warning` is hidden in-game.
- Both games: `[tool.sdkmod] supported_games` must list `"BL2"` and `"TPS"`, or `mods_base` shows
  the mod as `Incompatible` and locks the enable toggle in the missing game. Every hook target,
  field and function used here exists in both games with the same signature (checked against the
  game-generated stubs, `docs/sdk-notes.md`). Detect anything game-specific by looking for the
  class or field, never via `Game.get_current()`.
- `unrealsdk.find_all("SeqAct_Interp")` with the default `exact=True`: `WillowSeqAct_InterpMenu`
  and `WillowSeqAct_DayNightCycle` are subclasses that must never be skipped.

## Dev loop

Local checks (no game needed):

```sh
git submodule update --init .willow2-mod-manager
git -C .willow2-mod-manager submodule update --init src/mods_base src/keybinds src/console_mod_menu
python3 -m venv .venv && .venv/bin/pip install ruff     # once
.venv/bin/ruff check src && .venv/bin/ruff format --check src
npx --yes pyright src
```

In-game (the game is NOT installed on this dev machine; Caleb runs it elsewhere via Steam/Proton):

1. SDK release zip extracted into the game folder (`<game>/sdk_mods`,
   `<game>/Binaries/Win32/Plugins/`). `<game>` is `.../steamapps/common/Borderlands 2` (49520) or
   `.../steamapps/common/BorderlandsPreSequel` (261640); each game keeps its own
   `sdk_mods/settings/cutscene_skip.json`.
2. `<game>/Binaries/Win32/Plugins/unrealsdk.user.toml` pointing at this repo's `src/`:
   ```toml
   [mod_manager]
   extra_folders = ['Z:\home\caleb\Development\caleb\bl2-and-tps-cutscene-skip-sdk\src']
   ```
3. Steam launch options for Proton: `WINEDLLOVERRIDES="ddraw=n,b" %command% -pf_tricks=vcrun2022`
4. Enable the mod once from the main menu `MODS` entry (fresh installs start disabled).
5. Console = tilde twice. `rlm cutscene_skip` hot-reloads the module after edits. The log file is
   `<game>/Binaries/Win32/Plugins/unrealsdk.log` (truncated every launch). Caleb cannot paste into
   the console: test plans are in-game actions plus lines to copy out of the log.
6. Package: `cd src && zip -r ../cutscene_skip.sdkmod cutscene_skip -x '*__pycache__*'`.

## Hook targets in use

| Hook | Type | What it does |
|---|---|---|
| `Engine.PlayerController:NotifyDirectorControl` | PRE | `bNowControlling` + `CurrentMatinee`: remember the cutscene (WeakPointer), log `cutscene started`, queue a skip when Always Skip is on; False: forget, log `cutscene ended`. Local controller only |
| `WillowGame.WillowPlayerController:ClientSetCinematicMode` | POST | `bInCinematicMode` with Always Skip on: open a 2 s window in which the tick scans for playing director matinees every 0.25 s (backstop for a missing director notification) |
| `WillowGame.WillowPlayerController:PlayerTick` | POST | early return unless something is queued; runs the scan window and advances every `SkipAttempt` through the stages with `args.DeltaTime` |
| `WillowGame.WillowPlayerController:ClientPlayBinkMovie` | PRE | Always Skip on: `Block`, unless `MovieName` is `BinkLoadingMovieName`; logs `bForceNoSkip` |
| `WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie` | POST | map loaded: clear attempts, cutscenes, scan window |
| keybind `Skip Cutscene` | IE_Pressed | queue every remembered playing matinee, else one scan, else log `no cutscene is playing`; clients log `only the host can skip` |

Skip stages (`STAGES`), each checked 0.3 s later via `bIsPlaying`: `last frame`
(`bFireEventsWhenJumpToLastFrame`, `bFireCompleteEventWhenJumpToLastFrame`, `bIsSkipped` True,
`ForceActivateInput(5)`), `the game's own skip` (`bIsSkippable` True, `pc.SkipMatinee()`), `jump
to the end` (`SetPosition(InterpLength, False)`), `stop` (`Stop()`), then a "please report this"
warning.

## Later (deferred on purpose)

- Keep only the stage the playtest proves, once a log shows it.
- Cinematic-mode watchdog (`TurnOffCinematicMode()` when `bCinematicMode` outlives every matinee)
  if a report shows a frozen player after a skip.
- Stopping dialog that was started alongside a skipped cutscene, if it is reported as annoying.
- `SetCinematicAutoSkip(True)` / `ENGINE.bCinematicAutoSkip` as a possible one-line always-skip;
  probe listed in `docs/testing-probes.md`.
- Co-op clients skipping `bClientSideOnly` matinees; a client-initiated host skip.
- Assault on Dragon Keep standalone (`"AoDK"` in `supported_games`, unchecked).
- Nexus listing: `docs/nexus.md` is ready to paste; Caleb posts it after a playtest.
