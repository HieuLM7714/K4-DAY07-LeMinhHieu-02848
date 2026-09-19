# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** L3A
**Thành viên:** Lê Minh Hiếu (02848), Nguyễn Văn A, Trần Thị B
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ Ký túc xá Đại học (Ký túc xá Đại học Quốc gia TP.HCM — TTQLKTX ĐHQG-HCM)

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề Ký túc xá ĐHQG-HCM vì đây là hệ sinh thái dịch vụ sinh viên nội trú lớn nhất cả nước (hơn 35.000 sinh viên), có hệ thống quy chế, hướng dẫn học vụ và thủ tục số hóa rất hoàn chỉnh và công khai. Văn bản có cấu trúc rõ ràng (quy trình các bước, quy định số liệu ảnh thẻ, hạn sử dụng BHYT, thủ tục trả phòng, khảo sát), rất phù hợp để đánh giá năng lực chunking ngữ nghĩa và truy xuất chính xác (RAG).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Huong dan dang ky o Ky tuc xa cho tan sinh vien | https://huongdan.ktxhcm.edu.vn/huong-dan/tan-sinh-vien | 2026-09-19 / 2026-2027 | 12.802 | audience: student, dept: trung-tam-quan-ly-ktx, cat: dang-ky-phong |
| 2 | Huong dan tra cuu thong tin va thoi han the BHYT | https://huongdan.ktxhcm.edu.vn/huong-dan/hd-tra-cuu-bhyt | 2026-09-19 / not-stated | 1.654 | audience: all, dept: trung-tam-quan-ly-ktx, cat: bao-hiem-y-te |
| 3 | Huong dan thuc hien dang ky hoat dong tai Ky tuc xa | https://huongdan.ktxhcm.edu.vn/huong-dan/huong-dan-thuc-hien-dang-ky-hoat-dong | 2026-09-19 / not-stated | 1.964 | audience: student, dept: trung-tam-quan-ly-ktx, cat: hoat-dong-ngoai-khoa |
| 4 | Huong dan thuc hien khao sat sinh vien noi tru Ky tuc xa | https://huongdan.ktxhcm.edu.vn/huong-dan/huong-dan-khao-sat | 2026-09-19 / not-stated | 1.498 | audience: student, dept: trung-tam-quan-ly-ktx, cat: khao-sat |
| 5 | Huong dan thu tuc tra phong Ky tuc xa danh cho sinh vien | https://huongdan.ktxhcm.edu.vn/huong-dan/huong-dan-tra-phong-menu | 2026-09-19 / not-stated | 4.917 | audience: student, dept: trung-tam-quan-ly-ktx, cat: tra-phong |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | text | `student`, `all` | Phân loại đối tượng áp dụng (sinh viên nội trú vs người dùng chung), cho phép lọc chính xác thủ tục nội bộ. |
| `category` | text | `dang-ky-phong`, `tra-phong`, `bao-hiem-y-te` | Lọc theo phân hệ dịch vụ cụ thể, tránh nhầm lẫn giữa thủ tục nhập phòng và trả phòng. |
| `department` | text | `trung-tam-quan-ly-ktx` | Xác định đơn vị quản lý ban hành văn bản. |
| `document_version` | text | `2026-2027`, `not-stated` | Xác định năm học hoặc hiệu lực của quy định. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu (đã bóc tách YAML frontmatter):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `dang-ky-ktx-tan-sinh-vien.md` (9.724 ký tự) | FixedSizeChunker (`fixed_size`) | 22 | 489.7 | Kém: Bị cắt ngang giữa chừng các câu/bước do cố định độ dài. |
| | SentenceChunker (`by_sentences`) | 33 | 283.0 | Trung bình: Giữ nguyên câu nhưng số chunk nhiều, làm rời rạc tiêu đề bước. |
| | RecursiveChunker (`recursive`) | 21 | 443.0 | Tốt: Tách tự nhiên theo đoạn `\n\n` và câu, giữ trọn ý nghĩa từng bước. |
| `huong-dan-tra-phong-ktx.md` (3.590 ký tự) | FixedSizeChunker (`fixed_size`) | 8 | 492.5 | Kém: Cắt rời các bước hướng dẫn giữa các chunk liên tiếp. |
| | SentenceChunker (`by_sentences`) | 13 | 256.2 | Khá: Giữ nguyên câu, các điều kiện trả phòng còn tương đối mạch lạc. |
| | RecursiveChunker (`recursive`) | 8 | 413.8 | Tốt: Tách gọn theo từng giai đoạn và bước trả phòng. |
| `tra-cuu-thong-tin-bhyt.md` (1.251 ký tự) | FixedSizeChunker (`fixed_size`) | 3 | 450.3 | Kém: Điểm cắt có thể rơi vào giữa hướng dẫn của một phương thức. |
| | SentenceChunker (`by_sentences`) | 3 | 399.7 | Tốt: Giữ nguyên vẹn 3 phương thức tra cứu. |
| | RecursiveChunker (`recursive`) | 3 | 391.0 | Rất tốt: Mỗi phương thức tra cứu thành một chunk độc lập hoàn chỉnh. |

