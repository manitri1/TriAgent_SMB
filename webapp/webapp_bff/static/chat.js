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
// coordinator 위임은 실측 기준 25초~4분 걸릴 수 있다(docs/14-webapp-users-guide.md
// 6절). 타임아웃 후에도 컨테이너 안 작업은 계속될 수 있어(Active Verification),
// 자동으로 몇 차례 더 재조회해 사용자가 수동 새로고침을 안 해도 되게 한다.
const TIMEOUT_POLL_INTERVAL_MS = 15000;
const TIMEOUT_POLL_MAX_ATTEMPTS = 5;
const SLOW_HINT_THRESHOLD_SECONDS = 20;

function initChatWidget({ formId, inputId, threadId, profile, storageKey, placeholderText, onReply, onBusyChange, demoQueue, demoBarId, quickReplies, quickRepliesId }) {
  const form = document.getElementById(formId);
  const input = document.getElementById(inputId);
  const thread = document.getElementById(threadId);
  const demoBar = demoBarId ? document.getElementById(demoBarId) : null;
  let demoIndex = 0;
  let busy = false;
  let quickReplyButtons = [];
  let timeoutPollTimer = null;

  function setBusy(isBusy) {
    busy = isBusy;
    input.disabled = isBusy;
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = isBusy;
    quickReplyButtons.forEach((btn) => (btn.disabled = isBusy));
    if (onBusyChange) onBusyChange(isBusy);
  }

  function clearTimeoutPolling() {
    if (timeoutPollTimer) {
      clearInterval(timeoutPollTimer);
      timeoutPollTimer = null;
    }
  }

  function startTimeoutPolling() {
    if (!onReply) return;
    clearTimeoutPolling();
    let attempts = 0;
    timeoutPollTimer = setInterval(() => {
      attempts++;
      onReply();
      if (attempts >= TIMEOUT_POLL_MAX_ATTEMPTS) clearTimeoutPolling();
    }, TIMEOUT_POLL_INTERVAL_MS);
  }

  function conversationId() {
    return getConversationId(storageKey);
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

  // 응답 텍스트에 "승인"이 포함되면 HITL 승인 대기 상태로 간주해 버블을 강조한다
  // — 실제 승인 여부는 status 필드가 아니라 에이전트가 되묻는 문장으로 표현되기
  // 때문에(예: "...승인하시겠습니까?"), 텍스트 휴리스틱으로 판단한다.
  function isApprovalPrompt(role, text, statusClass) {
    return role === "agent" && !statusClass && /승인/.test(text);
  }

  function appendMessage(role, text, statusClass) {
    const approval = isApprovalPrompt(role, text, statusClass);
    const row = document.createElement("div");
    row.className = `chat-row chat-row--${role}${statusClass ? ` chat-row--${statusClass}` : ""}${approval ? " chat-row--approval" : ""}`;
    if (approval) {
      const label = document.createElement("div");
      label.className = "chat-approval-label";
      label.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.3 3.9 2.5 17a1.6 1.6 0 0 0 1.4 2.4h16.2a1.6 1.6 0 0 0 1.4-2.4L13.7 3.9a1.6 1.6 0 0 0-2.8 1"/></svg>승인 필요';
      row.appendChild(label);
    }
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    thread.appendChild(row);
    thread.scrollTop = thread.scrollHeight;
    return row;
  }

  async function send(message) {
    if (busy) return; // 응답 대기 중 중복 전송 방지 — 같은 세션에 겹쳐 보내면
    // 특히 주문 접수 화면에서 중복 주문으로 이어질 수 있다.
    clearTimeoutPolling();
    appendMessage("user", message);
    const pending = appendMessage("agent", "생각하는 중… (0초)", "pending");
    const pendingBubble = pending.querySelector(".chat-bubble");
    const startedAt = Date.now();
    const elapsedTimer = setInterval(() => {
      const secs = Math.floor((Date.now() - startedAt) / 1000);
      let text = `생각하는 중… (${secs}초)`;
      if (secs >= SLOW_HINT_THRESHOLD_SECONDS) {
        text += "\n보통 25초~4분 정도 걸려요. 잠시만 기다려 주세요.";
      }
      pendingBubble.textContent = text;
    }, 1000);

    setBusy(true);
    try {
      const res = await fetch("/api/agent/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, message, conversation_id: conversationId() }),
      });
      const data = await res.json();
      clearInterval(elapsedTimer);
      pending.remove();
      const statusClass = data.status === "ok" ? null : data.status;
      appendMessage("agent", data.text, statusClass);
      // 상태(ok/timeout/error)와 무관하게 재조회를 권한다 — 타임아웃이어도
      // 컨테이너 안에서는 작업이 이미 끝났을 수 있다(Phase 0 실측, Active
      // Verification 원칙).
      if (onReply) onReply(data);
      if (data.status === "timeout") startTimeoutPolling();
    } catch (err) {
      clearInterval(elapsedTimer);
      pending.remove();
      appendMessage("agent", "네트워크 오류가 발생했습니다. 다시 시도해 주세요.", "error");
    } finally {
      clearInterval(elapsedTimer);
      setBusy(false);
      if (demoQueue) {
        demoIndex++;
        loadDemoStep();
      }
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message || busy) return;
    input.value = "";
    send(message);
  });

  // 자주 묻는 질문 칩 — demoQueue(순차 시연용)와 달리 즉시 전송되는 독립 기능.
  function renderQuickReplies() {
    if (!quickReplies || !quickRepliesId) return;
    const bar = document.getElementById(quickRepliesId);
    if (!bar) return;
    bar.innerHTML = "";
    const label = document.createElement("span");
    label.className = "chip-row-label";
    label.textContent = "자주 묻는 질문";
    bar.appendChild(label);
    quickReplyButtons = [];
    quickReplies.forEach((q) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "quick-chip";
      chip.textContent = q.label;
      chip.addEventListener("click", () => {
        if (busy) return;
        send(q.message);
      });
      bar.appendChild(chip);
      quickReplyButtons.push(chip);
    });
  }

  if (placeholderText) input.placeholder = placeholderText;
  loadDemoStep();
  renderQuickReplies();
}
