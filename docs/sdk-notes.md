# SDK and game notes

Reference gathered on 2026-10-09 for v0.1 from: the willow2-mod-manager v3.8 source (the
`.willow2-mod-manager` submodule), Justin99x's game-generated class stubs (`bl-py-stubs`,
`gamestubs.zip`, with `bl2/`, `tps/` and `common/` trees), RobChiocchio's BL2 SDK dump
(`WillowGame_functions.cpp`, `Engine_functions.cpp`: function flags, no bodies), apocalyptech's
ft-explorer object dumps (every `SeqAct_Interp`, `InterpData`, `SeqAct_PlayBinkMovie` and
`SeqAct_ToggleCinematicMode` object in both games), FromDarkHell's Cutscene Disabler text mods
(BLCMods repo), ZooLSmith's helios-tracker in-game probes, and the primer from the
enemy_item_scaling session. "Verified" means read in those sources. Anything about what a native
function's body does is a guess unless it says otherwise: the games ship no UnrealScript source.

## Stack

Same as the enemy_item_scaling mod: willow2-mod-manager v3.8 (`mods_base` 1.12, `keybinds` 1.2,
embedded Python 3.14), one SDK zip and one `.sdkmod` for BL2 and TPS. See that repo's
`docs/sdk-notes.md` for the loader, settings file and hook mechanics. The facts this mod relies on:

- Hook strings are `Package.Class:Function`; unrealsdk matches the function actually called, so a
  function a subclass does not override is hooked on the class that declares it
  (`Engine.PlayerController:NotifyDirectorControl`, not `WillowGame.WillowPlayerController:...`).
  A hook on a function the running game lacks is inert.
- Native functions can be called from Python: `BoundFunction.__call__` sets `FUNC_NATIVE` on the
  function for the duration of the `ProcessEvent` call (`unrealsdk bound_function.cpp:51-58`).
  Natives called from C++ never reach a hook; natives called from script and all events do.
- `unrealsdk.unreal.WeakPointer(obj)` holds an object across frames; calling it returns the object
  or `None` once the engine has destroyed it. Plain `UObject` references held across a map change
  would dangle.
- Keybinds (`mods_base.keybind`, `KeybindType`) are dispatched from one PRE hook on
  `WillowGame.WillowUIInteraction:InputKey` (the `keybinds` package). That is the viewport's UI
  interaction, upstream of `PlayerInput`; cinematic mode only gates `PlayerInput` and movement
  (`bCinemaDisableInputMove/Look/Button`), so a mod keybind is expected to keep working during an
  in-engine cutscene. Not yet confirmed in-game.
- Settings: `<game>/sdk_mods/settings/cutscene_skip.json` holds `{"enabled", "options":
  {"Always Skip Cutscenes": bool}, "keybinds": {"Skip Cutscene": "F8" | null}}`.

## What a cutscene is in these games (verified)

Three different things get called a cutscene. The mod handles the first two.

### 1. In-engine cutscenes: Matinee

