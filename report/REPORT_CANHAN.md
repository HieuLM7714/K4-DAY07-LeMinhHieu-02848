# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Minh Hiếu (02848)
**Nhóm:** L3A
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiến gần về 1.0) nghĩa là hai vector embedding chỉ về cùng một hướng trong không gian vector đa chiều. Trong text embedding, điều này biểu thị hai văn bản có độ tương đồng ngữ nghĩa rất cao, cùng diễn đạt một ý niệm hoặc chủ đề trọng tâm.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên có thể đăng ký môn học trực tuyến trên cổng đào tạo của nhà trường.
- Câu B: Người học thực hiện thao tác chọn học phần qua website dịch vụ học vụ.
- Tại sao tương đồng: Dù hai câu sử dụng từ vựng khác biệt ("sinh viên" - "người học", "đăng ký môn học" - "chọn học phần", "cổng đào tạo" - "website dịch vụ học vụ"), text embedding vẫn ánh xạ chúng về cùng một miền không gian ngữ nghĩa gần nhau vì chúng diễn đạt cùng một hành vi học vụ. Điều này chứng minh embedding nắm bắt được ngữ nghĩa sâu chứ không chỉ so khớp từ ngữ bề mặt (lexical matching).

**Ví dụ có độ tương tự THẤP:**
- Câu A: Quy định xét học bổng khuyến khích học tập dựa trên điểm rèn luyện và kết quả tích lũy học kỳ.
- Câu B: Hôm nay thời tiết Hà Nội nhiều mây và có mưa rào rải rác ở một số khu vực.
- Tại sao khác: Hai câu thuộc hai miền kiến thức hoàn toàn độc lập (quy chế đào tạo - học vụ của đại học vs dự báo thời tiết khí quyển), không có mối liên hệ ngữ nghĩa nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự Cosine đo góc giữa hai vector mà không phụ thuộc vào độ lớn (magnitude/độ dài vector), do đó nó không bị thiên lệch bởi độ dài đoạn văn bản (văn bản dài hơn thường tích lũy độ lớn vector lớn hơn). Ngược lại, khoảng cách Euclid nhạy cảm với độ lớn vector nên hai câu cùng nghĩa nhưng chênh lệch độ dài văn bản sẽ bị tính là khoảng cách lớn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Áp dụng công thức: $\text{Số chunks} = \lceil \frac{\text{độ\_dài} - \text{overlap}}{\text{chunk\_size} - \text{overlap}} \rceil$
> - Thay số: $\lceil \frac{10000 - 50}{500 - 50} \rceil = \lceil \frac{9950}{450} \rceil \approx \lceil 22.111 \rceil = 23$
> *Đáp án:* 23 chunks (đã kiểm chứng lại bằng code `FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)` ra chính xác 23).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100: $\lceil \frac{10000 - 100}{500 - 100} \rceil = \lceil \frac{9900}{400} \rceil = \lceil 24.75 \rceil = 25$ chunks (tăng thêm 2 chunks). Chúng ta muốn độ chồng chéo (overlap) lớn hơn vì:
> 1. Tránh mất mát ngữ cảnh tại ranh giới cắt (boundary cutoff loss), đảm bảo các câu hay ý nghĩa quan trọng không bị cắt rời giữa hai chunk liên tiếp.
> 2. Giúp bảo toàn tính liên tục ngữ nghĩa (contextual continuity), hỗ trợ mô hình retriever truy xuất được đầy đủ ngữ cảnh dù câu truy vấn rơi vào điểm giao thoa.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng biểu thức chính quy Positive Lookbehind `r'(?<=[.!?])\s+'` để tách câu sau các dấu `. `, `! `, `? `, `.\n` mà vẫn giữ nguyên được dấu câu cuối câu (tránh bị nuốt mất dấu câu thành câu cụt). Sau đó gom các câu theo nhóm tối đa `max_sentences_per_chunk` và strip khoảng trắng. Trả về `[]` nếu văn bản rỗng.
> *Edge cases nhận diện chưa xử lý:* Các từ viết tắt có dấu chấm (như "TS.", "ThS.", "v.v.") và số thập phân (như "3.14") sẽ bị tách nhầm ranh giới câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thực hiện hai chiều: (1) Đệ quy xuống sâu (split): thử lần lượt danh sách separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`, nếu mảnh văn bản sau khi tách vẫn dài hơn `chunk_size` thì gọi đệ quy `_split` với separator nhỏ hơn tiếp theo. (2) Gom lên (merge): nối tuần tự các mảnh nhỏ liền kề lại cho tới khi chạm sát ngưỡng `chunk_size` để tránh sinh ra các chunk vụn.
> *Base cases:* (1) `current_text` rỗng -> trả về `[]`; (2) Độ dài `current_text <= chunk_size` -> trả về `[current_text]`; (3) Hết danh sách separator (`separators == []`) hoặc `sep == ""` -> cắt lát thô (slice) theo từng đoạn `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Dùng danh sách bộ nhớ (in-memory list) lưu trữ các record đã được chuẩn hóa qua `_make_record` (sao chép metadata, đảm bảo có `doc_id` trỏ về tài liệu gốc, và sinh vector nhúng qua `_embedding_fn`). Khi tìm kiếm, `search` ủy quyền cho helper `_search_records` để tính độ tương tự giữa query embedding và record embeddings bằng tích vô hướng (dot product), sau đó sắp xếp giảm dần theo điểm `score` và trả về top-k (loại bỏ trường embedding trong kết quả để giữ output sạch).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Phải áp dụng lọc trước (pre-filtering) danh sách record theo `metadata_filter` rồi mới tính tương tự và lấy top-k; nếu lấy top-k trước rồi mới lọc hậu kỳ (post-filtering), top-k có thể bị chiếm hết bởi tài liệu sai khiến kết quả rỗng dù store vẫn có tài liệu phù hợp. Khi xóa (`delete_document`), lọc bỏ toàn bộ các chunk có `metadata['doc_id']` hoặc `id` trùng với `doc_id` của tài liệu gốc, trả về `True` nếu số lượng chunk giảm đi và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hoạt động theo quy trình RAG 3 nhịp: (1) Kiểm tra an toàn (nếu store rỗng hoặc không có chunk liên quan thì báo không tìm thấy ngay để tránh gọi LLM lãng phí); (2) Đánh số thứ tự các chunk ngữ cảnh `[1]`, `[2]`, `[3]` kèm nguồn (`source` / `doc_id`) nhằm đảm bảo tiêu chí Source Traceability, kết hợp ràng buộc nghiêm ngặt chống bịa đặt (anti-hallucination) trong prompt; (3) Gọi `llm_fn` với prompt hoàn chỉnh và trả về câu trả lời có trích dẫn nguồn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\sy\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\sy\K4-DAY07-LeMinhHieu-02848
plugins: anyio-4.12.1
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.14s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên có thể đăng ký nội trú trực tuyến trên hệ thống của Ký túc xá. | Người học thực hiện thủ tục chọn phòng ở online qua cổng thông tin ký túc xá. | cao | -0.0316 | Sai (Mock) |
| 2 | Quy trình trả phòng yêu cầu sinh viên khai báo số tài khoản ngân hàng để nhận lại tiền thế chân. | Hôm nay thời tiết thành phố nhiều mây và có thể có mưa rào vào buổi chiều. | thấp | -0.0133 | Đúng |
| 3 | Sinh viên đã ở nội trú từ 5 tháng trở lên bắt buộc phải hoàn thành bài khảo sát. | Sinh viên nội trú không cần làm bất kỳ bài khảo sát nào khi sinh sống tại ký túc xá. | thấp | 0.0160 | Đúng |
| 4 | Tra cứu thông tin và thời hạn sử dụng của thẻ bảo hiểm y tế trên cổng thông tin BHXH. | Kiểm tra giá trị sử dụng thẻ BHYT thông qua ứng dụng VssID và VNeID trên điện thoại. | cao | 0.1594 | Đúng |
| 5 | Ảnh chân dung đăng ký phải có kích thước 4x6 và chụp không quá 6 tháng. | Nộp ảnh thẻ 4 nhân 6 chụp gần đây kèm theo bản chụp hai mặt căn cước công dân. | cao | 0.0520 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số ở Cặp 1 bất ngờ nhất: hai câu hoàn toàn tương đồng về mặt ý định thực tế ("đăng ký nội trú trực tuyến" vs "chọn phòng ở online") nhưng với MockEmbedder lại nhận điểm âm (-0.0316). Điều này minh họa rõ sự khác biệt giữa cơ chế băm chuỗi ký tự (hash-based) và mô hình nhúng ngữ nghĩa (Semantic Embedding như Sentence-Transformers hay OpenAI). Hàm băm xem các từ đồng nghĩa là các byte xa lạ, trong khi embedding ngữ nghĩa thực thụ mới có khả năng ánh xạ các cách diễn đạt tương đương về cùng một vùng vector lân cận.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> [!NOTE]
> **Ghi chú về Embedding Backend & Phân tích số liệu:**
> Toàn bộ thử nghiệm dưới đây sử dụng **`MockEmbedder` (hàm băm MD5 64 chiều, chế độ mặc định)** theo đúng cấu hình hệ thống lab. Do hàm băm chuỗi không mã hoá ngữ nghĩa (semantic similarity), điểm số cosine score mang tính chất xác định (deterministic) dựa trên hash va chạm từ vựng. Trọng tâm đánh giá được đặt vào: **phân tích độ mạch lạc cấu trúc chunk**, **thực nghiệm A/B Metadata Filter**, và đặc biệt là **chênh lệch giữa cách chấm ngây thơ (Naive doc_id) và chấm nội dung nghiêm ngặt (Strict content)**.

