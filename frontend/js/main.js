const API_BASE = "http://127.0.0.1:5000/api";

// ---------- Health check ----------
fetch(`${API_BASE}/health`)
  .then((res) => res.json())
  .then(() => {
    document.getElementById("statusDot").classList.add("online");
    document.getElementById("statusText").innerText = "All systems ready";
  })
  .catch(() => {
    document.getElementById("statusDot").classList.add("offline");
    document.getElementById("statusText").innerText = "Backend offline";
  });

// ---------- Toast notifications ----------
function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);

  // Auto-remove after 3 seconds
  setTimeout(() => toast.remove(), 3000);
}
// Generates skeleton placeholder HTML while real data is loading.
// count = how many skeleton rows/cards to show (mimics expected content length)
function skeletonList(count = 3) {
  return Array(count).fill(`
    <div class="skeleton-card">
      <div class="skeleton skeleton-line short"></div>
      <div class="skeleton skeleton-line" style="width: 90%;"></div>
    </div>
  `).join("");
}
function emptyState(icon, title, subtitle) {
  return `
    <div class="empty-state">
      <span class="empty-state-icon">${icon}</span>
      <p class="empty-state-title">${title}</p>
      <p class="empty-state-subtitle">${subtitle}</p>
    </div>
  `;
}

// ---------- Tab switching ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ---------- Upload PDF ----------
document.getElementById("uploadPdfBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("pdfInput");
  const file = fileInput.files[0];

  if (!file) {
    showToast("Please choose a PDF file first", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  const btn = document.getElementById("uploadPdfBtn");
  btn.disabled = true;
  btn.innerText = "Uploading...";

  try {
    const res = await fetch(`${API_BASE}/notes/upload-pdf`, {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Upload failed");
    }

    showToast(`"${data.title}" uploaded successfully`, "success");
    fileInput.value = "";
    loadNotes();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Upload PDF";
  }
});

// ---------- Upload Text ----------
document.getElementById("uploadTextBtn").addEventListener("click", async () => {
  const title = document.getElementById("textTitle").value.trim();
  const content = document.getElementById("textContent").value.trim();

  const btn = document.getElementById("uploadTextBtn");
  btn.disabled = true;
  btn.innerText = "Saving...";

  try {
    const res = await fetch(`${API_BASE}/notes/upload-text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Save failed");
    }

    showToast(`"${data.title}" saved successfully`, "success");
    document.getElementById("textTitle").value = "";
    document.getElementById("textContent").value = "";
    loadNotes();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Save Note";
  }
});

// ---------- Load & display notes ----------
async function loadNotes() {
  const notesList = document.getElementById("notesList");
  notesList.innerHTML = skeletonList(3);   // show placeholders while fetching

  try {
    const res = await fetch(`${API_BASE}/notes`);
    const data = await res.json();

    if (data.notes.length === 0) {
      notesList.innerHTML = emptyState("📭", "No notes yet", "Upload a PDF or paste text above to get started.");
      return;
    }
    // Refresh the Q&A dropdown too, so new notes appear there immediately
    const select = document.getElementById("noteSelect");
    select.innerHTML = '<option value="">All Notes</option>';
    data.notes.forEach((note) => {
      const option = document.createElement("option");
      option.value = note.id;
      option.textContent = note.title;
      select.appendChild(option);
    });
    // Refresh the Summary dropdown too
    populateSummaryDropdown();
    populateQuizDropdown();
    notesList.innerHTML = data.notes.map((note) => `
      <div class="note-item">
        <div>
          <h4>${note.title}</h4>
          <span>${note.source_type.toUpperCase()} • ${new Date(note.created_at).toLocaleString()}</span>
        </div>
        <button class="delete-btn" onclick="deleteNoteItem(${note.id})">Delete</button>
      </div>
    `).join("");
    loadDashboardStats();
  } catch (err) {
    notesList.innerHTML = "<p>Failed to load notes.</p>";
  }
}

// Load notes on page load
loadNotes();
// ---------- Populate note dropdown for Q&A ----------
async function populateNoteDropdown() {
  const select = document.getElementById("noteSelect");

  try {
    const res = await fetch(`${API_BASE}/notes`);
    const data = await res.json();

    // Keep the "All Notes" option, add one option per note
    data.notes.forEach((note) => {
      const option = document.createElement("option");
      option.value = note.id;
      option.textContent = note.title;
      select.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load notes for dropdown", err);
  }
}

// ---------- Ask a question ----------
document.getElementById("askBtn").addEventListener("click", async () => {
  const question = document.getElementById("questionInput").value.trim();
  const noteId = document.getElementById("noteSelect").value;

  if (!question) {
    showToast("Please type a question first", "error");
    return;
  }

  const btn = document.getElementById("askBtn");
  const answerBox = document.getElementById("answerBox");
  const answerText = document.getElementById("answerText");
  const answerMeta = document.getElementById("answerMeta");

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Thinking...';
  answerBox.style.display = "none";

  try {
    const res = await fetch(`${API_BASE}/qa/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        note_id: noteId ? parseInt(noteId) : null
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to get an answer");
    }

    answerText.innerText = data.answer;
    answerMeta.innerText = `Based on ${data.sources_used} matching section(s) from your notes`;
    answerBox.style.display = "block";
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Ask";
  }
});

// Populate dropdown once the page loads
populateNoteDropdown();
// ---------- Summarize feature state ----------
let selectedSummaryType = "short";

// Populate the summary note dropdown (separate from Q&A dropdown for clarity)
async function populateSummaryDropdown() {
  const select = document.getElementById("summaryNoteSelect");

  try {
    const res = await fetch(`${API_BASE}/notes`);
    const data = await res.json();

    select.innerHTML = '<option value="">Select a note...</option>';
    data.notes.forEach((note) => {
      const option = document.createElement("option");
      option.value = note.id;
      option.textContent = note.title;
      select.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load notes for summary dropdown", err);
  }
}

// Summary type button switching (Short / Detailed / Bullet)
document.querySelectorAll(".summary-type-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".summary-type-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    selectedSummaryType = btn.dataset.type;
  });
});

// Generate summary
document.getElementById("generateSummaryBtn").addEventListener("click", async () => {
  const noteId = document.getElementById("summaryNoteSelect").value;

  if (!noteId) {
    showToast("Please select a note first", "error");
    return;
  }

  const btn = document.getElementById("generateSummaryBtn");
  const summaryBox = document.getElementById("summaryBox");
  const summaryText = document.getElementById("summaryText");

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating...';
  summaryBox.style.display = "none";

  try {
    const res = await fetch(`${API_BASE}/summary/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        note_id: parseInt(noteId),
        summary_type: selectedSummaryType
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to generate summary");
    }

    summaryText.innerText = data.summary;
    summaryBox.style.display = "block";
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Generate Summary";
  }
});

// Populate summary dropdown on page load
populateSummaryDropdown();
// ---------- Quiz feature ----------
let currentQuizQuestions = [];   // stores the quiz so we can check answers/score later
let userAnswers = {};            // tracks what the user selected/typed per question

async function populateQuizDropdown() {
  const select = document.getElementById("quizNoteSelect");

  try {
    const res = await fetch(`${API_BASE}/notes`);
    const data = await res.json();

    select.innerHTML = '<option value="">Select a note...</option>';
    data.notes.forEach((note) => {
      const option = document.createElement("option");
      option.value = note.id;
      option.textContent = note.title;
      select.appendChild(option);
    });
  } catch (err) {
    console.error("Failed to load notes for quiz dropdown", err);
  }
}

document.getElementById("generateQuizBtn").addEventListener("click", async () => {
  const noteId = document.getElementById("quizNoteSelect").value;
  const questionType = document.getElementById("quizTypeSelect").value;
  const difficulty = document.getElementById("quizDifficultySelect").value;

  if (!noteId) {
    showToast("Please select a note first", "error");
    return;
  }

  const btn = document.getElementById("generateQuizBtn");
  const container = document.getElementById("quizContainer");

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating quiz...';
  container.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/quiz/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        note_id: parseInt(noteId),
        question_type: questionType,
        difficulty: difficulty,
        num_questions: 5
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to generate quiz");
    }

    currentQuizQuestions = data.questions;
    userAnswers = {};
    renderQuiz(currentQuizQuestions);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Generate Quiz";
  }
});

function renderQuiz(questions) {
  const container = document.getElementById("quizContainer");

  container.innerHTML = questions.map((q, index) => {
    if (q.type === "mcq") {
      return `
        <div class="quiz-question" data-index="${index}">
          <h4>Q${index + 1}. ${q.question}</h4>
          ${q.options.map((opt) => `
            <button class="quiz-option" data-option="${escapeHtml(opt)}" onclick="selectOption(${index}, this)">
              ${opt}
            </button>
          `).join("")}
          <button class="check-answer-btn" onclick="checkAnswer(${index})">Check Answer</button>
          <div class="quiz-explanation" id="explanation-${index}"></div>
        </div>
      `;
    } else {
      // short_answer
      return `
        <div class="quiz-question" data-index="${index}">
          <h4>Q${index + 1}. ${q.question}</h4>
          <input type="text" id="answer-input-${index}" placeholder="Type your answer..." />
          <button class="check-answer-btn" onclick="checkAnswer(${index})">Check Answer</button>
          <div class="quiz-explanation" id="explanation-${index}"></div>
        </div>
      `;
    }
  }).join("") + `
    <button id="submitQuizBtn" onclick="showFinalScore()">Finish Quiz & See Score</button>
    <div id="quizScoreBox"></div>
  `;
}

// Small helper to avoid breaking HTML if a question contains quotes/symbols
function escapeHtml(text) {
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

// Called when user clicks an MCQ option
function selectOption(index, buttonEl) {
  const question = currentQuizQuestions[index];
  const container = buttonEl.closest(".quiz-question");

  container.querySelectorAll(".quiz-option").forEach((btn) => btn.classList.remove("selected"));
  buttonEl.classList.add("selected");

  userAnswers[index] = buttonEl.dataset.option;
}

// Called when user clicks "Check Answer" on any question
function checkAnswer(index) {
  const question = currentQuizQuestions[index];
  const explanationBox = document.getElementById(`explanation-${index}`);

  if (question.type === "mcq") {
    const container = document.querySelector(`.quiz-question[data-index="${index}"]`);
    const selected = userAnswers[index];

    if (!selected) {
      showToast("Please select an option first", "error");
      return;
    }

    container.querySelectorAll(".quiz-option").forEach((btn) => {
      if (btn.dataset.option === question.correct_answer) {
        btn.classList.add("correct");
      } else if (btn.dataset.option === selected && selected !== question.correct_answer) {
        btn.classList.add("incorrect");
      }
    });
  } else {
    // short_answer - user self-grades by comparing to the model answer
    const inputEl = document.getElementById(`answer-input-${index}`);
    userAnswers[index] = inputEl.value.trim();

    if (!userAnswers[index]) {
      showToast("Please type an answer first", "error");
      return;
    }
  }

  explanationBox.innerHTML = `
    <strong>Correct answer:</strong> ${question.correct_answer}<br/>
    <strong>Explanation:</strong> ${question.explanation}
  `;
  explanationBox.style.display = "block";
}

// Shows a simple completion message (full auto-grading for short-answer
// would need another AI call - keeping this simple and honest for now)
function showFinalScore() {
  const total = currentQuizQuestions.length;
  const answered = Object.keys(userAnswers).length;

  const scoreBox = document.getElementById("quizScoreBox");
  scoreBox.innerHTML = `
    <div class="quiz-score">
      You answered ${answered} out of ${total} questions.
      Review the explanations above to check your understanding!
    </div>
  `;
}

// Populate quiz dropdown on page load
populateQuizDropdown();
// ---------- Study Timetable feature ----------
let subjectCount = 0;

function addSubjectRow() {
  subjectCount++;
  const list = document.getElementById("subjectsList");

  const row = document.createElement("div");
  row.className = "subject-row";
  row.innerHTML = `
    <input type="text" class="subject-name" placeholder="Subject (e.g. Math)" />
    <input type="date" class="subject-exam-date" />
    <select class="subject-priority">
      <option value="low">Low</option>
      <option value="medium" selected>Medium</option>
      <option value="high">High</option>
    </select>
    <button type="button" class="remove-subject-btn" onclick="this.parentElement.remove()">✕</button>
  `;

  list.appendChild(row);
}

document.getElementById("addSubjectBtn").addEventListener("click", addSubjectRow);

// Start with 2 empty subject rows so the form doesn't look empty
addSubjectRow();
addSubjectRow();

document.getElementById("generateTimetableBtn").addEventListener("click", async () => {
  // Collect all subject rows into a clean array
  const rows = document.querySelectorAll(".subject-row");
  const subjects = [];

  rows.forEach((row) => {
    const name = row.querySelector(".subject-name").value.trim();
    const examDate = row.querySelector(".subject-exam-date").value;
    const priority = row.querySelector(".subject-priority").value;

    if (name && examDate) {
      subjects.push({ name, exam_date: examDate, priority });
    }
  });

  const hoursPerDay = parseFloat(document.getElementById("hoursPerDay").value);

  if (subjects.length === 0) {
    showToast("Please fill in at least one subject with a name and exam date", "error");
    return;
  }

  if (!hoursPerDay || hoursPerDay <= 0) {
    showToast("Please enter valid study hours per day", "error");
    return;
  }

  const btn = document.getElementById("generateTimetableBtn");
  const resultBox = document.getElementById("timetableResult");

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating...';
  resultBox.innerHTML = "";

  try {
    const res = await fetch(`${API_BASE}/timetable/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subjects, hours_per_day: hoursPerDay })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to generate timetable");
    }

    renderTimetable(data.schedule);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Generate Timetable";
  }
});

