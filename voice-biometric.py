"""
voice_biometric.py

Simple voice biometric + debug mode manager for JARVIS v2.0.

Features:
- Voice enrollment: record N samples and store reference embeddings
- Voice verification: compare new sample against enrolled profile
- DebugModeManager: combines keyword + (optional) voice check
- File-based storage: ~/.jarvis/voice_profile.npz

This is intentionally lightweight and NOT a production-grade biometric system.
"""

import os
import time
import json
import hashlib
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple

import numpy as np
import sounddevice as sd
import soundfile as sf


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _hash_config(config: Dict[str, Any]) -> str:
    try:
        blob = json.dumps(config, sort_keys=True).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
    except Exception:
        return "default"


# ---------------------------------------------------------------------------
# VoiceBiometric: enrollment + verification
# ---------------------------------------------------------------------------

@dataclass
class VoiceBiometric:
    """
    Minimal voice biometric helper.

    Workflow:
      - enroll(): records several short samples, extracts simple embeddings,
                  and saves averaged embedding to disk.
      - verify(): records a sample and compares against stored embedding.

    Storage:
      - Base directory: ~/.jarvis/
      - Profile file: ~/.jarvis/voice_profile.npz
    """

    sample_rate: int = 16000
    channels: int = 1
    sample_seconds: int = 3
    enroll_samples: int = 3
    tolerance: float = 0.35  # lower = stricter; 0.3–0.4 is reasonable here
    base_dir: str = field(default_factory=lambda: os.path.join(os.path.expanduser("~"), ".jarvis"))
    profile_file: str = field(init=False)

    def __post_init__(self) -> None:
        self.profile_file = os.path.join(self.base_dir, "voice_profile.npz")
        _ensure_dir(self.base_dir)

    # ---- Audio capture -----------------------------------------------------

    def _record(self, seconds: int) -> np.ndarray:
        """Record audio from default microphone."""
        duration = int(seconds * self.sample_rate)
        audio = sd.rec(frames=duration, samplerate=self.sample_rate, channels=self.channels, dtype="float32")
        sd.wait()
        return audio.reshape(-1)

    # ---- Feature extraction -----------------------------------------------

    def _extract_embedding(self, audio: np.ndarray) -> np.ndarray:
        """
        Extremely simple embedding:
          - normalize
          - short-time energy in fixed windows
          - aggregate stats (mean, std, max, min)

        This is not a real ML speaker embedding, but enough to gate debug mode.
        """
        if audio.size == 0:
            raise ValueError("Empty audio input")

        # normalize
        audio = audio.astype(np.float32)
        max_abs = np.max(np.abs(audio)) or 1.0
        audio = audio / max_abs

        # windowed energy
        frame_size = int(0.02 * self.sample_rate)  # 20ms
        if frame_size <= 0:
            frame_size = 320
        num_frames = max(1, len(audio) // frame_size)
        audio = audio[: num_frames * frame_size]
        frames = audio.reshape(num_frames, frame_size)
        energy = np.mean(frames ** 2, axis=1)

        feats = np.array(
            [
                np.mean(energy),
                np.std(energy),
                np.max(energy),
                np.min(energy),
                np.median(energy),
                np.percentile(energy, 25),
                np.percentile(energy, 75),
            ],
            dtype=np.float32,
        )
        return feats

    # ---- Storage -----------------------------------------------------------

    def _save_profile(self, embedding: np.ndarray, meta: Dict[str, Any]) -> None:
        _ensure_dir(self.base_dir)
        np.savez(self.profile_file, embedding=embedding, meta=json.dumps(meta))

    def _load_profile(self) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        if not os.path.isfile(self.profile_file):
            return None
        data = np.load(self.profile_file, allow_pickle=False)
        embedding = data["embedding"].astype(np.float32)
        meta = json.loads(str(data["meta"]))
        return embedding, meta

    # ---- Public API --------------------------------------------------------

    def is_enrolled(self) -> bool:
        return os.path.isfile(self.profile_file)

    def enroll(self, progress_callback=None) -> bool:
        """
        Enroll user voice by recording `enroll_samples` samples.
        Returns True on success.
        """
        print("\n[VoiceBiometric] Starting voice enrollment.")
        print(f"Say a short phrase {self.enroll_samples} times (each ~{self.sample_seconds}s).")
        embeddings: List[np.ndarray] = []

        for i in range(self.enroll_samples):
            if progress_callback:
                progress_callback(i + 1, self.enroll_samples)
            print(f"\n[{i+1}/{self.enroll_samples}] Press ENTER and then speak...")
            input()
            audio = self._record(self.sample_seconds)
            emb = self._extract_embedding(audio)
            embeddings.append(emb)
            print("[VoiceBiometric] Sample recorded.")

        avg_embedding = np.mean(np.stack(embeddings, axis=0), axis=0)
        meta = {
            "created_at": time.time(),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_seconds": self.sample_seconds,
            "enroll_samples": self.enroll_samples,
        }
        self._save_profile(avg_embedding, meta)
        print("\n[VoiceBiometric] Enrollment completed and profile saved.")
        return True

    def verify(self) -> bool:
        """
        Verify current speaker against stored profile.
        Returns True if similarity is above threshold.
        """
        profile = self._load_profile()
        if profile is None:
            print("[VoiceBiometric] No enrolled profile found.")
            return False

        ref_emb, meta = profile
        print("\n[VoiceBiometric] Say the same phrase you used during enrollment...")
        input("Press ENTER and then speak...\n")
        audio = self._record(self.sample_seconds)
        emb = self._extract_embedding(audio)

        # cosine similarity
        def _cosine(a: np.ndarray, b: np.ndarray) -> float:
            denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
            return float(np.dot(a, b) / denom)

        sim = _cosine(ref_emb, emb)
        print(f"[VoiceBiometric] Similarity score: {sim:.3f}")

        if sim >= (1.0 - self.tolerance):
            print("[VoiceBiometric] Verification SUCCESS.")
            return True
        else:
            print("[VoiceBiometric] Verification FAILED.")
            return False


# ---------------------------------------------------------------------------
# DebugModeManager: wraps keyword + voice biometric
# ---------------------------------------------------------------------------

@dataclass
class DebugModeManager:
    """
    Manages debug mode / portal unlock:

    - Uses a keyword (e.g., 'debugmode code 0') in higher-level logic.
    - Optionally uses VoiceBiometric.verify() to confirm the user.
    - Tracks activation window so other modules can check debug status.
    """

    config: Optional[Dict[str, Any]] = None
    voice_bio: VoiceBiometric = field(default_factory=VoiceBiometric)
    debug_active: bool = False
    debug_expires_at: float = 0.0
    default_duration_sec: int = 300  # 5 minutes
    lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        # Derive tolerance from config if provided
        if self.config:
            vb_cfg = self.config.get("voice_biometric", {})
            tol = vb_cfg.get("tolerance")
            if isinstance(tol, (int, float)):
                self.voice_bio.tolerance = float(tol)

    # ---- Debug mode lifetime -----------------------------------------------

    def _activate_debug(self, duration_sec: Optional[int] = None) -> None:
        if duration_sec is None:
            duration_sec = self.default_duration_sec
        with self.lock:
            self.debug_active = True
            self.debug_expires_at = time.time() + duration_sec

    def is_debug_active(self) -> bool:
        with self.lock:
            if not self.debug_active:
                return False
            if time.time() > self.debug_expires_at:
                self.debug_active = False
                return False
            return True

    def remaining_debug_time(self) -> int:
        with self.lock:
            if not self.debug_active:
                return 0
            remaining = int(self.debug_expires_at - time.time())
            return max(0, remaining)

    # ---- Public API used by other modules ----------------------------------

    def handle_debug_keyword(self, require_voice: bool = False, duration_sec: Optional[int] = None) -> bool:
        """
        Called when the correct debug keyword has already been recognized
        (e.g., 'debugmode code 0').

        If require_voice is True, performs voice verification first.
        Returns True if debug mode is activated.
        """
        if require_voice:
            ok = self.voice_bio.verify()
            if not ok:
                return False

        self._activate_debug(duration_sec)
        return True

    def ensure_enrollment(self) -> bool:
        """
        Helper to start enrollment if profile is missing.
        Returns True if a profile exists after this call.
        """
        if self.voice_bio.is_enrolled():
            return True
        print("[DebugModeManager] No voice profile found. Starting enrollment...")
        return self.voice_bio.enroll()

    def get_status(self) -> Dict[str, Any]:
        return {
            "debug_active": self.is_debug_active(),
            "debug_remaining_sec": self.remaining_debug_time(),
            "voice_enrolled": self.voice_bio.is_enrolled(),
        }
