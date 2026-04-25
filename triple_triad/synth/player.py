import os
import threading
import time

# To remove pygame message at the beggining when imported
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


from .constants import SAMPLE_RATE
from .wave_generators import generate_music_buffer

try:
    import numpy as np
    import pygame

    HAS_AUDIO = True
except (ImportError, OSError):
    HAS_AUDIO = False


class ChiptunePlayer:
    """
    Looping chiptune player using pygame.mixer.
    Silent no-op when audio libraries are unavailable.
    """

    def __init__(self):
        self._sound: pygame.mixer.Sound | None = None
        self._is_playing = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self):
        """Start background music (non-blocking)."""
        if not HAS_AUDIO:
            return
        if self._is_playing:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._play_loop, daemon=True)
        self._thread.start()
        self._is_playing = True

    def stop(self):
        """Stop playback and release resources."""
        if not self._is_playing:
            return

        self._stop_event.set()

        with self._lock:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
            except Exception:
                pass

        if self._thread:
            self._thread.join(timeout=2.0)

        self._is_playing = False

    def is_playing(self) -> bool:
        return self._is_playing

    def _ensure_sound(self):
        """Generate the music buffer once and create a pygame Sound."""
        if self._sound is not None:
            return

        buf = generate_music_buffer()

        # Convert to int16 stereo  (pygame sndarray expects (N, 2))
        pcm = (buf * 32767).astype(np.int16)
        stereo = np.column_stack((pcm, pcm))

        if not pygame.mixer.get_init():
            pygame.mixer.init(
                frequency=SAMPLE_RATE,
                size=-16,  # signed 16-bit
                channels=2,  # stereo
                buffer=2048,
            )

        self._sound = pygame.sndarray.make_sound(stereo)

    def _play_loop(self):
        """Background thread: loop music until stop() is called."""
        try:
            self._ensure_sound()
        except Exception as e:
            print(f"  ♪ Could not generate music: {e}")
            return

        try:
            with self._lock:
                if self._stop_event.is_set():
                    return
                self._sound.play(loops=-1)
        except Exception as e:
            print(f"  ♪ Playback error: {e}")
            return

        while not self._stop_event.is_set():
            time.sleep(0.2)

        with self._lock:
            try:
                if pygame.mixer.get_init():
                    self._sound.stop()
            except Exception:
                pass
