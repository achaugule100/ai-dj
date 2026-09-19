import vlc
import pathlib
import random
from mutagen.easyid3 import EasyID3


class DJPlayer:
    def __init__(self):
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()

            self.queue = []
            self.index = 0

            self.transition_file = None
            self.transition_media = None
            self.transition_ready = False
            self.transition_started = False
            self.transition_building = False
            self.transition_for = None
            self.transition_exit_sec = None
            self.transition_resume_sec = 0.0
            self.transition_target_index = None

            self.pending_seek_ms = None
            self.ignore_end_until = 0.0

            self.current_song = None

    # ----------------------------
    # QUEUE MANAGEMENT
    # ----------------------------

    def load_playlist(self, songs):
        """Initial load into queue"""
        self.queue = songs
        self.index = 0

    def add_to_queue(self, song_path):
        """For future guest requests / AI auto-mix"""
        self.queue.append(song_path)

    def clear_transition(self):
            self.transition_file = None
            self.transition_media = None
            self.transition_ready = False
            self.transition_started = False
            self.transition_building = False
            self.transition_for = None
            self.transition_exit_sec = None
            self.transition_resume_sec = 0.0
            self.transition_target_index = None
            self.pending_seek_ms = None
    # ----------------------------
    # PLAYBACK CONTROL
    # ----------------------------

    def is_playing(self):
        return self.player.is_playing()

    def get_position_ms(self):
        return self.player.get_time()

    def get_duration_ms(self):
        return self.player.get_length()

    def get_current_song(self):
        return self.current_song
    
    def play_current(self, start_seconds=0.0):
        if not self.queue or self.index >= len(self.queue):
            return

        song = self.queue[self.index]
        self.current_song = song

        media = self.instance.media_new(song)
        self.player.set_media(media)
        self.player.play()

        # VLC start-time can be flaky, so apply seek after playback starts
        if start_seconds and start_seconds > 0:
            self.pending_seek_ms = int(start_seconds * 1000)
        else:
            self.pending_seek_ms = None

    def apply_pending_seek(self):
        if self.pending_seek_ms is None:
            return

        state = self.player.get_state()
        if state in (vlc.State.Playing, vlc.State.Paused):
            try:
                self.player.set_time(self.pending_seek_ms)
                self.pending_seek_ms = None
            except Exception as e:
                print("⚠️ Seek failed:", e)

    def play(self):
        state = self.player.get_state()
        if state == vlc.State.Paused:
            self.player.play()
            return

        self.play_current(0.0)

    def pause(self):
        state = self.player.get_state()
        if state == vlc.State.Playing:
            self.player.pause()
        elif state == vlc.State.Paused:
            self.player.play()

    def next(self):
        if not self.queue:
            return

        if self.index < len(self.queue) - 1:
            self.index += 1
            self.play_current(0.0)
        else:
            self.player.stop()
    # ----------------------------
    # METADATA (ARTIST - TITLE)
    # ----------------------------

    def get_current_song_name(self):
        if not self.queue or self.index >= len(self.queue):
            return "No song loaded"

        file_path = self.queue[self.index]

        try:
            audio = EasyID3(file_path)

            title = audio.get("title", ["Unknown Title"])[0]
            artist = audio.get("artist", ["Unknown Artist"])[0]

            return f"{title} - {artist}"

        except Exception:
            # fallback if no ID3 tags
            return pathlib.Path(file_path).stem

    # ----------------------------
    # CORE PLAYBACK
    # ----------------------------


    def ensure_playing(self):
        if not self.queue:
            return

        if not self.is_playing():
            self.play()

    def get_upcoming(self, n=3):
        return self.queue[self.index+1:self.index+1+n]

    # ----------------------------
    # STATUS FOR FRONTEND
    # ----------------------------

    def get_status(self):
        return {
            "index": self.index,
            "state": self.player.get_state().name,
            "currentSong": self.get_current_song_name()
        }
    
    def get_next_song(self):
        if not self.queue:
            return None

        next_index = self.index + 1
        if next_index >= len(self.queue):
            return None  # or loop if you want

        return self.queue[next_index]