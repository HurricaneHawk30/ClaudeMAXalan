"""Subject / skill / topic registry (docs/ARCHITECTURE.md section 2.2)."""
from __future__ import annotations

import importlib
import pkgutil
import re
from typing import Iterable

from .base import (
    MY_OWN_TOPIC_LABEL, PAST_PAPER_LABEL, Skill, Subject, Topic, YearSpec,
)

RESERVED_LABELS = (PAST_PAPER_LABEL, MY_OWN_TOPIC_LABEL, "🎓 Change year", "📘 Change subject")
_RESERVED_FOLDED = {x.casefold() for x in RESERVED_LABELS}


class RegistryError(ValueError):
    """Invalid content registration."""


def _norm_label(s: str) -> str:
    return " ".join(s.split()).casefold()


def _norm_text(s: str) -> str:
    s = s.lower().replace("’", "'").replace("½", "1/2")
    s = re.sub(r"\s*=\s*", "=", s)
    return " ".join(s.split())


def _check_level_map(lm: object, what: str) -> None:
    if (not isinstance(lm, (tuple, list)) or len(lm) != 5
            or any(isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 5 for v in lm)):
        raise RegistryError(f"{what}: level_map must be 5 integers in 1..5, got {lm!r}")


class Registry:
    def __init__(self) -> None:
        self._subjects: dict[str, Subject] = {}
        self._skills: dict[str, Skill] = {}
        self._skills_by_subject: dict[str, list[Skill]] = {}
        self._topics: dict[str, Topic] = {}
        # (subject, year) -> {folded label -> Topic}
        self._labels: dict[tuple[str, int], dict[str, Topic]] = {}
        self._past: dict[tuple[str, int], Topic] = {}

    # ------------------------------------------------------------ register
    def register(self, subject: Subject, skills: Iterable[Skill]) -> None:
        skills = list(skills)
        if not isinstance(subject, Subject):
            raise RegistryError("register() needs a Subject")
        sid = subject.id
        if not isinstance(sid, str) or not sid:
            raise RegistryError("subject id must be a non-empty string")
        if sid in self._subjects:
            raise RegistryError(f"duplicate subject id {sid!r}")
        if not isinstance(subject.title, str) or not subject.title.strip():
            raise RegistryError(f"subject {sid!r}: empty title")

        new_skill_ids: set[str] = set()
        for sk in skills:
            if not isinstance(sk, Skill):
                raise RegistryError(f"subject {sid!r}: not a Skill: {sk!r}")
            if sk.id in self._skills or sk.id in new_skill_ids:
                raise RegistryError(f"duplicate skill id {sk.id!r}")
            if sk.subject != sid:
                raise RegistryError(
                    f"skill {sk.id!r} has subject {sk.subject!r}, expected {sid!r}")
            new_skill_ids.add(sk.id)

        known = new_skill_ids  # a subject's topics may only use its own skills
        new_topics: dict[str, Topic] = {}
        new_labels: dict[tuple[str, int], dict[str, Topic]] = {}
        new_past: dict[tuple[str, int], Topic] = {}

        def add_topic(t: Topic) -> None:
            if t.id in self._topics or t.id in new_topics:
                raise RegistryError(f"duplicate topic id {t.id!r}")
            new_topics[t.id] = t

        for year, spec in sorted(subject.years.items()):
            where = f"subject {sid!r} year {year}"
            if not isinstance(year, int) or isinstance(year, bool):
                raise RegistryError(f"{where}: year must be an int")
            if not isinstance(spec, YearSpec):
                raise RegistryError(f"{where}: not a YearSpec")
            if not spec.rows:
                raise RegistryError(f"{where}: no rows")
            _check_level_map(spec.past_paper_level_map, f"{where} past_paper_level_map")
            labels: dict[str, Topic] = {}
            union: list[str] = []
            for ri, row in enumerate(spec.rows):
                if not 1 <= len(row) <= 2:
                    raise RegistryError(
                        f"{where} row {ri}: a row needs 1 or 2 topics, got {len(row)}")
                for t in row:
                    if not isinstance(t, Topic):
                        raise RegistryError(f"{where} row {ri}: not a Topic")
                    if not t.id or t.id.startswith("own:"):
                        raise RegistryError(f"{where}: bad topic id {t.id!r}")
                    if not t.label or not t.label.strip():
                        raise RegistryError(f"{where}: topic {t.id!r} has an empty label")
                    folded = _norm_label(t.label)
                    if folded in _RESERVED_FOLDED:
                        raise RegistryError(f"{where}: label {t.label!r} is reserved")
                    if folded in labels:
                        raise RegistryError(f"{where}: duplicate label {t.label!r}")
                    if not t.skills:
                        raise RegistryError(f"topic {t.id!r}: no skills")
                    for k in t.skills:
                        if k not in known:
                            raise RegistryError(
                                f"topic {t.id!r} references unknown skill {k!r}")
                        if k not in union:
                            union.append(k)
                    _check_level_map(t.level_map, f"topic {t.id!r}")
                    add_topic(t)
                    labels[folded] = t
            past = Topic(
                id=f"{sid}.y{year}.past_paper", label=PAST_PAPER_LABEL,
                skills=tuple(union), level_map=spec.past_paper_level_map, exam=True)
            add_topic(past)
            new_labels[(sid, year)] = labels
            new_past[(sid, year)] = past

        # everything validated: commit
        self._subjects[sid] = subject
        self._skills_by_subject[sid] = list(skills)
        for sk in skills:
            self._skills[sk.id] = sk
        self._topics.update(new_topics)
        self._labels.update(new_labels)
        self._past.update(new_past)

    # ------------------------------------------------------------- queries
    def subjects_for_year(self, year: int) -> list[Subject]:
        subs = [s for s in self._subjects.values() if year in s.years]
        return sorted(subs, key=lambda s: s.order)  # stable: ties keep registration order

    def years(self) -> list[int]:
        return sorted({y for s in self._subjects.values() for y in s.years})

    def subject(self, subject_id: str) -> Subject | None:
        return self._subjects.get(subject_id)

    def skill(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def skills_of(self, subject_id: str) -> list[Skill]:
        return list(self._skills_by_subject.get(subject_id, ()))

    def topic_rows(self, subject_id: str, year: int) -> list[tuple[str, ...]]:
        s = self._subjects.get(subject_id)
        spec = s.years.get(year) if s else None
        if spec is None:
            return []
        return [tuple(t.label for t in row) for row in spec.rows]

    def topic_by_label(self, subject_id: str, year: int, label: str) -> Topic | None:
        if not isinstance(label, str):
            return None
        key = _norm_label(label)
        if key == _norm_label(PAST_PAPER_LABEL):
            return self._past.get((subject_id, year))
        return self._labels.get((subject_id, year), {}).get(key)

    def topic(self, topic_id: str) -> Topic | None:
        if not isinstance(topic_id, str):
            return None
        if topic_id.startswith("own:"):
            sk = self._skills.get(topic_id[4:])
            return self.own_topic(sk.id) if sk else None
        return self._topics.get(topic_id)

    def own_topic(self, skill_id: str) -> Topic:
        sk = self._skills.get(skill_id)
        if sk is None:
            raise RegistryError(f"unknown skill {skill_id!r}")
        return Topic(id="own:" + skill_id, label=sk.title, skills=(skill_id,))

    def match_skills(self, subject_id: str, text: str) -> list[str]:
        if not isinstance(text, str):
            return []
        t = _norm_text(text)
        scored: list[tuple[int, int, str]] = []
        for idx, sk in enumerate(self._skills_by_subject.get(subject_id, ())):
            best = 0
            for alias in sk.aliases:
                a = _norm_text(alias)
                if not a or len(a) <= best:
                    continue
                pat = r"(?<![^\W_])" + re.escape(a) + r"s?(?![^\W_])"
                if re.search(pat, t):
                    best = len(a)
            if best:
                scored.append((-best, idx, sk.id))
        scored.sort()
        return [sid for _, _, sid in scored]


def load_registry(banks: Iterable[str] = ()) -> Registry:
    """Build a new Registry from tutor.subjects.* modules and optional JSON banks."""
    reg = Registry()
    root = (__package__ or "tutor.content").rsplit(".", 1)[0]
    pkg_name = root + ".subjects"
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError as e:
        if e.name not in (pkg_name, root):
            raise
        pkg = None
    if pkg is not None and hasattr(pkg, "__path__"):
        names = sorted(m.name for m in pkgutil.iter_modules(pkg.__path__)
                       if not m.name.startswith("_"))
        for name in names:
            mod = importlib.import_module(f"{pkg_name}.{name}")
            fn = getattr(mod, "register", None)
            if not callable(fn):
                raise RegistryError(f"{pkg_name}.{name} has no register(reg) function")
            fn(reg)
    if banks:
        from .bank import register_bank
        for path in banks:
            register_bank(reg, path)
    return reg