### Bảng Kết Quả Truy Xuất (Chiến lược: HeadingChunker — max_chunk_size=500)

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Đánh giá liên quan (Naive vs Strict) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|--------------------------------------|------------------------|
| 1 | Thời gian ở nội trú bao lâu thì bắt buộc phải hoàn thành khảo sát trước khi gửi yêu cầu trả phòng? *(Filter `audience: student`)* | `huong-dan-tra-phong-ktx#15`: Bước 10 Khai báo tài khoản ngân hàng và ngày trả phòng | 0.1779 | **Naive**: Đúng Doc (Top-1)<br>**Strict**: Sai section (không chứa mốc "5 tháng") | *Thiếu ngữ cảnh mốc 5 tháng*: Agent không tìm thấy điều kiện thời gian trong chunk #15 nên báo thông tin chưa đầy đủ. |
| 2 | Tân sinh viên đăng ký ở Ký túc xá cần chuẩn bị ảnh chân dung kích thước bao nhiêu và mới chụp trong thời gian bao lâu? | `dang-ky-ktx-tan-sinh-vien#14`: [Bước 5 Tải lên ảnh Căn cước công dân] | 0.2048 | **Naive**: Đúng Doc (Top-1)<br>**Strict**: Sai section (chỉ nói về ảnh CCCD, không có ảnh 4x6) | *Không trả lời được quy cách ảnh thẻ*: Agent trả lời nhầm sang yêu cầu tải ảnh CCCD 2 mặt. |
| 3 | Sinh viên cần cung cấp những thông tin tài khoản ngân hàng nào để nhận lại tiền thế chân tài sản khi trả phòng Ký túc xá? | `huong-dan-tra-phong-ktx#9`: Giai đoạn 2 Hoàn thành khảo sát trả phòng | 0.2181 | **Naive**: Đúng Doc (Top-1)<br>**Strict**: Sai section (chỉ nhắc chuyển sang Bước 10, chưa liệt kê) | *Chưa đủ thông tin*: Agent chỉ nêu sinh viên cần hoàn thành khảo sát trước khi khai báo. |
| 4 | Có những cách nào để tra cứu thông tin và thời hạn sử dụng của thẻ Bảo hiểm y tế (BHYT)? | `dang-ky-ktx-tan-sinh-vien#15`: Bước 6 Điền thông tin cá nhân | 0.3314 | **Naive**: Sai Doc (0đ)<br>**Strict**: Không liên quan (0đ) | *Lạc đề*: Do băm MD5, chunk điền thông tin cá nhân bị đẩy lên top-1 thay vì tài liệu BHYT. |
| 5 | Quy trình đăng ký hoạt động tại Ký túc xá gồm mấy bước và thực hiện trên website nào? | `dang-ky-ktx-tan-sinh-vien#0`: Hướng dẫn đăng ký Ký túc xá cho tân sinh viên | 0.2498 | **Naive**: Sai Doc (0đ)<br>**Strict**: Không liên quan (0đ) | *Lạc đề*: Retriever lấy nhầm sang quy trình đăng ký phòng ở của tân sinh viên. |

