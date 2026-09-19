import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import socket
import random
import vlc
import pathlib
from backend.player import DJPlayer
import asyncio
import vlc
import asyncio
import subprocess
from pathlib import Path
import re
from difflib import get_close_matches
from mutagen.easyid3 import EasyID3

MUSIC_DIR = r"D:\Projects\ai-dj\music"
transition_lock = asyncio.Lock()
TRANSITION_BUFFER_SEC = 120   # give AI 2 minutes to generate mix
TRANSITION_TRIGGER_SEC = 90    # start thinking about mixing early
TRANSITION_SWAP_SEC = 5       # when to actually switch audio

def normalize_song_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())
def get_random_song():
    songs = list(Path(MUSIC_DIR).glob("*.mp3"))
    if not songs:
        return None
    return str(random.choice(songs))

def build_song_index():
    index = {}

    for file_path in Path(MUSIC_DIR).glob("*.mp3"):
        candidates = {
            normalize_song_text(file_path.stem)
        }

        try:
            audio = EasyID3(str(file_path))
            title = audio.get("title", [file_path.stem])[0]
            artist = audio.get("artist", [""])[0]

            candidates.add(normalize_song_text(title))

            if artist:
                candidates.add(normalize_song_text(artist))
                candidates.add(normalize_song_text(f"{artist} {title}"))
                candidates.add(normalize_song_text(f"{title} {artist}"))
        except Exception:
            pass

        for key in candidates:
            if key:
                index[key] = str(file_path)

    return index


SONG_INDEX = build_song_index()


def find_song_file(query: str) -> str | None:
    q = normalize_song_text(query)

    if not q:
        return None

    if q in SONG_INDEX:
        return SONG_INDEX[q]

    matches = get_close_matches(
        q,
        list(SONG_INDEX.keys()),
        n=1,
        cutoff=0.55
    )

    if matches:
        return SONG_INDEX[matches[0]]

    return None

def windows_path_to_wsl(path: str) -> str:
    p = Path(path)
    drive = p.drive[0].lower()
    rest = str(p).replace(p.drive, "").replace("\\", "/")
    return f"/mnt/{drive}{rest}"

def run_transition_mixer(song1_path: str, song2_path: str):
    wsl_song1 = windows_path_to_wsl(song1_path)
    wsl_song2 = windows_path_to_wsl(song2_path)

    output_windows = rf"D:\temp\mix_{uuid.uuid4().hex}.wav"
    output_wsl = windows_path_to_wsl(output_windows)

    Path(r"D:\temp").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "wsl",
            "-d",
            "Ubuntu",
            "python3",
            "/mnt/d/Projects/ai-dj/backend/automix_engine.py",
            wsl_song1,
            wsl_song2,
            output_wsl
        ],
        capture_output=True,
        text=True,
        check=True
    )

    print(result.stdout)

    meta_path = Path(output_windows + ".json")
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    return output_windows, meta

app = FastAPI()
player = DJPlayer()
song_requests = []

#songs = list(pathlib.Path("songs").glob("*.mp3"))

#selected_song = random.choice(songs)
player.load_playlist([
    r"D:\Projects\ai-dj\music\Echoes.mp3",
    r"D:\Projects\ai-dj\music\Fade.mp3"
])

print(player.queue)
current_index = 0


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))  # doesn't actually send data
    ip = s.getsockname()[0]
    s.close()
    return ip

    
async def send_status(ws):
    await ws.send_text(json.dumps({
        "type": "status",
        "currentSong": player.get_current_song_name(),
        "index": player.index
    }))

