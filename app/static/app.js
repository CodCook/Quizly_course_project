const historyList = document.getElementById("history-list");
const reloadHistoryButton = document.getElementById("reload-history");
const uploadPanel = document.querySelector(".upload-panel");

let currentUploadId = null;
let currentUploadFilename = null;
let loadingTipTimer = null;
let panelTransitionTimer = null;
const SESSION_HISTORY_STORAGE_KEY = "quizly.currentSessionHistory";

const LOADING_TIPS = {
  summary: [
    "Generating summary...",
    "Identifying key points...",
    "Condensing your content...",
  ],
  quiz: [
    "Generating quiz...",
    "Crafting balanced questions...",
    "Matching answers to options...",
  ],
  flashcards: [
    "Generating flashcards...",
    "Extracting core terms...",
    "Writing study-friendly definitions...",
  ],
  default: [
    "Generating...",
    "Analyzing your content...",
    "Almost there...",
  ],
};

function getUploadElements() {
  return {
    dropzone: document.getElementById("dropzone"),
    fileInput: document.getElementById("file-input"),
    browseButton: document.getElementById("browse-button")
  };
}

function getPostUploadActions() {
  return document.getElementById("post-upload-actions");
}

function getGenerationOverlayElements() {
  return {
    overlay: document.getElementById("generation-loading-overlay"),
    label: document.getElementById("generation-loading-label"),
  };
}

function ensureGenerationOverlay() {
  const existing = getGenerationOverlayElements().overlay;
  if (existing) return;

  const overlay = document.createElement("div");
  overlay.id = "generation-loading-overlay";
  overlay.className = "generation-loading-overlay hidden";
  overlay.innerHTML = `
    <div class="generation-loading-card">
      <div class="generation-spinner" aria-hidden="true"></div>
      <p id="generation-loading-label" class="generation-loading-label">Generating...</p>
    </div>
  `;

  document.body.appendChild(overlay);
}

function setGenerationLoading(isLoading, message = "Generating...") {
  ensureGenerationOverlay();
  const { overlay, label } = getGenerationOverlayElements();
  if (!overlay || !label) return;

  label.textContent = message;
  overlay.classList.toggle("hidden", !isLoading);
}

function stopLoadingTips() {
  if (loadingTipTimer) {
    clearInterval(loadingTipTimer);
    loadingTipTimer = null;
  }
}

function startLoadingTips(action) {
  stopLoadingTips();

  const tips = LOADING_TIPS[action] || LOADING_TIPS.default;
  let index = 0;
  setGenerationLoading(true, tips[index]);

  loadingTipTimer = setInterval(() => {
    index = (index + 1) % tips.length;
    setGenerationLoading(true, tips[index]);
  }, 1200);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatInlineMarkdown(text) {
  let safe = escapeHtml(text);
  safe = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/\*(.+?)\*/g, "<em>$1</em>");
  safe = safe.replace(/`(.+?)`/g, "<code>$1</code>");
  return safe;
}

function formatSummaryText(rawSummary) {
  if (!rawSummary) {
    return "<p>No summary available.</p>";
  }

  const lines = String(rawSummary).replace(/\r\n/g, "\n").split("\n");
  const html = [];
  let listType = null;

  const closeList = () => {
    if (listType) {
      html.push(`</${listType}>`);
      listType = null;
    }
  };

  lines.forEach((line) => {
    const trimmed = line.trim();

    if (!trimmed) {
      closeList();
      return;
    }

    const headingMatch = trimmed.match(/^#{1,3}\s+(.+)$/);
    if (headingMatch) {
      closeList();
      html.push(`<h4>${formatInlineMarkdown(headingMatch[1])}</h4>`);
      return;
    }

    const boldHeadingMatch = trimmed.match(/^\*\*(.+?)\*\*:?$/);
    if (boldHeadingMatch) {
      closeList();
      html.push(`<h4>${formatInlineMarkdown(boldHeadingMatch[1])}</h4>`);
      return;
    }

    const unorderedMatch = trimmed.match(/^[-*]\s+(.+)$/);
    if (unorderedMatch) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        html.push("<ul>");
      }
      html.push(`<li>${formatInlineMarkdown(unorderedMatch[1])}</li>`);
      return;
    }

    const orderedMatch = trimmed.match(/^\d+\.\s+(.+)$/);
    if (orderedMatch) {
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        html.push("<ol>");
      }
      html.push(`<li>${formatInlineMarkdown(orderedMatch[1])}</li>`);
      return;
    }

    closeList();
    html.push(`<p>${formatInlineMarkdown(trimmed)}</p>`);
  });

  closeList();
  return html.join("");
}