function renderTimetable(schedule) {
  const resultBox = document.getElementById("timetableResult");

  if (schedule.length === 0) {
    resultBox.innerHTML = "<p>No schedule could be generated.</p>";
    return;
  }

  resultBox.innerHTML = schedule.map((day) => `
    <div class="timetable-day">
      <h4>${day.day_name}, ${day.date}</h4>
      ${day.allocations.map((a) => `
        <div class="timetable-allocation">
          <span>${a.subject}</span>
          <span class="hours-badge">${a.hours} hrs</span>
        </div>
      `).join("")}
    </div>
  `).join("");
}
// ---------- Assignment Reminders feature ----------

document.getElementById("addAssignmentBtn").addEventListener("click", async () => {
  const title = document.getElementById("assignmentTitle").value.trim();
  const subject = document.getElementById("assignmentSubject").value.trim();
  const dueDate = document.getElementById("assignmentDueDate").value;

  if (!title || !subject || !dueDate) {
    showToast("Please fill in all fields", "error");
    return;
  }

  const btn = document.getElementById("addAssignmentBtn");
  btn.disabled = true;
  btn.innerText = "Adding...";

  try {
    const res = await fetch(`${API_BASE}/assignments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, subject, due_date: dueDate })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Failed to add assignment");
    }

    showToast("Assignment added", "success");
    document.getElementById("assignmentTitle").value = "";
    document.getElementById("assignmentSubject").value = "";
    document.getElementById("assignmentDueDate").value = "";
    loadAssignments();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.innerText = "Add Assignment";
  }
});

async function loadAssignments() {
  const list = document.getElementById("assignmentsList");
  list.innerHTML = skeletonList(3);   // show placeholders while fetching

  try {
    const res = await fetch(`${API_BASE}/assignments`);
    const data = await res.json();

    if (data.assignments.length === 0) {
      list.innerHTML = emptyState("🎉", "All clear!", "No assignments yet — add one above to start tracking deadlines.");
      return;
    }

    const urgencyLabels = {
      overdue: "Overdue",
      due_soon: "Due Soon",
      upcoming: "Upcoming",
      completed: "Completed"
    };

    list.innerHTML = data.assignments.map((a) => `
      <div class="assignment-item ${a.urgency}">
        <div class="assignment-info">
          <h4>${a.title}
            <span class="urgency-tag ${a.urgency}">${urgencyLabels[a.urgency]}</span>
          </h4>
          <span>${a.subject} • Due ${a.due_date}</span>
        </div>
        <div class="assignment-actions">
          ${a.status === "pending"
            ? `<button class="complete-btn" onclick="toggleAssignmentStatus(${a.id}, 'completed')">Mark Done</button>`
            : `<button class="undo-btn" onclick="toggleAssignmentStatus(${a.id}, 'pending')">Undo</button>`
          }
          <button class="delete-btn" onclick="deleteAssignmentItem(${a.id})">Delete</button>
        </div>
      </div>
    `).join("");
    loadDashboardStats();
  } catch (err) {
    list.innerHTML = "<p>Failed to load assignments.</p>";
  }
}

async function toggleAssignmentStatus(id, newStatus) {
  try {
    const res = await fetch(`${API_BASE}/assignments/${id}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });

    if (!res.ok) throw new Error("Failed to update assignment");

    loadAssignments();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function deleteAssignmentItem(id) {
  try {
    const res = await fetch(`${API_BASE}/assignments/${id}`, { method: "DELETE" });

    if (!res.ok) throw new Error("Failed to delete assignment");

    showToast("Assignment deleted", "success");
    loadAssignments();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Load assignments on page load
loadAssignments();
async function deleteNoteItem(noteId) {
  if (!confirm("Delete this note? This can't be undone.")) return;

  try {
    const res = await fetch(`${API_BASE}/notes/${noteId}`, { method: "DELETE" });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Failed to delete note");

    showToast("Note deleted", "success");
    loadNotes();
  } catch (err) {
    showToast(err.message, "error");
  }
}
// ============ PAGE NAVIGATION ============
function navigateTo(pageName) {
  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.getElementById(`page-${pageName}`).classList.add("active");

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.page === pageName);
  });

  // Close mobile sidebar after navigating
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebarOverlay").classList.remove("open");

  window.scrollTo(0, 0);
}

// Sidebar nav buttons
document.querySelectorAll(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => navigateTo(btn.dataset.page));
});

