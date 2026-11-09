"""
Field-specific simulation profiles for Chaos Budget.

Each field has tuned parameters for:
  - event_type_luck_bias: how much luck each event type carries in this field
  - career_transitions: Markov chain for positive career progression
  - negative_transitions: Markov chain for setback/missed-opportunity progression
  - keyword_boost_multiplier: how strongly luck keywords affect the score
  - description: human-readable field description

If a user's field doesn't match any profile, the DEFAULT profile is used.
"""

from __future__ import annotations

# ── Field matching aliases ────────────────────────────────────────────
# Maps common user inputs to canonical field names.

FIELD_ALIASES: dict[str, str] = {
    # Software / Tech
    "software engineering": "tech",
    "software": "tech",
    "software engineer": "tech",
    "computer science": "tech",
    "cs": "tech",
    "it": "tech",
    "tech": "tech",
    "technology": "tech",
    "data science": "tech",
    "data engineering": "tech",
    "machine learning": "tech",
    "ai": "tech",
    "devops": "tech",
    "frontend": "tech",
    "backend": "tech",
    "full stack": "tech",
    "fullstack": "tech",
    "web development": "tech",
    "sde": "tech",
    "swe": "tech",
    "cybersecurity": "tech",
    "cloud": "tech",
    "product management": "tech",

    # Medicine / Healthcare
    "medicine": "medicine",
    "medical": "medicine",
    "doctor": "medicine",
    "healthcare": "medicine",
    "nursing": "medicine",
    "pharmacy": "medicine",
    "dentistry": "medicine",
    "mbbs": "medicine",
    "md": "medicine",

    # Finance / Banking
    "finance": "finance",
    "banking": "finance",
    "investment banking": "finance",
    "fintech": "finance",
    "accounting": "finance",
    "chartered accountant": "finance",
    "ca": "finance",
    "actuarial": "finance",
    "trading": "finance",
    "wealth management": "finance",

    # Law
    "law": "law",
    "legal": "law",
    "lawyer": "law",
    "advocate": "law",
    "judiciary": "law",

    # MBA / Management / Consulting
    "mba": "management",
    "management": "management",
    "consulting": "management",
    "business": "management",
    "operations": "management",
    "marketing": "management",
    "hr": "management",
    "human resources": "management",
    "strategy": "management",
    "supply chain": "management",

    # Academia / Research
    "academia": "academia",
    "research": "academia",
    "professor": "academia",
    "phd": "academia",
    "teaching": "academia",
    "education": "academia",
    "academic": "academia",
}


def resolve_field(user_field: str) -> str:
    """Map a user's free-text field input to a canonical profile name."""
    normalized = user_field.strip().lower()
    return FIELD_ALIASES.get(normalized, "default")


# ── Profile definitions ───────────────────────────────────────────────

