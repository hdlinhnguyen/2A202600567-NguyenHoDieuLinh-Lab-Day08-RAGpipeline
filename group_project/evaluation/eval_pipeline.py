"""
RAG Evaluation Pipeline — DeepEval + heuristic fallback.

Yêu cầu README (Chấm Điểm — Bài Nhóm 12 điểm):
    1. Golden dataset ≥15 Q&A pairs
    2. 4 metrics: faithfulness, answer_relevance, context_recall, context_precision
    3. So sánh A/B ≥2 configs
    4. Báo cáo results.md + worst performers

Chạy:
    python group_project/evaluation/eval_pipeline.py
    python group_project/evaluation/eval_pipeline.py --mode deepeval   # cần API credits
    python group_project/evaluation/eval_pipeline.py --quick           # 5 cases, nhanh
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from src.task10_generation import (  # noqa: E402
    TOP_K,
    format_context,
    reorder_for_llm,
    _call_llm,
    SYSTEM_PROMPT,
)
from src.task5_semantic_search import semantic_search  # noqa: E402
from src.task9_retrieval_pipeline import retrieve  # noqa: E402

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

METRIC_NAMES = (
    "faithfulness",
    "answer_relevance",
    "context_recall",
    "context_precision",
)

VI_STOPWORDS = {
    "là", "la", "của", "cua", "và", "va", "có", "co", "không", "khong",
    "theo", "nào", "nao", "gì", "gi", "được", "duoc", "trong", "với", "voi",
    "một", "mot", "các", "cac", "những", "nhung", "cho", "từ", "tu", "đến", "den",
    "bị", "bi", "về", "ve", "khi", "này", "nay", "đó", "do", "thì", "thi",
}


@dataclass
class EvalCaseResult:
    id: str
    question: str
    category: str
    answer: str
    scores: dict[str, float]
    retrieval_source: str
    failure_stage: str = ""


@dataclass
class EvalRunResult:
    config_name: str
    cases: list[EvalCaseResult] = field(default_factory=list)

    @property
    def averages(self) -> dict[str, float]:
        if not self.cases:
            return {m: 0.0 for m in METRIC_NAMES}
        return {
            m: round(sum(c.scores[m] for c in self.cases) / len(self.cases), 3)
            for m in METRIC_NAMES
        }

    @property
    def average_all(self) -> float:
        avgs = self.averages
        return round(sum(avgs.values()) / len(avgs), 3)


def load_golden_dataset() -> list[dict]:
    with GOLDEN_DATASET_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if len(data) < 15:
        raise ValueError(f"Golden dataset cần ≥15 cases, hiện có {len(data)}")
    return data


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Zà-ỹÀ-Ỹ0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in VI_STOPWORDS}


def _keywords_from_item(item: dict) -> set[str]:
    parts = [item.get("expected_context", ""), item.get("expected_answer", "")]
    return _tokenize(" ".join(parts))


class EvalRAGPipeline:
    """RAG pipeline với config retrieval khác nhau cho A/B test."""

    def __init__(self, config_name: str):
        self.config_name = config_name

    def _retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        if self.config_name == "hybrid_rerank":
            chunks = retrieve(query, top_k=top_k, use_reranking=True)
        elif self.config_name == "dense_only":
            chunks = semantic_search(query, top_k=top_k)
            for c in chunks:
                c["source"] = "dense"
        else:
            raise ValueError(f"Unknown config: {self.config_name}")

        return chunks

    def generate_with_citation(self, query: str, top_k: int = TOP_K) -> dict:
        chunks = self._retrieve(query, top_k=top_k)
        reordered = reorder_for_llm(chunks)
        context = format_context(reordered)
        user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
        answer = _call_llm(SYSTEM_PROMPT, user_message)
        return {
            "answer": answer,
            "sources": chunks,
            "retrieval_source": chunks[0].get("source", "none") if chunks else "none",
        }


# =============================================================================
# Heuristic metrics (fallback — không cần LLM judge)
# =============================================================================

def score_faithfulness(answer: str, contexts: list[str]) -> float:
    """Proxy: tỷ lệ từ khóa trong answer xuất hiện trong context."""
    answer_tokens = _tokenize(answer)
    if not answer_tokens:
        return 0.0
    haystack = " ".join(contexts).lower()
    hits = sum(1 for t in answer_tokens if t in haystack)
    return round(hits / len(answer_tokens), 3)


def score_answer_relevance(answer: str, expected: str, question: str) -> float:
    """Proxy: overlap answer với expected_answer + question."""
    expected_tokens = _tokenize(expected) | _tokenize(question)
    answer_tokens = _tokenize(answer)
    if not expected_tokens or not answer_tokens:
        return 0.0
    hits = len(answer_tokens & expected_tokens)
    return round(min(1.0, hits / max(3, len(expected_tokens) * 0.4)), 3)


def score_context_recall(contexts: list[str], item: dict) -> float:
    """Proxy: expected_context/answer keywords có trong chunks retrieve không."""
    keywords = _keywords_from_item(item)
    if not keywords:
        return 0.0
    haystack = " ".join(contexts).lower()
    hits = sum(1 for k in keywords if k in haystack)
    return round(hits / len(keywords), 3)


def score_context_precision(contexts: list[str], question: str) -> float:
    """Proxy: % chunks chứa từ khóa từ câu hỏi."""
    q_tokens = _tokenize(question)
    if not contexts or not q_tokens:
        return 0.0
    useful = 0
    for ctx in contexts:
        ctx_tokens = _tokenize(ctx)
        if len(ctx_tokens & q_tokens) >= 2:
            useful += 1
    return round(useful / len(contexts), 3)


def _infer_failure_stage(scores: dict[str, float], contexts: list[str]) -> str:
    if not contexts:
        return "retrieval"
    if scores["context_recall"] < 0.4:
        return "retrieval"
    if scores["context_precision"] < 0.4:
        return "retrieval"
    if scores["faithfulness"] < 0.5:
        return "generation"
    if scores["answer_relevance"] < 0.5:
        return "generation"
    return "ok"


def evaluate_heuristic(
    pipeline: EvalRAGPipeline,
    golden_dataset: list[dict],
    *,
    verbose: bool = True,
) -> EvalRunResult:
    run = EvalRunResult(config_name=pipeline.config_name)

    for i, item in enumerate(golden_dataset, 1):
        if verbose:
            print(f"  [{pipeline.config_name}] {i}/{len(golden_dataset)}: {item['id']}")

        result = pipeline.generate_with_citation(item["question"])
        contexts = [c.get("content", "") for c in result["sources"]]

        scores = {
            "faithfulness": score_faithfulness(result["answer"], contexts),
            "answer_relevance": score_answer_relevance(
                result["answer"], item["expected_answer"], item["question"]
            ),
            "context_recall": score_context_recall(contexts, item),
            "context_precision": score_context_precision(contexts, item["question"]),
        }

        run.cases.append(EvalCaseResult(
            id=item["id"],
            question=item["question"],
            category=item.get("category", "unknown"),
            answer=result["answer"][:300],
            scores=scores,
            retrieval_source=result["retrieval_source"],
            failure_stage=_infer_failure_stage(scores, contexts),
        ))

    return run


# =============================================================================
# DeepEval (khi có đủ API credits)
# =============================================================================

def evaluate_with_deepeval(
    pipeline: EvalRAGPipeline,
    golden_dataset: list[dict],
) -> EvalRunResult:
    from deepeval import evaluate as deepeval_run
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        FaithfulnessMetric,
    )
    from deepeval.test_case import LLMTestCase

    test_cases: list[LLMTestCase] = []
    meta: list[dict] = []

    print(f"  Generating answers for {len(golden_dataset)} cases...")
    for item in golden_dataset:
        result = pipeline.generate_with_citation(item["question"])
        contexts = [c.get("content", "") for c in result["sources"]]
        test_cases.append(LLMTestCase(
            input=item["question"],
            actual_output=result["answer"],
            expected_output=item["expected_answer"],
            retrieval_context=contexts,
        ))
        meta.append({**item, "answer": result["answer"], "retrieval_source": result["retrieval_source"]})

    metrics = [
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
        ContextualRecallMetric(threshold=0.7),
        ContextualPrecisionMetric(threshold=0.7),
    ]

    print("  Running DeepEval metrics...")
    deepeval_run(test_cases, metrics)

    run = EvalRunResult(config_name=pipeline.config_name)
    metric_map = {
        "Faithfulness": "faithfulness",
        "Answer Relevancy": "answer_relevance",
        "Contextual Recall": "context_recall",
        "Contextual Precision": "context_precision",
    }

    for item, tc in zip(meta, test_cases):
        scores: dict[str, float] = {}
        for metric in metrics:
            key = metric_map.get(metric.__class__.__name__.replace("Metric", ""), "")
            if not key:
                name = metric.__name__ if hasattr(metric, "__name__") else type(metric).__name__
                for mk, mv in metric_map.items():
                    if mk.lower().replace(" ", "_") in name.lower():
                        key = mv
                        break
            score = getattr(metric, "score", None)
            if score is None and hasattr(metric, "success"):
                score = 1.0 if metric.success else 0.0
            if key:
                scores[key] = round(float(score or 0), 3)

        for m in METRIC_NAMES:
            scores.setdefault(m, 0.0)

        contexts = tc.retrieval_context or []
        run.cases.append(EvalCaseResult(
            id=item["id"],
            question=item["question"],
            category=item.get("category", "unknown"),
            answer=item["answer"][:300],
            scores=scores,
            retrieval_source=item["retrieval_source"],
            failure_stage=_infer_failure_stage(scores, contexts),
        ))

    return run


def _deepeval_available() -> bool:
    """Chỉ bật DeepEval LLM-judge khi explicitly yêu cầu (cần API credits)."""
    if os.getenv("DEEPEVAL_FORCE", "").lower() not in ("1", "true", "yes"):
        return False
    try:
        import deepeval  # noqa: F401
        return bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
    except ImportError:
        return False


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(
    golden_dataset: list[dict],
    *,
    mode: str = "heuristic",
    verbose: bool = True,
) -> dict[str, EvalRunResult]:
    configs = {
        "hybrid_rerank": "Hybrid search (dense + BM25) + cross-encoder reranking",
        "dense_only": "Dense-only semantic search, không reranking",
    }

    results: dict[str, EvalRunResult] = {}
    for config_name in configs:
        print(f"\n=== Config: {config_name} ===")
        pipeline = EvalRAGPipeline(config_name)
        if mode == "deepeval":
            results[config_name] = evaluate_with_deepeval(pipeline, golden_dataset)
        else:
            results[config_name] = evaluate_heuristic(pipeline, golden_dataset, verbose=verbose)

    return results


# =============================================================================
# Export results.md
# =============================================================================

def _worst_performers(run: EvalRunResult, n: int = 3) -> list[EvalCaseResult]:
    def avg_score(c: EvalCaseResult) -> float:
        return sum(c.scores.values()) / len(c.scores)

    return sorted(run.cases, key=avg_score)[:n]


def export_results(
    comparison: dict[str, EvalRunResult],
    *,
    mode: str,
    total_cases: int,
) -> None:
    config_a = comparison.get("hybrid_rerank")
    config_b = comparison.get("dense_only")
    if not config_a or not config_b:
        raise ValueError("Cần kết quả cả 2 configs")

    avgs_a = config_a.averages
    avgs_b = config_b.averages

    lines = [
        "# RAG Evaluation Results",
        "",
        f"> **Ngày chạy:** tự động generate bởi `eval_pipeline.py`",
        f"> **Framework:** {'DeepEval' if mode == 'deepeval' else 'DeepEval-compatible heuristic (local)'}",
        f"> **Golden dataset:** {total_cases} cặp Q&A",
        "",
        "---",
        "",
        "## Overall Scores",
        "",
        "| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |",
        "|--------|---------------------------|----------------------|---|",
    ]

    for metric in METRIC_NAMES:
        label = metric.replace("_", " ").title()
        a, b = avgs_a[metric], avgs_b[metric]
        delta = round(a - b, 3)
        sign = "+" if delta > 0 else ""
        lines.append(f"| {label} | {a:.3f} | {b:.3f} | {sign}{delta:.3f} |")

    lines += [
        f"| **Average** | **{config_a.average_all:.3f}** | **{config_b.average_all:.3f}** | "
        f"**{config_a.average_all - config_b.average_all:+.3f}** |",
        "",
        "---",
        "",
        "## A/B Comparison Analysis",
        "",
        "**Config A — hybrid_rerank:**",
        "> Dense + BM25 (RRF merge) + cross-encoder reranking + PageIndex fallback.",
        "",
        "**Config B — dense_only:**",
        "> Chỉ semantic search (all-MiniLM-L6-v2), không BM25, không reranking.",
        "",
        "**Kết luận:**",
    ]

    winner = "Config A (hybrid + rerank)" if config_a.average_all >= config_b.average_all else "Config B (dense-only)"
    diff = abs(config_a.average_all - config_b.average_all)
    recall_delta = avgs_a["context_recall"] - avgs_b["context_recall"]
    lines.append(
        f"> **{winner}** tốt hơn với average score chênh {diff:.3f}. "
        f"Context Recall: hybrid {avgs_a['context_recall']:.3f} vs dense {avgs_b['context_recall']:.3f} "
        f"(Δ {recall_delta:+.3f}). "
        "Hybrid (BM25 + rerank) thường tốt hơn cho exact keyword (Điều X, tên nghệ sĩ); "
        "dense-only đôi khi ổn với câu hỏi ngữ nghĩa rộng."
    )

    lines += ["", "---", "", "## Worst Performers (Bottom 3) — Config A", ""]
    lines += [
        "| # | ID | Question | Faith. | Relev. | Recall | Prec. | Stage | Root Cause |",
        "|---|-----|----------|--------|--------|--------|-------|-------|------------|",
    ]

    for i, case in enumerate(_worst_performers(config_a), 1):
        s = case.scores
        cause = _root_cause(case)
        q = case.question[:50] + ("..." if len(case.question) > 50 else "")
        lines.append(
            f"| {i} | {case.id} | {q} | {s['faithfulness']:.2f} | "
            f"{s['answer_relevance']:.2f} | {s['context_recall']:.2f} | "
            f"{s['context_precision']:.2f} | {case.failure_stage} | {cause} |"
        )

    lines += ["", "---", "", "## Recommendations", ""]

    recommendations = _build_recommendations(config_a, config_b)
    for i, rec in enumerate(recommendations, 1):
        lines += [
            f"### Cải tiến {i}",
            f"**Action:** {rec['action']}",
            f"**Expected impact:** {rec['impact']}",
            "",
        ]

    if mode == "heuristic":
        lines += [
            "---",
            "",
            "## Lưu ý",
            "",
            "Kết quả trên dùng **heuristic metrics** (keyword overlap) vì DeepEval LLM-judge "
            "cần API credits. Chạy lại với `--mode deepeval` khi có đủ OpenRouter credits "
            "để có điểm chính xác hơn theo framework DeepEval.",
            "",
        ]

    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✓ Đã ghi kết quả → {RESULTS_PATH}")


def _root_cause(case: EvalCaseResult) -> str:
    s = case.scores
    if s["context_recall"] < 0.4:
        if case.category == "news":
            return "Retriever miss bài báo / chunk rác crawl"
        return "Chunk pháp luật không chứa điều khoản đúng"
    if s["answer_relevance"] < 0.5:
        return "LLM trả lời lệch hoặc từ chối không cần thiết"
    if s["faithfulness"] < 0.5:
        return "Answer không bám context (hallucination)"
    return "Điểm tổng thể thấp — cần review thủ công"


def _build_recommendations(
    config_a: EvalRunResult,
    config_b: EvalRunResult,
) -> list[dict[str, str]]:
    recs = []

    recall_a = config_a.averages["context_recall"]
    recall_b = config_b.averages["context_recall"]
    recall_delta = recall_a - recall_b
    if recall_delta >= 0:
        recs.append({
            "action": "Giữ hybrid retrieval (dense + BM25 + rerank) làm mặc định.",
            "impact": f"Context Recall {'tăng' if recall_delta > 0 else 'tương đương'} ({recall_delta:+.2f}) so với dense-only.",
        })
    else:
        recs.append({
            "action": "Xem xét tăng trọng số BM25 hoặc full-source coverage cho hybrid config.",
            "impact": f"Hybrid đang thua dense-only về recall ({recall_delta:.2f}) — cần tune RRF/rerank.",
        })

    news_cases = [c for c in config_a.cases if c.category == "news"]
    low_news = [c for c in news_cases if c.scores["context_recall"] < 0.5]
    if low_news:
        recs.append({
            "action": "Lọc chunk rác crawl (404, sidebar) và boost news case keywords khi retrieve.",
            "impact": f"Cải thiện {len(low_news)} câu hỏi tin tức có recall thấp.",
        })

    low_rel = [c for c in config_a.cases if c.scores["answer_relevance"] < 0.5]
    if low_rel:
        recs.append({
            "action": "Tinh chỉnh system prompt — trả lời tự nhiên, liệt kê vụ án cụ thể từ bài báo.",
            "impact": f"Tăng Answer Relevance cho {len(low_rel)} worst cases.",
        })

    if len(recs) < 3:
        recs.append({
            "action": "Re-index sau khi làm sạch markdown (bỏ nav/footer từ crawl).",
            "impact": "Giảm noise, tăng Context Precision toàn pipeline.",
        })

    return recs[:3]


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="RAG Evaluation Pipeline")
    parser.add_argument(
        "--mode",
        choices=["heuristic", "deepeval", "auto"],
        default="heuristic",
        help="heuristic=local metrics (mặc định), deepeval=LLM judge (cần DEEPEVAL_FORCE=1 + credits)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Chỉ chạy 5 cases đầu (smoke test)",
    )
    args = parser.parse_args()

    golden = load_golden_dataset()
    if args.quick:
        golden = golden[:5]
        print(f"⚡ Quick mode: {len(golden)} cases")

    mode = args.mode
    if mode == "auto":
        mode = "deepeval" if _deepeval_available() else "heuristic"
        print(f"Mode: {mode}")

    print(f"Loaded {len(golden)} test cases from golden_dataset.json")
    comparison = compare_configs(golden, mode=mode)
    export_results(comparison, mode=mode, total_cases=len(golden))

    for name, run in comparison.items():
        print(f"\n{name}: average = {run.average_all}")
        for m, v in run.averages.items():
            print(f"  {m}: {v}")


if __name__ == "__main__":
    main()