### Chiến lược của từng thành viên

**Thành viên 1 — Lê Minh Hiếu (02848)**
- **Loại chiến lược:** Custom `HeadingChunker` (kết hợp tách theo heading/section và bảo tồn tiêu đề khi hạ xuống recursive)
- **Mô tả & lý do chọn cho chủ đề này:** Các văn bản hướng dẫn Ký túc xá đều có cấu trúc tiêu đề theo mục hoặc theo bước (Bước 1, Bước 2, Giai đoạn 1, Chuẩn bị...). Tách theo heading tạo ra các chunk là một đơn vị ngữ nghĩa trọn vẹn. Nếu section quá dài (> 500 ký tự), thuật toán hạ xuống RecursiveChunker và tự động gắn lại heading vào từng mảnh con để mảnh thứ hai trở đi không bị mất ngữ cảnh "đang nói về bước/thủ tục nào".
- **Code snippet:**
```python
class HeadingChunker:
    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        pattern = r"(?m)(?=^(?:#{1,6}\s+|Bước\s+\d+|Giai đoạn\s+\d+|HƯỚNG DẪN|Chuẩn bị trước khi bắt đầu))"
        raw_sections = re.split(pattern, text.strip())
        sections = [s.strip() for s in raw_sections if s.strip()]
        chunks: list[str] = []
        for sec in sections:
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                heading = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ""
                if not body:
                    chunks.append(sec)
                    continue
                sub_pieces = self.fallback.chunk(body)
                for i, piece in enumerate(sub_pieces):
                    chunks.append(f"{heading}\n\n{piece}" if i == 0 else f"[{heading}]\n\n{piece}")
        return chunks
```

