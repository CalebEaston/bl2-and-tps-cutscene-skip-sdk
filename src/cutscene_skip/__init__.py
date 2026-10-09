from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import ENGINE, BoolOption, build_mod, hook, keybind
from unrealsdk import logging
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import WeakPointer

if TYPE_CHECKING:
    from collections.abc import Callable

    from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

# Injected by build_mod() from pyproject.toml
__version__: str
__version_info__: tuple[int, ...]

LOG_PREFIX = "[Cutscene Skip]"

always_skip = BoolOption(
    "Always Skip Cutscenes",
    False,
    description=(
        "Skip every cutscene the moment it starts: in-game cutscenes and full-screen videos"
        " (DLC intros and endings). Loading screens are left alone."
    ),
)

# Every Matinee node in these games has six inputs: Play, Reverse, Stop, Pause, Change Dir and
# Last Frame. Activating the last one jumps the cutscene to its end.
LAST_FRAME_INPUT = 5

# How long to wait after each skip attempt before checking whether the cutscene has stopped
STAGE_WAIT_SECONDS = 0.3

# After cinematic mode turns on, how long and how often to look for a cutscene that didn't
# announce itself through the director notification
SCAN_SECONDS = 2.0
SCAN_INTERVAL_SECONDS = 0.25

# WorldInfo.NetMode of a co-op client. The host owns the cutscene; a client can't end it.
NM_CLIENT = 3


@dataclass
class SkipAttempt:
    """A cutscene the mod is trying to end, and how far down the list of methods it has got."""

    matinee: WeakPointer
    name: str
    stage: int = 0
    stage_started: bool = False
    waited: float = 0.0


# Cutscenes being skipped right now, keyed by the matinee's path
_attempts: dict[str, SkipAttempt] = {}
# Matinees currently controlling the camera, keyed by path
_cutscenes: dict[str, WeakPointer] = {}
# Seconds left in the scan window opened by cinematic mode, and seconds since the last scan
_scan_left = 0.0
_scan_since = 0.0


def _is_coop_client() -> bool:
    """Whether this game is a co-op client, which can't end a cutscene the host owns."""
    world = ENGINE.GetCurrentWorldInfo()
    return world is not None and int(world.NetMode) == NM_CLIENT


def _cutscene_length(matinee: UObject) -> float:
    data = matinee.InterpData
    return 0.0 if data is None else float(data.InterpLength)


def _has_director(matinee: UObject) -> bool:
    """Whether a Matinee node drives a camera, which is what makes it a cutscene."""
    data = matinee.InterpData
    if data is None:
        return False
    if data.CachedDirectorGroup is not None:
        return True
    director = unrealsdk.find_class("InterpGroupDirector")
    return any(group is not None and group.Class._inherits(director) for group in data.InterpGroups)


def _find_playing_cutscenes() -> list[UObject]:
    """
    Finds every in-engine cutscene that is playing right now.

    Exact class match on purpose: the menu camera (WillowSeqAct_InterpMenu) and the day/night
    cycle are Matinee subclasses and must be left alone.
    """
    return [
        matinee
        for matinee in unrealsdk.find_all("SeqAct_Interp")
        if bool(matinee.bIsPlaying) and _has_director(matinee)
    ]


def _request_skip(matinee: UObject, reason: str) -> None:
    """
    Queues a cutscene to be skipped on the next tick.

    Args:
        matinee: The playing SeqAct_Interp.
        reason: What asked for the skip, for the log line.
    """
    name = matinee._path_name()
    if name in _attempts:
        return
    logging.info(f"{LOG_PREFIX} skipping {name} ({reason})")
    _attempts[name] = SkipAttempt(WeakPointer(matinee), name)


def _stage_last_frame(matinee: UObject, _pc: UObject) -> None:
    # The flags make the jump fire the node's event outputs and its Completed output; most
    # cutscenes have the first off and a few have the second off, and the level script waits on
    # them.
    matinee.bFireEventsWhenJumpToLastFrame = True
    matinee.bFireCompleteEventWhenJumpToLastFrame = True
    matinee.bIsSkipped = True
    matinee.ForceActivateInput(LAST_FRAME_INPUT)


def _stage_skip_matinee(matinee: UObject, pc: UObject) -> None:
    matinee.bIsSkippable = True
    pc.SkipMatinee()


def _stage_set_position(matinee: UObject, _pc: UObject) -> None:
    # bJump False runs the tracks through to the end, so event keys on the way still fire
    matinee.SetPosition(_cutscene_length(matinee), False)


def _stage_stop(matinee: UObject, _pc: UObject) -> None:
    matinee.Stop()


# In the order they are tried. Each one is a different way of ending a Matinee; the first that
# leaves it not playing wins, and the log says which it was.
STAGES: tuple[tuple[str, Callable[[UObject, UObject], None]], ...] = (
    ("last frame", _stage_last_frame),
    ("the game's own skip", _stage_skip_matinee),
    ("jump to the end", _stage_set_position),
    ("stop", _stage_stop),
)


def _run_stage(attempt: SkipAttempt, matinee: UObject, pc: UObject) -> None:
    label, action = STAGES[attempt.stage]
    try:
        action(matinee, pc)
    except Exception as ex:  # noqa: BLE001 - a failing method must not stop the next from running
        logging.warning(f"{LOG_PREFIX} {label} failed on {attempt.name}: {ex!r}")
    attempt.stage_started = True
    attempt.waited = 0.0


