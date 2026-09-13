# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Lê Công Tâm  
> **Mã Sinh Viên / Mã Học viên:** 2A202602406  
> **Chủ đề Lựa chọn:** Trợ lý Quản lý Thư viện & Tài liệu (Gợi ý 1.2 — Lĩnh vực Giáo dục & Đào tạo)  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Bài toán yêu cầu suy luận đa bước rõ ràng: khi bạn đọc yêu cầu "kiểm tra sách rồi gia hạn nếu đang mượn", Agent phải tra cứu trạng thái sách trước (bước 1), phân tích kết quả (bước 2), rồi mới quyết định gọi tool gia hạn (bước 3). Không đạt 5/5 vì một số trường hợp chỉ cần 1 bước đơn lẻ (tra cứu đơn thuần). |
| **2. Tool Interaction** | 5 / 5 | Hệ thống bắt buộc phải kết nối MCP Server để truy vấn cơ sở dữ liệu sách (vị trí, trạng thái mượn/trả) và thực thi thao tác gia hạn tài liệu. Không có Tool thì Agent không thể cung cấp dữ liệu thời gian thực, chỉ có thể trả lời câu hỏi chung về nội quy. |
| **3. Dynamic Decision** | 4 / 5 | Bước tiếp theo phụ thuộc hoàn toàn vào Observation: nếu sách đang AVAILABLE thì không thể gia hạn; nếu sách BORROWED và đúng người mượn mới cho phép gia hạn; nếu NOT_FOUND thì Agent phải trả lời trung thực. Quyết định gọi tool nào được xác định động dựa trên kết quả trước đó. |
| **4. Long Horizon Goal** | 3 / 5 | Trong trường hợp multi-step (TC04), Agent phải giữ mục tiêu xuyên suốt qua 2–3 lượt xử lý (tra cứu → phân tích → gia hạn). Tuy nhiên, phần lớn tác vụ thư viện hoàn thành trong 1–2 bước nên không yêu cầu duy trì mục tiêu dài hạn phức tạp như các hệ thống planning. |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | *Tổng điểm 16/20 > 12/20: Bài toán Quản lý Thư viện & Tài liệu rất phù hợp triển khai Agentic System với ReAct Agent + MCP Server.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu thông tin cuốn sách có mã BK-AI-01 trong thư viện, cho tôi biết vị trí đặt sách và tình trạng hiện tại.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "book_query",
    "arguments": {
      "book_id": "BK-AI-01"
    },
    "observation": {
      "status": "SUCCESS",
      "book_id": "BK-AI-01",
      "data": {
        "title": "Trí Tuệ Nhân Tạo - Nền Tảng và Ứng Dụng",
        "author": "PGS.TS Nguyễn Thanh Tùng",
        "category": "Công nghệ Thông tin",
        "location": "Tầng 2 - Khu A - Kệ 03",
        "status": "BORROWED",
        "borrower_id": "DG001",
        "due_date": "20/09/2026"
      }
    },
    "latency_ms": 930.56
  },
  {
    "step": 2,
    "query": "Hãy tra cứu thông tin cuốn sách có mã BK-AI-01 trong thư viện, cho tôi biết vị trí đặt sách và tình trạng hiện tại.",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Thông tin sách BK-AI-01: 'Trí Tuệ Nhân Tạo - Nền Tảng và Ứng Dụng' của PGS.TS Nguyễn Thanh Tùng. Chuyên ngành: Công nghệ Thông tin. Vị trí: Tầng 2 - Khu A - Kệ 03. Trạng thái: Đang được mượn. Người mượn: DG001. Hạn trả: 20/09/2026.",
    "latency_ms": 10.0
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt (`book_query` & `extend_book_loan`).
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!

