let currentScanId = null;
let pollInterval = null;

const startButton = document.getElementById("startScanButton");
const statusOutput = document.getElementById("statusOutput");
const resultsOutput = document.getElementById("resultsOutput");
const scanMessageEl = document.getElementById("scanMessage");

const statusBadge = document.getElementById("statusBadge");
const spinner = document.getElementById("spinner");

function displayMessage(message, type = "success") {
    scanMessageEl.innerText = message;
    scanMessageEl.style.display = "block";
    scanMessageEl.className = type;
}

function setButtonState(scanning) {
    startButton.disabled = scanning;
    startButton.innerText = scanning ? "Scanning..." : "Start Scan";
}

/* ---------- UX MESSAGE HELPERS ---------- */

function getStatusMessage(status) {
    switch (status) {
        case "queued":
            return "⏳ Scan queued. Preparing environment...";
        case "running":
            return "🔍 Scan in progress. Discovering hosts and ports...";
        case "completed":
            return "✅ Scan completed successfully.";
        case "failed":
            return "❌ Scan failed. Please try again or switch to Demo Mode.";
        default:
            return "ℹ️ Awaiting scan status...";
    }
}

function getModeMessage(mode) {
    switch (mode) {
        case "demo":
            return "🧪 Demo mode enabled (simulated results)";
        case "cloud":
            return "☁️ Cloud-safe mode (live scanning disabled)";
        case "live":
            return "🌐 Live network scan";
        default:
            return "";
    }
}

/* ---------- VISUAL STATUS HANDLER ---------- */

function updateVisualStatus(status) {
    statusBadge.className = "status-badge";

    switch (status) {
        case "queued":
            statusBadge.classList.add("status-queued");
            statusBadge.innerText = "Queued";
            spinner.classList.add("hidden");
            break;

        case "running":
            statusBadge.classList.add("status-running");
            statusBadge.innerText = "Running";
            spinner.classList.remove("hidden");
            break;

        case "completed":
            statusBadge.classList.add("status-completed");
            statusBadge.innerText = "Completed";
            spinner.classList.add("hidden");
            break;

        case "failed":
            statusBadge.classList.add("status-failed");
            statusBadge.innerText = "Failed";
            spinner.classList.add("hidden");
            break;

        default:
            statusBadge.classList.add("status-idle");
            statusBadge.innerText = "Idle";
            spinner.classList.add("hidden");
    }
}

/* ---------- SAFE RESPONSE PARSER ---------- */

async function safeParseJSON(response) {
    const text = await response.text();
    try {
        return JSON.parse(text);
    } catch {
        return { raw: text };
    }
}

async function startScan() {
    scanMessageEl.style.display = "none";
    resultsOutput.innerText = "";
    statusOutput.innerText = "";

    updateVisualStatus("queued");
    setButtonState(true);

    const ipRange = document.getElementById("ipRange").value.trim();
    const gateway = document.getElementById("gateway").value.trim();
    const portsInput = document.getElementById("ports").value;
    const demoMode = document.getElementById("demoMode").checked;

    if (!ipRange) {
        displayMessage("IP range is required", "error");
        setButtonState(false);
        updateVisualStatus("failed");
        return;
    }

    const ports = portsInput
        .split(",")
        .map(p => parseInt(p.trim()))
        .filter(p => Number.isInteger(p) && p > 0 && p <= 65535);

    try {
        const response = await fetch("/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ip_range: ipRange,
                gateway: gateway || null,
                ports: ports.length ? ports : [22, 80, 443],
                demo: demoMode
            })
        });

        const data = await safeParseJSON(response);

        if (!response.ok) {
            const msg =
                data.detail ||
                data.message ||
                data.raw ||
                "Internal server error";
            throw new Error(msg);
        }

        currentScanId = data.scan_id;
        displayMessage(`Scan started (ID ${currentScanId})`);
        pollInterval = setInterval(fetchResults, 3000);

    } catch (err) {
        displayMessage(err.message, "error");
        setButtonState(false);
        updateVisualStatus("failed");
    }
}

async function fetchResults() {
    if (!currentScanId) return;

    try {
        const response = await fetch(`/results/${currentScanId}`);
        const data = await safeParseJSON(response);

        if (!response.ok) {
            throw new Error(
                data.detail || data.raw || "Failed to fetch results"
            );
        }

        /* Visual status update */
        updateVisualStatus(data.status);

        const statusMessage = getStatusMessage(data.status);
        const modeMessage = getModeMessage(data.mode);

        statusOutput.innerText = JSON.stringify(
            {
                status: data.status,
                message: statusMessage,
                mode: data.mode,
                mode_info: modeMessage,
                gateway: data.gateway,
                created_at: data.created_at
            },
            null,
            2
        );

        resultsOutput.innerText = JSON.stringify(
            data.results || [],
            null,
            2
        );

        if (data.status === "completed" || data.status === "failed") {
            clearInterval(pollInterval);
            setButtonState(false);
        }

    } catch (err) {
        clearInterval(pollInterval);
        setButtonState(false);
        updateVisualStatus("failed");
        displayMessage(err.message, "error");
    }
}