// Dashboard feature cards also navigate
document.querySelectorAll(".feature-card").forEach((card) => {
  card.addEventListener("click", () => navigateTo(card.dataset.page));
});

// ============ MOBILE SIDEBAR TOGGLE ============
document.getElementById("hamburgerBtn").addEventListener("click", () => {
  document.getElementById("sidebar").classList.add("open");
  document.getElementById("sidebarOverlay").classList.add("open");
});

document.getElementById("sidebarOverlay").addEventListener("click", () => {
  document.getElementById("sidebar").classList.remove("open");
  document.getElementById("sidebarOverlay").classList.remove("open");
});

// ============ DARK / LIGHT MODE ============
function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  document.getElementById("themeIcon").innerText = theme === "dark" ? "☀️" : "🌙";
  document.getElementById("themeLabel").innerText = theme === "dark" ? "Light Mode" : "Dark Mode";
  localStorage.setItem("theme", theme);
}

document.getElementById("themeToggleBtn").addEventListener("click", () => {
  const current = document.body.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark");
});

// Load saved theme preference (or default to light)
applyTheme(localStorage.getItem("theme") || "light");

// ============ DASHBOARD STATS ============
async function loadDashboardStats() {
  document.getElementById("statNotesCount").innerHTML = '<span class="skeleton skeleton-stat"></span>';
  document.getElementById("statPendingCount").innerHTML = '<span class="skeleton skeleton-stat"></span>';
  document.getElementById("statDueSoonCount").innerHTML = '<span class="skeleton skeleton-stat"></span>';

  try {
    const [notesRes, assignmentsRes] = await Promise.all([
      fetch(`${API_BASE}/notes`),
      fetch(`${API_BASE}/assignments`)
    ]);

    const notesData = await notesRes.json();
    const assignmentsData = await assignmentsRes.json();

    document.getElementById("statNotesCount").innerText = notesData.notes.length;

    const pending = assignmentsData.assignments.filter((a) => a.status === "pending");
    const dueSoonOrOverdue = pending.filter((a) => a.urgency === "due_soon" || a.urgency === "overdue");

    document.getElementById("statPendingCount").innerText = pending.length;
    document.getElementById("statDueSoonCount").innerText = dueSoonOrOverdue.length;
  } catch (err) {
    console.error("Failed to load dashboard stats", err);
  }
}

loadDashboardStats();