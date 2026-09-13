"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
Đề tài: Trợ lý Quản lý Thư viện & Tài liệu
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def _extract_id(self, prompt: str, prefix: str) -> str:
        """Trích xuất ID từ prompt, loại bỏ dấu câu thừa cuối token"""
        import re
        for token in prompt.split():
            cleaned = re.sub(r'[,.\;:!?\'"]+$', '', token)
            if cleaned.upper().startswith(prefix):
                return cleaned.upper()
        return None

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Mô phỏng nhận diện intent cho đề tài Thư viện
        
        # Ưu tiên 0: Multi-step — nếu câu hỏi vừa có "kiểm tra/tra cứu" VÀ "gia hạn/nếu"
        # thì gọi book_query TRƯỚC (bước 1 của multi-step ReAct)
        has_lookup = any(kw in prompt_lower for kw in ["kiểm tra", "tra cứu", "tình trạng", "xem"])
        has_extend = "gia hạn" in prompt_lower
        has_condition = any(kw in prompt_lower for kw in ["nếu", "rồi", "sau đó", "thì hãy"])
        
        # Phát hiện bước 2 của multi-step: context đã chứa kết quả tra cứu từ bước trước
        is_step2 = "kết quả tra cứu bước trước" in prompt_lower or "bước tiếp theo" in prompt_lower
        
        if is_step2 and has_extend:
            # Bước 2: Đã có Observation từ book_query, giờ gọi extend_book_loan
            book_id = self._extract_id(prompt, "BK-") or "BK-AI-01"
            reader_id = self._extract_id(prompt, "DG") or "DG001"
            import re
            days_match = re.search(r'(\d+)\s*ngày', prompt_lower)
            extend_days = int(days_match.group(1)) if days_match else 7
            return {
                "type": "tool_call",
                "tool_name": "extend_book_loan",
                "arguments": {"book_id": book_id, "reader_id": reader_id, "extend_days": extend_days},
                "thought": f"Bước 2 multi-step: Kết quả tra cứu cho thấy sách đang BORROWED bởi {reader_id}. Tiến hành gia hạn sách {book_id}."
            }
        
        if has_lookup and has_extend and has_condition:
            book_id = self._extract_id(prompt, "BK-") or "BK-AI-01"
            return {
                "type": "tool_call",
                "tool_name": "book_query",
                "arguments": {"book_id": book_id},
                "thought": f"Câu hỏi yêu cầu multi-step: kiểm tra sách trước rồi mới gia hạn. Bước 1: Tra cứu thông tin sách {book_id}."
            }
        
        # Ưu tiên 1: Nhận diện yêu cầu gia hạn sách (đơn bước)
        if has_extend:
            book_id = self._extract_id(prompt, "BK-") or "BK-AI-01"
            reader_id = self._extract_id(prompt, "DG") or "DG001"
            # Trích xuất số ngày gia hạn
            extend_days = 7
            import re
            days_match = re.search(r'(\d+)\s*ngày', prompt_lower)
            if days_match:
                extend_days = int(days_match.group(1))
            
            return {
                "type": "tool_call",
                "tool_name": "extend_book_loan",
                "arguments": {"book_id": book_id, "reader_id": reader_id, "extend_days": extend_days},
                "thought": f"Người dùng yêu cầu gia hạn sách {book_id} cho độc giả {reader_id}. Tôi sẽ gọi tool extend_book_loan."
            }
        
        # Ưu tiên 2: Nhận diện yêu cầu tra cứu sách (có mã sách cụ thể)
        elif any(kw in prompt_lower for kw in ["tra cứu", "tìm", "kiểm tra", "thông tin sách", "tình trạng", "vị trí"]):
            book_id = self._extract_id(prompt, "BK-") or "BK-AI-01"
            return {
                "type": "tool_call",
                "tool_name": "book_query",
                "arguments": {"book_id": book_id},
                "thought": f"Người dùng muốn tra cứu thông tin sách {book_id}. Tôi sẽ gọi tool book_query."
            }
        
        # Ưu tiên 3: Câu hỏi chung -> trả lời trực tiếp
        else:
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Thư viện Đại học VinUni mở cửa từ 7:30 đến 21:00, Thứ Hai đến Thứ Bảy. Mỗi sinh viên được mượn tối đa 5 cuốn sách, thời hạn mượn 14 ngày. Có thể gia hạn tối đa 2 lần, mỗi lần 7 ngày. Sách trả muộn bị phạt 2.000 VNĐ/ngày/cuốn.",
                "thought": "Câu hỏi chung về nội quy thư viện, trả lời trực tiếp không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-3.6-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