async def song_watcher():
    CHECK_INTERVAL = 0.03 # check every 30ms for song end / transition point
    SWAP_LEAD_SEC = 1.5  # bump this to 1.25 if it still lands a hair late

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        if not player.queue:
            fallback = get_random_song()

            if fallback:
                print("🎲 No queue → playing random fallback:", fallback)

                player.queue.append(fallback)
                player.index = 0
                player.ensure_playing()

                await manager.send_to_host({
                    "type": "status",
                    "currentSong": player.get_current_song_name(),
                    "index": player.index
                })

            continue
                
        state = player.player.get_state()

        if not player.queue:
            continue

        # Ignore the short fake Ended event caused by stopping VLC manually
        if time.monotonic() < player.ignore_end_until and state == vlc.State.Ended:
            continue

        # If a bridge is playing and it naturally ends, resume the next song
        if state == vlc.State.Ended:
            if player.transition_started:
                print("🎧 Bridge finished naturally")

                resume_sec = player.transition_resume_sec
                target_index = player.transition_target_index

                player.clear_transition()

                print("\n========== TRANSITION END ==========")
                print("Queue:")

                for i, song in enumerate(player.queue):
                    marker = " <-- CURRENT INDEX" if i == player.index else ""
                    print(f"{i}: {Path(song).stem}{marker}")

                print("Index before increment IN LINE 196:", player.index)
                if target_index is None:
                    target_index = player.index + 1

                
                print("Index after increment IN LINE 196:", player.index)

                if player.index < len(player.queue):
                    print(
                        "Will resume into:",
                        Path(player.queue[player.index]).stem
                    )

                player.index = target_index

                if player.index < len(player.queue):
                    print(
                        f"▶ Resuming {Path(player.queue[player.index]).stem} "
                        f"at {resume_sec:.2f}s"
                    )
                    player.play_current(resume_sec)
                    await manager.send_to_host({
                        "type": "status",
                        "currentSong": player.get_current_song_name(),
                        "index": player.index
                    })
                    await asyncio.sleep(0.15)
                    player.apply_pending_seek()
                else:
                    player.player.stop()

            else:
                print("🎵 Song ended normally")
                player.clear_transition()
                old_song = player.queue[player.index] if player.queue else None

                player.next()

                new_song = player.get_current_song_name()

                await manager.send_to_host({
                    "type": "song_finished",
                    "song": old_song
                })

                await manager.send_to_host({
                    "type": "status",
                    "currentSong": new_song,
                    "index": player.index
                })
            continue

        if not player.is_playing():
            continue

        player.apply_pending_seek()

        duration = player.get_duration_ms()
        position = player.get_position_ms()

        if duration <= 0 or position < 0:
            continue

        current_sec = position / 1000.0
        remaining_sec = (duration - position) / 1000.0

        next_song = player.get_next_song()

        print(
            f"[DJ] idx={player.index}/{len(player.queue)-1} "
            f"cur={Path(player.queue[player.index]).stem} "
            f"next={(Path(next_song).stem if next_song else 'NONE')} "
            f"state={state} "
            f"pos={current_sec:.2f}s "
            f"rem={remaining_sec:.2f}s "
            f"ready={player.transition_ready} "
            f"started={player.transition_started} "
            f"building={player.transition_building}"
        )

        # Pre-generate as soon as a next song exists
        if (
            next_song
            and not player.transition_ready
            and not player.transition_building
            and not player.transition_started
        ):
            print("🎧 Pre-generating transition ASAP...")
            asyncio.create_task(prepare_transition())

        # Switch into the bridge at the planned exit point
        if (
            player.transition_ready
            and not player.transition_started
            and player.transition_exit_sec is not None
            and next_song is not None
            and player.transition_for == (player.queue[player.index], next_song)
            and current_sec >= max(0.0, player.transition_exit_sec - SWAP_LEAD_SEC)
        ):
            print("\n========== TRANSITION END ==========")
            print("Queue:")

            for i, song in enumerate(player.queue):
                marker = " <-- CURRENT INDEX" if i == player.index else ""
                print(f"{i}: {Path(song).stem}{marker}")

            print("Index before increment IN LINE 283:", player.index)
            player.transition_started = True
            player.transition_target_index = player.index + 1
            player.ignore_end_until = time.monotonic() + 0.9

            print("Index after increment IN LINE 283:", player.index)

            if player.index < len(player.queue):
                print(
                    "Will resume into:",
                    Path(player.queue[player.index]).stem
                )
            print(
                f"🔥 Switching into bridge: "
                f"{Path(player.transition_file).name} | "
                f"target={Path(next_song).stem}"
            )

            player.player.stop()
            player.player.set_media(
                player.transition_media or player.instance.media_new(player.transition_file)
            )
            player.player.play()

