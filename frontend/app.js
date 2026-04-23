/**
 * app.js — RAG Text-to-SQL Query Generator Frontend Logic
 *
 * Responsibilities:
 * - Capture user natural language query
 * - Send POST request to Flask backend (/query)
 * - Display generated SQL with syntax highlighting
 * - Render results in a dynamic table
 * - Handle loading states and errors gracefully
 */

// -------------------------------------------------------
// Constants
// -------------------------------------------------------

const API_URL = "http://localhost:5000/query";

// -------------------------------------------------------
// DOM References (cached on load)
// -------------------------------------------------------

const queryInput   = document.getElementById("query-input");
const submitBtn    = document.getElementById("submit-btn");
const btnText      = document.getElementById("btn-text");
const btnIcon      = document.getElementById("btn-icon");
const btnSpinner   = document.getElementById("btn-spinner");
const statusBar    = document.getElementById("status-bar");
const statusMsg    = document.getElementById("status-msg");
const resultsSection = document.getElementById("results-section");
const sqlOutput    = document.getElementById("sql-output");
const resultsTable = document.getElementById("results-table");
const rowCountBadge = document.getElementById("row-count-badge");
const chartBlock   = document.getElementById("chart-block");
const chartCanvas  = document.getElementById("results-chart");

let currentChart = null;

// -------------------------------------------------------
// Utility Functions
// -------------------------------------------------------

/**
 * Highlights SQL keywords in a query string with span tags.
 * @param {string} sql - The raw SQL string.
 * @returns {string} HTML string with keyword spans.
 */
function highlightSQL(sql) {
  const keywords = [
    "SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN",
    "INNER JOIN", "ON", "ORDER BY", "GROUP BY", "HAVING", "LIMIT",
    "OFFSET", "AS", "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN",
    "COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT", "NULL",
    "IS NULL", "IS NOT NULL", "DESC", "ASC", "UNION", "CASE",
    "WHEN", "THEN", "ELSE", "END"
  ];

  let highlighted = sql;

  // Sort by length (longest first) to avoid partial replacements
  keywords.sort((a, b) => b.length - a.length);

  keywords.forEach(kw => {
    const regex = new RegExp(`\\b(${kw})\\b`, "gi");
    highlighted = highlighted.replace(
      regex,
      `<span style="color:#ff7b72;font-weight:600">$1</span>`
    );
  });

  // Highlight strings in single quotes
  highlighted = highlighted.replace(
    /'([^']*)'/g,
    `<span style="color:#a5d6ff">'$1'</span>`
  );

  // Highlight numbers
  highlighted = highlighted.replace(
    /\b(\d+\.?\d*)\b/g,
    `<span style="color:#79c0ff">$1</span>`
  );

  return highlighted;
}

/**
 * Shows the status bar with a given message and type.
 * @param {string} message - Status message to display.
 * @param {'loading'|'error'} type - Visual style type.
 */
function showStatus(message, type = "loading") {
  statusBar.className = type;
  statusMsg.textContent = message;
  statusBar.style.display = "flex";
}

/** Hides the status bar. */
function hideStatus() {
  statusBar.style.display = "none";
  statusMsg.textContent = "";
}

/**
 * Sets the button to loading state (disabled, spinner visible).
 * @param {boolean} isLoading
 */
function setLoadingState(isLoading) {
  submitBtn.disabled = isLoading;
  btnSpinner.style.display = isLoading ? "block" : "none";
  btnIcon.style.display = isLoading ? "none" : "block";
  btnText.textContent = isLoading ? "Generating..." : "Run Query";
}

/**
 * Builds a dynamic HTML table from an array of result objects.
 * @param {Array<Object>} results - Array of row objects.
 */