A Kismet `Engine.SeqAct_Interp` ("Matinee") node in the level script, driving an `InterpData` that
has an `InterpGroupDirector` (the camera director group that takes over the player's view). Counts
from the dumps: BL2 has 2113 `SeqAct_Interp` nodes, 118 of them driving director data (plot
cutscenes, boss title cards, scripted camera moments); TPS has 1388 and 61. Director cutscenes run
0.2 to 74 s in BL2 (median 11.8) and 2 to 101 s in TPS.

Fields (`common/Engine/SeqAct_Interp.pyi`, identical in both games): `bIsPlaying`, `bPaused`,
`Position`, `PlayRate`, `bLooping`, `bRewindOnPlay`, `bClientSideOnly` (4 BL2 / 2 TPS cutscenes),
`bIsSkippable` (True on 16 BL2 / 5 TPS nodes, none of them plot cutscenes: "Challenges" camera
pans and a few DLC nodes), `bIsSkipped` (False everywhere in the dumps),
`bFireEventsWhenJumpToLastFrame` (class default False; True on 11 of the 118 BL2 cutscenes, 0 of
61 in TPS), `bFireCompleteEventWhenJumpToLastFrame` (class default True; False on 6 BL2 cutscenes,
among them the Brick intro `Sandworm_Mission_Main...SeqAct_Interp_1` and the Cassius cutscene
`ResearchCenter_MissionMain...PlotMission050.SeqAct_Interp_7`, and 1 in TPS),
`bLastFrameEventFired`, `InterpData` (None in the dumps: the data is linked through the "Data"
variable link and the field is filled when the node starts playing), `GroupInst`.
`InterpGroup.bRunTracksWhenSkippingToLastFrame` exists per group. `InterpData.InterpLength` is the
length; `InterpData.CachedDirectorGroup` is set on every director cutscene in the dumps.

Functions: `Stop()`, `SetPosition(NewPosition, bJump)`, `AddPlayerToDirectorTracks(PC)` (all
native final), `Reset()` (script). On the Kismet op: `ForceActivateInput(InputIdx)`,
`ForceActivateOutput(OutputIdx)`, `ActivateOutputLink(OutputIdx)` (native), and the
`InputLinks[i].bHasImpulse` / `QueuedActivations` fields.

Input links, the same on every node in both games: 0 `Play`, 1 `Reverse`, 2 `Stop`, 3 `Pause`,
4 `Change Dir`, 5 **`Last Frame`**. The last one is a Gearbox addition to UE3's Matinee: it jumps
the sequence to its end (the game uses it to restore doors and movers when a save is loaded). The
two `...WhenJumpToLastFrame` flags say whether that jump fires the node's event outputs and its
`Completed` output. Output links: 0 `Completed`, 1 `Reversed`, then one per event-track key.
54 of the 118 BL2 cutscenes and 30 of the 61 TPS ones have event outputs, with names like
`SpawnRolandBot`, `AdvanceToNextObj`, `SendEllieToStation`, `ElevatorLowered`, `WallExplosion`:
the gameplay a cutscene causes hangs off those links and off `Completed`. A skip that does not
fire them leaves the level script waiting.

Director control notification: `Engine.PlayerController:NotifyDirectorControl(bNowControlling,
CurrentMatinee)` is an event (flags `0x00020802`) the director track calls when it takes or
releases a local player's camera. `WillowPlayerController` does not override it in either game.
`PlayerController.ControllingDirTrackInst` points at the controlling director track instance.

### 2. Video cutscenes: Bink movies

`WillowGame.WillowPlayerController:ClientPlayBinkMovie(MovieName, bStreamed=, bLooping=,
bForceNoSkip=)` is an event and native (`0x01024DC0`). Kismet plays them through
`WillowGame.SeqAct_PlayBinkMovie` (`BinkMovieName`, `PlayStreamed`, `BlockUntilFinished`,
`LoopPlayback`; outputs `In` / `Finished`). Movies in the dumps: BL2 `TC_Zed`, `TC_Marcus`,
`TC_Tannis`, `TC_Scooter` (Sanctuary title cards), `Orchid_Intro`, `Iris_Intro`, `Sage_Intro`,
`Aster_Intro`, `Aster_Outro`, `Anemone_Intro_Part1/2`, `Anemone_Outro`,
`Anemone_Outro_PostCredit`; TPS `Ending`, `Ending_PostCredits`, `Jack_OutroCard`, `MegaOutro`,
`SUBCON_crash_screen` (the one non-blocking node). The game intro goes through
`ClientPlayIntroMovie()` / `IntroMovieName` (TPS's `MegaIntro`, 323 s, was seen through the
`ClientPlayBinkMovie` hook by helios-tracker; profile flag `WPS_IntroMovieViewed`).

While a Bink plays the game renders nothing and ticks nothing: helios-tracker's probe on
`Orchid_Intro` saw zero `PostRender` and zero ticks for its 65 s. So no hook and no keybind can run
during a video; the only lever is to stop it from starting. Related functions, identical in both
games: `StopAnyBinkMovie()`, `IsBinkMoviePlaying(MovieName)`, `IsAnyBinkMoviePlaying()`,
`SetLoadingMovieSkipEnabled(bEnabled)`, `BinkLoadingMovieName` (the loading screen's Bink).
Loading screens are a separate path (`WillowShowLoadingMovie`, `WillowClientShowLoadingMovie`,
`WillowClientDisableLoadingMovie`) that mods use as the "map finished loading" signal; left alone.
`GameFramework.GamePlayerController` also has the stock `ClientPlayMovie(...)` /
`ClientStopMovie(DelayInSeconds, bAllowMovieToFinish, bForceStopNonSkippable,
bForceStopLoadingMovie)`.

### 3. Cinematic mode

Not a cutscene by itself: the state where the player is frozen, hidden and HUD-less. Kismet
`Engine.SeqAct_ToggleCinematicMode` (`bDisableMovement`, `bDisableTurning`, `bHidePlayer`,
`bDisableInput`, `bHideHUD`, `bEnableGodMode`, `bEnableNoTarget`, `bPauseDialog`; 212 nodes in
BL2, 100 in TPS, most with everything on) -> `PlayerController.OnToggleCinematicMode(Action)` ->
`WillowPlayerController.SetCinematicMode(bInCinematicMode, bHidePlayer, bAffectsHUD,
bAffectsMovement, bAffectsTurning, bAffectsButtons, ...)` -> `ClientSetCinematicMode(...)` (both
overridden by WPC). Flags: `PlayerController.bCinematicMode`, `bKismetEnabledCinematicMode`,
`bCinemaDisableInputMove/Look/Button`, `bCinematicModeHidePlayer`; WPC `bWasCinematic`,
`TurnOffCinematicMode()`, `SetMapChangeCinematicMode()`. Map changes also use cinematic mode
(`pc.bCinematicMode` stays True for about 4 s after a load, per helios-tracker), so cinematic
mode alone does not mean a cutscene. helios-tracker's recorded DLC intro:
`SeqAct_ToggleCinematicMode` -> `SetCinematicMode(True, ...)` -> the Bink -> cinematic mode off.

## The game's own skip machinery (names and flags verified, bodies unknown)

- `WillowPlayerController:SkipMatinee()`: exec (`0x00020202`), script, no args; calls
  `ServerSkipMatinee()` (`0x002200C2`: a reliable server RPC). Present with identical signatures
  in BL2 and TPS. By name this is the "press a key to skip" handler for a `bIsSkippable` matinee.
  Nothing in the shipped games binds it to a key.
- `SetCinematicAutoSkip(bInSkip)` and `ToggleCinematicAutoSkip() -> bool` (native),
  `CinematicAutoSkip(Arg: str = ...)` (script, not exec). The engine object (`WillowGameEngine_0`,
  `mods_base.ENGINE`) has `bCinematicAutoSkip`, `CinematicAutoSkipDelay` and
  `CinematicAutoSkipMaps` (a list of map names). A QA feature: auto-skip cinematics, probably
  after a delay and maybe only on listed maps or only skippable ones. Not used in v0.1; a lever to
  probe if the staged skip disappoints.
- UE4's Matinee (a port of this code) documents `bIsSkippable` as "Lets you skip the matinee with
  the CANCELMATINEE exec command. Triggers all events to the end along the way." The engine's
  skip is therefore a jump to the end that fires the intermediate events, which in Willow is the
  `Last Frame` input plus the two `...WhenJumpToLastFrame` flags.

## Prior art

- FromDarkHell, "Rendered Cutscene Disabler" (BL2: 220 hotfixes over 31 maps) and "TPS Cutscene
  Disabler" (61 over 2 maps), in the BLCMods repo under `FromDarkHell/Quality of Life/`. Text
  mods, so per-cutscene surgery: Kismet output links rewired past the matinee to the Teleport /
  Toggle / ApplyBehavior / MissionCustomEvent nodes the cutscene would have triggered;
  `SeqAct_PlayBinkMovie.BinkMovieName` blanked (12 BL2 videos, 4 TPS); every
  `SeqAct_ToggleCinematicMode` flag set False (121 edits) so a player is never locked; and on two
  matinees `Position` / `ForceStartPosition` set to the end plus `bIsSkipped True` (and a
  `bSkippable True` that targets a property that does not exist). Lesson: the consequences of a
  cutscene live in its Kismet links and event keys, so a skip has to fire `Completed` and the
  event outputs. Credited by BL2Fix as the basis of its cutscene skip.
- BL2Fix (Nexus mod 277, legacy PythonSDK, source not public): ships "a full Python
  implementation of cutscene skip"; its notes say it removed the Lt. Tetra cutscene skip "to
  prevent softlocks".
- MOW531's "Cutscene Skip" for BL1 (new SDK): per-map Kismet rewiring from a
  `WillowGameInfo:PreCommitMapChange` POST hook. Not generalisable, but it shows `find_object` +
  `make_struct("SeqOpOutputInputLink", ...)` edits work from Python.
- ZetaDaemon's Dialog Skipper (willow2 mod DB): dialog only, not cutscenes.
- helios-tracker (ZooLSmith): `tools/probes/probe_cutscene.py` lists playing matinees with
  `unrealsdk.find_all("SeqAct_Interp", exact=False)` filtered on `bIsPlaying`; its notes are the
  source of the Bink and cinematic-mode observations above.
- There is no cutscene-skip mod for BL2/TPS on the willow2 mod DB.

## v0.1 design

Two options, exactly as asked: the `Always Skip Cutscenes` toggle and the `Skip Cutscene` key
(unbound by default). Everything the mod does is logged with the `[Cutscene Skip]` prefix;
cutscenes are rare, so there is no logging toggle.

Detecting an in-engine cutscene:

- Primary: PRE hook on `Engine.PlayerController:NotifyDirectorControl`. `bNowControlling` True
  with a `CurrentMatinee`: remember it (`WeakPointer`, keyed by path) and log `cutscene started`;
  with `Always Skip Cutscenes` on, queue a skip. False: forget it, log `cutscene ended`. Only for
  `IsLocalPlayerController()`.
- Secondary (`Always Skip Cutscenes` only): POST hook on
  `WillowGame.WillowPlayerController:ClientSetCinematicMode` with `bInCinematicMode` True starts a
  2 s window during which the tick hook scans `unrealsdk.find_all("SeqAct_Interp")` every 0.25 s
  for nodes with `bIsPlaying` whose `InterpData` has a director group (`CachedDirectorGroup`, or
  an `InterpGroupDirector` among `InterpGroups`). Catches a cutscene whose director notification
  never arrives. Exact class match on purpose: `WillowSeqAct_InterpMenu` (menu cameras) and
  `WillowSeqAct_DayNightCycle` are subclasses and must not be touched.
- Keybind: queue every remembered matinee that is still playing; if there is none, run one scan;
  if still none, log `no cutscene is playing`.

Skipping, from a POST hook on `WillowGame.WillowPlayerController:PlayerTick`, never from inside
the director or Kismet hooks (the notification is sent from inside the matinee's own update, and
changing the matinee there would be re-entrant). Staged, because no body of any native is known:

0. `bFireEventsWhenJumpToLastFrame = True`, `bFireCompleteEventWhenJumpToLastFrame = True`,
   `bIsSkipped = True`, then `ForceActivateInput(5)` (the `Last Frame` input). The flags make the
   jump fire the event outputs and `Completed`, which 107 and 6 of the BL2 cutscenes would
   otherwise not do.
1. `bIsSkippable = True`, then `pc.SkipMatinee()` (the game's own path).
2. `SetPosition(InterpData.InterpLength, bJump=False)`: moves to the end running the tracks
   through, so event keys fire; the next update completes the sequence.
3. `Stop()`: ends it without firing anything further. Last resort.

After each stage the tick hook waits 0.3 s and checks `bIsPlaying`; False means done (logged
with the stage that worked); True means the next stage. After stage 3 a `please report this`
warning. A stage that raises is logged and skipped. The first playtest log therefore says which
stage works, which is the one later versions keep.

Videos (`Always Skip Cutscenes` only): PRE hook on
`WillowGame.WillowPlayerController:ClientPlayBinkMovie` returns `Block`, unless the movie is the
loading-screen Bink (`BinkLoadingMovieName`). `bForceNoSkip` is logged, not honoured. A blocked
`SeqAct_PlayBinkMovie` is expected to finish at once because nothing is playing (guess; the
alternative, re-calling with an empty `MovieName`, is what FromDarkHell's blanked names amount
to). The key cannot interrupt a video: nothing ticks while one plays.

Co-op: the matinee lives on the host and replicates through a `MatineeActor`, so a client's local
jump would be overwritten. On a client (`WorldInfo.NetMode == NM_Client`, 3) the mod skips no
matinees (logged once per attempt) but still blocks videos. `coop_support = "HostOnly"`.

Map load (`WillowClientDisableLoadingMovie` POST): forget every remembered matinee, attempt and
scan window.

## Open until played

- Which stage works. Stage 0 is expected to; if the log says stage 1, the game's own skip handles
  something stage 0 does not and should become the primary.
- Whether `NotifyDirectorControl` fires for every cutscene (a `cutscene started` line per
  cutscene). If it never does, the cinematic-mode scan is carrying the always-skip and the key's
  scan is doing the work; both are logged with their reason.
- Whether the keybind's `InputKey` hook fires while in cinematic mode.
- Whether blocking `ClientPlayBinkMovie` lets `SeqAct_PlayBinkMovie` reach `Finished`, and what
  the game does for the intro movie and for `TC_*` title cards.
- Whether dialog started alongside a cutscene keeps playing after the skip (likely: it is
  triggered by separate Kismet nodes).
- Whether a skipped cutscene leaves the player in cinematic mode. The `Completed` output normally
  drives the toggle back off; if a report shows a frozen player with no cutscene, a watchdog that
  calls `TurnOffCinematicMode()` when `bCinematicMode` outlives every matinee is the fix.
- What `bIsSkipped` does, and whether `SetCinematicAutoSkip(True)` is a one-line always-skip.
- TPS: nothing played yet. Every hook target, field and function above exists there with the same
  signature (checked in the `tps/` stubs).

## Credits and prior art (audited 2026-10-09)

Caleb asked for a Credits section like enemy_item_scaling's. Audit: the only third-party mod code
read while building v0.1 was MOW531's BL1 Cutscene Skip (`__init__.py`, `maps.py`) and
helios-tracker's `tools/probes/probe_cutscene.py`. A line-by-line comparison against
`src/cutscene_skip/__init__.py` found no identical lines and one near-identical one, the bare SDK
call `ENGINE.GetCurrentWorldInfo()`. So no code was copied or closely adapted; what was taken is
hook target names, game facts and techniques, none of which carries a licence obligation.
Player-facing credits are in the README's Credits section and `docs/nexus.md`; this is the full
list.

| Source | Author | Licence | What it gave this mod |
|---|---|---|---|
| PythonSDK: willow2-mod-manager, mods_base, keybinds, unrealsdk, pyunrealsdk | apple1417 and bl-sdk contributors | LGPL-3.0 | the runtime, the API and the keybind dispatch; not bundled in the `.sdkmod` (players install it), so LGPL imposes nothing |
| Rendered Cutscene Disabler (BL2), TPS Cutscene Disabler | FromDarkHell | none (BLCMods has a disclaimer, no licence grant) | which Kismet nodes each cutscene uses; the lesson that a cutscene's consequences hang off its `Completed` and event outputs; its `bIsSkipped` / `Position` edits suggested the last-frame stage; its blanked `BinkMovieName`s suggested blocking videos. Text mods, nothing copied |
| Helios Tracker research notes and `probe_cutscene.py` | ZooLSmith | GPL-3.0 | a Bink renders no frames (so the key can't interrupt a video); the `ClientPlayBinkMovie` hook target and `bForceNoSkip`; the cinematic-mode sequence around a video and `bCinematicMode` staying on after a map load; the `find_all("SeqAct_Interp")` + `bIsPlaying` scan idea. No code copied |
| bl-py-stubs (`gamestubs.zip`) | Justin99x | none found | dev only: every class, field and function name and signature in both games; the BL2/TPS identity checks |
| BL2-SDK dump | RobChiocchio | none found | dev only: function flags (native, exec, event, server RPC) |
| FT/BLCMM Explorer object dumps | apocalyptech | BSD-3-Clause | dev only: every `SeqAct_Interp`, `InterpData`, `SeqAct_PlayBinkMovie` and `SeqAct_ToggleCinematicMode` in both games; the `Last Frame` input and the `...WhenJumpToLastFrame` flag counts |
| Unreal Engine 4 Matinee API docs (`AMatineeActor.bIsSkippable`) | Epic Games | documentation | dev only: what `bIsSkippable` means in the engine Willow's Matinee descends from |
| Official SDK install guide (bl-sdk.github.io/willow2-mod-db) | bl-sdk contributors | none found | the README install steps are condensed from it (via the enemy_item_scaling README), and say so |
| bl-sdk repos' ruff/pyright config | apple1417 | GPL-3.0 / LGPL-3.0 | the root `pyproject.toml` lint lists are copied verbatim (via enemy_item_scaling); dev only, never shipped |

Looked at and not used: MOW531's BL1 Cutscene Skip (per-map Kismet rewiring, BL1 only; the
approach was not taken), BL2Fix (Nexus mod 277; source not public, only its description read),
ZetaDaemon's Dialog Skipper (dialog only; source not read), the BLCM wiki's Kismet page. If code
from any GPL source is ever copied in, the mod would have to be GPL-3.0; keep borrowing ideas and
facts, not code.