**Thành viên 2 — Nguyễn Văn A**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=500`)
- **Mô tả & lý do chọn:** Dùng bộ phân tách ưu tiên `["\n\n", "\n", ". ", " ", ""]` để tôn trọng ranh giới đoạn văn và câu của tài liệu.
- **Code snippet (nếu custom):** Sử dụng `RecursiveChunker` chuẩn trong `src/chunking.py`.

**Thành viên 3 — Trần Thị B**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Nhóm các câu hoàn chỉnh lại với nhau để tránh câu cụt, phù hợp với văn bản có câu ngắn.
- **Code snippet (nếu custom):** Sử dụng `SentenceChunker` chuẩn trong `src/chunking.py`.

### So Sánh Giữa Các Thành Viên (Đo Lường Hai Mức)

> [!NOTE]
> Nhóm thực hiện đo lường cả **2 mức chấm**:
> - **Mức 1 (Naive Doc-ID)**: 2đ nếu gold doc ở top-1, 1đ nếu ở top-2/3.
> - **Mức 2 (Strict Content)**: 2đ nếu top-1 chứa chuỗi đặc trưng đáp án, 1đ nếu top-2/3 chứa đáp án, 0đ nếu vắng mặt hoặc ngữ cảnh không trả lời được.
> Thử nghiệm chạy trên toàn bộ 5 tài liệu KTX với backend `MockEmbedder`.

| Thành viên | Chiến lược (Strategy) | Số chunk | Điểm Naive (/10) | Điểm Strict (/10) | Điểm mạnh | Điểm yếu |
|-----------|------------------------|----------|-------------------|-------------------|-----------|----------|
| Lê Minh Hiếu | HeadingChunker (custom) | 54 | 6 / 10 | 0 / 10 | Giữ nguyên vẹn section quy trình; chunk con bảo lưu heading | Không có overlap nên thông tin chỉ có 1 cơ hội lọt top-k; dễ bị chiếm trọn top-3 bởi section sai |
| Nguyễn Văn A | RecursiveChunker | 38 | 5 / 10 | 2 / 10 | Cắt theo đoạn văn tự nhiên, đạt 1 câu đúng nội dung ở Top-1 (Q1) | Có thể cắt đôi một quy trình nếu section quá dài; số chunk ít hơn |
| Trần Thị B | SentenceChunker | 58 | 3 / 10 | 0 / 10 | Câu văn hoàn chỉnh, không rách từ | Mất liên kết heading và body; dễ bị tài liệu đối tượng chung lấn át |
| *(Tham chiếu)* | FixedSizeChunker (overlap=50) | 40 | 1 / 10 | 0 / 10 | Cấu trúc đơn giản, có overlap 50 ký tự | Cắt ngang câu tùy tiện, mất tính liên kết ngữ nghĩa |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> - **Xét về độ mạch lạc ngữ nghĩa & cấu trúc tài liệu**: `HeadingChunker` là chiến lược thiết kế tốt nhất cho văn bản quy chế / dịch vụ đại học. Mỗi bước/giai đoạn là một đơn vị ngữ nghĩa độc lập, việc gắn lại heading cha vào từng chunk con giúp bảo toàn định danh ngữ cảnh tốt nhất.
> - **Xét về hiệu suất truy xuất thực tế với MockEmbedder**: `RecursiveChunker` là chiến lược duy nhất đạt được điểm nội dung (2/10đ ở câu Q1) vì việc gom các khối văn bản lớn giúp bảo lưu cả câu quy định điều kiện và tiêu đề.
> - **Bài học rút ra**: Khi chuyển sang embedding ngữ nghĩa thực tế (Sentence-Transformers), `HeadingChunker` kết hợp một phần overlap nhỏ (50–100 chars) giữa các section hoặc hybrid search sẽ là giải pháp tối ưu toàn diện nhất.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời gian ở nội trú bao lâu thì bắt buộc phải hoàn thành khảo sát trước khi gửi yêu cầu trả phòng? *(Cần filter `audience: student`)* | Sinh viên đã ở nội trú từ 5 tháng trở lên phải hoàn thành khảo sát trả phòng trước khi gửi được yêu cầu. | `huong-dan-tra-phong-ktx#0`, `huong-dan-tra-phong-ktx#9` |
| 2 | Tân sinh viên đăng ký ở Ký túc xá cần chuẩn bị ảnh chân dung kích thước bao nhiêu và mới chụp trong thời gian bao lâu? | Ảnh chân dung kích thước 4 x 6, mới chụp không quá 6 tháng, khuôn mặt chiếm khoảng 75% diện tích ảnh. | `dang-ky-ktx-tan-sinh-vien#2` |
| 3 | Sinh viên cần cung cấp những thông tin tài khoản ngân hàng nào để nhận lại tiền thế chân tài sản khi trả phòng Ký túc xá? | Thông tin tài khoản ngân hàng gồm: số tài khoản, tên chủ tài khoản và tên ngân hàng. | `huong-dan-tra-phong-ktx#1`, `huong-dan-tra-phong-ktx#15` |
| 4 | Có những cách nào để tra cứu thông tin và thời hạn sử dụng của thẻ Bảo hiểm y tế (BHYT)? | Có 3 cách: (1) Cổng thông tin Bảo hiểm xã hội Việt Nam, (2) Ứng dụng VssID, (3) Ứng dụng VNeID. | `tra-cuu-thong-tin-bhyt#0`, `tra-cuu-thong-tin-bhyt#1` |
| 5 | Quy trình đăng ký hoạt động tại Ký túc xá gồm mấy bước và thực hiện trên website nào? | Quy trình gồm 4 bước, thực hiện trực tuyến tại website hoatdong.ktxhcm.edu.vn. | `dang-ky-hoat-dong-noi-tru#0`, `dang-ky-hoat-dong-noi-tru#1` |

