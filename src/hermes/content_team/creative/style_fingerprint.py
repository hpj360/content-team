"""文风指纹（创作者视角 Round 8 · A2'）。

从作者**自己的旧稿**提炼可注入生成 prompt 的风格约束，解决"AI 稿是技能文档
平均值、没有我的声音"这一创作者第一诉求。

纯规则、零依赖、可测试；不调 LLM。指纹只描述**可量化**的声线特征，
不复制原句（避免版权与抄袭）。
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

_CJK = r"\u4e00-\u9fff"
_SENT_SPLIT_RE = re.compile(r"[。！？!?…]+")
_CJK_BIGRAM_RE = re.compile(f"([{_CJK}])([{_CJK}])")
_PARA_SPLIT_RE = re.compile(r"\n\s*\n")
_DIALOG_RE = re.compile(r"[「『“\"].+?[」』”\"]")
_PUNCT_RE = re.compile(r"[，。！？；：、—…「」『』“”]")

# 常用中文虚词（不计入风格实词）
_STOP_BIGRAMS = {"的了", "了的", "一下", "一个", "什么", "这个", "那个"}


@dataclass
class StyleFingerprint:
    """可量化的作者声线指纹。"""

    sample_chars: int = 0
    sentence_len_avg: float = 0.0
    short_sentence_ratio: float = 0.0   # ≤12 字句占比
    paragraph_len_avg: float = 0.0      # 每段句数
    dialogue_ratio: float = 0.0         # 对话行占比
    dash_per_1k: float = 0.0            # 破折号密度（每千字）
    top_words: list[str] = field(default_factory=list)
    punctuation_mix: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def extract_fingerprint(samples: list[str]) -> StyleFingerprint:
    """从若干文本样本提取指纹（样本可为多章，自动拼接统计）。"""
    text = "\n\n".join(s for s in (samples or []) if s and s.strip())
    if not text.strip():
        return StyleFingerprint()

    paragraphs = [p for p in _PARA_SPLIT_RE.split(text) if p.strip()]
    sentences = [s for s in _SENT_SPLIT_RE.split(text) if s.strip()]

    sent_lens = [len(s) for s in sentences] or [0]
    avg_sent = sum(sent_lens) / len(sent_lens)
    short_ratio = sum(1 for n in sent_lens if n <= 12) / len(sent_lens)

    para_sent_counts = [
        max(1, len([s for s in _SENT_SPLIT_RE.split(p) if s.strip()]))
        for p in paragraphs
    ] or [0]
    avg_para = sum(para_sent_counts) / len(para_sent_counts)

    dialogue_lines = len(_DIALOG_RE.findall(text))
    total_lines = max(1, len([ln for ln in text.splitlines() if ln.strip()]))
    dash_density = text.count("——") / max(1, len(text)) * 1000

    bigram_counter: dict[str, int] = {}
    for a, b in _CJK_BIGRAM_RE.findall(text):
        gram = f"{a}{b}"
        if gram in _STOP_BIGRAMS:
            continue
        bigram_counter[gram] = bigram_counter.get(gram, 0) + 1
    top_words = [
        w
        for w, _c in sorted(
            bigram_counter.items(), key=lambda kv: (-kv[1], kv[0])
        )[:8]
    ]

    punct_mix: dict[str, int] = {}
    for ch in _PUNCT_RE.findall(text):
        punct_mix[ch] = punct_mix.get(ch, 0) + 1

    return StyleFingerprint(
        sample_chars=len(text),
        sentence_len_avg=round(avg_sent, 2),
        short_sentence_ratio=round(short_ratio, 3),
        paragraph_len_avg=round(avg_para, 2),
        dialogue_ratio=round(dialogue_lines / total_lines, 3),
        dash_per_1k=round(dash_density, 2),
        top_words=top_words,
        punctuation_mix=punct_mix,
    )


def fingerprint_to_prompt(fp: StyleFingerprint) -> str:
    """把指纹渲染为生成 prompt 中的风格约束段（供 LLM drafter 消费）。"""
    if fp.sample_chars <= 0:
        return ""
    parts = [
        f"模仿以下作者声线（样本 {fp.sample_chars} 字）：",
        f"- 句子均长约 {fp.sentence_len_avg:.0f} 字，短句（≤12 字）占 {fp.short_sentence_ratio:.0%}",
        f"- 每段约 {fp.paragraph_len_avg:.1f} 句",
    ]
    if fp.dialogue_ratio > 0:
        parts.append(f"- 对话行占比约 {fp.dialogue_ratio:.0%}")
    if fp.dash_per_1k < 1:
        parts.append("- 少用破折号")
    elif fp.dash_per_1k > 5:
        parts.append("- 破折号使用频繁，可保留该习惯")
    if fp.top_words:
        parts.append(f"- 作者常用词：{'、'.join(fp.top_words)}")
    parts.append("- 禁止 AI 腔（不由得/顿时/心中暗道/值得一提的是）")
    return "\n".join(parts)


def compare_fingerprints(
    a: StyleFingerprint, b: StyleFingerprint
) -> float:
    """两枚指纹的相似度（0–1，1 为完全一致），用于"越用越像你"验证。"""
    if a.sample_chars <= 0 or b.sample_chars <= 0:
        return 0.0
    pairs = [
        (a.sentence_len_avg, b.sentence_len_avg, 1.0),
        (a.short_sentence_ratio, b.short_sentence_ratio, 1.0),
        (a.paragraph_len_avg, b.paragraph_len_avg, 1.0),
        (a.dialogue_ratio, b.dialogue_ratio, 1.0),
        (a.dash_per_1k, b.dash_per_1k, 1.0),
    ]
    scores: list[float] = []
    for x, y, scale in pairs:
        denom = max(abs(x), abs(y), scale)
        scores.append(1.0 - min(1.0, abs(x - y) / denom))
    a_words, b_words = set(a.top_words), set(b.top_words)
    if a_words or b_words:
        jaccard = len(a_words & b_words) / max(1, len(a_words | b_words))
        scores.append(jaccard)
    return round(sum(scores) / len(scores), 3)
