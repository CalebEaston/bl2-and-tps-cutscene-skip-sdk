# Playtest checklist

Plain steps, nothing to type into the console. Every setting is under the main menu's `MODS`
entry, `Cutscene Skip` (enable the mod there first). The mod writes one line to
`<game>\Binaries\Win32\Plugins\unrealsdk.log` for everything it does (`<game>` is the folder
that contains `sdk_mods`). The file is emptied each time the game starts, so copy lines out
before relaunching. Searching it for `Cutscene Skip` finds every line of ours. The developer
version with console probes is [testing-probes.md](testing-probes.md).

Nothing here has been played yet, so the first run is as much about which lines appear as about
what you see. Section 1 matters most.

A full run of a skipped cutscene looks like this in the log (the long name in the middle is the
game's internal name for the cutscene; I match those up against the game data):

```
[Cutscene Skip] cutscene started: SouthernShelf_Dynamic.TheWorld:PersistentLevel.Main_Sequence.SeqAct_Interp_3 (11.8 s)
[Cutscene Skip] skipping SouthernShelf_Dynamic.TheWorld:PersistentLevel.Main_Sequence.SeqAct_Interp_3 (Always Skip Cutscenes)
[Cutscene Skip] skipped SouthernShelf_Dynamic.TheWorld:PersistentLevel.Main_Sequence.SeqAct_Interp_3 (last frame)
[Cutscene Skip] cutscene ended: SouthernShelf_Dynamic.TheWorld:PersistentLevel.Main_Sequence.SeqAct_Interp_3
```

The word in brackets on the `skipped` line is which of the mod's four methods ended the cutscene:
`last frame`, `the game's own skip`, `jump to the end` or `stop`. If the first one did not work
there is an extra `is still playing; trying ...` line before it. Whatever it says, send it: the
method that works is the one later versions will keep.

## 1. Always skip, in-game cutscenes

Settings: `Always Skip Cutscenes` on. A character early in the story, or a new one. Southern
Shelf has three in a row: Boom and Bewm's intro, Captain Flynt's intro, and the Claptrap scenes;
Windshear Waste has Knuckle Dragger pulling out Claptrap's eye.

- Each cutscene ends within a second of starting. The game goes on as if it had played: the
  boss is there, the door is open, the mission objective moved on.
- The log has the four lines above for each one.
- Dialogue from the cutscene may keep talking over the fight. Expected; say if it bothers you.
- If you are left standing still with no HUD and nothing happening for more than a few seconds:
  note which cutscene, and send the lines. That is the one failure that matters most.
- If a cutscene played in full with no `cutscene started` line: note which, and whether any
  `skipping ... (cinematic mode)` line appeared instead.
- If a cutscene played in full and the log has a `please report this` line: send it with the
  `is still playing` lines before it.
- `cutscene started` lines for things that are not cutscenes (a camera pan when you complete a
  challenge, an elevator ride) are fine as long as nothing broke; mention them anyway.

## 2. Always skip, videos

Settings: `Always Skip Cutscenes` on. Enter a DLC for the first time on a character (Oasis for
Captain Scarlett, the Badass Crater for Mr. Torgue, Hunter's Grotto for Hammerlock, Unassuming
Docks for Tiny Tina), or start a brand-new character for the opening movie.

- The video does not play; you are in the level straight away.
- The log has `skipping video Orchid_Intro` (or `Iris_Intro`, `Sage_Intro`, `Aster_Intro`, the
  intro's own name) and nothing else about it.
- If the screen stays black or the game hangs where the video would have been: note where, and
  send every `[Cutscene Skip]` line. Quit with Alt+F4 if you must.
- Meeting Zed, Marcus, Tannis or Scooter in Sanctuary for the first time on a character: their
  short title-card videos (`TC_Zed`...) are skipped too. Say if anything looks wrong afterwards.
- Loading screens must look exactly as before. If one is missing or black, say so.

## 3. The key

Settings: `Always Skip Cutscenes` off, `Skip Cutscene` bound to a key you don't use (F8, say).
A cutscene that you can trigger again, or a fresh character.

- Let the cutscene start, press the key: it ends. The log has `skipping ... (Skip Cutscene key)`
  and a `skipped` line.
- Press the key when no cutscene is playing: nothing happens in the game; the log says
  `no cutscene is playing`.
- Press the key during a DLC intro video: nothing happens (the game ignores everything while a
  video plays). Expected; this is what `Always Skip Cutscenes` is for.
- If the key does nothing during a cutscene and the log has no `skipping` line at all: the game
  is swallowing the key during cutscenes. Say which key you bound, and whether the key works
  outside a cutscene (bind it, press it during normal play, look for `no cutscene is playing`).

## 4. Off

Settings: `Always Skip Cutscenes` off, `Skip Cutscene` unbound. Cutscenes play as normal, and
the log only has `cutscene started` / `cutscene ended` lines (and `skipping video` must never
appear).

## 5. Co-op

Only if convenient. As host with `Always Skip Cutscenes` on, cutscenes end for everyone. A
client pressing the key gets `only the host can skip a cutscene in co-op` in its log and nothing
else happens.

## 6. The Pre-Sequel

Same mod file, same SDK zip, installed into the Pre-Sequel folder. Nothing here has been played.

- Main menu `MODS`: the mod must be enableable, not shown as yellow `Incompatible`.
- Section 1 on a new character: Jack's intro and the Claptrap intro cutscenes on the Helios
  landing are the first ones. Section 3 with any later cutscene.
- Section 2: the opening movie on a new character.
- Any block containing `Traceback` or `AttributeError` after the first map load: send the whole
  block.

## What to send

The log lines mentioned above, which game (Borderlands 2 or The Pre-Sequel), the mod version
shown in the `MODS` menu, which options were set, and which cutscene (where you were, who it was
about). One line about what you were doing is enough. Post it at
https://github.com/CalebEaston/bl2-and-tps-cutscene-skip-sdk/issues or wherever you got the mod.