function formatDate(value) {
  if (!value) {
    return "Unknown date";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function animatePanelSwap(renderFn) {
  if (!uploadPanel) {
    renderFn();
    return;
  }

  if (panelTransitionTimer) {
    clearTimeout(panelTransitionTimer);
  }

  uploadPanel.classList.add("panel-switch-out");
  panelTransitionTimer = setTimeout(() => {
    renderFn();
    uploadPanel.classList.remove("panel-switch-out");
    uploadPanel.classList.add("panel-switch-in");
    requestAnimationFrame(() => {
      uploadPanel.classList.remove("panel-switch-in");
    });
  }, 150);
}

function renderUploadPanel(content, onReady) {
  animatePanelSwap(() => {
    uploadPanel.innerHTML = content;
    if (typeof onReady === "function") {
      onReady();
    }

    uploadPanel.querySelectorAll(".summary-display, .upload-dropzone").forEach((node) => {
      node.classList.add("content-pop");
      node.addEventListener("animationend", () => {
        node.classList.remove("content-pop");
      }, { once: true });
    });
  });
}

function hidePostUploadActions() {
  const postUploadActions = getPostUploadActions();
  if (!postUploadActions) return;
  postUploadActions.classList.add("hidden");
  postUploadActions.innerHTML = "";
}

function normalizeSession(session) {
  const quiz = Array.isArray(session.quiz) ? session.quiz : (Array.isArray(session.quiz_json) ? session.quiz_json : []);
  const flashcards = Array.isArray(session.flashcards) ? session.flashcards : (Array.isArray(session.flashcards_json) ? session.flashcards_json : []);

  return {
    ...session,
    summary: session.summary || "",
    quiz,
    flashcards,
  };
}

function readSessionHistoryEntries() {
  try {
    const raw = window.sessionStorage.getItem(SESSION_HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeSessionHistoryEntries(entries) {
  try {
    window.sessionStorage.setItem(SESSION_HISTORY_STORAGE_KEY, JSON.stringify(entries));
  } catch {
    // Ignore sessionStorage failures; app can continue without sidebar persistence.
  }
}

function initializeSessionHistory() {
  // Treat each page load as a fresh user session for the sidebar history.
  try {
    window.sessionStorage.removeItem(SESSION_HISTORY_STORAGE_KEY);
  } catch {
    // Ignore storage access failures.
  }
}

function addSessionHistoryEntry(session) {
  const normalized = normalizeSession(session);
  const id = normalized.session_id || normalized.id || normalized.upload_id || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const entry = {
    id: String(id),
    session_id: normalized.session_id ? String(normalized.session_id) : "",
    upload_id: normalized.upload_id ? String(normalized.upload_id) : "",
    filename: normalized.filename || "Uploaded file",
    created_at: normalized.created_at || new Date().toISOString(),
    summary: normalized.summary || "",
    quiz: Array.isArray(normalized.quiz) ? normalized.quiz : [],
    flashcards: Array.isArray(normalized.flashcards) ? normalized.flashcards : [],
  };

  const existing = readSessionHistoryEntries().filter((item) => String(item.id) !== String(entry.id));
  existing.unshift(entry);
  writeSessionHistoryEntries(existing);
}

function upsertSessionHistoryEntry(session) {
  addSessionHistoryEntry(session);
}

function removeSessionHistoryEntry(session) {
  const id = String(session?.id || "");
  const sessionId = String(session?.session_id || "");
  if (!id && !sessionId) return;

  const remaining = readSessionHistoryEntries().filter((item) => {
    const itemId = String(item?.id || "");
    const itemSessionId = String(item?.session_id || "");
    if (id && itemId === id) return false;
    if (sessionId && itemSessionId === sessionId) return false;
    return true;
  });

  writeSessionHistoryEntries(remaining);
}

function isUuidLike(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(String(value || ""));
}

async function loadHistory() {
  historyList.innerHTML = '<li class="history-empty">Loading history...</li>';

  try {
    const sessions = readSessionHistoryEntries();

    if (!sessions.length) {
      historyList.innerHTML = '<li class="history-empty">No uploads in this session yet. Upload and generate to build your history.</li>';
      return;
    }

    historyList.innerHTML = sessions
      .map((session) => {
        const label = session.filename || `Session #${session.id || "?"}`;
        return `
          <li class="history-item" data-session-id="${escapeHtml(String(session.id))}">
            <p class="history-item-title">${escapeHtml(label)}</p>
            <p class="history-item-time">${formatDate(session.created_at)}</p>
          </li>
        `;
      })
      .join("");

    document.querySelectorAll(".history-item").forEach((item) => {
      item.addEventListener("click", () => {
        const sessionId = item.getAttribute("data-session-id");
        loadSessionDetails(sessionId);
      });
    });
  } catch (error) {
    historyList.innerHTML = `<li class="history-empty state-bad">Could not load history: ${error.message}</li>`;
  }
}

async function loadSessionDetails(sessionId) {
  try {
    const sessions = readSessionHistoryEntries();
    const session = sessions.find((item) => String(item.id) === String(sessionId));

    if (!session) {
      throw new Error("Session not found in this browser session");
    }

    showHistoryMaterialChooser(normalizeSession(session));
  } catch (error) {
    alert(`Error loading session: ${error.message}`);
  }
}

function showHistoryMaterialChooser(session) {
  const safeFileName = escapeHtml(session.filename || "Uploaded file");
  const hasSummary = Boolean((session.summary || "").trim());
  const hasQuiz = Array.isArray(session.quiz) && session.quiz.length > 0;
  const hasFlashcards = Array.isArray(session.flashcards) && session.flashcards.length > 0;

  renderUploadPanel(`
    <h2>Choose Material</h2>
    <div class="summary-display">
      <p class="summary-title"><strong>File:</strong> ${safeFileName}</p>
      <p class="upload-text">Select what you want to open from this file.</p>
      <div class="summary-actions">
        <button class="button ${hasSummary ? "solid" : "ghost"}" id="open-history-summary-btn" type="button">${hasSummary ? "Summary" : "Generate Summary"}</button>
        <button class="button ${hasQuiz ? "solid" : "ghost"}" id="open-history-quiz-btn" type="button">${hasQuiz ? "Quiz" : "Generate Quiz"}</button>
        <button class="button ${hasFlashcards ? "solid" : "ghost"}" id="open-history-flashcards-btn" type="button">${hasFlashcards ? "Flashcards" : "Generate Flashcards"}</button>
        <button class="button ghost" id="new-upload-btn" type="button">Upload Another File</button>
      </div>
    </div>
  `, () => {
    const summaryBtn = document.getElementById("open-history-summary-btn");
    const quizBtn = document.getElementById("open-history-quiz-btn");
    const flashcardsBtn = document.getElementById("open-history-flashcards-btn");

    if (summaryBtn) {
      summaryBtn.addEventListener("click", async () => {
        if (hasSummary) {
          displaySessionSummary(session);
          return;
        }
        await generateFromHistorySession(session, "summary");
      });
    }

    if (quizBtn) {
      quizBtn.addEventListener("click", async () => {
        if (hasQuiz) {
          displayQuizReady(session);
          return;
        }
        await generateFromHistorySession(session, "quiz");
      });
    }

    if (flashcardsBtn) {
      flashcardsBtn.addEventListener("click", async () => {
        if (hasFlashcards) {
          displayFlashcards(session);
          return;
        }
        await generateFromHistorySession(session, "flashcards");
      });
    }

    document.getElementById("new-upload-btn").addEventListener("click", resetUpload);
    hidePostUploadActions();
  });
}

async function generateFromHistorySession(session, action) {
  const persistentSessionId = session.session_id || (isUuidLike(session.id) ? session.id : "");
  const uploadId = session.upload_id || "";

  if (!persistentSessionId && !uploadId) {
    alert("Cannot generate from this history item in this tab session.");
    return;
  }

  try {
    startLoadingTips(action);

    let response = null;

    if (persistentSessionId) {
      response = await fetch(`/api/history/${persistentSessionId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });

      // Stale DB entry: fall back to current-server upload cache if available.
      if (response.status === 404 && uploadId) {
        response = await fetch("/api/upload/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ upload_id: uploadId, action }),
        });
      }
    } else {
      response = await fetch("/api/upload/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ upload_id: uploadId, action }),
      });
    }

    if (!response.ok) {
      if (response.status === 404) {
        removeSessionHistoryEntry(session);
        await loadHistory();
        throw new Error("This history item is no longer available. Please upload the file again.");
      }

      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Generation failed: ${response.statusText}`);
    }

    const generated = normalizeSession(await response.json());
    const merged = {
      ...session,
      session_id: generated.session_id || session.session_id || persistentSessionId,
      upload_id: session.upload_id || uploadId,
      summary: action === "summary" ? generated.summary : session.summary,
      quiz: action === "quiz" ? generated.quiz : session.quiz,
      flashcards: action === "flashcards" ? generated.flashcards : session.flashcards,
    };

    upsertSessionHistoryEntry(merged);
    await loadHistory();

    if (action === "summary") {
      displaySessionSummary(merged);
    } else if (action === "quiz") {
      displayQuizReady(merged);
      if (Array.isArray(merged.quiz) && merged.quiz.length > 0) {
        openQuizModal(merged.filename || "Uploaded file", merged.quiz);
      }
    } else {
      displayFlashcards(merged);
    }
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    stopLoadingTips();
    setGenerationLoading(false);
  }
}

function displaySessionSummary(session) {
  const safeFileName = escapeHtml(session.filename || "Uploaded file");
  const formattedSummary = formatSummaryText(session.summary);
  const showQuizBtn = session.quiz.length > 0;
  const canGenerateQuizNow = !showQuizBtn && Boolean(currentUploadId);

  renderUploadPanel(`
    <h2>Summary Generated</h2>
    <div class="summary-display">
      <p class="summary-title"><strong>File:</strong> ${safeFileName}</p>
      <div class="summary-content">
        <h3>Summary</h3>
        ${formattedSummary}
      </div>
      <div class="summary-actions">
        ${showQuizBtn ? '<button class="button solid" id="practice-quiz-btn" type="button">Practice Quiz</button>' : ""}
        ${canGenerateQuizNow ? '<button class="button solid" id="generate-quiz-from-summary-btn" type="button">Practice Quiz</button>' : ""}
        <button class="button ghost" id="new-upload-btn" type="button">Upload Another File</button>
      </div>
    </div>
  `, () => {
    if (showQuizBtn) {
      document.getElementById("practice-quiz-btn").addEventListener("click", () => {
        openQuizModal(session.filename || "Uploaded file", session.quiz);
      });
    }

    if (canGenerateQuizNow) {
      document.getElementById("generate-quiz-from-summary-btn").addEventListener("click", async (event) => {
        const btn = event.currentTarget;
        btn.disabled = true;
        btn.textContent = "Preparing quiz...";
        await generateSelectedOutput("quiz");
      });
    }

    document.getElementById("new-upload-btn").addEventListener("click", resetUpload);
    hidePostUploadActions();
  });
}

function displayFlashcards(session) {
  const safeFileName = escapeHtml(session.filename || "Uploaded file");

  renderUploadPanel(`
    <h2>Flashcards Generated</h2>
    <div class="summary-display">
      <p class="summary-title"><strong>File:</strong> ${safeFileName}</p>
      <div class="summary-content">
        <h3>Flashcards</h3>
        <div class="flashcards-grid">
          ${session.flashcards
            .map(
              (card) => `
            <article class="flashcard-item">
              <h4>${escapeHtml(card.term || "Term")}</h4>
              <p>${escapeHtml(card.definition || "")}</p>
            </article>
          `
            )
            .join("")}
        </div>
      </div>
      <div class="summary-actions">
        <button class="button ghost" id="new-upload-btn" type="button">Upload Another File</button>
      </div>
    </div>
  `, () => {
    document.getElementById("new-upload-btn").addEventListener("click", resetUpload);
    hidePostUploadActions();
  });
}

function displayQuizReady(session) {
  const safeFileName = escapeHtml(session.filename || "Uploaded file");

  renderUploadPanel(`
    <h2>Quiz Ready</h2>
    <div class="summary-display">
      <p class="summary-title"><strong>File:</strong> ${safeFileName}</p>
      <p class="upload-text">Your quiz is ready. Start when you are ready.</p>
      <div class="summary-actions">
        <button class="button solid" id="practice-quiz-btn" type="button">Practice Quiz</button>
        <button class="button ghost" id="new-upload-btn" type="button">Upload Another File</button>
      </div>
    </div>
  `, () => {
    document.getElementById("practice-quiz-btn").addEventListener("click", () => {
      openQuizModal(session.filename || "Uploaded file", session.quiz);
    });
    document.getElementById("new-upload-btn").addEventListener("click", resetUpload);
    hidePostUploadActions();
  });
}

function displaySessionOutput(session) {
  if (session.summary) {
    displaySessionSummary(session);
    return;
  }

  if (session.flashcards.length) {
    displayFlashcards(session);
    return;
  }

  if (session.quiz.length) {
    displayQuizReady(session);
    return;
  }

  renderUploadPanel(`
    <h2>No Content Generated</h2>
    <div class="summary-display">
      <p class="upload-text">This session does not contain summary, quiz, or flashcards yet.</p>
      <div class="summary-actions">
        <button class="button ghost" id="new-upload-btn" type="button">Upload Another File</button>
      </div>
    </div>
  `, () => {
    document.getElementById("new-upload-btn").addEventListener("click", resetUpload);
    hidePostUploadActions();
  });
}

function showPostUploadActions(filename) {
  const postUploadActions = getPostUploadActions();
  if (!postUploadActions) return;

  postUploadActions.innerHTML = `
    <h3>Choose what to generate</h3>
    <p class="post-upload-subtitle">${escapeHtml(filename)} uploaded successfully.</p>
    <div class="post-upload-buttons">
      <button class="button solid" data-action="summary" type="button">Generate Summary</button>
      <button class="button ghost" data-action="quiz" type="button">Generate Quiz</button>
      <button class="button ghost" data-action="flashcards" type="button">Generate Flashcards</button>
    </div>
  `;
  postUploadActions.classList.remove("hidden");
  postUploadActions.classList.add("actions-pop");
  postUploadActions.addEventListener("animationend", () => {
    postUploadActions.classList.remove("actions-pop");
  }, { once: true });

  postUploadActions.querySelectorAll("[data-action]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const action = btn.getAttribute("data-action") || "";
      generateSelectedOutput(action);
    });
  });
}

async function generateSelectedOutput(action) {
  if (!currentUploadId) {
    alert("Please upload a file first.");
    return;
  }

  const postUploadActions = getPostUploadActions();
  const actionButtons = postUploadActions ? [...postUploadActions.querySelectorAll("[data-action]")] : [];
  actionButtons.forEach((btn) => {
    btn.disabled = true;
  });

  try {
    startLoadingTips(action);

    const response = await fetch("/api/upload/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ upload_id: currentUploadId, action })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Generation failed: ${response.statusText}`);
    }

    const result = await response.json();
    const normalized = normalizeSession(result);
    addSessionHistoryEntry({
      ...normalized,
      upload_id: currentUploadId,
    });
    displaySessionOutput(normalized);

    if (action === "quiz" && normalized.quiz.length > 0) {
      openQuizModal(normalized.filename || "Uploaded file", normalized.quiz);
    }

    historyList.innerHTML = '<li class="history-empty">Updating history...</li>';
    loadHistory();
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    stopLoadingTips();
    setGenerationLoading(false);
    actionButtons.forEach((btn) => {
      btn.disabled = false;
    });
  }
}

async function uploadFile(file) {
  if (!file) return;

  const { dropzone, browseButton } = getUploadElements();
  const formData = new FormData();
  formData.append("file", file);

  try {
    if (dropzone) {
      dropzone.style.opacity = "0.6";
    }
    if (browseButton) {
      browseButton.disabled = true;
      browseButton.textContent = "Uploading...";
    }

    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
    }

    const result = await response.json();
    if (result.success) {
      currentUploadId = result.upload_id;
      currentUploadFilename = result.filename || file.name;
      showPostUploadActions(currentUploadFilename);
    }
  } catch (error) {
    alert(`Error: ${error.message}`);
  } finally {
    if (dropzone) {
      dropzone.style.opacity = "1";
    }
    if (browseButton) {
      browseButton.disabled = false;
      browseButton.textContent = "Or browse files";
    }
  }
}

function resetUpload() {
  currentUploadId = null;
  currentUploadFilename = null;

  renderUploadPanel(`
    <h2>Upload Your Notes</h2>
    <div class="upload-dropzone" id="dropzone">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="17 8 12 3 7 8"></polyline>
        <line x1="12" y1="3" x2="12" y2="15"></line>
      </svg>
      <p class="upload-text">Drag and drop your PDF, DOCX, or PPTX file here</p>
      <input type="file" id="file-input" accept=".pdf,.docx,.ppt,.pptx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-powerpoint,application/vnd.openxmlformats-officedocument.presentationml.presentation" hidden />
      <button class="button solid" id="browse-button" type="button">Or browse files</button>
    </div>
    <div id="post-upload-actions" class="post-upload-actions hidden"></div>
  `, () => {
    hidePostUploadActions();
    setupDropzoneListeners();
  });
}

function setupDropzoneListeners() {
  const { dropzone, fileInput, browseButton } = getUploadElements();
  if (!dropzone || !fileInput || !browseButton) return;

  browseButton.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadFile(file);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");

    const files = e.dataTransfer?.files;
    if (files?.length) {
      uploadFile(files[0]);
    }
  });
}

