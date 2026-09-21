const API_URL = "http://127.0.0.1:8000/api/v1";

// FAIL-PROOF GPS LOGIC
function getGPSLocation() {
    const latInput = document.getElementById("latitude");
    const lonInput = document.getElementById("longitude");
    
    latInput.value = "Fetching...";
    lonInput.value = "Fetching...";

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                latInput.value = pos.coords.latitude.toFixed(6);
                lonInput.value = pos.coords.longitude.toFixed(6);
            },
            (err) => { 
                alert("GPS blocked or taking too long. Auto-filling test coordinates!");
                latInput.value = "27.7172";
                lonInput.value = "85.3240";
            },
            { timeout: 5000 }
        );
    } else {
        latInput.value = "27.7172";
        lonInput.value = "85.3240";
    }
}

// Form Submission with Media
async function handleFormSubmit(event) {
    event.preventDefault();
    const submitBtn = document.getElementById("submitBtn");
    submitBtn.innerText = "Transmitting...";

    const payload = {
        disaster_type: document.getElementById("disaster_type").value,
        latitude: parseFloat(document.getElementById("latitude").value),
        longitude: parseFloat(document.getElementById("longitude").value),
        description: document.getElementById("description").value
    };

    const fileInput = document.getElementById("media_upload");
    const formData = new FormData();
    formData.append("payload", JSON.stringify(payload));
    if (fileInput.files.length > 0) {
        formData.append("media", fileInput.files[0]);
    }

    try {
        await fetch(`${API_URL}/report/submit`, { method: "POST", body: formData });
        submitBtn.innerText = "Transmit Emergency Report";
        document.getElementById("citizenForm").reset();
        fetchLiveFeed();
    } catch (err) {
        alert("Server error. Ensure backend is running.");
        submitBtn.innerText = "Transmit Emergency Report";
    }
}

// LIVE TIME CALCULATOR
function timeSince(dateString) {
    const date = new Date(dateString);
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return "Just now";
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

// Live Transparency Feed
async function fetchLiveFeed() {
    try {
        const res = await fetch(`${API_URL}/reports`);
        const data = await res.json();
        const container = document.getElementById("feedContainer");
        container.innerHTML = "";

        if (!data.reports || data.reports.length === 0) {
            container.innerHTML = '<p style="color: #94a3b8;">No active emergencies logged.</p>';
            return;
        }

        data.reports.forEach(r => {
            let badgeColor = "#eab308"; // Yellow
            let displayStatus = r.status.replace("_", " ");
            let timeDisplay = `🕒 ${timeSince(r.timestamp)}`;

            if (r.status === "UNITS_DEPLOYED") {
                badgeColor = "#3b82f6"; // Blue
            } else if (r.status === "RESOLVED") {
                badgeColor = "#22c55e"; // Green
                displayStatus = "✅ RESOLVED";
                timeDisplay = "Issue Solved";
            }

            const div = document.createElement("div");
            div.className = "feed-item";
            if (r.status === "RESOLVED") {
                div.style.borderLeft = "4px solid #22c55e";
            }

            div.innerHTML = `
                <span class="time-elapsed">${timeDisplay}</span>
                <span class="status-badge" style="background:${badgeColor}; color:${r.status === 'AWAITING_REVIEW' ? 'black' : 'white'};">${displayStatus}</span>
                <h4 style="margin: 8px 0;">${r.user_input.disaster_type}</h4>
                <p style="font-size: 0.9rem; color: #cbd5e1;">${r.user_input.description}</p>
                <div style="font-size: 0.8rem; color: #38bdf8; margin-top: 6px;">📍 GPS: [${r.user_input.latitude}, ${r.user_input.longitude}] | ID: ${r.report_id}</div>
                <div class="gov-note"><strong>🏛️ Gov Response:</strong> ${r.gov_response}</div>
            `;
            container.appendChild(div);
        });
    } catch (err) {
        console.error("Feed error:", err);
    }
}

// Initial fetch and periodic polling
setInterval(fetchLiveFeed, 10000);
fetchLiveFeed();