FIELD_PROFILES: dict[str, dict] = {

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "tech": {
        "description": "Software Engineering / Technology",
        "event_luck_bias": {
            "failure":     0.75,   # Layoffs in tech are very market-driven
            "relocation":  0.60,   # Visa/relocation somewhat circumstantial
            "personal":    0.50,
            "job":         0.50,   # Campus placements, referrals = high luck
            "achievement": 0.25,   # Hackathons, open source = more skill
            "education":   0.20,   # College choice matters but is deliberate
            "skill":       0.10,   # Learning a framework is pure effort
            "other":       0.40,
        },
        "career_transitions": {
            "student":   {"student": 0.08, "junior": 0.72, "mid": 0.15, "senior": 0.04, "lead": 0.01, "executive": 0.00},
            "junior":    {"student": 0.01, "junior": 0.25, "mid": 0.55, "senior": 0.15, "lead": 0.03, "executive": 0.01},
            "mid":       {"student": 0.00, "junior": 0.03, "mid": 0.30, "senior": 0.45, "lead": 0.17, "executive": 0.05},
            "senior":    {"student": 0.00, "junior": 0.01, "mid": 0.05, "senior": 0.35, "lead": 0.40, "executive": 0.19},
            "lead":      {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.08, "lead": 0.44, "executive": 0.45},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.01, "senior": 0.04, "lead": 0.10, "executive": 0.85},
        },
        "negative_transitions": {
            "student":   {"student": 0.55, "junior": 0.35, "mid": 0.08, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.08, "junior": 0.55, "mid": 0.27, "senior": 0.08, "lead": 0.02, "executive": 0.00},
            "mid":       {"student": 0.01, "junior": 0.12, "mid": 0.52, "senior": 0.27, "lead": 0.06, "executive": 0.02},
            "senior":    {"student": 0.00, "junior": 0.03, "mid": 0.18, "senior": 0.50, "lead": 0.22, "executive": 0.07},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.06, "senior": 0.22, "lead": 0.50, "executive": 0.21},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.08, "lead": 0.29, "executive": 0.60},
        },
        "keyword_boost_multiplier": 1.0,  # baseline
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "medicine": {
        "description": "Medicine / Healthcare",
        "event_luck_bias": {
            "failure":     0.40,   # Medical failures are rare and usually systemic
            "relocation":  0.55,   # Posting locations can be luck-based
            "personal":    0.50,
            "job":         0.35,   # NEET/residency is merit-heavy
            "achievement": 0.20,   # Publications, surgeries = skill
            "education":   0.30,   # NEET rank has luck but heavily prep-based
            "skill":       0.10,   # Clinical skills = pure effort
            "other":       0.35,
        },
        "career_transitions": {
            "student":   {"student": 0.15, "junior": 0.65, "mid": 0.15, "senior": 0.04, "lead": 0.01, "executive": 0.00},
            "junior":    {"student": 0.02, "junior": 0.40, "mid": 0.42, "senior": 0.13, "lead": 0.02, "executive": 0.01},
            "mid":       {"student": 0.00, "junior": 0.03, "mid": 0.40, "senior": 0.40, "lead": 0.13, "executive": 0.04},
            "senior":    {"student": 0.00, "junior": 0.01, "mid": 0.05, "senior": 0.50, "lead": 0.32, "executive": 0.12},
            "lead":      {"student": 0.00, "junior": 0.00, "mid": 0.02, "senior": 0.10, "lead": 0.53, "executive": 0.35},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.01, "senior": 0.03, "lead": 0.11, "executive": 0.85},
        },
        "negative_transitions": {
            "student":   {"student": 0.65, "junior": 0.28, "mid": 0.05, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.10, "junior": 0.60, "mid": 0.22, "senior": 0.06, "lead": 0.02, "executive": 0.00},
            "mid":       {"student": 0.01, "junior": 0.10, "mid": 0.58, "senior": 0.24, "lead": 0.05, "executive": 0.02},
            "senior":    {"student": 0.00, "junior": 0.02, "mid": 0.12, "senior": 0.55, "lead": 0.24, "executive": 0.07},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.05, "senior": 0.15, "lead": 0.55, "executive": 0.24},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.02, "senior": 0.07, "lead": 0.21, "executive": 0.70},
        },
        "keyword_boost_multiplier": 0.7,  # luck keywords matter less in medicine
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "finance": {
        "description": "Finance / Banking / Fintech",
        "event_luck_bias": {
            "failure":     0.85,   # Market crashes, fund collapses = very high luck
            "relocation":  0.60,
            "personal":    0.50,
            "job":         0.65,   # Target school pipelines, networking-heavy
            "achievement": 0.35,   # Deals closed involve timing + relationships
            "education":   0.35,   # B-school admission has significant luck
            "skill":       0.15,   # Modelling/analysis skills = effort
            "other":       0.45,
        },
        "career_transitions": {
            "student":   {"student": 0.10, "junior": 0.68, "mid": 0.17, "senior": 0.04, "lead": 0.01, "executive": 0.00},
            "junior":    {"student": 0.02, "junior": 0.28, "mid": 0.48, "senior": 0.17, "lead": 0.04, "executive": 0.01},
            "mid":       {"student": 0.00, "junior": 0.05, "mid": 0.32, "senior": 0.40, "lead": 0.17, "executive": 0.06},
            "senior":    {"student": 0.00, "junior": 0.02, "mid": 0.08, "senior": 0.38, "lead": 0.35, "executive": 0.17},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.04, "senior": 0.10, "lead": 0.40, "executive": 0.45},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.02, "senior": 0.05, "lead": 0.13, "executive": 0.80},
        },
        "negative_transitions": {
            "student":   {"student": 0.60, "junior": 0.30, "mid": 0.08, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.12, "junior": 0.50, "mid": 0.25, "senior": 0.10, "lead": 0.03, "executive": 0.00},
            "mid":       {"student": 0.02, "junior": 0.15, "mid": 0.48, "senior": 0.25, "lead": 0.08, "executive": 0.02},
            "senior":    {"student": 0.00, "junior": 0.05, "mid": 0.20, "senior": 0.42, "lead": 0.25, "executive": 0.08},
            "lead":      {"student": 0.00, "junior": 0.02, "mid": 0.10, "senior": 0.25, "lead": 0.40, "executive": 0.23},
            "executive": {"student": 0.00, "junior": 0.01, "mid": 0.05, "senior": 0.12, "lead": 0.30, "executive": 0.52},
        },
        "keyword_boost_multiplier": 1.2,  # luck keywords hit harder in finance
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "law": {
        "description": "Law / Legal",
        "event_luck_bias": {
            "failure":     0.55,   # Case losses can be luck or client-driven
            "relocation":  0.60,
            "personal":    0.50,
            "job":         0.45,   # Bar exam + clerkship: mixed merit/connections
            "achievement": 0.25,   # Winning cases = mostly skill
            "education":   0.30,   # CLAT/law school admission: prep-heavy
            "skill":       0.12,   # Legal research, argumentation = effort
            "other":       0.40,
        },
        "career_transitions": {
            "student":   {"student": 0.12, "junior": 0.68, "mid": 0.15, "senior": 0.04, "lead": 0.01, "executive": 0.00},
            "junior":    {"student": 0.02, "junior": 0.38, "mid": 0.43, "senior": 0.13, "lead": 0.03, "executive": 0.01},
            "mid":       {"student": 0.00, "junior": 0.04, "mid": 0.38, "senior": 0.40, "lead": 0.14, "executive": 0.04},
            "senior":    {"student": 0.00, "junior": 0.01, "mid": 0.06, "senior": 0.48, "lead": 0.33, "executive": 0.12},
            "lead":      {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.10, "lead": 0.50, "executive": 0.37},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.01, "senior": 0.04, "lead": 0.12, "executive": 0.83},
        },
        "negative_transitions": {
            "student":   {"student": 0.62, "junior": 0.30, "mid": 0.06, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.08, "junior": 0.58, "mid": 0.24, "senior": 0.08, "lead": 0.02, "executive": 0.00},
            "mid":       {"student": 0.01, "junior": 0.10, "mid": 0.55, "senior": 0.26, "lead": 0.06, "executive": 0.02},
            "senior":    {"student": 0.00, "junior": 0.03, "mid": 0.14, "senior": 0.52, "lead": 0.24, "executive": 0.07},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.06, "senior": 0.18, "lead": 0.52, "executive": 0.23},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.08, "lead": 0.24, "executive": 0.65},
        },
        "keyword_boost_multiplier": 0.9,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "management": {
        "description": "MBA / Management / Consulting",
        "event_luck_bias": {
            "failure":     0.70,   # Layoffs in consulting are cycle-driven
            "relocation":  0.60,
            "personal":    0.50,
            "job":         0.60,   # MBA placements = school brand + luck
            "achievement": 0.35,   # Case comps, promotions: mix of merit + politics
            "education":   0.40,   # B-school admission: brand/networking heavy
            "skill":       0.15,
            "other":       0.45,
        },
        "career_transitions": {
            "student":   {"student": 0.10, "junior": 0.65, "mid": 0.18, "senior": 0.05, "lead": 0.02, "executive": 0.00},
            "junior":    {"student": 0.01, "junior": 0.22, "mid": 0.52, "senior": 0.18, "lead": 0.05, "executive": 0.02},
            "mid":       {"student": 0.00, "junior": 0.03, "mid": 0.28, "senior": 0.43, "lead": 0.19, "executive": 0.07},
            "senior":    {"student": 0.00, "junior": 0.01, "mid": 0.05, "senior": 0.32, "lead": 0.40, "executive": 0.22},
            "lead":      {"student": 0.00, "junior": 0.00, "mid": 0.02, "senior": 0.07, "lead": 0.41, "executive": 0.50},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.01, "senior": 0.03, "lead": 0.11, "executive": 0.85},
        },
        "negative_transitions": {
            "student":   {"student": 0.58, "junior": 0.32, "mid": 0.08, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.10, "junior": 0.48, "mid": 0.28, "senior": 0.10, "lead": 0.03, "executive": 0.01},
            "mid":       {"student": 0.01, "junior": 0.12, "mid": 0.48, "senior": 0.28, "lead": 0.08, "executive": 0.03},
            "senior":    {"student": 0.00, "junior": 0.04, "mid": 0.16, "senior": 0.45, "lead": 0.26, "executive": 0.09},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.07, "senior": 0.20, "lead": 0.45, "executive": 0.27},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.10, "lead": 0.28, "executive": 0.59},
        },
        "keyword_boost_multiplier": 1.1,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "academia": {
        "description": "Academia / Research / Teaching",
        "event_luck_bias": {
            "failure":     0.55,   # Grant rejections have luck, but also quality
            "relocation":  0.65,   # Postdoc locations = very luck-dependent
            "personal":    0.50,
            "job":         0.55,   # Faculty positions are scarce + timing-heavy
            "achievement": 0.30,   # Publications: peer review has randomness
            "education":   0.25,   # PhD admission is mostly merit
            "skill":       0.10,   # Research skills = pure effort
            "other":       0.40,
        },
        "career_transitions": {
            "student":   {"student": 0.20, "junior": 0.60, "mid": 0.15, "senior": 0.04, "lead": 0.01, "executive": 0.00},
            "junior":    {"student": 0.05, "junior": 0.42, "mid": 0.38, "senior": 0.12, "lead": 0.02, "executive": 0.01},
            "mid":       {"student": 0.01, "junior": 0.05, "mid": 0.42, "senior": 0.38, "lead": 0.11, "executive": 0.03},
            "senior":    {"student": 0.00, "junior": 0.02, "mid": 0.07, "senior": 0.50, "lead": 0.30, "executive": 0.11},
            "lead":      {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.12, "lead": 0.50, "executive": 0.35},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.02, "senior": 0.05, "lead": 0.13, "executive": 0.80},
        },
        "negative_transitions": {
            "student":   {"student": 0.68, "junior": 0.25, "mid": 0.05, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.12, "junior": 0.58, "mid": 0.22, "senior": 0.06, "lead": 0.02, "executive": 0.00},
            "mid":       {"student": 0.02, "junior": 0.10, "mid": 0.55, "senior": 0.25, "lead": 0.06, "executive": 0.02},
            "senior":    {"student": 0.00, "junior": 0.03, "mid": 0.14, "senior": 0.53, "lead": 0.23, "executive": 0.07},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.06, "senior": 0.18, "lead": 0.52, "executive": 0.23},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.03, "senior": 0.08, "lead": 0.25, "executive": 0.64},
        },
        "keyword_boost_multiplier": 0.85,
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "default": {
        "description": "General / Other fields",
        "event_luck_bias": {
            "failure":     0.70,
            "relocation":  0.65,
            "personal":    0.50,
            "job":         0.40,
            "achievement": 0.30,
            "education":   0.25,
            "skill":       0.15,
            "other":       0.40,
        },
        "career_transitions": {
            "student":   {"student": 0.10, "junior": 0.70, "mid": 0.15, "senior": 0.04, "lead": 0.01, "executive": 0.00},
            "junior":    {"student": 0.02, "junior": 0.30, "mid": 0.50, "senior": 0.14, "lead": 0.03, "executive": 0.01},
            "mid":       {"student": 0.00, "junior": 0.05, "mid": 0.35, "senior": 0.40, "lead": 0.15, "executive": 0.05},
            "senior":    {"student": 0.00, "junior": 0.02, "mid": 0.08, "senior": 0.40, "lead": 0.35, "executive": 0.15},
            "lead":      {"student": 0.00, "junior": 0.01, "mid": 0.04, "senior": 0.10, "lead": 0.45, "executive": 0.40},
            "executive": {"student": 0.00, "junior": 0.00, "mid": 0.02, "senior": 0.05, "lead": 0.13, "executive": 0.80},
        },
        "negative_transitions": {
            "student":   {"student": 0.60, "junior": 0.30, "mid": 0.08, "senior": 0.02, "lead": 0.00, "executive": 0.00},
            "junior":    {"student": 0.10, "junior": 0.55, "mid": 0.25, "senior": 0.08, "lead": 0.02, "executive": 0.00},
            "mid":       {"student": 0.02, "junior": 0.15, "mid": 0.50, "senior": 0.25, "lead": 0.06, "executive": 0.02},
            "senior":    {"student": 0.00, "junior": 0.05, "mid": 0.20, "senior": 0.45, "lead": 0.22, "executive": 0.08},
            "lead":      {"student": 0.00, "junior": 0.02, "mid": 0.08, "senior": 0.25, "lead": 0.45, "executive": 0.20},
            "executive": {"student": 0.00, "junior": 0.01, "mid": 0.04, "senior": 0.10, "lead": 0.30, "executive": 0.55},
        },
        "keyword_boost_multiplier": 1.0,
    },
}


def get_profile(field: str) -> dict:
    """Get the simulation profile for a field. Falls back to 'default'."""
    canonical = resolve_field(field)
    return FIELD_PROFILES.get(canonical, FIELD_PROFILES["default"])