function renderTable(results) {
  resultsTable.innerHTML = "";

  if (!results || results.length === 0) {
    resultsTable.innerHTML = `
      <tbody>
        <tr>
          <td>
            <div class="no-results">
              <span class="no-icon">📭</span>
              <span>No rows returned for this query.</span>
            </div>
          </td>
        </tr>
      </tbody>`;
    rowCountBadge.textContent = "0 rows";
    return;
  }

  const columns = Object.keys(results[0]);

  // Build thead
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  columns.forEach(col => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  resultsTable.appendChild(thead);

  // Build tbody
  const tbody = document.createElement("tbody");
  results.forEach(row => {
    const tr = document.createElement("tr");
    columns.forEach(col => {
      const td = document.createElement("td");
      const val = row[col];
      if (val === null || val === undefined) {
        td.innerHTML = `<span class="null-val">NULL</span>`;
      } else {
        td.textContent = val;
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  resultsTable.appendChild(tbody);

  rowCountBadge.textContent = `${results.length} row${results.length !== 1 ? "s" : ""}`;
}

/**
 * Detects chartable data and renders a Chart.js visualization.
 * It alternates between 'pie' and 'bar' based on size.
 */
function renderChart(results) {
  // Hide chart block by default
  if (!chartBlock) return;
  chartBlock.style.display = "none";
  
  if (currentChart) {
    currentChart.destroy();
    currentChart = null;
  }

  if (!results || results.length === 0 || results.length > 50) {
    return; // Don't chart empty or massive datasets
  }

  const columns = Object.keys(results[0]);
  if (columns.length < 2) return;

  // Attempt to map X to string and Y to number robustly
  let labelCol = null;
  let dataCol = null;

  for (const col of columns) {
    const val = results[0][col];
    const isNum = val !== null && val !== "" && !isNaN(parseFloat(val));
    const colLower = col.toLowerCase();

    // Prefer non-ID, non-date numerical columns for the Y-Axis
    if (isNum && !dataCol && !colLower.includes("id") && !colLower.includes("date")) {
      dataCol = col;
    } 
    // Prefer non-numeric strings for the X-Axis label
    else if (!isNum && !labelCol) {
      labelCol = col;
    }
  }

  // Fallbacks if optimal columns weren't found
  if (!labelCol) labelCol = columns[0];
  if (!dataCol && columns.length > 1) dataCol = columns[1];
  if (!dataCol) return; // Cannot chart without a second column

  // Verify the data column actually contains something we can parse as a number
  const isDataNumeric = results.some(row => row[dataCol] !== null && !isNaN(parseFloat(row[dataCol])));
  if (!isDataNumeric) return; // Cannot chart non-numeric

  // Extract
  const labels = results.map(row => row[labelCol] || "Unknown");
  const data = results.map(row => parseFloat(row[dataCol]) || 0);

  // Decide chart type: pie for <= 7 items, bar for > 7
  const chartType = results.length <= 7 ? 'pie' : 'bar';

  chartBlock.style.display = "block";

  currentChart = new Chart(chartCanvas, {
    type: chartType,
    data: {
      labels: labels,
      datasets: [{
        label: dataCol,
        data: data,
        backgroundColor: [
          'rgba(88, 166, 255, 0.7)',
          'rgba(163, 113, 247, 0.7)',
          'rgba(63, 185, 80, 0.7)',
          'rgba(248, 81, 73, 0.7)',
          'rgba(210, 153, 34, 0.7)',
          'rgba(238, 130, 238, 0.7)',
          'rgba(255, 165, 0, 0.7)'
        ],
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#e6edf3' },
          position: chartType === 'pie' ? 'right' : 'top'
        }
      },
      scales: chartType === 'bar' ? {
        y: { ticks: { color: '#8b949e' }, grid: { color: '#30363d' } },
        x: { ticks: { color: '#8b949e' }, grid: { display: false } }
      } : {}
    }
  });
}

/**
 * Copies text to the clipboard and briefly updates button label.
 * @param {string} text - Text to copy.
 * @param {HTMLElement} btn - The copy button element.
 */
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = "✓ Copied!";
    setTimeout(() => (btn.textContent = original), 1800);
  });
}

// -------------------------------------------------------
// Core: Submit Query
// -------------------------------------------------------

/**
 * Main handler: sends user query to backend and renders results.
 */
async function submitQuery() {
  const query = queryInput.value.trim();

  // Validate input
  if (!query) {
    queryInput.focus();
    queryInput.style.borderColor = "var(--accent-red)";
    setTimeout(() => (queryInput.style.borderColor = ""), 1200);
    return;
  }

  // Reset UI state
  hideStatus();
  resultsSection.style.display = "none";
  setLoadingState(true);
  showStatus("🔍 Retrieving schema context via RAG...", "loading");

  try {
    // Simulate brief loading step for UX clarity
    await new Promise(r => setTimeout(r, 400));
    statusMsg.textContent = "🤖 Generating SQL with Gemini...";

    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      // Show error details
      const errMsg = data.error || "Unknown error from server.";
      const hint   = data.hint ? `\n💡 ${data.hint}` : "";
      showStatus(`❌ ${errMsg}${hint}`, "error");

      // If we still got a SQL query back, show it
      if (data.generated_sql) {
        sqlOutput.innerHTML = highlightSQL(data.generated_sql);
        renderTable([]);
        resultsSection.style.display = "flex";
      }
      return;
    }

    // Success — hide status and render results
    hideStatus();

    // Render SQL
    sqlOutput.innerHTML = highlightSQL(data.generated_sql);

    // Store SQL for copy button
    sqlOutput.dataset.raw = data.generated_sql;

    // Render results table & chart
    renderTable(data.results);
    renderChart(data.results);

    // Show the results section
    resultsSection.style.display = "flex";

    // Smooth scroll to results
    setTimeout(() => {
      resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);

  } catch (err) {
    console.error("[app.js] Fetch error:", err);
    showStatus(
      "❌ Cannot connect to backend. Is Flask running on http://localhost:5000?",
      "error"
    );
  } finally {
    setLoadingState(false);
  }
}

// -------------------------------------------------------
// Event Listeners
// -------------------------------------------------------

// Submit button click
submitBtn.addEventListener("click", submitQuery);

// Enter key (Ctrl+Enter or Cmd+Enter in textarea)
queryInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    submitQuery();
  }
});

// Copy SQL button
document.getElementById("copy-sql-btn").addEventListener("click", () => {
  const rawSql = sqlOutput.dataset.raw || sqlOutput.textContent;
  copyToClipboard(rawSql, document.getElementById("copy-sql-btn"));
});

// Example query chips
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    queryInput.value = chip.dataset.query;
    queryInput.focus();
  });
});

// -------------------------------------------------------
// Initialize
// -------------------------------------------------------

// Focus input on page load
window.addEventListener("load", () => {
  queryInput.focus();
  console.log("[app.js] RAG Text-to-SQL frontend initialized.");
  console.log("[app.js] Backend URL:", API_URL);
});