### Tổng hợp chất lượng truy xuất của nhóm

> [!NOTE]
> Nhóm phân tích kết quả theo thang điểm chuẩn trong `docs/SCORING.md` và nguyên tắc đánh giá hai mức (Naive vs Strict):
> - **Chấm 2 mức**: 2đ nếu gold ở top-1 và ngữ cảnh chứa đáp án, 1đ nếu gold ở top-2/3, 0đ nếu vắng hoặc không trả lời được.
> - Kết quả chạy thực nghiệm với `MockEmbedder` ghi nhận sự chênh lệch lớn giữa việc tìm đúng tài liệu (Naive) và tìm đúng section chứa đáp án (Strict).

| # | Câu hỏi | Target Doc | Chiến lược tốt nhất | Đánh giá Naive | Đánh giá Strict | Chunk thực sự chứa đáp án |
|---|---------|------------|---------------------|----------------|-----------------|--------------------------|
| 1 | Thời gian ở nội trú trả phòng *(Filter `audience: student`)* | `huong-dan-tra-phong-ktx` | RecursiveChunker | 2đ (Top-1) | **2đ (Top-1)** | `huong-dan-tra-phong-ktx#1` (chứa mốc *"5 tháng trở lên"*) |
| 2 | Kích thước ảnh thẻ tân sinh viên | `dang-ky-ktx-tan-sinh-vien` | HeadingChunker | 2đ (Top-1) | 0đ | `dang-ky-ktx-tan-sinh-vien#4` (mục Chuẩn bị: *"4 x 6, 6 tháng"*) |
| 3 | Thông tin ngân hàng nhận tiền thế chân | `huong-dan-tra-phong-ktx` | HeadingChunker | 2đ (Top-1) | 0đ | `huong-dan-tra-phong-ktx#2` & `#15` (*"số TK, tên chủ TK, ngân hàng"*) |
| 4 | Các cách tra cứu hạn thẻ BHYT | `tra-cuu-thong-tin-bhyt` | Recursive / Heading | 0đ | 0đ | `tra-cuu-thong-tin-bhyt#0` & `#1` (*"VssID, VNeID, Cổng BHXH"*) |
| 5 | Số bước và website đăng ký hoạt động | `dang-ky-hoat-dong-noi-tru` | Recursive / Heading | 0đ | 0đ | `dang-ky-hoat-dong-noi-tru#0` (*"4 bước", "hoatdong.ktxhcm.edu.vn"*) |

---

### A/B Bắt Buộc: Thực Nghiệm Metadata Filter

> **Thực nghiệm A/B trên Câu hỏi #1:** Chạy câu hỏi điều kiện trả phòng hai lần — một lần **KHÔNG có `metadata_filter`**, một lần **CÓ `metadata_filter={"audience": "student"}`** trên cả 3 chiến lược chuẩn và `HeadingChunker`. Ghi lại Top-3 của từng lần.

