"""MI-1 · mijiedarbības kopsavilkums un nākamā soļa ieteikums.

Funkcijas līgums (prasību saraksts, 5. nodaļa):
    kopsavilkums(teksts) -> {"kopsavilkums": str, "nakamais_solis": str, "avots": "claude" | "imitacija"}

Ja vidē ir ANTHROPIC_API_KEY un uzstādīta pakotne `anthropic`, izmanto Claude API.
Citādi (arī kļūdas, noildzes > 10 s vai atteikuma gadījumā) izmanto atslēgvārdu imitāciju.
Teksts šeit netiek rakstīts žurnālā (N2).
"""

from __future__ import annotations

import logging
import os
import re

log = logging.getLogger("app.ai")

MODEL = os.environ.get("MI_MODEL", "claude-opus-5-5")
TIMEOUT_SECONDS = 10.0
MAX_SENTENCES = 3
INPUT_MAX = 4000

SYSTEM_PROMPT = (
    "Tu palīdzi pašvaldības darbiniekam sakārtot piezīmes par sarunu ar organizāciju. "
    "No darbinieka piezīmēm uzraksti lietišķu kopsavilkumu latviešu valodā, ne vairāk kā trīs teikumos, "
    "un vienu konkrētu nākamo soli darbiniekam. Izmanto tikai piezīmēs minēto informāciju, neko neizdomā. "
    "Neiekļauj personas kodus, veselības datus vai citus sensitīvus personas datus, pat ja tie ir piezīmēs."
)

# Imitācija: teikumi ar šiem vārdiem ir svarīgāki kopsavilkumā
KEY_WORDS = ("vienojā", "nolēm", "līgum", "termiņ", "pieprasīj", "projekt", "seminār", "sanāksm",
             "budžet", "problēm", "jautāj", "lūdz", "apstiprin", "piedāvā")
# Imitācija: teikumi ar šiem vārdiem satur nākamo soli
ACTION_WORDS = ("nosūtīt", "nosūtīs", "sagatavot", "sagatavos", "piezvanīt", "zvanīs", "sarunāt", "organizēt",
                "rezervēt", "pārbaudīt", "saskaņot", "atbildēt", "jānosūta", "jāsagatavo", "jāpiezvana",
                "jāsaskaņo", "jāatbild", "nākamais solis", "nākamreiz", "līdz ")
DEFAULT_NEXT_STEP = "Sazināties ar organizāciju un vienoties par nākamajiem soļiem."


def kopsavilkums(teksts: str) -> dict:
    teksts = " ".join(teksts.split())[:INPUT_MAX]
    if not teksts:
        return {"kopsavilkums": "", "nakamais_solis": "", "avots": "imitacija"}
    result = _claude(teksts) if os.environ.get("ANTHROPIC_API_KEY") else None
    return result or _imitacija(teksts)


def claude_enabled() -> bool:
    """Vai teksts tiks sūtīts ārējam pakalpojumam (to parāda brīdinājumā formā)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


# --- Claude API ----------------------------------------------------------------


def _claude(teksts: str) -> dict | None:
    try:
        import anthropic
        from pydantic import BaseModel
    except ImportError:
        log.warning("MI-1: anthropic package not installed, using imitation")
        return None

    class Summary(BaseModel):
        kopsavilkums: str
        nakamais_solis: str

    try:
        client = anthropic.Anthropic(timeout=TIMEOUT_SECONDS, max_retries=1)
        response = client.messages.parse(
            model=MODEL,
            max_tokens=2000,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Darbinieka piezīmes:\n\n{teksts}"}],
            output_format=Summary,
        )
    except anthropic.APITimeoutError:
        log.warning("MI-1: Claude API timeout, using imitation")
        return None
    except anthropic.APIConnectionError:
        log.warning("MI-1: Claude API connection error, using imitation")
        return None
    except anthropic.APIStatusError as exc:
        log.warning("MI-1: Claude API error %s, using imitation", exc.status_code)
        return None

    if response.stop_reason == "refusal" or response.parsed_output is None:
        log.warning("MI-1: Claude declined (%s), using imitation", response.stop_reason)
        return None
    data = response.parsed_output
    return {
        "kopsavilkums": _limit_sentences(data.kopsavilkums.strip()),
        "nakamais_solis": data.nakamais_solis.strip(),
        "avots": "claude",
    }


# --- Atslēgvārdu imitācija -----------------------------------------------------


def _sentences(teksts: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", teksts.strip())
    return [p.strip() for p in parts if p.strip()]


def _limit_sentences(teksts: str) -> str:
    return " ".join(_sentences(teksts)[:MAX_SENTENCES])


def _ensure_period(s: str) -> str:
    return s if s[-1:] in ".!?" else s + "."


def _imitacija(teksts: str) -> dict:
    sentences = _sentences(teksts)
    action = next((s for s in sentences if any(w in s.lower() for w in ACTION_WORDS)), None)
    rest = [s for s in sentences if s is not action]

    # Pirmais teikums vienmēr (konteksts), tad tikai teikumi ar atslēgvārdiem, sākotnējā secībā
    def weight(sentence: str) -> int:
        return sum(w in sentence.lower() for w in KEY_WORDS)

    chosen = rest[:1]
    ranked = sorted((s for s in rest[1:] if weight(s)), key=lambda s: -weight(s))
    chosen += ranked[: MAX_SENTENCES - len(chosen)]
    chosen.sort(key=rest.index)
    summary = " ".join(_ensure_period(s) for s in chosen) or _ensure_period(action or teksts[:200])

    return {
        "kopsavilkums": summary,
        "nakamais_solis": _ensure_period(action) if action else DEFAULT_NEXT_STEP,
        "avots": "imitacija",
    }