def _advance_attempt(name: str, attempt: SkipAttempt, pc: UObject, delta: float) -> None:
    matinee = attempt.matinee()
    if matinee is None:
        # The level it belonged to is gone
        del _attempts[name]
        return
    if not attempt.stage_started:
        _run_stage(attempt, matinee, pc)
        return
    attempt.waited += delta
    if attempt.waited < STAGE_WAIT_SECONDS:
        return
    label = STAGES[attempt.stage][0]
    if not bool(matinee.bIsPlaying):
        logging.info(f"{LOG_PREFIX} skipped {name} ({label})")
        del _attempts[name]
        return
    attempt.stage += 1
    attempt.stage_started = False
    if attempt.stage >= len(STAGES):
        logging.warning(
            f"{LOG_PREFIX} could not skip {name}: still playing after every method"
            " (please report this)",
        )
        del _attempts[name]
        return
    logging.info(f"{LOG_PREFIX} {name} is still playing; trying {STAGES[attempt.stage][0]}")


def _scan_for_cutscenes(delta: float) -> None:
    """Looks for a playing cutscene every so often while the scan window is open."""
    global _scan_left, _scan_since
    _scan_left -= delta
    _scan_since += delta
    if _scan_since < SCAN_INTERVAL_SECONDS:
        return
    _scan_since = 0.0
    found = _find_playing_cutscenes()
    if not found:
        return
    _scan_left = 0.0
    for matinee in found:
        _request_skip(matinee, "cinematic mode")


@hook("Engine.PlayerController:NotifyDirectorControl")
def on_director_control(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Notices a cutscene taking or releasing the camera.

    Nothing is changed here: the matinee sends this from inside its own update, so the skip
    itself waits for the next tick.
    """
    matinee = args.CurrentMatinee
    if matinee is None or not obj.IsLocalPlayerController():
        return
    name = matinee._path_name()
    if not bool(args.bNowControlling):
        if _cutscenes.pop(name, None) is not None:
            logging.info(f"{LOG_PREFIX} cutscene ended: {name}")
        return
    if name not in _cutscenes:
        _cutscenes[name] = WeakPointer(matinee)
        logging.info(f"{LOG_PREFIX} cutscene started: {name} ({_cutscene_length(matinee):.1f} s)")
    if always_skip.value and not _is_coop_client():
        _request_skip(matinee, "Always Skip Cutscenes")


@hook("WillowGame.WillowPlayerController:ClientSetCinematicMode", Type.POST)
def on_cinematic_mode(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Opens a short window of looking for a playing cutscene whenever cinematic mode turns on.

    Backstop for a cutscene whose director notification never arrives. Map changes use cinematic
    mode too; a scan that finds nothing costs nothing.
    """
    global _scan_left, _scan_since
    if not bool(args.bInCinematicMode) or not always_skip.value:
        return
    if not obj.IsLocalPlayerController() or _is_coop_client():
        return
    _scan_left = SCAN_SECONDS
    _scan_since = SCAN_INTERVAL_SECONDS


@hook("WillowGame.WillowPlayerController:PlayerTick", Type.POST)
def on_player_tick(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """Runs the queued skips and the cinematic-mode scan, one step per frame."""
    if not _attempts and _scan_left <= 0.0:
        return
    delta = float(args.DeltaTime)
    if _scan_left > 0.0:
        _scan_for_cutscenes(delta)
    for name, attempt in list(_attempts.items()):
        _advance_attempt(name, attempt, obj, delta)


def _is_loading_movie(pc: UObject, movie_name: str) -> bool:
    loading = str(pc.BinkLoadingMovieName)
    strip = movie_name.lower().removesuffix(".bik")
    return bool(strip) and strip == loading.lower().removesuffix(".bik")


@hook("WillowGame.WillowPlayerController:ClientPlayBinkMovie")
def on_play_bink_movie(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    """
    Stops a full-screen video from starting when every cutscene is to be skipped.

    Nothing runs while a video plays, so the only time to stop one is before it starts.
    """
    if not always_skip.value:
        return None
    movie_name = str(args.MovieName)
    if _is_loading_movie(obj, movie_name):
        return None
    note = " (the game marked it as not skippable)" if bool(args.bForceNoSkip) else ""
    logging.info(f"{LOG_PREFIX} skipping video {movie_name or '(unnamed)'}{note}")
    return Block


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST)
def on_map_loaded(
    _obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """Forgets everything from the previous map once a new one has loaded."""
    global _scan_left
    _attempts.clear()
    _cutscenes.clear()
    _scan_left = 0.0


@keybind(
    "Skip Cutscene",
    None,
    description=(
        "Skips the in-game cutscene that is playing right now.\n"
        "Can't interrupt a full-screen video; turn on Always Skip Cutscenes for those."
    ),
)
def skip_cutscene() -> None:
    """Skips every cutscene that is playing, starting with the ones that have the camera."""
    if _is_coop_client():
        logging.info(f"{LOG_PREFIX} only the host can skip a cutscene in co-op")
        return
    targets = [
        matinee
        for pointer in _cutscenes.values()
        if (matinee := pointer()) is not None and bool(matinee.bIsPlaying)
    ]
    if not targets:
        targets = _find_playing_cutscenes()
    if not targets:
        logging.info(f"{LOG_PREFIX} no cutscene is playing")
        return
    for matinee in targets:
        _request_skip(matinee, "Skip Cutscene key")


mod = build_mod(
    options=[always_skip],
    keybinds=[skip_cutscene],
)
