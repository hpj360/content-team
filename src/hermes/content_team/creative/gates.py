"""创作质量门（可机器验证断言）。

蒸馏并融合自公开高热度创作 skill 的审查机制：

- 分镜分级/时长硬门（段 ≤15s、镜 2–5s）——短剧/分镜套件的确定性质量门
- 剧本价值转折/场景完整性 + 合规词表 + 去 AI 味检测——短剧与"去 AI 味"skill
- 小说 logline/章节/伏笔与状态契约——网文 skill 的状态守卫
- 导演风格与阐述完整性——电影导演 skill 的出口门

本模块为**纯函数库**：输入规范化 dict，输出 ``GateReport``，不依赖数据库，
便于单元测试与在 builder/checker 之外的独立审查器中复用。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

Severity = Literal["error", "warn"]

# ---------------------------------------------------------------------------
# 阈值常量（跨模块复用；pipeline 会 re-export 以保持向后兼容）
# ---------------------------------------------------------------------------

MAX_LOGLINE_CHARS = 200
MIN_SCENES = 3

# 分镜质量门（蒸馏自短剧/分镜 skill）：单镜时长硬门 [2, 5] 秒，段 ≤ 15 秒
SHOT_MIN_SECONDS: float = 2.0
SHOT_MAX_SECONDS: float = 5.0
SEGMENT_MAX_SECONDS: float = 15.0

# 小说章节字数建议区间（仅警告，不阻断）
CHAPTER_MIN_WORDS = 500
CHAPTER_MAX_WORDS = 8000

# 审查通过分数线（0–100）
REVIEW_PASS_SCORE = 80.0

# 惩分权重
ERROR_PENALTY = 12.0
WARN_PENALTY = 3.0

# 各阶段维度权重（用于加权总分的展示）
DIMENSION_WEIGHTS: dict[str, float] = {
    "structure": 0.30,
    "compliance": 0.20,
    "consistency": 0.20,
    "pacing": 0.15,
    "craft": 0.15,
}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GateIssue:
    """单条审查问题。"""

    code: str
    message: str
    severity: Severity = "error"
    dimension: str = "structure"


@dataclass
class GateReport:
    """单个阶段的审查结果。"""

    stage: str
    issues: list[GateIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[GateIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[GateIssue]:
        return [i for i in self.issues if i.severity == "warn"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def error_messages(self) -> list[str]:
        return [i.message for i in self.errors]


# ---------------------------------------------------------------------------
# 词表与正则（蒸馏）
# ---------------------------------------------------------------------------

# AI 套路化表达（"去 AI 味"skill 蒸馏）：命中计警告
AI_CLICHE_TOKENS: tuple[str, ...] = (
    "不由得",
    "顿时",
    "心中暗道",
    "殊不知",
    "不禁",
    "值得一提的是",
    "五味杂陈",
    "无法言喻",
    "交织",
    "画卷",
    "奏响",
    "栩栩如生",
    "淋漓尽致",
)

# 旁白式心理描写（剧本应改为可拍动作）：命中计警告
PSYCH_NARRATION_RE = re.compile(r"(他心里|她心里|心想|暗自想|内心想|心中想|脑海中浮现)")

# 场景标题（中文场次 / 英文 slugline / 内景外景），仅匹配行首，避免重复计数
SCENE_HEADER_RE = re.compile(
    r"^\s*(?:第\s*[0-9一二三四五六七八九十百千]+\s*场|INT\.|EXT\.|内景|外景)",
    re.MULTILINE,
)

# 内容合规阻断词（示例性最小集，实际部署应外置为可配置词库）
COMPLIANCE_BLOCKLIST: tuple[str, ...] = (
    "法轮功",
    "代开发票",
    "办证刻章",
    "枪支买卖",
    "毒品交易",
)


def find_tokens(text: str, tokens: Iterable[str]) -> list[str]:
    """返回文本中命中的词表项。"""
    return [t for t in tokens if t in text]


def count_scenes(body: str) -> int:
    """统计正文字段中的场景数。"""
    return len(SCENE_HEADER_RE.findall(body or ""))


def _field(shot: Any, name: str, default: Any = None) -> Any:
    """兼容 dict 与对象的字段读取（供规范化数据与 ORM 实体共用）。"""
    if isinstance(shot, dict):
        return shot.get(name, default)
    return getattr(shot, name, default)


def validate_shot_durations(shots: Iterable[Any]) -> list[str]:
    """校验镜头时长硬门与段时长，返回错误消息列表（空表示通过）。

    入参元素可为 dict（``duration_seconds`` 字段）或对象
    （``duration_seconds`` 属性），兼容规范化数据与 ORM 实体。
    """
    errors: list[str] = []
    total = 0.0
    for shot in shots:
        duration = float(_field(shot, "duration_seconds", 0.0) or 0.0)
        total += duration
        if not (SHOT_MIN_SECONDS <= duration <= SHOT_MAX_SECONDS):
            number = _field(shot, "shot_number", "?")
            errors.append(
                f"镜头 {number} 时长 {duration}s 超出 "
                f"[{SHOT_MIN_SECONDS}, {SHOT_MAX_SECONDS}]s"
            )
    if total > SEGMENT_MAX_SECONDS:
        errors.append(f"段时长 {total}s 超过 {SEGMENT_MAX_SECONDS}s")
    return errors


# ---------------------------------------------------------------------------
# 各阶段质量门（输入规范化 dict）
# ---------------------------------------------------------------------------


def gate_novel(data: dict[str, Any]) -> GateReport:
    """小说阶段质量门。

    ``data`` 字段：``title`` / ``logline`` / ``chapters``（每章含 ``body``/``word_count``）。
    """
    report = GateReport(stage="NOVEL")
    logline = str(data.get("logline") or "")
    if not logline.strip():
        report.issues.append(GateIssue("N001", "logline 为空", "error", "structure"))
    elif len(logline) > MAX_LOGLINE_CHARS:
        report.issues.append(
            GateIssue("N002", f"logline 超过 {MAX_LOGLINE_CHARS} 字", "error", "structure")
        )
    if not str(data.get("title") or "").strip():
        report.issues.append(GateIssue("N003", "小说标题为空", "error", "structure"))

    chapters = data.get("chapters") or []
    if not chapters:
        report.issues.append(GateIssue("N004", "小说没有章节", "error", "structure"))
    for idx, chapter in enumerate(chapters, start=1):
        body = str(chapter.get("body") or "")
        words = int(chapter.get("word_count") or 0)
        if not body.strip():
            report.issues.append(
                GateIssue("N005", f"第 {idx} 章正文为空", "error", "structure")
            )
        elif words and not (CHAPTER_MIN_WORDS <= words <= CHAPTER_MAX_WORDS):
            report.issues.append(
                GateIssue(
                    "N006",
                    f"第 {idx} 章字数 {words} 超出建议区间 "
                    f"[{CHAPTER_MIN_WORDS}, {CHAPTER_MAX_WORDS}]",
                    "warn",
                    "pacing",
                )
            )
    return report


def gate_script(data: dict[str, Any]) -> GateReport:
    """剧本阶段质量门。

    ``data`` 字段：``logline`` / ``body``。
    """
    report = GateReport(stage="SCRIPT")
    logline = str(data.get("logline") or "")
    body = str(data.get("body") or "")

    if not logline.strip():
        report.issues.append(GateIssue("S001", "logline 为空", "error", "structure"))
    elif len(logline) > MAX_LOGLINE_CHARS:
        report.issues.append(
            GateIssue("S002", f"logline 超过 {MAX_LOGLINE_CHARS} 字", "error", "structure")
        )
    if not body.strip():
        report.issues.append(GateIssue("S003", "剧本正文为空", "error", "structure"))

    scenes = count_scenes(body)
    if scenes < MIN_SCENES:
        report.issues.append(
            GateIssue("S004", f"场景数 {scenes} 少于 {MIN_SCENES}", "error", "structure")
        )

    if PSYCH_NARRATION_RE.search(body):
        report.issues.append(
            GateIssue("S005", "存在旁白式心理描写，应改为可拍动作", "warn", "craft")
        )
    cliches = find_tokens(body, AI_CLICHE_TOKENS)
    if cliches:
        report.issues.append(
            GateIssue(
                "S006",
                f"命中 AI 套路化表达：{'、'.join(cliches)}",
                "warn",
                "craft",
            )
        )
    blocked = find_tokens(body, COMPLIANCE_BLOCKLIST)
    if blocked:
        report.issues.append(
            GateIssue(
                "S007", f"命中合规阻断词：{'、'.join(blocked)}", "error", "compliance"
            )
        )
    return report


def gate_storyboard(data: dict[str, Any]) -> GateReport:
    """分镜阶段质量门。

    ``data`` 字段：``shots``（每镜含 ``shot_number`` / ``description`` /
    ``shot_size`` / ``camera_movement`` / ``duration_seconds``）。
    """
    report = GateReport(stage="STORYBOARD")
    shots = data.get("shots") or []
    if not shots:
        report.issues.append(GateIssue("B001", "分镜没有镜头", "error", "structure"))
        return report

    for shot in shots:
        if not str(shot.get("description") or "").strip():
            report.issues.append(
                GateIssue(
                    "B002",
                    f"镜头 {shot.get('shot_number', '?')} 描述为空",
                    "error",
                    "structure",
                )
            )

    numbers = [int(s.get("shot_number") or 0) for s in shots]
    expected = list(range(1, len(shots) + 1))
    if numbers != expected:
        report.issues.append(
            GateIssue("B003", "镜头号未从 1 连续递增", "error", "consistency")
        )

    for message in validate_shot_durations(shots):
        report.issues.append(GateIssue("B004", message, "error", "pacing"))

    for prev, cur in zip(shots, shots[1:]):
        if prev.get("shot_size") == cur.get("shot_size"):
            report.issues.append(
                GateIssue(
                    "B005",
                    f"相邻镜头 {prev.get('shot_number')}/{cur.get('shot_number')} "
                    "景别重复",
                    "warn",
                    "consistency",
                )
            )
    return report


def gate_directing(data: dict[str, Any]) -> GateReport:
    """导演阶段质量门。

    ``data`` 字段：``style`` / ``tone`` / ``pacing`` / ``director_notes``。
    """
    report = GateReport(stage="DIRECTING")
    for code, key, label in (
        ("D001", "style", "风格"),
        ("D002", "tone", "基调"),
        ("D003", "pacing", "节奏"),
        ("D004", "director_notes", "导演阐述"),
    ):
        if not str(data.get(key) or "").strip():
            report.issues.append(
                GateIssue(code, f"导演方案{label}为空", "error", "craft")
            )
    return report


# ---------------------------------------------------------------------------
# 故事状态 schema（状态落盘契约）
# ---------------------------------------------------------------------------

TRACKING_FIELDS: frozenset[str] = frozenset(
    {
        "position",       # 当前位置（卷/章）
        "recent_summary", # 近 5 章摘要
        "active_characters",  # 活跃角色
        "pending_foreshadowing",  # 待回收伏笔
        "volume_goal",    # 当前卷目标
        "global_rules",   # 全局约束
        "next_step",      # 下一步计划
    }
)

CHARACTER_DIMENSIONS: frozenset[str] = frozenset(
    {"ability", "psychology", "relations", "goals"}
)

FORESHADOWING_FIELDS: frozenset[str] = frozenset(
    {"id", "content", "planted_at", "planned_resolution", "status"}
)

FORESHADOWING_STATUSES: frozenset[str] = frozenset(
    {"planted", "in_progress", "resolved", "abandoned"}
)

GOAL_LEVELS: tuple[str, ...] = ("global", "volume", "chapter")


def gate_story_state(data: dict[str, Any]) -> GateReport:
    """故事状态 schema 门（唯一结构化权威状态）。

    ``data`` 字段：``tracking`` / ``characters`` / ``foreshadowing`` / ``goals``。
    违规码 T001–T006；缺字段为 error，仅缺部分摘要类内容为 warn。
    """
    report = GateReport(stage="STORY_STATE")

    tracking = data.get("tracking") or {}
    missing_tracking = [f for f in sorted(TRACKING_FIELDS) if not str(tracking.get(f) or "").strip()]
    if missing_tracking:
        report.issues.append(
            GateIssue(
                "T001",
                f"状态卡缺少栏位：{'、'.join(missing_tracking)}",
                "error",
                "consistency",
            )
        )

    characters = data.get("characters") or []
    if not characters:
        report.issues.append(
            GateIssue("T002", "角色状态为空（至少一名主要角色）", "error", "structure")
        )
    for idx, char in enumerate(characters, start=1):
        name = str(char.get("name") or "").strip()
        if not name:
            report.issues.append(
                GateIssue("T003", f"第 {idx} 个角色缺少 name", "error", "structure")
            )
        missing_dims = [
            d for d in sorted(CHARACTER_DIMENSIONS) if not str(char.get(d) or "").strip()
        ]
        if missing_dims:
            report.issues.append(
                GateIssue(
                    "T004",
                    f"角色 {name or idx} 缺少状态维度：{'、'.join(missing_dims)}",
                    "warn",
                    "structure",
                )
            )

    foreshadowing = data.get("foreshadowing") or []
    for idx, item in enumerate(foreshadowing, start=1):
        missing = [
            f for f in sorted(FORESHADOWING_FIELDS) if not str(item.get(f) or "").strip()
        ]
        if missing:
            report.issues.append(
                GateIssue(
                    "T005",
                    f"伏笔 #{idx} 缺少字段：{'、'.join(missing)}",
                    "error",
                    "structure",
                )
            )
            continue
        status = str(item.get("status") or "")
        if status != "planted":
            report.issues.append(
                GateIssue(
                    "T006",
                    f"伏笔 {item.get('id')} 状态 {status} 非初始 planted",
                    "warn",
                    "structure",
                )
            )

    goals = data.get("goals") or {}
    missing_goals = [g for g in GOAL_LEVELS if not str(goals.get(g) or "").strip()]
    if missing_goals:
        report.issues.append(
            GateIssue(
                "T007",
                f"目标分层缺少：{'、'.join(missing_goals)}",
                "error",
                "structure",
            )
        )
    return report


GOAL_LEVELS: tuple[str, ...] = ("global", "volume", "chapter")

# 伏笔生命周期一致性门（Round 4/5）
# L001：埋设缺口 —— 状态卡的伏笔未能在小说正文中找到命中词（error，全局兜底）
# L002：状态不在枚举内（error）
# L003：计划回收位置缺失（error）
# L004：埋设章区间缺口 —— planted_at 指定章正文存在但未命中关键词（error）
# L005：回收章缺口 —— status=resolved 且 planned_resolution 指定章存在但未命中（error）

# "第N章" 章号提取（中文章号；英文 INT./EXT. 不适用于章级区间）
CHAPTER_NUM_RE = re.compile(r"第\s*([0-9一二三四五六七八九十百千]+)\s*章")
_CN_DIGITS = {
    "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    "百": 100, "千": 1000,
}


def parse_chapter_number(text: str) -> int | None:
    """从"第N章"文本提取章号（支持阿拉伯数字与中文数字 1–9999）。"""
    match = CHAPTER_NUM_RE.search(text or "")
    if match is None:
        return None
    raw = match.group(1)
    if raw.isdigit():
        return int(raw)
    total = 0
    current = 0
    for ch in raw:
        if ch in ("十", "百", "千"):
            unit = {"十": 10, "百": 100, "千": 1000}[ch]
            total += (current or 1) * unit
            current = 0
        elif ch in _CN_DIGITS:
            current = current * 10 + _CN_DIGITS[ch]
        else:
            return None
    result = total + current
    return result if result > 0 else None


def gate_foreshadowing_lifecycle(data: dict[str, Any]) -> GateReport:
    """伏笔生命周期门：正文 ↔ 状态卡交叉验证（含章号区间，Round 5）。

    ``data`` 字段：
      ``foreshadowing``：状态卡伏笔（id/content/planted_at/planned_resolution/status/keyword）
      ``chapter_bodies``：正文按章列表 [ {"chapter_number": int, "body": str} ]

    判定优先级：章号区间可解析且对应章正文存在 → 区间校验（L004/L005）；
    否则退化为全局关键词命中（L001）。
    """
    report = GateReport(stage="STORY_FORESHADOWING")
    items = data.get("foreshadowing") or []
    chapters = data.get("chapter_bodies") or []
    bodies_by_number: dict[int, str] = {}
    for chapter in chapters:
        number = int(chapter.get("chapter_number") or 0)
        bodies_by_number[number] = str(chapter.get("body") or "")

    for item in items:
        fid = str(item.get("id") or "")
        content = str(item.get("content") or "")
        keyword = str(item.get("keyword") or "").strip() or content[:4]
        status = str(item.get("status") or "")
        planted_at = str(item.get("planted_at") or "")
        planned = str(item.get("planned_resolution") or "")

        if status and status not in FORESHADOWING_STATUSES:
            report.issues.append(
                GateIssue(
                    "L002",
                    f"伏笔 {fid} 状态 {status} 不在 {sorted(FORESHADOWING_STATUSES)}",
                    "error",
                    "consistency",
                )
            )
        if not planned.strip():
            report.issues.append(
                GateIssue(
                    "L003",
                    f"伏笔 {fid} 缺少计划回收位置 planned_resolution",
                    "error",
                    "consistency",
                )
            )
            continue
        if not keyword:
            continue  # 未提供可验证关键词，卡内一致性已由 gate_story_state 覆盖

        planted_ch = parse_chapter_number(planted_at)
        planted_body = (
            bodies_by_number.get(planted_ch) if planted_ch is not None else None
        )
        range_checked = False

        if planted_body is not None:
            # 埋设章已写：区间校验优先于全局兜底
            range_checked = True
            if keyword not in planted_body:
                report.issues.append(
                    GateIssue(
                        "L004",
                        f"伏笔 {fid} 埋设章（第{planted_ch}章）未命中关键词「{keyword}」",
                        "error",
                        "consistency",
                    )
                )
        if not range_checked:
            # 无法区间校验（未解析章号或埋设章未写）→ 全局兜底
            matched = any(keyword in body for body in bodies_by_number.values())
            if not matched:
                report.issues.append(
                    GateIssue(
                        "L001",
                        f"伏笔 {fid} 关键词「{keyword}」未在正文中出现",
                        "error",
                        "consistency",
                    )
                )

        # 回收章校验：仅当已声明 resolved 且回收章正文已写
        if status == "resolved":
            planned_ch = parse_chapter_number(planned)
            planned_body = (
                bodies_by_number.get(planned_ch) if planned_ch is not None else None
            )
            if planned_body is not None and keyword not in planned_body:
                report.issues.append(
                    GateIssue(
                        "L005",
                        f"伏笔 {fid} 标记 resolved，但回收章（第{planned_ch}章）"
                        f"未命中关键词「{keyword}」",
                        "error",
                        "consistency",
                    )
                )

    return report


STAGE_GATES = {
    "NOVEL": gate_novel,
    "SCRIPT": gate_script,
    "STORYBOARD": gate_storyboard,
    "DIRECTING": gate_directing,
    "STORY_STATE": gate_story_state,
    "STORY_FORESHADOWING": gate_foreshadowing_lifecycle,
}


def score_reports(reports: Iterable[GateReport]) -> tuple[float, dict[str, float]]:
    """由若干阶段报告计算加权总分与维度得分（0–100）。

    返回 ``(total, dimension_scores)``。
    """
    errors = 0
    warnings = 0
    by_dimension: dict[str, list[GateIssue]] = {}
    for report in reports:
        for issue in report.issues:
            by_dimension.setdefault(issue.dimension, []).append(issue)
            if issue.severity == "error":
                errors += 1
            else:
                warnings += 1

    raw = 100.0 - errors * ERROR_PENALTY - warnings * WARN_PENALTY
    total = max(0.0, min(100.0, raw))

    dimension_scores: dict[str, float] = {}
    for name in DIMENSION_WEIGHTS:
        issues = by_dimension.get(name, [])
        penalty = sum(
            ERROR_PENALTY if i.severity == "error" else WARN_PENALTY for i in issues
        )
        dimension_scores[name] = max(0.0, min(100.0, 100.0 - penalty))
    return total, dimension_scores
