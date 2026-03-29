const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const browseButton = document.getElementById("browse-button");
const historyList = document.getElementById("history-list");
const reloadHistoryButton = document.getElementById("reload-history");
const uploadPanel = document.querySelector(".upload-panel");

let currentSummary = null;

function getUploadElements() {
  return {
    dropzone: document.getElementById("dropzone"),
    fileInput: document.getElementById("file-input"),
    browseButton: document.getElementById("browse-button")
  };
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

async function loadHistory() {
  historyList.innerHTML = '<li class="history-empty">Loading history...</li>';

  try {
    const response = await fetch("/api/history");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    const sessions = Array.isArray(payload.sessions) ? payload.sessions : [];

    if (!sessions.length) {
      historyList.innerHTML = '<li class="history-empty">No sessions yet. Upload your first document to get started.</li>';
      return;
    }

    historyList.innerHTML = sessions
      .map((session) => {
        const label = session.input_text || `Session #${session.id || "?"}`;
        return `
          <li class="history-item">
            <p class="history-item-title">${label}</p>
            <p class="history-item-time">${formatDate(session.created_at)}</p>
          </li>
        `;
      })
      .join("");
  } catch (error) {
    historyList.innerHTML = `<li class="history-empty state-bad">Could not load history: ${error.message}</li>`;
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
      browseButton.textContent = "Generating summary...";
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
      currentSummary = result.summary;
      displaySummary(result);
      // Refresh history panel and provide visual feedback
      historyList.innerHTML = '<li class="history-empty">Updating history...</li>';
      loadHistory();
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

function displaySummary(result) {
  const safeFileName = escapeHtml(result.filename || "Uploaded file");
  const formattedSummary = formatSummaryText(result.summary);

  uploadPanel.innerHTML = `
    <h2>Summary Generated</h2>
    <div class="summary-display">
      <p class="summary-title"><strong>File:</strong> ${safeFileName}</p>
      <div class="summary-content">
        <h3>Summary</h3>
        ${formattedSummary}
      </div>
      <button class="button ghost" id="new-upload-btn" type="button">Upload Another File</button>
    </div>
  `;
  
  document.getElementById("new-upload-btn").addEventListener("click", resetUpload);
}

function resetUpload() {
  uploadPanel.innerHTML = `
    <h2>Upload Your Notes</h2>
    <div class="upload-dropzone" id="dropzone">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="17 8 12 3 7 8"></polyline>
        <line x1="12" y1="3" x2="12" y2="15"></line>
      </svg>
      <p class="upload-text">Drag and drop your PDF here</p>
      <input type="file" id="file-input" accept=".pdf,application/pdf" hidden />
      <button class="button solid" id="browse-button" type="button">Or browse files</button>
    </div>
  `;
  
  setupDropzoneListeners();
  currentSummary = null;
}

function setupDropzoneListeners() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const browseButton = document.getElementById("browse-button");
  
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

reloadHistoryButton.addEventListener("click", loadHistory);

// Defer initial history load until page is fully loaded
window.addEventListener("load", () => {
  loadHistory();
});
