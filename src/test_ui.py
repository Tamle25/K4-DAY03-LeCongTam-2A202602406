"""
🧪 TEST UI — Giao diện kiểm thử tối giản cho ReAct Agent
Sử dụng http.server (thư viện chuẩn Python) — không thêm dependency mới.
Đề tài: Trợ lý Quản lý Thư viện & Tài liệu
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import REACT_AGENT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from dotenv import load_dotenv

load_dotenv()

# Khởi tạo global instances
provider = get_llm_provider()
mcp_server = MCPAcademicServer()


def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(base_dir, "config", "test_cases.example.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_agent_for_ui(user_query: str) -> dict:
    """Chạy ReAct Agent và trả về kết quả cấu trúc cho UI"""
    steps = []
    tools_list = mcp_server.list_tools()
    accumulated_context = user_query
    step = 0
    final_answer = ""

    while step < MAX_ITERATIONS:
        step += 1
        step_start = time.time()

        llm_response = provider.generate_with_tools(
            accumulated_context, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )
        latency_ms = round((time.time() - step_start) * 1000, 2)
        thought = llm_response.get("thought", "Đang suy luận...")

        if llm_response.get("type") == "text":
            final_answer = llm_response.get("content", "")
            steps.append({
                "step": step,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_answer,
                "latency_ms": latency_ms
            })
            break

        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})

            steps.append({
                "step": step,
                "action_type": "TOOL_EXECUTION",
                "thought": thought,
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "mcp_response": mcp_result,
                "latency_ms": latency_ms
            })

            # Tổng hợp final answer
            if obs_data.get("status") == "SUCCESS":
                if "data" in obs_data:
                    d = obs_data["data"]
                    if "title" in d:
                        status_text = "Đang được mượn" if d.get("status") == "BORROWED" else "Có sẵn trên kệ"
                        final_answer = (
                            f"Thông tin sách {obs_data.get('book_id', '')}: "
                            f"'{d.get('title', '')}' của {d.get('author', '')}. "
                            f"Vị trí: {d.get('location', '')}. Trạng thái: {status_text}."
                        )
                        if d.get("status") == "BORROWED":
                            final_answer += f" Người mượn: {d.get('borrower_id', '')}. Hạn trả: {d.get('due_date', '')}."
                    else:
                        final_answer = json.dumps(obs_data, ensure_ascii=False)
                elif "message" in obs_data:
                    final_answer = obs_data["message"]
                else:
                    final_answer = json.dumps(obs_data, ensure_ascii=False)
            elif obs_data.get("status") == "NOT_FOUND":
                final_answer = obs_data.get("message", "Không tìm thấy.")
            elif obs_data.get("status") in ("INVALID_READER", "NOT_BORROWED", "WRONG_BORROWER"):
                final_answer = obs_data.get("message", "Không thể thực hiện.")
            else:
                final_answer = json.dumps(obs_data, ensure_ascii=False)

            # Multi-step check
            query_lower = user_query.lower()
            has_multi = any(kw in query_lower for kw in ["nếu", "rồi", "sau đó", "thì hãy"])
            if has_multi and tool_name == "book_query" and obs_data.get("status") == "SUCCESS":
                data = obs_data.get("data", {})
                accumulated_context = (
                    f"Kết quả tra cứu bước trước: Sách {obs_data.get('book_id', '')} "
                    f"'{data.get('title', '')}' đang ở trạng thái {data.get('status', '')}"
                )
                if data.get("borrower_id"):
                    accumulated_context += f", người mượn: {data['borrower_id']}, hạn trả: {data.get('due_date', '')}"
                accumulated_context += f". Yêu cầu ban đầu: {user_query}. Hãy thực hiện bước tiếp theo."
                continue

            # Single step done
            steps.append({
                "step": step + 1,
                "action_type": "FINAL_ANSWER",
                "thought": "Tổng hợp kết quả từ MCP Server.",
                "output": final_answer,
                "latency_ms": 0
            })
            break

    # Tự động nối thêm (append) vào file trace_waterfall.json
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        trace_path = os.path.join(base_dir, "docs", "trace_waterfall.json")
        existing_traces = []
        if os.path.exists(trace_path):
            try:
                with open(trace_path, "r", encoding="utf-8") as f:
                    existing_traces = json.load(f)
                    if not isinstance(existing_traces, list):
                        existing_traces = []
            except Exception:
                existing_traces = []
        
        # Thêm các bước mới vào lịch sử hiện có
        existing_traces.extend(steps)
        
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(existing_traces, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Lỗi lưu trace_waterfall.json từ UI: {e}")

    return {
        "query": user_query,
        "final_answer": final_answer,
        "steps": steps,
        "total_steps": len(steps),
        "provider": provider.__class__.__name__
    }


HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trợ lý Quản lý Thư viện & Tài liệu</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #f8fafc; color: #1e293b;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }
  .container { max-width: 960px; margin: 0 auto; padding: 32px 20px; }

  h1 { 
    font-size: 1.6rem; font-weight: 700; margin-bottom: 4px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
  }
  .subtitle { color: #64748b; font-size: 0.875rem; margin-bottom: 24px; }

  /* Input area */
  .input-area {
    background: #ffffff; border-radius: 12px; padding: 20px;
    margin-bottom: 20px; border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  }
  .input-row { display: flex; gap: 10px; margin-bottom: 12px; }
  #queryInput {
    flex: 1; padding: 10px 16px; border-radius: 8px;
    background: #f8fafc; border: 1px solid #cbd5e1; color: #0f172a;
    font-size: 0.95rem; outline: none; transition: all 0.2s ease;
  }
  #queryInput:focus {
    background: #ffffff;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }
  #queryInput::placeholder { color: #94a3b8; }
  #sendBtn {
    padding: 10px 22px; border-radius: 8px; border: none;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #ffffff; font-weight: 600; cursor: pointer; font-size: 0.9rem;
    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    transition: all 0.2s ease;
  }
  #sendBtn:hover { opacity: 0.95; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(37, 99, 235, 0.25); }
  #sendBtn:active { transform: translateY(0); }
  #sendBtn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }

  /* Test cases */
  .tc-bar { display: flex; gap: 8px; flex-wrap: wrap; }
  .tc-btn {
    padding: 6px 14px; border-radius: 6px; border: 1px solid #e2e8f0;
    background: #f1f5f9; color: #475569; cursor: pointer;
    font-size: 0.8rem; font-weight: 500; transition: all 0.2s ease;
  }
  .tc-btn:hover { border-color: #93c5fd; color: #2563eb; background: #eff6ff; }
  .tc-btn.active { border-color: #3b82f6; color: #1d4ed8; background: #dbeafe; font-weight: 600; }

  /* Results area */
  .result-card {
    background: #ffffff; border-radius: 12px; padding: 20px;
    margin-bottom: 16px; border: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    display: none;
  }
  .result-card.visible { display: block; }
  .result-card h3 { 
    font-size: 0.8rem; font-weight: 700; margin-bottom: 14px;
    color: #475569; text-transform: uppercase; letter-spacing: 0.05em;
  }

  /* Final answer */
  .final-answer {
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 8px; padding: 16px; font-size: 0.95rem;
    line-height: 1.6; color: #166534;
  }

  /* Steps */
  .step {
    border-left: 3px solid #cbd5e1; margin: 12px 0; padding: 12px 16px;
    border-radius: 0 8px 8px 0; background: #f8fafc;
    border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9;
  }
  .step.tool-step { border-left-color: #f59e0b; background: #fffbeb; }
  .step.text-step { border-left-color: #10b981; background: #f0fdf4; }
  .step-header {
    display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
    font-size: 0.8rem; color: #64748b;
  }
  .step-badge {
    padding: 3px 8px; border-radius: 4px; font-size: 0.7rem;
    font-weight: 600; text-transform: uppercase;
  }
  .badge-tool { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
  .badge-text { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
  .badge-error { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }

  .thought { color: #2563eb; font-style: italic; margin: 8px 0; font-size: 0.875rem; }

  .detail-block {
    background: #f8fafc; border-radius: 6px; padding: 12px;
    margin: 8px 0; font-family: 'Cascadia Code', 'Fira Code', ui-monospace, monospace;
    font-size: 0.8rem; overflow-x: auto; color: #334155;
    border: 1px solid #e2e8f0;
  }

  .latency { color: #94a3b8; font-size: 0.75rem; font-weight: 500; }

  /* Provider badge */
  .provider-badge {
    display: inline-block; padding: 4px 10px; border-radius: 4px;
    font-size: 0.75rem; font-weight: 600; margin-bottom: 14px;
    background: #eff6ff; color: #1d4ed8;
    border: 1px solid #bfdbfe;
  }

  /* Loading */
  .loading { text-align: center; padding: 40px; color: #64748b; font-size: 0.9rem; }
  .spinner {
    display: inline-block; width: 24px; height: 24px;
    border: 3px solid #e2e8f0; border-top-color: #3b82f6;
    border-radius: 50%; animation: spin 0.8s linear infinite;
    margin-bottom: 10px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* NOT_FOUND highlight */
  .not-found {
    background: #fef2f2; border: 1px solid #fecaca;
    border-radius: 8px; padding: 16px; color: #991b1b;
  }
</style>
</head>
<body>
<div class="container">
  <h1>📚 Trợ lý Quản lý Thư viện & Tài liệu</h1>
  <p class="subtitle">ReAct Agent + MCP Server — Test Interface (Lab 3)</p>
  
  <div class="input-area">
    <div class="input-row">
      <input id="queryInput" type="text" placeholder="Nhập câu hỏi cho Agent..." 
             onkeydown="if(event.key==='Enter')sendQuery()">
      <button id="sendBtn" onclick="sendQuery()">Gửi</button>
    </div>
    <div class="tc-bar">
      <span style="color:#64748b;font-size:0.8rem;line-height:2;">Test Cases:</span>
      <button class="tc-btn" onclick="loadTC(0)">TC01 Direct</button>
      <button class="tc-btn" onclick="loadTC(1)">TC02 Query</button>
      <button class="tc-btn" onclick="loadTC(2)">TC03 Action</button>
      <button class="tc-btn" onclick="loadTC(3)">TC04 Multi-step</button>
      <button class="tc-btn" onclick="loadTC(4)">TC05 Edge</button>
      <button class="tc-btn" onclick="runAllTC()" style="border-color:#f59e0b;color:#f59e0b;">▶ Run All</button>
    </div>
  </div>
  
  <div id="resultArea"></div>
</div>

<script>
let testCases = [];

// Load test cases on page load
fetch('/api/test_cases')
  .then(r => r.json())
  .then(data => { testCases = data; });

function loadTC(idx) {
  if (testCases[idx]) {
    document.getElementById('queryInput').value = testCases[idx].question;
    document.querySelectorAll('.tc-btn').forEach((b,i) => b.classList.toggle('active', i===idx));
  }
}

function sendQuery() {
  const input = document.getElementById('queryInput');
  const query = input.value.trim();
  if (!query) return;
  
  const btn = document.getElementById('sendBtn');
  btn.disabled = true; btn.textContent = '⏳';
  
  const area = document.getElementById('resultArea');
  area.innerHTML = '<div class="loading"><div class="spinner"></div><br>Agent đang suy luận...</div>';
  
  fetch('/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: query})
  })
  .then(r => r.json())
  .then(data => renderResult(data))
  .catch(e => { area.innerHTML = '<div class="not-found">Lỗi: ' + e.message + '</div>'; })
  .finally(() => { btn.disabled = false; btn.textContent = 'Gửi'; });
}

async function runAllTC() {
  const area = document.getElementById('resultArea');
  area.innerHTML = '';
  const btn = document.getElementById('sendBtn');
  btn.disabled = true;
  
  for (let i = 0; i < testCases.length; i++) {
    const tc = testCases[i];
    document.getElementById('queryInput').value = tc.question;
    document.querySelectorAll('.tc-btn').forEach((b,j) => b.classList.toggle('active', j===i));
    
    try {
      const r = await fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: tc.question})
      });
      const data = await r.json();
      const card = buildResultCard(data, tc);
      area.insertAdjacentHTML('beforeend', card);
    } catch(e) {
      area.insertAdjacentHTML('beforeend', '<div class="result-card visible"><div class="not-found">Lỗi TC'+(i+1)+': '+e.message+'</div></div>');
    }
  }
  btn.disabled = false;
}

function renderResult(data) {
  document.getElementById('resultArea').innerHTML = buildResultCard(data);
}

function buildResultCard(data, tc) {
  let html = '<div class="result-card visible">';
  
  // TC label if provided
  if (tc) {
    html += '<div style="margin-bottom:8px;"><span class="step-badge badge-tool">' + tc.id + ' — ' + tc.type + '</span>';
    html += ' <span class="latency">Kỳ vọng: ' + tc.expected_behavior.substring(0, 80) + '...</span></div>';
  }
  
  html += '<span class="provider-badge">🔌 ' + data.provider + '</span>';
  
  // Final Answer
  const hasNotFound = data.final_answer && data.final_answer.includes('Không tìm thấy');
  html += '<h3>🏁 Câu trả lời cuối cùng</h3>';
  html += '<div class="' + (hasNotFound ? 'not-found' : 'final-answer') + '">' + escapeHtml(data.final_answer || '(không có)') + '</div>';
  
  // Steps
  html += '<h3 style="margin-top:14px;">📊 Các bước ReAct (' + data.total_steps + ' steps)</h3>';
  
  for (const step of data.steps) {
    const isTool = step.action_type === 'TOOL_EXECUTION';
    html += '<div class="step ' + (isTool ? 'tool-step' : 'text-step') + '">';
    html += '<div class="step-header">';
    html += '<strong>Step ' + step.step + '</strong>';
    html += '<span class="step-badge ' + (isTool ? 'badge-tool' : 'badge-text') + '">' + step.action_type + '</span>';
    html += '<span class="latency">' + (step.latency_ms || 0) + 'ms</span>';
    html += '</div>';
    
    html += '<div class="thought">🧠 ' + escapeHtml(step.thought || '') + '</div>';
    
    if (isTool) {
      html += '<div class="detail-block">🛠️ Tool: <strong>' + step.tool_name + '</strong><br>';
      html += '📥 Arguments: ' + JSON.stringify(step.arguments) + '</div>';
      
      const obs = step.observation || {};
      const obsStatus = obs.status || '';
      const badgeClass = (obsStatus === 'SUCCESS') ? 'badge-text' : 'badge-error';
      html += '<div class="detail-block">👁️ Observation: <span class="step-badge ' + badgeClass + '">' + obsStatus + '</span><br>';
      html += '<pre style="margin-top:6px;white-space:pre-wrap;">' + JSON.stringify(obs, null, 2) + '</pre></div>';
    }
    
    if (step.action_type === 'FINAL_ANSWER' && step.output) {
      html += '<div class="detail-block">📝 ' + escapeHtml(step.output) + '</div>';
    }
    
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
</script>
</body>
</html>"""


class TestUIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/test_cases':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            tc = load_test_cases()
            self.wfile.write(json.dumps(tc, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/query':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            query = data.get('query', '')

            result = run_agent_for_ui(query)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == '__main__':
    port = 8080
    print("==========================================================")
    print("🧪 TEST UI — Trợ lý Quản lý Thư viện & Tài liệu")
    print("==========================================================")
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}")
    print(f"\n🌐 Mở trình duyệt: http://localhost:{port}")
    print("   Nhấn Ctrl+C để dừng server.\n")

    server = HTTPServer(('localhost', port), TestUIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Đã dừng Test UI Server ngay lập tức.")
        try:
            server.server_close()
        except Exception:
            pass
        sys.exit(0)
