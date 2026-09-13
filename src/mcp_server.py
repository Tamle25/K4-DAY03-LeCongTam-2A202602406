"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
Đề tài: Trợ lý Quản lý Thư viện & Tài liệu
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPAcademicServer:
    """
    Giả lập MCP Server tuân thủ chuẩn giao thức Model Context Protocol
    Phục vụ đề tài: Trợ lý Quản lý Thư viện & Tài liệu
    """
    def __init__(self, server_name: str = "vinuni-library-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0
        """
        # Bước 1: Gọi dispatch_tool_call để lấy chuỗi JSON kết quả từ Tool Router
        result_json_str = dispatch_tool_call(tool_name, arguments)

        # Bước 2: Chuyển đổi chuỗi JSON kết quả thành Python Dictionary
        try:
            content = json.loads(result_json_str)
        except json.JSONDecodeError:
            content = {"status": "PARSE_ERROR", "raw": result_json_str}

        # Bước 3: Đóng gói phản hồi theo chuẩn giao thức MCP JSON-RPC 2.0
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (vinuni-library-mcp-server)")
    print("==========================================================")
    
    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố qua MCP: {len(tools)}")
    
    # Liệt kê các tool đã đăng ký
    for tool in tools:
        props = tool.get("parameters", {}).get("properties", {})
        print(f"   🛠️ {tool['name']}: {tool['description'][:60]}... | Params: {list(props.keys())}")

    # Kiểm tra Tool Schema book_query
    bq_tool = next((t for t in tools if t.get("name") == "book_query"), None)
    if bq_tool and bq_tool.get("parameters", {}).get("properties"):
        print("✅ Tool 'book_query' đã có schema đầy đủ.")
    else:
        print("⏳ Tool 'book_query' chưa được định nghĩa properties.")

    # Kiểm tra Tool Schema extend_book_loan
    el_tool = next((t for t in tools if t.get("name") == "extend_book_loan"), None)
    if el_tool and el_tool.get("parameters", {}).get("properties"):
        print("✅ Tool 'extend_book_loan' đã có schema đầy đủ.")
    else:
        print("⏳ Tool 'extend_book_loan' chưa được định nghĩa properties.")

    # Test dispatch tool 'book_query'
    print("\n--- Test 1: Tra cứu sách BK-AI-01 ---")
    test_result = server.call_tool("book_query", {"book_id": "BK-AI-01"})
    if test_result and test_result.get("result"):
        print(f"✅ Test dispatch tool 'book_query' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False, indent=2)}")
    else:
        print("⏳ Hàm call_tool() đang trả về rỗng.")

    # Test dispatch tool 'extend_book_loan'
    print("\n--- Test 2: Gia hạn sách BK-AI-01 cho DG001 ---")
    test_result2 = server.call_tool("extend_book_loan", {"book_id": "BK-AI-01", "reader_id": "DG001", "extend_days": 7})
    if test_result2 and test_result2.get("result"):
        print(f"✅ Test dispatch tool 'extend_book_loan' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result2, ensure_ascii=False, indent=2)}")
    else:
        print("⏳ Hàm call_tool() đang trả về rỗng.")

    # Test edge case: sách không tồn tại
    print("\n--- Test 3: Tra cứu sách không tồn tại BK-UNKNOWN-999 ---")
    test_result3 = server.call_tool("book_query", {"book_id": "BK-UNKNOWN-999"})
    print(f"✅ Test NOT_FOUND:")
    print(f"   Phản hồi JSON-RPC: {json.dumps(test_result3, ensure_ascii=False, indent=2)}")