def should_swap(player, swap_sec=5):
    current_time = player.get_position_ms() / 1000
    duration = player.get_duration_ms() / 1000
    return current_time >= (duration - swap_sec)

async def prepare_transition():
    if player.transition_building:
        return

    player.transition_building = True
    build_index = player.index

    try:
        current = player.queue[build_index]
        next_song = player.get_next_song()

        if not next_song:
            print("No next song available.")
            return

        expected_pair = (current, next_song)
        print(f"🎧 Generating mix: {Path(current).stem} → {Path(next_song).stem}")

        mix_file, meta = await asyncio.to_thread(
            run_transition_mixer,
            current,
            next_song
        )

        # Queue may have changed while mixing
        if build_index != player.index:
            print("⚠️ Transition discarded: index changed during build.")
            return

        if player.get_next_song() != next_song or player.queue[player.index] != current:
            print("⚠️ Transition discarded: current/next pair changed during build.")
            return

        player.transition_file = mix_file
        player.transition_media = player.instance.media_new(mix_file)
        player.transition_exit_sec = float(meta.get("exit_time_sec", 0.0))
        player.transition_resume_sec = float(meta.get("resume_offset_sec", 0.0))
        player.transition_for = expected_pair
        print(
            f"TRANSITION GENERATED FOR:\n"
            f"FROM={Path(current).stem}\n"
            f"TO={Path(next_song).stem}"
        )
        player.transition_target_index = build_index + 1
        player.transition_ready = True
        player.transition_started = False

        print(
            "TRANSITION WAS FOR:",
            player.transition_for
        )

        print(
            f"✅ Transition ready: {Path(mix_file).name} | "
            f"exit={player.transition_exit_sec:.2f}s "
            f"resume={player.transition_resume_sec:.2f}s "
            f"pair=({Path(current).stem} -> {Path(next_song).stem})"
        )

    except Exception as e:
        print("❌ Transition generation failed:")
        print(e)

    finally:
        player.transition_building = False


class ConnectionManager:
    def __init__(self):
        self.active_guests: dict[str, WebSocket] = {}
        self.host_connection: WebSocket | None = None
    
    async def connect_host(self, websocket: WebSocket):
        await websocket.accept()
        self.host_connection = websocket
        print("✅ HOST STORED IN MANAGER:", self.host_connection)
        await send_status(websocket)

    async def connect_guest(self, websocket: WebSocket):
        await websocket.accept()
        guest_id = str(uuid.uuid4())
        self.active_guests[guest_id] = websocket
        print("GUEST CONNECTED - ID:", guest_id)
        return guest_id


    def disconnect_guest(self, guest_id: str):
        if guest_id in self.active_guests:
            del self.active_guests[guest_id]
            print("GUEST DISCONNECTED - ID:", guest_id)
    
    async def disconnect_host(self):
        print("HOST DISCONNECTING...")

        if self.host_connection:
            try:
                await self.host_connection.close()
            except:
                pass

        self.host_connection = None

    async def send_to_host(self, message):
        if self.host_connection:
            await self.host_connection.send_text(json.dumps(message))
        else:
            print("No host connected to send message")

manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    asyncio.create_task(song_watcher())
 #   run_transition_mixer(
 #       r"D:\Projects\ai-dj\music\CantTameHer.mp3",
 #       r"D:\Projects\ai-dj\music\TurnDownForWhat.mp3"
 #   )
    print("DONE TRYING TO RUN TRANSITION MIXER ON STARTUP") ################################################################################################################################################################################