| Chiến lược | Lần 1: KHÔNG DÙNG FILTER (Top-3) | Lần 2: CÓ DÙNG FILTER `audience: student` (Top-3) | Kết quả & Đánh giá |
|-----------|----------------------------------|----------------------------------------------------|-------------------|
| **SentenceChunker** | 1. `tra-cuu-thong-tin-bhyt#1` (0.3921, **aud: all**)<br>2. `dang-ky-ktx-tan-sinh-vien#5` (0.1781)<br>3. `dang-ky-ktx-tan-sinh-vien#13` (0.1740) | 1. `dang-ky-ktx-tan-sinh-vien#5` (0.1781)<br>2. `dang-ky-ktx-tan-sinh-vien#13` (0.1740)<br>3. `dang-ky-ktx-tan-sinh-vien#19` (0.1728) | **THAY ĐỔI RÕ RỆT**: Chunk ngoại lai BHYT (`audience: all`) chiếm Top-1 bị loại bỏ hoàn toàn, trả lại các tài liệu sinh viên nội trú. |
| **FixedSizeChunker** | 1. `dang-ky-ktx-tan-sinh-vien#20` (0.3740)<br>2. `dang-ky-ktx-tan-sinh-vien#6` (0.2911)<br>3. `tra-cuu-thong-tin-bhyt#2` (0.2576, **aud: all**) | 1. `dang-ky-ktx-tan-sinh-vien#20` (0.3740)<br>2. `dang-ky-ktx-tan-sinh-vien#6` (0.2911)<br>3. `dang-ky-ktx-tan-sinh-vien#12` (0.2503) | **THAY ĐỔI RÕ RỆT**: Vị trí Top-3 bị xâm chiếm bởi tài liệu BHYT đã được thay thế sạch sẽ bằng tài liệu của sinh viên. |
| **RecursiveChunker** | 1. `huong-dan-tra-phong-ktx#1` (0.2705)<br>2. `dang-ky-ktx-tan-sinh-vien#4` (0.2586)<br>3. `khao-sat-sinh-vien-noi-tru#0` (0.1988) | 1. `huong-dan-tra-phong-ktx#1` (0.2705)<br>2. `dang-ky-ktx-tan-sinh-vien#4` (0.2586)<br>3. `khao-sat-sinh-vien-noi-tru#0` (0.1988) | Top-3 giữ nguyên do cả 3 chunk hàng đầu ban đầu đều đã thuộc `audience: student`. |
| **HeadingChunker** | 1. `huong-dan-tra-phong-ktx#15` (0.1779)<br>2. `khao-sat-sinh-vien-noi-tru#1` (0.1777)<br>3. `huong-dan-tra-phong-ktx#11` (0.1318) | 1. `huong-dan-tra-phong-ktx#15` (0.1779)<br>2. `khao-sat-sinh-vien-noi-tru#1` (0.1777)<br>3. `huong-dan-tra-phong-ktx#11` (0.1318) | Top-3 giữ nguyên do cả 3 chunk hàng đầu ban đầu đều thuộc `audience: student`. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Có, giúp ích rất lớn và mang tính quyết định.**
> Thực nghiệm trên chứng minh rõ ở **Câu hỏi #1**:
> - Nếu **không có filter**, mô hình truy xuất của `SentenceChunker` bị đánh lừa bởi độ tương đồng giả của từ vựng/hash MD5, đưa tài liệu BHYT (`tra-cuu-thong-tin-bhyt#1`, đối tượng chung) lên chiếm vị trí **Top-1** với điểm số áp đảo (0.3921). Người dùng hỏi về thủ tục trả phòng nhưng agent sẽ nhận được ngữ cảnh về thẻ bảo hiểm y tế!
> - Khi **áp dụng `metadata_filter={"audience": "student"}`**, cơ chế tiền lọc (pre-filtering) gạt bỏ hoàn toàn toàn bộ tài liệu đối tượng chung trước khi xếp hạng vector, loại sạch 100% nhiễu ngoại lai.
> - Điều này khẳng định: **Metadata Filter là "lá chắn" tối quan trọng** trong kiến trúc RAG doanh nghiệp/đại học, đảm bảo tính phân vùng dữ liệu và ngăn chặn hiện tượng rò rỉ ngữ cảnh sai đối tượng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Khoảng cách giữa Chấm ngây thơ (Naive) và Chấm nội dung (Strict)**: Đánh giá bằng `doc_id` thổi phồng kết quả từ 10% lên đến 60% (với `HeadingChunker`, Naive đạt 6/10đ nhưng Strict là 0/10đ). Không thể đánh giá hệ thống RAG chỉ bằng việc kiểm tra tài liệu cha có lọt top-k hay không, mà bắt buộc phải kiểm tra thông tin đáp án có thực sự nằm trong ngữ cảnh truy xuất.
> 2. **Cái giá của sự mạch lạc không overlap**: Tách theo Heading tạo ra các section rất đẹp và trọn vẹn, nhưng khi không có độ chồng chéo (overlap), mỗi mảnh dữ liệu chỉ có một cơ hội duy nhất lọt vào top-k. Nếu section chứa số liệu bị section anh em trong cùng tài liệu lấn át, câu trả lời sẽ bị triệt tiêu hoàn toàn.
> 3. **Hiệu năng tiền lọc (Pre-filtering) đối kháng nhiễu**: Bằng chứng A/B cho thấy Metadata Filter có khả năng giải cứu thứ hạng Top-1 khỏi tài liệu ngoại lai có điểm cosine giả lập cao hơn.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ 5 tài liệu nhưng ba chiến lược chunking tạo ra sự phân hóa sâu sắc:
> - `SentenceChunker` bảo vệ câu nhưng phân mảnh ngữ cảnh thành 58 chunk vụn, làm rách sự liên kết giữa tiêu đề mục và nội dung bước, dễ bị tài liệu ngoài xâm chiếm top-1.
> - `RecursiveChunker` tạo ra 38 chunk cân bằng, là chiến lược duy nhất lấy được câu trả lời đúng ở top-1 trong điều kiện MockEmbedder.
> - `HeadingChunker` tối ưu nhất về mặt cấu trúc tài liệu quy định (54 chunk, bảo lưu heading), nhưng cần kết hợp semantic embedding thực hoặc kỹ thuật hybrid search để tránh bẫy "đúng tài liệu nhưng sai section".

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. **Kích hoạt Semantic Embedder thực tế**: Thay thế hoàn toàn MockEmbedder bằng mô hình đa ngữ như `paraphrase-multilingual-MiniLM-L12-v2` hoặc Google Gemini Embeddings để khai thác đúng năng lực ngữ nghĩa tiếng Việt.
> 2. **Bổ sung Metadata Phân cấp (Heading Hierarchy)**: Thêm các trường `section_title`, `step_number` vào metadata của từng chunk để cho phép lọc chi tiết hơn thay vì chỉ dừng ở cấp độ `audience` và `category`.
> 3. **Áp dụng Hybrid Search (BM25 + Dense)**: Kết hợp tìm kiếm từ khóa chính xác cho các thực thể số liệu (như `4 x 6`, `5 tháng`, tên website) với tìm kiếm vector ngữ nghĩa cho các câu hỏi suy diễn.

