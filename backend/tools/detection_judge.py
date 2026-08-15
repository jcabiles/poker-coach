"""Blind-detection judging harness (flywheel S6 T5) — owner-run panel scorer.

Takes ONLY `presentation.json` (T4's blinded artifact: `presentation_id` +
`rendered_text` + `sha256`, plus `duplicate_for_slot` on the per-judge repeat
bundles) and drives the §d.3-pinned 5-vendor LLM panel over it. This module
NEVER reads `unblinding.json` and has no CLI path that accepts one — every
loaded input is passed through `_assert_no_label_bearing_keys`, which refuses
to proceed if the JSON carries any key that could betray a class, a source, or
a control flag (`class`/`label`/`is_control`/`source` substrings, anywhere,
however nested).

Pinned protocol pieces (estimand-contract.md §d.3, lines 494-529, plus the
`flywheel-s6.md` §A amendments):

    JUDGE_PROMPT_TEMPLATE   the §d.3 prompt, verbatim, `{SEAT_ID}` substituted
                            from the bundle's own "Player under review: Pn"
                            header — never from a label-bearing source.
    BASE_RATE_PREAMBLE      §A.2's pinned system preamble (the 50/50 base-rate
                            statement §d.3's prompt body omits).

Wire shape actually sent to each vendor (`build_user_prompt`, `judge_pair`):

    system message = BASE_RATE_PREAMBLE (verbatim, §A.2)
    user message    = JUDGE_PROMPT_TEMPLATE (verbatim, {SEAT_ID} filled)
                       + HAND_HISTORY_DELIMITER ("\n\n--- HAND HISTORY ---\n\n")
                       + bundle["rendered_text"]   <- the 30-hand history itself

The delimiter is this module's own framing, not part of the §d.3 pin, so the
verbatim template constant never has to change to carry it.

Vendors (5 hosted slots + 1 deterministic `stub` for dry runs/tests), all via
stdlib `urllib.request` — no SDKs. API keys and optional base-URL overrides
come ONLY from environment variables, never from files:

    S6_JUDGE_ANTHROPIC_KEY   S6_JUDGE_ANTHROPIC_BASE_URL (optional)
    S6_JUDGE_OPENAI_KEY      S6_JUDGE_OPENAI_BASE_URL    (optional)
    S6_JUDGE_GOOGLE_KEY      S6_JUDGE_GOOGLE_BASE_URL    (optional)
    S6_JUDGE_META_KEY        S6_JUDGE_META_BASE_URL      (REQUIRED — Meta has
                                                            no vendor-native
                                                            hosted API; slot is
                                                            implemented against
                                                            an OpenAI-compatible
                                                            chat endpoint at
                                                            whatever host the
                                                            owner points it at)
    S6_JUDGE_DEEPSEEK_KEY    S6_JUDGE_DEEPSEEK_BASE_URL  (optional)
    S6_JUDGE_STUB_KEY        (unused; stub needs no credential)

Run shape (one process, resumable):

    1. `load_presentation` — read + blind-guard `presentation.json`, hash it.
    2. Preflight (first run only): every configured vendor's credential is
       exercised with one cheap call; requested vs provider-resolved model
       IDs are recorded in an immutable `launch.json`
       (`presentation_sha256` pinned; a later run with a different
       `presentation.json` at the same `--out` is refused, not silently
       re-launched). A resumed run skips preflight and re-verifies the hash.
    3. Per-slot order (`order/slot-{k}.json`, also immutable/reused on
       resume): canonical-sorted non-duplicate bundles + slot k's own
       HUMAN-class duplicate (if the manifest has one), independently shuffled
       per `derive_order_seed(order_seed, slot)`.
    4. Judging: one `responses/slot-{k}/{presentation_id}.json` per pair,
       atomic (temp + rename). Malformed output gets ONE retry with the
       IDENTICAL prompt, then `malformed-final`. Transport failures retry with
       bounded exponential backoff, then `transport_failed` (non-terminal — a
       later rerun retries them; `ok`/`malformed-final` are terminal and are
       skipped on resume).
    5. `judging_complete.json` — per-slot ok/malformed/transport_failed counts
       for every pair this invocation was scoped to (respecting
       `--only-slot`/`--only-presentation-id`).

CLI (repo convention — run as a module, not a bare script):

    python -m tools.detection_judge run \\
        --deck <dir with presentation.json> \\
        --judges anthropic:claude-x,openai:gpt-x,... \\
        --order-seed 20260807 \\
        [--only-slot K] [--only-presentation-id B003] [--out <dir>]

`--only-slot K --only-presentation-id B###` together are the control
pre-screen: one bundle, one vendor, before the paid run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# §d.3 pinned prompt (estimand-contract.md lines 505-513) + §A.2 preamble
# (flywheel-s6.md §A.2). Copied verbatim; any wording change is a formal
# amendment (spec, "Constraints"). Do not "clean up" this text.
# ---------------------------------------------------------------------------

JUDGE_PROMPT_TEMPLATE = (
    "You are an experienced live low-stakes no-limit hold'em cash-game player "
    "reviewing anonymized hand histories. You will see 30 consecutive hands "
    "played by seat {SEAT_ID}. Decide whether this seat was played by a HUMAN "
    "or a BOT. Consider tendencies a human would notice: bet-sizing patterns, "
    "timing-free logic of calls and raises, consistency vs adaptability, "
    "strange folds or calls, repetitive lines. Respond in exactly this JSON "
    'format: {"label": "human"|"bot", "confidence_human": <integer 0-100>, '
    '"reason": "<≤50 words>"}.'
)

BASE_RATE_PREAMBLE = (
    "The set of seats you will review contains humans and bots in equal "
    "proportion: the true base rate is 50/50."
)

# A cheap, off-protocol call used ONLY for preflight credential/model-snapshot
# verification. Never sent as part of judging; never counted as a pair.
_PREFLIGHT_PROMPT = "Reply with exactly one word: OK."
_PREFLIGHT_TIMEOUT = 30.0
_JUDGE_TIMEOUT = 60.0

# The wire user-message is the pinned §d.3 template (verbatim, {SEAT_ID}
# filled) followed by this delimiter and the bundle's actual rendered hand
# text. The delimiter is NOT part of the pinned prompt — it is this module's
# own framing, kept separate from `JUDGE_PROMPT_TEMPLATE` so the verbatim
# constant never has to change. The §A.2 base-rate preamble stays a SYSTEM
# message and is never concatenated into this user prompt.
HAND_HISTORY_DELIMITER = "\n\n--- HAND HISTORY ---\n\n"

REQUIRED_RESPONSE_KEYS = frozenset({"label", "confidence_human", "reason"})

# Keys whose presence anywhere in an INPUT document would betray a label. The
# harness's own output records legitimately use "label"/"reason" (the judge's
# answer) — this guard only ever runs on documents we READ (presentation.json).
_FORBIDDEN_INPUT_KEY_TOKENS = ("class", "label", "is_control", "source")

_SEAT_ID_RE = re.compile(r"^Player under review:\s*(\S+)")


class HarnessError(RuntimeError):
    """Any structural problem — blinding guard, immutability, bad schema."""


class TransportError(RuntimeError):
    """Network/HTTP failure calling a vendor — distinct from a malformed body."""


class ResponseParseError(ValueError):
    """The judge's raw text did not satisfy the pinned strict response schema."""