setupDropzoneListeners();
initializeSessionHistory();

let currentQuizQuestions = [];
let userAnswers = {};

const quizModal = document.getElementById("quiz-modal");
const closeQuizBtn = document.getElementById("close-quiz-btn");
const submitQuizBtn = document.getElementById("submit-quiz-btn");
const quizBody = document.getElementById("quiz-body");
const quizTitle = document.getElementById("quiz-title");
const quizProgress = document.getElementById("quiz-progress");

function openQuizModal(topic, questions) {
  currentQuizQuestions = questions;
  userAnswers = {};

  quizTitle.textContent = `Quiz: ${topic}`;
  quizModal.classList.remove("hidden");
  submitQuizBtn.classList.remove("hidden");
  submitQuizBtn.textContent = "Submit Quiz";

  renderQuestions();
  updateProgress();
}

function renderQuestions() {
  quizBody.innerHTML = currentQuizQuestions.map((q, qIdx) => `
    <div class="quiz-question" id="q-${qIdx}">
      <h4>${qIdx + 1}. ${escapeHtml(q.question)}</h4>
      <div class="quiz-options-grid">
        ${q.options.map((opt) => `
          <button class="quiz-option-btn" onclick="selectOption(${qIdx}, '${escapeHtml(opt)}')">
            ${escapeHtml(opt)}
          </button>
        `).join("")}
      </div>
    </div>
  `).join("");
}