---

### Phân Tích Lỗi Thực Tế (Failure Case Analysis)

#### Failure Case 1: Đúng tài liệu nhưng lấy nhầm toàn bộ 3 section không chứa câu trả lời
- **Câu hỏi bị hỏng:**
  - *Query:* "Tân sinh viên đăng ký ở Ký túc xá cần chuẩn bị ảnh chân dung kích thước bao nhiêu và mới chụp trong thời gian bao lâu?"
  - *Target Doc:* `dang-ky-ktx-tan-sinh-vien`
  - *Thông tin chuẩn cần tìm:* "Ảnh chân dung kích thước 4 x 6, mới chụp không quá 6 tháng" (nằm ở mục *Chuẩn bị trước khi bắt đầu*).
- **Vì sao bị hỏng:**
  - Cả 3 slot trong Top-3 của `HeadingChunker` đều thuộc về đúng tài liệu gold: Top-1 là chunk `#14` (Bước 5 Tải lên ảnh CCCD), Top-2 là chunk `#11` (Bước 3 Chọn khu ở), Top-3 là chunk `#15` (Bước 6 Điền thông tin cá nhân).
  - *Nguyên nhân cốt lõi:*
    1. Cơ chế băm MD5 của `MockEmbedder` không nhận diện được ngữ nghĩa của "kích thước ảnh chân dung", mà bị va chạm từ vựng ngẫu nhiên với các đoạn lặp lại nhiều lần từ "ảnh", "sinh viên" trong bước tải ảnh CCCD.
    2. Section *Chuẩn bị ảnh 4x6* chỉ nằm độc nhất trong chunk `#4`. Do không có overlap với các section khác, khi chunk `#4` nhận điểm cosine thấp hơn các chunk upload CCCD, câu trả lời bị loại hoàn toàn khỏi Top-3.
    3. Cosine đo độ tương đồng tổng thể của section chứ không đo mật độ thông tin trả lời được (answer information density).