# ---------------------------------------------------------------------------
# Blind input loading
# ---------------------------------------------------------------------------


def _label_bearing_keys(document: Any, path: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(document, Mapping):
        for key, value in document.items():
            lowered = str(key).lower()
            if any(token in lowered for token in _FORBIDDEN_INPUT_KEY_TOKENS):
                found.append(f"{path}{key}")
            found.extend(_label_bearing_keys(value, f"{path}{key}."))
    elif isinstance(document, (list, tuple)):
        for index, value in enumerate(document):
            found.extend(_label_bearing_keys(value, f"{path}{index}."))
    return found


def assert_no_label_bearing_keys(document: Any) -> None:
    """Refuse any input whose JSON carries a label-bearing key, anywhere.

    This is the harness's ONLY defense against being handed `unblinding.json`
    (or anything shaped like it) by mistake — there is deliberately no CLI
    flag that accepts an unblinding-file path at all.
    """
    stray = _label_bearing_keys(document)
    if stray:
        raise HarnessError(f"input JSON has label-bearing keys: {sorted(stray)}")


def load_presentation(deck_dir: Path) -> tuple[dict, str]:
    """Read + blind-guard `presentation.json`; return (document, sha256-of-bytes)."""
    path = Path(deck_dir) / "presentation.json"
    raw_bytes = path.read_bytes()
    document = json.loads(raw_bytes)
    assert_no_label_bearing_keys(document)
    if not isinstance(document.get("bundles"), list) or not document["bundles"]:
        raise HarnessError("presentation.json has no bundles")
    return document, hashlib.sha256(raw_bytes).hexdigest()


def build_user_prompt(seat_id: str, rendered_text: str) -> str:
    """The pinned §d.3 instructions (verbatim, `{SEAT_ID}` filled) + delimiter
    + the bundle's rendered hand history — the actual wire user-message."""
    # NOT `.format()`: the pinned prompt text itself contains literal JSON
    # braces (the response-format example), so a plain substring replace is
    # the only way to fill `{SEAT_ID}` without also tripping on them.
    instructions = JUDGE_PROMPT_TEMPLATE.replace("{SEAT_ID}", seat_id)
    return instructions + HAND_HISTORY_DELIMITER + rendered_text


def extract_seat_id(rendered_text: str) -> str:
    """Pull the opaque `{SEAT_ID}` from the renderer's own header line.

    Never taken from any label-bearing source — the renderer's "Player under
    review: Pn" line is the one place the harness is allowed to read it from.
    """
    match = _SEAT_ID_RE.match(rendered_text)
    if not match:
        raise HarnessError(
            "rendered_text does not start with a 'Player under review:' header"
        )
    return match.group(1)


# ---------------------------------------------------------------------------
# Strict response parsing — no coercion
# ---------------------------------------------------------------------------

# Tolerance: an optional markdown code fence (``` or ```json ... ```) wrapping
# the WHOLE response is stripped. Nothing else is trimmed or repaired — no
# trailing-comma fixups, no quote normalization, no partial-match extraction.
_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    match = _FENCE_RE.match(stripped)
    return match.group(1).strip() if match else stripped


def parse_judge_response(raw_text: str) -> dict:
    """Strict-parse a judge's raw response text; raise `ResponseParseError` on
    ANY deviation from the pinned schema (exact keys, exact types, exact
    label/range domain — no coercion)."""
    candidate = _strip_code_fence(raw_text)
    try:
        obj = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ResponseParseError(f"invalid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ResponseParseError("response is not a JSON object")
    if set(obj) != REQUIRED_RESPONSE_KEYS:
        raise ResponseParseError(
            f"keys {sorted(obj)} != {sorted(REQUIRED_RESPONSE_KEYS)}"
        )
    label = obj["label"]
    if label not in ("human", "bot"):
        raise ResponseParseError(f"label {label!r} not in ('human', 'bot')")
    confidence = obj["confidence_human"]
    if isinstance(confidence, bool) or not isinstance(confidence, int):
        raise ResponseParseError(f"confidence_human {confidence!r} is not an integer")
    if not 0 <= confidence <= 100:
        raise ResponseParseError(f"confidence_human {confidence!r} out of range 0-100")
    reason = obj["reason"]
    if not isinstance(reason, str):
        raise ResponseParseError("reason is not a string")
    return {"label": label, "confidence_human": confidence, "reason": reason}


# ---------------------------------------------------------------------------
# Vendor adapters — stdlib urllib only
# ---------------------------------------------------------------------------


def _post_json(url: str, headers: dict, body: dict, timeout: float) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            raw = response.read()
    except urllib.error.HTTPError as exc:
        # Surface the vendor's error body — a bare "HTTP Error 400" is undiagnosable.
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001 — IncompleteRead etc.; never let diagnostics raise
            detail = "<error body unreadable>"
        # Redact anything key-shaped BEFORE truncating — truncation first could cut a
        # token below the pattern's minimum length and let the fragment through.
        detail = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED-KEY]", detail)[:2000]
        raise TransportError(f"{exc}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TransportError(str(exc)) from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TransportError(f"non-JSON transport body: {exc}") from exc


def _call_openai_compatible(
    base_url: str,
    path: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    timeout: float,
    temperature: int | None = 0,
) -> tuple[str, str]:
    url = base_url.rstrip("/") + path
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if temperature is not None:
        body["temperature"] = temperature
    obj = _post_json(url, headers, body, timeout)
    try:
        raw_text = obj["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise TransportError(f"unexpected response shape: {exc}") from exc
    return raw_text, obj.get("model", model)


def call_openai(
    model: str, system_prompt: str, user_prompt: str, api_key: str,
    base_url: str | None, timeout: float, *, context: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    del context
    # No temperature: gpt-5.6 reasoning models reject explicit temperature 0
    # (400 unsupported_value, observed 2026-08-14) — provider default only.
    # Contract branch: "temperature 0 (or the provider's deterministic
    # setting; recorded)" — recorded in detection-pilot-s6.md and launch.json.
    return _call_openai_compatible(
        base_url or "https://api.openai.com/v1", "/chat/completions",
        model, system_prompt, user_prompt, api_key, timeout, temperature=None,
    )


def call_deepseek(
    model: str, system_prompt: str, user_prompt: str, api_key: str,
    base_url: str | None, timeout: float, *, context: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    del context
    return _call_openai_compatible(
        base_url or "https://api.deepseek.com", "/chat/completions",
        model, system_prompt, user_prompt, api_key, timeout,
    )


def call_meta(
    model: str, system_prompt: str, user_prompt: str, api_key: str,
    base_url: str | None, timeout: float, *, context: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    del context
    # Meta has no vendor-native hosted judge API; the slot is implemented
    # against WHATEVER OpenAI-compatible host the owner configures.
    if not base_url:
        raise TransportError(
            "meta vendor requires S6_JUDGE_META_BASE_URL (hosted "
            "OpenAI-compatible endpoint) — Meta has no default"
        )
    return _call_openai_compatible(
        base_url, "/chat/completions", model, system_prompt, user_prompt, api_key, timeout,
    )


def call_anthropic(
    model: str, system_prompt: str, user_prompt: str, api_key: str,
    base_url: str | None, timeout: float, *, context: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    del context
    url = (base_url or "https://api.anthropic.com").rstrip("/") + "/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }
    body = {
        "model": model,
        # 4096, not 300: current models think by default (cannot be disabled) and
        # thinking tokens count INSIDE max_tokens — a small cap risks thinking-only
        # truncation (stop_reason max_tokens, no text block) on bundle-sized input.
        # Reasoning effort is left at the provider default: an earlier low-effort
        # setting coincided with the control pre-screen miss (recorded in
        # detection-pilot-s6.md §5) and judge sensitivity outranks token cost here.
        "max_tokens": 4096,
        # No temperature: Anthropic deprecated the parameter for current models
        # (400 invalid_request_error, observed 2026-08-14). The contract's decoding
        # pin — "temperature 0 or the provider's deterministic setting; recorded"
        # (estimand-contract.md §d.3) — covers using the provider default here;
        # recorded in detection-pilot-s6.md.
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    obj = _post_json(url, headers, body, timeout)
    try:
        # content may lead with non-text blocks (e.g. a "thinking" block on
        # current Opus models) — take the first text block, not content[0].
        raw_text = next(
            block["text"] for block in obj["content"]
            if isinstance(block, dict) and block.get("type") == "text"
        )
    except (KeyError, IndexError, TypeError, StopIteration) as exc:
        raise TransportError(f"unexpected response shape: {exc}") from exc
    return raw_text, obj.get("model", model)


def call_google(
    model: str, system_prompt: str, user_prompt: str, api_key: str,
    base_url: str | None, timeout: float, *, context: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    del context
    base = (base_url or "https://generativelanguage.googleapis.com").rstrip("/")
    url = f"{base}/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0},
    }
    obj = _post_json(url, headers, body, timeout)
    try:
        raw_text = obj["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise TransportError(f"unexpected response shape: {exc}") from exc
    return raw_text, obj.get("modelVersion", model)


def call_stub(
    model: str, system_prompt: str, user_prompt: str, api_key: str,
    base_url: str | None, timeout: float, *, context: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """Deterministic, no network. Seeded from presentation_id+slot (`context`)
    so a resumed/rerun pair reproduces byte-identical output."""
    del system_prompt, api_key, base_url, timeout
    ctx = context or {}
    material = f"s6-stub-judge|{ctx.get('presentation_id')}|{ctx.get('slot')}"
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:8], "big"))
    confidence = rng.randint(0, 100)
    label = "human" if confidence >= 50 else "bot"
    raw_text = json.dumps(
        {
            "label": label,
            "confidence_human": confidence,
            "reason": "stub judge: deterministic placeholder for dry runs.",
        }
    )
    return raw_text, f"{model}-stub-resolved"


@dataclass(frozen=True, slots=True)
class VendorAdapter:
    name: str
    default_base_url: str | None
    call: Callable[..., tuple[str, str]]


VENDOR_ADAPTERS: dict[str, VendorAdapter] = {
    "anthropic": VendorAdapter("anthropic", "https://api.anthropic.com", call_anthropic),
    "openai": VendorAdapter("openai", "https://api.openai.com/v1", call_openai),
    "google": VendorAdapter(
        "google", "https://generativelanguage.googleapis.com", call_google
    ),
    "meta": VendorAdapter("meta", None, call_meta),
    "deepseek": VendorAdapter("deepseek", "https://api.deepseek.com", call_deepseek),
    "stub": VendorAdapter("stub", None, call_stub),
}


def env_var_name(vendor: str) -> str:
    return f"S6_JUDGE_{vendor.upper()}_KEY"


def base_url_env_var_name(vendor: str) -> str:
    return f"S6_JUDGE_{vendor.upper()}_BASE_URL"


# ---------------------------------------------------------------------------
# Seeding / ordering
# ---------------------------------------------------------------------------


def derive_order_seed(order_seed: int, slot: int) -> int:
    material = f"s6-judge-order|{order_seed}|{slot}"
    return int.from_bytes(hashlib.sha256(material.encode("utf-8")).digest()[:16], "big")


def build_slot_deck(document: Mapping, slot: int) -> list[dict]:
    """Judge `slot`'s deck: all non-duplicate entries + ONLY its own duplicate
    (if the manifest has one), canonical-sorted then independently shuffled.
    No adjacency guarantee for the duplicate."""
    bundles = document["bundles"]
    non_duplicates = sorted(
        (b for b in bundles if "duplicate_for_slot" not in b),
        key=lambda b: int(b["presentation_id"][1:]),
    )
    duplicates = [b for b in bundles if b.get("duplicate_for_slot") == slot]
    if len(duplicates) > 1:
        raise HarnessError(f"slot {slot} has {len(duplicates)} duplicate entries, expected <=1")
    return [*non_duplicates, *duplicates]


def order_slot_deck(deck: Sequence[dict], order_seed: int, slot: int) -> list[dict]:
    rng = random.Random(derive_order_seed(order_seed, slot))
    ordered = list(deck)
    rng.shuffle(ordered)
    return ordered


# ---------------------------------------------------------------------------
# Atomic / immutable JSON writes
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    tmp.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _write_immutable_json(path: Path, document: dict) -> None:
    if path.exists():
        raise HarnessError(f"{path} already exists and is immutable")
    _atomic_write_json(path, document)


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------


def judge_pair(
    adapter: VendorAdapter,
    model: str,
    api_key: str,
    base_url: str | None,
    seat_id: str,
    rendered_text: str,
    presentation_id: str,
    slot: int,
    *,
    timeout: float = _JUDGE_TIMEOUT,
    malformed_retries: int = 1,
    transport_attempts: int = 3,
    backoff_base: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Judge one (bundle, judge-slot) pair. Always returns a terminal record:

        status: "ok" | "malformed-final" | "transport_failed"
        attempts: [{"kind": "transport_error"|"malformed", "detail": str}, ...]
        raw_responses: every raw text received (ALWAYS preserved)
        parsed: the strict-parsed {label, confidence_human, reason} or None

    The wire user-message is the pinned §d.3 template + `rendered_text`
    (`build_user_prompt`) — the panel is judging the bundle's actual hand
    history, not the instructions alone.
    """
    prompt = build_user_prompt(seat_id, rendered_text)
    context = {"presentation_id": presentation_id, "slot": slot, "seat_id": seat_id}
    attempts: list[dict] = []

    def _call() -> str | None:
        for attempt in range(transport_attempts):
            try:
                text, _resolved = adapter.call(
                    model, BASE_RATE_PREAMBLE, prompt, api_key, base_url, timeout,
                    context=context,
                )
                return text
            except TransportError as exc:
                attempts.append({"kind": "transport_error", "detail": str(exc)})
                if attempt < transport_attempts - 1:
                    sleep(backoff_base * (2**attempt))
        return None

    raw_text = _call()
    if raw_text is None:
        return {
            "status": "transport_failed", "attempts": attempts,
            "raw_responses": [], "parsed": None,
        }

    raw_responses = [raw_text]
    for parse_try in range(malformed_retries + 1):
        try:
            parsed = parse_judge_response(raw_responses[-1])
            return {
                "status": "ok", "attempts": attempts,
                "raw_responses": raw_responses, "parsed": parsed,
            }
        except ResponseParseError as exc:
            attempts.append({"kind": "malformed", "detail": str(exc)})
            if parse_try < malformed_retries:
                retry_text = _call()
                if retry_text is None:
                    return {
                        "status": "transport_failed", "attempts": attempts,
                        "raw_responses": raw_responses, "parsed": None,
                    }
                raw_responses.append(retry_text)
    return {
        "status": "malformed-final", "attempts": attempts,
        "raw_responses": raw_responses, "parsed": None,
    }


_STATUS_COUNT_KEY = {
    "ok": "ok", "malformed-final": "malformed", "transport_failed": "transport_failed",
}


def _preflight_and_write_launch(
    launch_path: Path,
    judges: Sequence[tuple[str, str]],
    presentation_sha256: str,
    order_seed: int,
    env: Mapping[str, str],
) -> dict:
    judge_records = []
    decoding = {}
    failures: list[str] = []
    for slot, (vendor, model) in enumerate(judges):
        adapter = VENDOR_ADAPTERS[vendor]
        api_key = env.get(env_var_name(vendor), "")
        if vendor != "stub" and not api_key:
            raise HarnessError(
                f"missing credential env var {env_var_name(vendor)!r} for vendor {vendor!r}"
            )
        base_url = env.get(base_url_env_var_name(vendor)) or adapter.default_base_url
        try:
            _raw, resolved_model = adapter.call(
                model, BASE_RATE_PREAMBLE, _PREFLIGHT_PROMPT, api_key, base_url,
                _PREFLIGHT_TIMEOUT,
                context={
                    "presentation_id": "__preflight__", "slot": slot,
                    "seat_id": "__preflight__",
                },
            )
        except TransportError as exc:
            # Collect every slot's failure rather than raising on the first —
            # one preflight run must surface ALL broken slots at once.
            failures.append(f"vendor {vendor!r} (slot {slot}): {exc}")
            continue
        judge_records.append(
            {
                "slot": slot, "vendor": vendor,
                "requested_model": model, "resolved_model": resolved_model,
            }
        )
        # launch.json must record what is actually sent (§d.3 "recorded"):
        # anthropic and openai current-generation models both reject an explicit
        # temperature, so those slots run at the provider default.
        if vendor == "anthropic":
            decoding[vendor] = {
                "temperature": "provider-default (explicit value rejected by provider)",
                "max_tokens": 4096,
                "reasoning_effort": "provider-default",
                "thinking": "provider-forced adaptive (cannot be disabled)",
            }
        elif vendor == "openai":
            decoding[vendor] = {
                "temperature": "provider-default (explicit value rejected by provider)"
            }
        else:
            decoding[vendor] = {"temperature": 0}
    if failures:
        raise HarnessError(
            "preflight failed for "
            + str(len(failures))
            + " slot(s):\n  - "
            + "\n  - ".join(failures)
        )
    launch = {
        "schema_version": SCHEMA_VERSION,
        "judges": judge_records,
        "presentation_sha256": presentation_sha256,
        "order_seed": order_seed,
        "decoding": decoding,
        "started_at": datetime.now(UTC).isoformat(),
    }
    _write_immutable_json(launch_path, launch)
    return launch


def parse_judges_arg(judges_arg: str) -> list[tuple[str, str]]:
    judges: list[tuple[str, str]] = []
    for item in judges_arg.split(","):
        item = item.strip()
        if not item:
            continue
        vendor, sep, model = item.partition(":")
        vendor, model = vendor.strip(), model.strip()
        if not sep or not vendor or not model:
            raise HarnessError(f"--judges entry {item!r} is not 'vendor:model'")
        if vendor not in VENDOR_ADAPTERS:
            raise HarnessError(f"unknown vendor {vendor!r}; choices: {sorted(VENDOR_ADAPTERS)}")
        judges.append((vendor, model))
    if not judges:
        raise HarnessError("--judges must list at least one vendor:model")
    return judges


def run(
    deck_dir: Path,
    judges_arg: str,
    order_seed: int,
    *,
    out_dir: Path | None = None,
    only_slot: int | None = None,
    only_presentation_id: str | None = None,
    env: Mapping[str, str] | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """Run (or resume) a judging pass. Returns the `judging_complete.json`
    document for the pairs this invocation was scoped to."""
    env = os.environ if env is None else env
    deck_dir = Path(deck_dir)
    out_dir = Path(out_dir) if out_dir is not None else deck_dir

    document, presentation_sha256 = load_presentation(deck_dir)
    judges = parse_judges_arg(judges_arg)

    launch_path = out_dir / "launch.json"
    if launch_path.exists():
        launch = json.loads(launch_path.read_text(encoding="utf-8"))
        if launch["presentation_sha256"] != presentation_sha256:
            raise HarnessError(
                f"{launch_path} was launched against a different presentation.json "
                f"(recorded {launch['presentation_sha256']}, current {presentation_sha256})"
            )
    else:
        launch = _preflight_and_write_launch(
            launch_path, judges, presentation_sha256, order_seed, env
        )

    slots_to_process = (
        [only_slot] if only_slot is not None else list(range(len(judges)))
    )
    for slot in slots_to_process:
        if not 0 <= slot < len(judges):
            raise HarnessError(
                f"--only-slot {slot} out of range for {len(judges)} configured judges"
            )

    bundle_by_id = {b["presentation_id"]: b for b in document["bundles"]}
    responses_root = out_dir / "responses"
    order_root = out_dir / "order"

    per_slot_counts: dict[str, dict[str, int]] = {}
    for slot in slots_to_process:
        vendor, model = judges[slot]
        adapter = VENDOR_ADAPTERS[vendor]
        api_key = env.get(env_var_name(vendor), "")
        base_url = env.get(base_url_env_var_name(vendor)) or adapter.default_base_url

        order_path = order_root / f"slot-{slot}.json"
        if order_path.exists():
            slot_order = json.loads(order_path.read_text(encoding="utf-8"))["presentation_ids"]
        else:
            deck = order_slot_deck(build_slot_deck(document, slot), order_seed, slot)
            slot_order = [b["presentation_id"] for b in deck]
            _write_immutable_json(
                order_path,
                {
                    "schema_version": SCHEMA_VERSION, "slot": slot, "vendor": vendor,
                    "order_seed": order_seed, "presentation_ids": slot_order,
                },
            )

        counts = {"ok": 0, "malformed": 0, "transport_failed": 0}
        slot_dir = responses_root / f"slot-{slot}"
        for presentation_id in slot_order:
            if only_presentation_id is not None and presentation_id != only_presentation_id:
                continue
            response_path = slot_dir / f"{presentation_id}.json"
            if response_path.exists():
                existing = json.loads(response_path.read_text(encoding="utf-8"))
                if existing["status"] in ("ok", "malformed-final"):
                    counts[_STATUS_COUNT_KEY[existing["status"]]] += 1
                    continue

            bundle = bundle_by_id[presentation_id]
            rendered_text = bundle["rendered_text"]
            seat_id = extract_seat_id(rendered_text)
            result = judge_pair(
                adapter, model, api_key, base_url, seat_id, rendered_text,
                presentation_id, slot, sleep=sleep,
            )
            record = {
                "schema_version": SCHEMA_VERSION, "slot": slot, "vendor": vendor,
                "model": model, "presentation_id": presentation_id, **result,
            }
            _atomic_write_json(response_path, record)
            counts[_STATUS_COUNT_KEY[result["status"]]] += 1
        per_slot_counts[str(slot)] = counts

    completion = {
        "schema_version": SCHEMA_VERSION,
        "per_slot": per_slot_counts,
        "total": sum(sum(c.values()) for c in per_slot_counts.values()),
    }
    _atomic_write_json(out_dir / "judging_complete.json", completion)
    return completion


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tools.detection_judge")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="run or resume a judging pass")
    run_parser.add_argument(
        "--deck", required=True, type=Path, help="dir containing presentation.json"
    )
    run_parser.add_argument("--judges", required=True, help="vendor:model,vendor:model,...")
    run_parser.add_argument("--order-seed", required=True, type=int)
    run_parser.add_argument("--only-slot", type=int, default=None)
    run_parser.add_argument("--only-presentation-id", default=None)
    run_parser.add_argument("--out", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.command == "run":
        completion = run(
            args.deck, args.judges, args.order_seed,
            out_dir=args.out, only_slot=args.only_slot,
            only_presentation_id=args.only_presentation_id,
        )
        print(json.dumps(completion, indent=2, sort_keys=True))
        return 0
    raise HarnessError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
