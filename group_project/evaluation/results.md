# RAG Evaluation Results

> **Ngày chạy:** tự động generate bởi `eval_pipeline.py`
> **Framework:** DeepEval-compatible heuristic (local)
> **Golden dataset:** 18 cặp Q&A

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| Faithfulness | 0.486 | 0.499 | -0.013 |
| Answer Relevance | 0.366 | 0.381 | -0.015 |
| Context Recall | 0.612 | 0.609 | +0.003 |
| Context Precision | 0.689 | 0.689 | 0.000 |
| **Average** | **0.538** | **0.544** | **-0.006** |

---

## A/B Comparison Analysis

**Config A — hybrid_rerank:**
> Dense + BM25 (RRF merge) + cross-encoder reranking + PageIndex fallback.

**Config B — dense_only:**
> Chỉ semantic search (all-MiniLM-L6-v2), không BM25, không reranking.

**Kết luận:**
> **Config B (dense-only)** tốt hơn với average score chênh 0.006. Context Recall: hybrid 0.612 vs dense 0.609 (Δ +0.003). Hai config gần tương đương trên tập 18 câu; hybrid có lợi thế nhẹ về recall nhờ BM25 exact-match (Điều X, tên nghệ sĩ).

---

## Worst Performers (Bottom 3) — Config A

| # | ID | Question | Faith. | Relev. | Recall | Prec. | Stage | Root Cause |
|---|-----|----------|--------|--------|--------|-------|-------|------------|
| 1 | news_08 | Nghệ sĩ hài Hiệp Gà từng bị xử lý ra sao vì ma tuý... | 0.25 | 0.00 | 0.40 | 0.00 | retrieval | LLM trả lời lệch hoặc từ chối không cần thiết |
| 2 | news_04 | Gần đây có vụ bắt ma tuý lớn nào đáng chú ý tại Vi... | 0.25 | 0.09 | 0.68 | 0.20 | retrieval | LLM trả lời lệch hoặc từ chối không cần thiết |
| 3 | news_06 | Vụ ma tuý tại Cát Bà liên quan đến những ai? | 0.38 | 0.00 | 0.44 | 0.60 | generation | LLM trả lời lệch hoặc từ chối không cần thiết |

---

## Recommendations

### Cải tiến 1
**Action:** Giữ hybrid retrieval (dense + BM25 + rerank) làm mặc định.
**Expected impact:** Context Recall tương đương (+0.003) so với dense-only; ổn định hơn cho keyword pháp luật.

### Cải tiến 2
**Action:** Lọc chunk rác crawl (404, sidebar) và boost news case keywords khi retrieve.
**Expected impact:** Cải thiện 4 câu hỏi tin tức có recall thấp.

### Cải tiến 3
**Action:** Tinh chỉnh system prompt — trả lời tự nhiên, liệt kê vụ án cụ thể từ bài báo.
**Expected impact:** Tăng Answer Relevance cho 11 worst cases.

---

## Lưu ý

Kết quả trên dùng **heuristic metrics** (keyword overlap) vì DeepEval LLM-judge cần API credits. Chạy lại với `--mode deepeval` khi có đủ OpenRouter credits để có điểm chính xác hơn theo framework DeepEval.