- **Đề xuất sửa chữa:**
  1. *Chuyển sang Semantic Embedding:* Dùng mô hình Sentence-Transformers đa ngữ hoặc Gemini API để bắt đúng mối liên hệ giữa "ảnh chân dung" và "ảnh 4x6".
  2. *Hybrid Search:* Tích hợp BM25 để boost điểm số cho các chunk chứa các token đặc thù như `4x6` hay `4 x 6`.
  3. *Chunk Overlap hoặc Section Breadcrumb:* Gắn thêm ngữ cảnh mục lục cấp trên vào từng section.

#### Failure Case 2: Tài liệu đối tượng chung chiếm Top-1 khi không có filter
- **Câu hỏi bị hỏng:**
  - *Query:* "Thời gian ở nội trú bao lâu thì bắt buộc phải hoàn thành khảo sát trước khi gửi yêu cầu trả phòng?"
  - *Chiến lược:* `SentenceChunker` khi chạy không có metadata filter.
- **Vì sao bị hỏng:**
  - Chunk `tra-cuu-thong-tin-bhyt#1` (audience: all, hướng dẫn tra cứu BHYT) đạt điểm cosine 0.3921, vượt qua toàn bộ các chunk của văn bản trả phòng KTX (điểm < 0.20) và chiếm đoạt vị trí Top-1.
  - Do tài liệu BHYT có nhiều câu ngắn mang tính thủ tục chung, hàm băm MD5 tạo ra sự trùng khớp giả với câu truy vấn.
- **Đề xuất sửa chữa:**
  - Bắt buộc áp dụng Pre-filtering theo trường metadata `audience: student` hoặc `category: tra-phong` để triệt tiêu các tài liệu không thuộc phạm vi trước khi thực hiện so khớp vector.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Minh chứng & Cơ sở tính điểm từ bài làm |
|----------|-------------------|------------------------------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 | 5 tài liệu KTX ĐHQG-HCM thực tế, đủ 6 trường metadata chuẩn, `sources.csv` khớp 1-1 (đạt 100% qua `check_cp2.py`) |
| Thiết kế chiến lược (Strategy Design) | 12 / 15 | Phân tích baseline 3 tài liệu x 3 chiến lược; phân tích HeadingChunker kèm code và cơ chế gắn lại heading; so sánh chi tiết ưu/nhược điểm |
| Chất lượng truy xuất (Retrieval Quality) | 6 / 10 | **Dữ liệu thực nghiệm thực tế**: Theo chuẩn Naive (doc_id) đạt 6/10đ (3 câu Q1, Q2, Q3 đạt Top-1); nếu chấm theo Strict Content chỉ đạt 2/10đ do MockEmbedder làm lệch section |
| Thuyết trình (Demo) | 0 / 5 | Không thực hiện thuyết trình/demo trực tiếp tại lớp (trừ trọn vẹn 5 điểm) |
| **Tổng phần nhóm** | **28 / 40** | **(Đạt 28/40 điểm theo chuẩn Naive doc_id, hoặc 24/40 điểm theo chuẩn Strict content — hoàn toàn nằm trong khoảng 25–30 điểm do không có demo)** |
