"""US-7 · MI ieteikums darbiniekam: tēma un atbildes projekts.

Līgums (nemainās): ieteikums(apraksts) -> {"tema": <viena no 6 tēmām>, "atbildes_projekts": <teksts>}
Noklusēti atslēgvārdu imitācija bez tīkla. Ja vidē ir ANTHROPIC_API_KEY un pakotne `anthropic`,
izmanto Claude API ar to pašu līgumu; kļūdas, noildzes (10 s) vai atteikuma gadījumā — imitācija.
Apraksts netiek rakstīts žurnālā (VDAR). Riska klasifikācija: docs/mi-riska-novertejums.md (minimāls risks).
"""

from __future__ import annotations

import logging
import os
from typing import Literal

log = logging.getLogger("iesniegumi.ai")

TEMAS = ("Ceļi un bedres", "Ielu apgaismojums", "Atkritumi", "Bērnudārza rinda", "Sociālā palīdzība", "Cits")
MODEL = os.environ.get("MI_MODEL", "claude-opus-5-5")
TIMEOUT_SECONDS = 10.0

KEYWORDS = {
    "Ceļi un bedres": ("bedr", "ceļ", "asfalt", "grant", "brauktuv", "tilt", "ietv", "izskalot"),
    "Ielu apgaismojums": ("lamp", "apgaismo", "gaism", "tumš", "nedeg", "mirgo", "laternas"),
    "Atkritumi": ("atkritum", "konteiner", "izvest", "izved", "šķiro", "stikl", "maisi", "izgāztuv"),
    "Bērnudārza rinda": ("bērnudārz", "pirmsskol", "rindā", "rinda", "grupiņ", "audzinātāj"),
    "Sociālā palīdzība": ("pabalst", "palīdzīb", "sociāl", "grūtīb", "ienākum", "pensij", "mājokļ", "trūcīg", "darba zaudē"),
}

PROJEKTI = {
    "Ceļi un bedres": "Labdien!\n\nPaldies par ziņu par ceļa stāvokli. Iesniegumu esam nodevuši komunālajam dienestam, kas vietu apsekos un plānos remontu. Par darbu izpildi informēsim.\n\nAr cieņu,\nEzermalas novada pašvaldība",
    "Ielu apgaismojums": "Labdien!\n\nPaldies par ziņu par ielu apgaismojumu. Esam nodevuši informāciju apgaismojuma uzturētājam; bojājumus parasti novērš 10 darba dienu laikā.\n\nAr cieņu,\nEzermalas novada pašvaldība",
    "Atkritumi": "Labdien!\n\nPaldies par iesniegumu par atkritumu apsaimniekošanu. Esam sazinājušies ar atkritumu apsaimniekotāju un lūguši novērst problēmu. Ja situācija neuzlabojas, lūdzu, informējiet mūs atkārtoti.\n\nAr cieņu,\nEzermalas novada pašvaldība",
    "Bērnudārza rinda": "Labdien!\n\nPaldies par jautājumu par vietu pirmsskolas izglītības iestādē. Pārbaudīsim rindas datus un nosūtīsim informāciju par jūsu bērna vietu rindā un iespējamo laiku.\n\nAr cieņu,\nEzermalas novada pašvaldība",
    "Sociālā palīdzība": "Labdien!\n\nPaldies, ka vērsāties pašvaldībā. Sociālais darbinieks ar jums sazināsies, lai vienotos par konsultāciju un pastāstītu, kāda palīdzība un kādi dokumenti nepieciešami.\n\nAr cieņu,\nEzermalas novada pašvaldība",
    "Cits": "Labdien!\n\nPaldies par iesniegumu. Esam to reģistrējuši un nodevuši atbildīgajam speciālistam, kas sniegs atbildi.\n\nAr cieņu,\nEzermalas novada pašvaldība",
}

SYSTEM_PROMPT = (
    "Tu palīdzi pašvaldības darbiniekam apstrādāt iedzīvotāju iesniegumus. No iesnieguma apraksta izvēlies "
    "vienu tēmu no dotā saraksta un uzraksti īsu, pieklājīgu atbildes projektu latviešu valodā (3–6 teikumi) "
    "pašvaldības vārdā. Nesoli konkrētus termiņus, naudu vai lēmumus par pabalstiem — to izlemj darbinieks. "
    "Neizdomā faktus, kas nav aprakstā. Neatkārto personas datus. Projektu pirms nosūtīšanas pārbaudīs cilvēks."
)


def ieteikums(apraksts: str) -> dict:
    """Līgums: {"tema", "atbildes_projekts"}."""
    return ieteikums_ar_avotu(apraksts)[0]


def ieteikums_ar_avotu(apraksts: str) -> tuple[dict, str]:
    """Tas pats ieteikums un avots ("claude" vai "imitacija") marķējumam saskarnē."""
    teksts = " ".join(apraksts.split())[:4000]
    if os.environ.get("ANTHROPIC_API_KEY"):
        result = _claude(teksts)
        if result is not None:
            return result, "claude"
    return _imitacija(teksts), "imitacija"


def claude_enabled() -> bool:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return True


def _imitacija(teksts: str) -> dict:
    lower = teksts.casefold()
    scores = {tema: sum(lower.count(k) for k in keys) for tema, keys in KEYWORDS.items()}
    best = max(scores, key=lambda t: (scores[t], -TEMAS.index(t)))
    tema = best if scores[best] > 0 else "Cits"
    return {"tema": tema, "atbildes_projekts": PROJEKTI[tema]}


def _claude(teksts: str) -> dict | None:
    try:
        import anthropic
        from pydantic import BaseModel
    except ImportError:
        log.warning("US-7: anthropic package not installed, using imitation")
        return None

    class Ieteikums(BaseModel):
        tema: Literal["Ceļi un bedres", "Ielu apgaismojums", "Atkritumi", "Bērnudārza rinda", "Sociālā palīdzība", "Cits"]
        atbildes_projekts: str

    try:
        client = anthropic.Anthropic(timeout=TIMEOUT_SECONDS, max_retries=1)
        response = client.messages.parse(
            model=MODEL,
            max_tokens=2000,
            output_config={"effort": "low"},
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Tēmas: {', '.join(TEMAS)}.\n\nIesnieguma apraksts:\n{teksts}"}],
            output_format=Ieteikums,
        )
    except anthropic.APITimeoutError:
        log.warning("US-7: Claude API timeout, using imitation")
        return None
    except anthropic.APIConnectionError:
        log.warning("US-7: Claude API connection error, using imitation")
        return None
    except anthropic.APIStatusError as exc:
        log.warning("US-7: Claude API error %s, using imitation", exc.status_code)
        return None
    if response.stop_reason == "refusal" or response.parsed_output is None:
        log.warning("US-7: Claude declined (%s), using imitation", response.stop_reason)
        return None
    return {"tema": response.parsed_output.tema, "atbildes_projekts": response.parsed_output.atbildes_projekts.strip()}