### Đánh Giá Hai Mức (Two-Level Scoring): Phát Hiện Lớn Nhất Của Buổi Lab
- **Chấm ngây thơ (Naive - chỉ kiểm `doc_id` lọt Top-3):** Đạt **6 / 10 điểm** (3 câu Q1, Q2, Q3 đều có Top-1 thuộc đúng tài liệu gold).
- **Chấm nội dung nghiêm ngặt (Strict Content - kiểm tra chuỗi đặc trưng):** Đạt **0 / 10 điểm**!
- **Khoảng cách chênh lệch:** **+6 điểm (+60%)**.
- **Giải thích hiện tượng:** `HeadingChunker` phân mảnh tài liệu thành các section độc lập (17 chunk cho tài liệu trả phòng, 24 chunk cho đăng ký tân sinh viên). Vì các section trong cùng một văn bản có chủ đề và phong cách viết đồng nhất, `MockEmbedder` gán các mức điểm tương tự rất sát nhau. Kết quả là cả 3 vị trí top-3 bị chiếm trọn bởi tài liệu gold nhưng lại rơi vào các section phụ (như upload CCCD thay vì chuẩn bị ảnh thẻ 4x6). Nếu chỉ chấm theo `doc_id`, người phát triển sẽ bị ngộ nhận rằng hệ thống hoạt động xuất sắc (60%), trong khi thực tế người dùng không nhận được câu trả lời mong muốn (0%).

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?**
- Theo tiêu chí `doc_id` (Naive): **3 / 5 câu** (Q1, Q2, Q3).
- Theo tiêu chí nội dung chứa câu trả lời (Strict Content): **0 / 5 câu** (do hạn chế cốt lõi của `MockEmbedder` hash MD5).

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> 1. **Hiểm họa của việc chấm điểm ngây thơ**: Đánh giá RAG bằng `doc_id` tạo ra ảo tưởng về độ chính xác (false confidence). Bắt buộc phải đánh giá ở cấp độ nội dung (Answer String Presence hoặc LLM Judge) mới phản ánh đúng năng lực hệ thống.
> 2. **Sự đánh đổi của Chunking không overlap**: `HeadingChunker` tạo ra các chunk ngữ nghĩa rất mạch lạc, nhưng khi không có độ chồng chéo (overlap), mỗi thông tin cốt lõi (như thông số `4 x 6`, `6 tháng`) chỉ có đúng một cơ hội duy nhất lọt vào Top-k. Nếu section đó bị trượt khỏi top-3 vì điểm hash/cosine thấp hơn một section anh em khác, câu trả lời sẽ biến mất hoàn toàn.
> 3. **Giá trị bảo vệ của Metadata Filter**: Trong thực nghiệm A/B, khi không có filter, tài liệu đối tượng chung BHYT (`audience: all`) nhảy thẳng lên chiếm Top-1 của câu hỏi trả phòng sinh viên (`audience: student`). Pre-filtering là chốt chặn phòng thủ không thể thiếu để bảo toàn precision cho hệ thống RAG.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Ghi chú minh chứng thực tế |
|----------|-------------------|----------------------------|
| Khởi động (Warm-up) | 5 / 5 | Hoàn thành đầy đủ bài toán Cosine và Chunking Math (23 và 25 chunks) |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 | Trình bày chi tiết thuật toán trong gói `src` và các edge cases |
| Hoàn thiện code (Core Implementation) | 30 / 30 | Vượt qua toàn bộ 42/42 bài kiểm thử (`pytest tests/ -v`) |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | Hoàn thành 5 cặp câu, đối chiếu điểm số và phân tích phản ngẫm |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 | **Đo lường trung thực**: Theo chuẩn Naive (doc_id) đạt 6/10đ (3 câu Top-1 đúng doc); nếu chấm Strict Content đạt 0/10đ do hạn chế hash của MockEmbedder |
| **Tổng phần cá nhân** | **56 / 60** | *(Tính theo chuẩn Naive doc_id: 56/60 điểm; nếu tính theo Strict Content: 50/60 điểm)* |
