# Console probes

The developer version of [testing.md](testing.md): things to type or paste into the console
(tilde twice) and what each one settles. Everything else, including the expected log lines, is
in the plain checklist.

## 0. The mod is live

```
py import cutscene_skip as m; print(m.mod.is_enabled, [h.get_active_count() for h in m.mod.hooks], m.skip_cutscene.key)
```

Expect `True`, a list of ones (one hook each), and the bound key or `None`. A count only proves a
hook is registered, not that its function exists in this game; the next probe proves existence.

```
py import unrealsdk; print([(f, [p.Name for p in unrealsdk.find_object('Function', f)._properties()]) for f in ('Engine.PlayerController:NotifyDirectorControl', 'WillowGame.WillowPlayerController:ClientSetCinematicMode', 'WillowGame.WillowPlayerController:PlayerTick', 'WillowGame.WillowPlayerController:ClientPlayBinkMovie', 'WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie', 'WillowGame.WillowPlayerController:SkipMatinee', 'Engine.SeqAct_Interp:SetPosition', 'Engine.SequenceOp:ForceActivateInput')])
```

Expect every function to resolve (a `ValueError` names a missing one) with the parameters
`bNowControlling, CurrentMatinee`; `bInCinematicMode, ...`; `DeltaTime`; `MovieName, bStreamed,
bLooping, bForceNoSkip`; none; none; `NewPosition, bJump`; `InputIdx`.

## 1. What is playing right now

Run during a cutscene (pause with the key unbound and the toggle off, or just type fast):

```
py import unrealsdk; print([(s._path_name(), s.bIsPlaying, round(s.Position, 2), s.InterpData is not None and s.InterpData.CachedDirectorGroup is not None, s.bIsSkippable, s.bFireEventsWhenJumpToLastFrame, s.bFireCompleteEventWhenJumpToLastFrame, [l.LinkDesc for l in s.InputLinks]) for s in unrealsdk.find_all('SeqAct_Interp') if s.bIsPlaying])
```

Settles: which Matinee nodes are playing, whether the cutscene's `InterpData` is filled in and
has a director group (what `_find_playing_cutscenes` relies on), the flag values, and that input
5 is `Last Frame`.

```
py from mods_base import get_pc; pc = get_pc(); print(pc.bCinematicMode, pc.bKismetEnabledCinematicMode, pc.bCinemaDisableInputButton, pc.ControllingDirTrackInst, pc.IsLocalPlayerController())
```

Settles: whether cinematic mode is on and whether the director track instance is set on the
controller (a second way to find the cutscene).

## 2. Trying one method by hand

With the mod's toggle off, during a cutscene, one of these at a time. Each is one of the mod's
stages; the log's `cutscene ended` line (or `bIsPlaying` going False in probe 1) says it worked.

```
py import unrealsdk; s = [s for s in unrealsdk.find_all('SeqAct_Interp') if s.bIsPlaying and s.InterpData and s.InterpData.CachedDirectorGroup][0]; s.bFireEventsWhenJumpToLastFrame = True; s.bFireCompleteEventWhenJumpToLastFrame = True; s.ForceActivateInput(5); print(s._path_name())
```

```
py from mods_base import get_pc; import unrealsdk; s = [s for s in unrealsdk.find_all('SeqAct_Interp') if s.bIsPlaying and s.InterpData and s.InterpData.CachedDirectorGroup][0]; s.bIsSkippable = True; get_pc().SkipMatinee(); print(s._path_name())
```

```
py import unrealsdk; s = [s for s in unrealsdk.find_all('SeqAct_Interp') if s.bIsPlaying and s.InterpData and s.InterpData.CachedDirectorGroup][0]; s.SetPosition(s.InterpData.InterpLength, False); print(s._path_name())
```

## 3. The game's own auto-skip

Unknown semantics; worth one try on a map with a repeatable cutscene. Before the cutscene:

```
py from mods_base import ENGINE, get_pc; get_pc().SetCinematicAutoSkip(True); ENGINE.CinematicAutoSkipDelay = 0.0; print(ENGINE.bCinematicAutoSkip, ENGINE.CinematicAutoSkipDelay, list(ENGINE.CinematicAutoSkipMaps))
```

If the cutscene skips itself (with the mod's toggle off), `SetCinematicAutoSkip(True)` is a
one-line always-skip and worth comparing with the staged one. Turn it back off with
`get_pc().SetCinematicAutoSkip(False)`.

## 4. Does the keybind hook fire in cinematic mode

```
py import unrealsdk; unrealsdk.hooks.log_all_calls(True)
```

Press the bound key during a cutscene, then `log_all_calls(False)`, and grep the log for
`WillowUIInteraction:InputKey` around that moment. Present means the SDK keybind path works in
cinematic mode; absent means the game stops input before the UI interaction and the key needs
another path (`WillowGame.WillowPlayerInput:InputKey`, or the game's own `SkipMatinee` exec bound
in `WillowInput.ini`).

## 5. After a skipped video

```
py from mods_base import get_pc; pc = get_pc(); print(pc.IsAnyBinkMoviePlaying(), pc.bCinematicMode, pc.myHUD.bShowHUD)
```

Expect `False`, `False`, `True` once the level is in. `bCinematicMode` still True long after a
skipped video means the level script is waiting on the video's `Finished` output; the fallback
is to re-call `ClientPlayBinkMovie` with an empty name instead of blocking it.
