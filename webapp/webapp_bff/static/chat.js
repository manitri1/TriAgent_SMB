/**
 * 공용 채팅 위젯. 화면 1(고객 문의)이 사용하고, 화면 2(주문 접수)의 자유
 * 채팅창도 같은 함수를 재사용한다 — 결국 모두 동일한 /api/agent/message
 * 릴레이 하나로 수렴한다(curried-percolating-ocean.md).
 *
 * conversation_id는 화면별로 localStorage에 저장해, 새로고침해도 같은 hermes
 * session_id(--resume)로 이어지게 한다.
 *
 * demoQueue: [{label, message}, ...]를 넘기면 데모 모드가 켜진다 — 입력창에
 * 첫 데모 문구가 미리 채워지고, 기존 "보내기" 버튼을 누르면 그대로 전송된다.
 * 응답을 받으면 자동으로 다음 데모 문구가 채워져, 발표자가 타이핑 없이 버튼만
 * 눌러가며 시연을 이어갈 수 있다. demoBarId를 함께 넘기면 진행 상황(n/총n)과
 * "처음부터" 리셋 버튼이 그 자리에 렌더링된다.
 */
function initChatWidget({ formId, inputId, threadId, profile, storageKey, placeholderText, onReply, demoQueue, demoBarId }) {
  const form = document.getElementById(formId);
  const input = document.getElementById(inputId);
  const thread = document.getElementById(threadId);
  const demoBar = demoBarId ? document.getElementById(demoBarId) : null;
  let demoIndex = 0;

  function conversationId() {
    let id = localStorage.getItem(storageKey);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(storageKey, id);
    }
    return id;
  }

  function renderDemoBar() {
    if (!demoBar) return;
    if (demoIndex >= demoQueue.length) {
      demoBar.innerHTML = `<span class="demo-label">데모 완료</span>`;
    } else {
      const step = demoQueue[demoIndex];
      demoBar.innerHTML = `<span class="demo-label">데모 ${demoIndex + 1}/${demoQueue.length} · ${step.label}</span>`;
    }
    const resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.className = "demo-reset";
    resetBtn.textContent = "처음부터";
    resetBtn.addEventListener("click", () => {
      demoIndex = 0;
      loadDemoStep();
    });
    demoBar.appendChild(resetBtn);
  }

  function loadDemoStep() {
    if (!demoQueue) return;
    renderDemoBar();
    if (demoIndex < demoQueue.length) {
      input.value = demoQueue[demoIndex].message;
    }
  }

  function appendMessage(role, text, statusClass) {
    const row = document.createElement("div");
    row.className = `chat-row chat-row--${role}${statusClass ? ` chat-row--${statusClass}` : ""}`;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    thread.appendChild(row);
    thread.scrollTop = thread.scrollHeight;
    return row;
  }

  async function send(message) {
    appendMessage("user", message);
    const pending = appendMessage("agent", "생각하는 중…", "pending");

    try {
      const res = await fetch("/api/agent/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, message, conversation_id: conversationId() }),
      });
      const data = await res.json();
      pending.remove();
      const statusClass = data.status === "ok" ? null : data.status;
      appendMessage("agent", data.text, statusClass);
      // 상태(ok/timeout/error)와 무관하게 재조회를 권한다 — 타임아웃이어도
      // 컨테이너 안에서는 작업이 이미 끝났을 수 있다(Phase 0 실측, Active
      // Verification 원칙).
      if (onReply) onReply(data);
    } catch (err) {
      pending.remove();
      appendMessage("agent", "네트워크 오류가 발생했습니다. 다시 시도해 주세요.", "error");
    } finally {
      if (demoQueue) {
        demoIndex++;
        loadDemoStep();
      }
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    send(message);
  });

  if (placeholderText) input.placeholder = placeholderText;
  loadDemoStep();
}