window.selectOption = (qIdx, option) => {
  if (submitQuizBtn.textContent === "Close Quiz") return;

  userAnswers[qIdx] = option;

  const btns = document.querySelectorAll(`#q-${qIdx} .quiz-option-btn`);
  btns.forEach((btn) => {
    if (btn.textContent.trim() === option) {
      btn.classList.add("selected");
    } else {
      btn.classList.remove("selected");
    }
  });

  updateProgress();
};

function updateProgress() {
  const answeredCount = Object.keys(userAnswers).length;
  quizProgress.textContent = `Answered ${answeredCount} of ${currentQuizQuestions.length}`;
}

async function submitQuiz() {
  if (submitQuizBtn.textContent === "Close Quiz") {
    closeQuizModal();
    return;
  }

  const answeredCount = Object.keys(userAnswers).length;
  if (answeredCount < currentQuizQuestions.length) {
    if (!confirm("You haven't answered all questions. Submit anyway?")) return;
  }

  let score = 0;
  currentQuizQuestions.forEach((q, idx) => {
    const userAns = userAnswers[idx];
    const isCorrect = userAns === q.answer;
    if (isCorrect) score++;

    const btns = document.querySelectorAll(`#q-${idx} .quiz-option-btn`);
    btns.forEach((btn) => {
      const btnText = btn.textContent.trim();
      btn.disabled = true;
      if (btnText === q.answer) {
        btn.classList.add("correct");
        if (btnText === userAns) {
          btn.innerHTML += " ✓";
        }
      } else if (btnText === userAns && !isCorrect) {
        btn.classList.add("wrong");
        btn.innerHTML += " ✗";
      }
    });
  });

  const scoreHtml = `
    <div class="results-summary reveal">
      <p>Quiz Completed!</p>
      <div class="score-display">${score} / ${currentQuizQuestions.length}</div>
      <p>${score === currentQuizQuestions.length ? "Perfect score! Well done." : "Keep studying to improve your score!"}</p>
    </div>
    <hr style="opacity: 0.1; margin: 2rem 0;">
  `;
  quizBody.insertAdjacentHTML("afterbegin", scoreHtml);

  submitQuizBtn.textContent = "Close Quiz";
  quizBody.scrollTo({ top: 0, behavior: "smooth" });
}

function closeQuizModal() {
  quizModal.classList.add("hidden");
  quizBody.innerHTML = "";
}

closeQuizBtn.addEventListener("click", closeQuizModal);
submitQuizBtn.addEventListener("click", submitQuiz);
reloadHistoryButton.addEventListener("click", loadHistory);
window.addEventListener("load", () => {
  loadHistory();
});
