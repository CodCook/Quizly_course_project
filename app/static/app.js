const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const browseButton = document.getElementById("browse-button");
const historyList = document.getElementById("history-list");
const reloadHistoryButton = document.getElementById("reload-history");

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

browseButton.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (file) {
    console.log("File selected:", file.name);
    // TODO: implement file upload and processing
    alert(`File selected: ${file.name}\nFile upload coming soon!`);
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
    const file = files[0];
    console.log("File dropped:", file.name);
    // TODO: implement file upload and processing
    alert(`File dropped: ${file.name}\nFile upload coming soon!`);
  }
});

reloadHistoryButton.addEventListener("click", loadHistory);

loadHistory();
