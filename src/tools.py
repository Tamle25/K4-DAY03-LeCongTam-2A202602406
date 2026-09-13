"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Đề tài: Trợ lý Quản lý Thư viện & Tài liệu
"""

import json
from typing import Dict, Any
from datetime import datetime, timedelta

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu thông tin sách trong thư viện
    {
        "name": "book_query",
        "description": "Tra cứu thông tin sách trong thư viện bằng mã sách (book_id). Trả về tên sách, tác giả, chuyên ngành, vị trí kệ, trạng thái mượn/trả, người đang mượn và hạn trả.",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "Mã định danh sách cần tra cứu (ví dụ: 'BK-AI-01')"
                }
            },
            "required": ["book_id"]
        }
    },

    # Tool 2: Gia hạn mượn tài liệu cho bạn đọc
    {
        "name": "extend_book_loan",
        "description": "Gia hạn thời gian mượn sách cho bạn đọc. Kiểm tra điều kiện (sách phải đang được mượn bởi đúng bạn đọc) và cập nhật hạn trả mới.",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "Mã sách cần gia hạn (ví dụ: 'BK-AI-01')"
                },
                "reader_id": {
                    "type": "string",
                    "description": "Mã thẻ độc giả yêu cầu gia hạn (ví dụ: 'DG001')"
                },
                "extend_days": {
                    "type": "integer",
                    "description": "Số ngày muốn gia hạn thêm (mặc định 7 ngày)"
                }
            },
            "required": ["book_id", "reader_id"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU THƯ VIỆN (MOCK DATABASE — IN-MEMORY DICTIONARY)
# ==============================================================================

# Cơ sở dữ liệu sách
BOOKS_DB = {
    "BK-AI-01": {
        "title": "Trí Tuệ Nhân Tạo - Nền Tảng và Ứng Dụng",
        "author": "PGS.TS Nguyễn Thanh Tùng",
        "category": "Công nghệ Thông tin",
        "location": "Tầng 2 - Khu A - Kệ 03",
        "status": "BORROWED",
        "borrower_id": "DG001",
        "due_date": "20/09/2026"
    },
    "BK-DS-02": {
        "title": "Cấu Trúc Dữ Liệu và Giải Thuật",
        "author": "TS. Trần Minh Hoàng",
        "category": "Khoa học Máy tính",
        "location": "Tầng 2 - Khu A - Kệ 05",
        "status": "AVAILABLE",
        "borrower_id": None,
        "due_date": None
    },
    "BK-ML-03": {
        "title": "Machine Learning cơ bản",
        "author": "Vũ Hữu Tiệp",
        "category": "Công nghệ Thông tin",
        "location": "Tầng 3 - Khu B - Kệ 01",
        "status": "BORROWED",
        "borrower_id": "DG002",
        "due_date": "25/09/2026"
    },
    "BK-MATH-04": {
        "title": "Toán Cao Cấp cho Kỹ sư",
        "author": "GS.TSKH Nguyễn Đình Trí",
        "category": "Toán học",
        "location": "Tầng 1 - Khu C - Kệ 02",
        "status": "AVAILABLE",
        "borrower_id": None,
        "due_date": None
    }
}

# Cơ sở dữ liệu bạn đọc
READERS_DB = {
    "DG001": {
        "name": "Lê Công Tâm",
        "class": "AI-K4",
        "email": "tam.lc@vinuni.edu.vn",
        "borrowed_books": ["BK-AI-01"]
    },
    "DG002": {
        "name": "Nguyễn Thị Mai",
        "class": "CS-K4",
        "email": "mai.nt@vinuni.edu.vn",
        "borrowed_books": ["BK-ML-03"]
    },
    "DG003": {
        "name": "Trần Văn Hùng",
        "class": "AI-K4",
        "email": "hung.tv@vinuni.edu.vn",
        "borrowed_books": []
    }
}


# ==============================================================================
# 3. HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

def execute_book_query(book_id: str) -> str:
    """Thực thi tra cứu thông tin sách theo mã sách"""
    book = BOOKS_DB.get(book_id.strip().upper())
    if book:
        return json.dumps({
            "status": "SUCCESS",
            "book_id": book_id,
            "data": book
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sách có mã '{book_id}' trong hệ thống thư viện."
        }, ensure_ascii=False)


def execute_extend_book_loan(book_id: str, reader_id: str, extend_days: int = 7) -> str:
    """Thực thi gia hạn mượn sách cho bạn đọc"""
    book = BOOKS_DB.get(book_id.strip().upper())
    if not book:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sách có mã '{book_id}' trong hệ thống thư viện."
        }, ensure_ascii=False)

    reader = READERS_DB.get(reader_id.strip().upper())
    if not reader:
        return json.dumps({
            "status": "INVALID_READER",
            "message": f"Không tìm thấy độc giả có mã thẻ '{reader_id}'."
        }, ensure_ascii=False)

    if book["status"] != "BORROWED":
        return json.dumps({
            "status": "NOT_BORROWED",
            "message": f"Sách '{book['title']}' hiện đang trên kệ (AVAILABLE), không cần gia hạn."
        }, ensure_ascii=False)

    if book["borrower_id"] != reader_id.strip().upper():
        return json.dumps({
            "status": "WRONG_BORROWER",
            "message": f"Sách '{book['title']}' đang được mượn bởi độc giả khác, không phải '{reader_id}'."
        }, ensure_ascii=False)

    # Tính hạn trả mới
    try:
        current_due = datetime.strptime(book["due_date"], "%d/%m/%Y")
    except (ValueError, TypeError):
        current_due = datetime.now()

    new_due = current_due + timedelta(days=extend_days)
    new_due_str = new_due.strftime("%d/%m/%Y")

    # Cập nhật mock database
    book["due_date"] = new_due_str

    return json.dumps({
        "status": "SUCCESS",
        "extension_id": f"EXT-{book_id}-{reader_id}-{extend_days}",
        "book_id": book_id,
        "reader_id": reader_id,
        "reader_name": reader["name"],
        "book_title": book["title"],
        "previous_due_date": current_due.strftime("%d/%m/%Y"),
        "new_due_date": new_due_str,
        "extended_days": extend_days,
        "message": f"Gia hạn thành công! Sách '{book['title']}' cho độc giả {reader['name']} ({reader_id}). Hạn trả mới: {new_due_str} (thêm {extend_days} ngày)."
    }, ensure_ascii=False)


# ==============================================================================
# 4. ROUTER GỌI TOOL THỰC TẾ
# ==============================================================================

TOOL_ROUTER = {
    "book_query": execute_book_query,
    "extend_book_loan": execute_extend_book_loan
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