@app.get("/") #decorator - when someone goes to the home page, this function will be executed
def home():
    return {"message": "YAY Server is runninggggg"}

"""
@app.websocket("/ws/test") #websocket endpoint
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept() #accept connection
    while True:
        message = await websocket.receive_text() #wait for message from client
        await websocket.send_text(f"Message received: {message}") #send response back to client
"""

@app.get("/config")
def config():
    return {
        "ip": get_local_ip(),
        "port": 8000
    }

@app.websocket("/ws/host")
async def websocket_host(websocket: WebSocket):
    await manager.connect_host(websocket)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print("Bad JSON:", raw)
                continue

            msg_type = data.get("type")

            # ---- control logic ----
            if msg_type == "play":
                player.play()

            elif msg_type == "pause":
                player.pause()

            elif msg_type == "next":
                if not player.queue or player.index >= len(player.queue) - 1:
                    fallback = get_random_song()
                    if fallback:
                        player.add_to_queue(fallback)

                player.next()

            else:
                print("Unknown command:", msg_type)

            # ALWAYS send updated state AFTER action
            await send_status(websocket)

    except WebSocketDisconnect:
        await manager.disconnect_host()
        player.player.stop()


def find_song_file(user_input: str):
    """
    Tries to find the closest matching mp3 in MUSIC_DIR.
    Handles:
    - spaces
    - punctuation
    - capitalization
    - minor misspellings
    - artist names in request
    """

    user_input = user_input.lower()

    # remove special chars
    user_input = re.sub(r"[^a-z0-9 ]", "", user_input)

    music_files = list(Path(MUSIC_DIR).glob("*.mp3"))

    lookup = {}

    for file in music_files:

        # TurnDownForWhat -> turndownforwhat
        key = re.sub(
            r"[^a-z0-9]",
            "",
            file.stem.lower()
        )

        lookup[key] = str(file)

    search_term = re.sub(
        r"[^a-z0-9]",
        "",
        user_input
    )

    # exact match
    if search_term in lookup:
        return lookup[search_term]

    # fuzzy match
    matches = get_close_matches(
        search_term,
        lookup.keys(),
        n=1,
        cutoff=0.55
    )

    if matches:
        return lookup[matches[0]]

    return None

@app.websocket("/ws/guest")
async def guest_endpoint(websocket: WebSocket):
    guest_id = await manager.connect_guest(websocket)

    try:
        while True:
            raw_data = await websocket.receive_text()
            print("📩 RAW GUEST MESSAGE:", raw_data)

            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                print("Bad JSON:", raw_data)
                continue

            msg_type = data.get("type")
            if msg_type != "request_song":
                print("Ignoring message type:", msg_type)
                continue

            requested = (data.get("song") or "").strip()
            if not requested:
                print("Empty song request ignored")
                continue

            print("🎵 SONG REQUEST:", requested)

            song_path = find_song_file(requested)

            if not song_path:
                print("❌ NO MATCH FOUND:", requested)
                await manager.send_to_host({
                    "type": "invalid_request",
                    "song": requested,
                    "id": guest_id
                })
                continue

            if song_path in player.queue:
                print("Skipping duplicate request:", song_path)
                continue

            print("MATCHED:", song_path)
            player.add_to_queue(song_path)
            print("QUEUE:", player.queue)

            if not player.is_playing():
                player.ensure_playing()

            try:
                audio = EasyID3(song_path)
                title = audio.get("title", [Path(song_path).stem])[0]
                artist = audio.get("artist", ["Unknown Artist"])[0]
                display_name = f"{title} — {artist}"
            except Exception:
                display_name = Path(song_path).stem

            await manager.send_to_host({
                "type": "song_request",
                "song": display_name,
                "id": guest_id
            })

            await manager.send_to_host({
                "type": "status",
                "currentSong": player.get_current_song_name(),
                "index": player.index
            })

    except WebSocketDisconnect:
        manager.disconnect_guest(guest_id)