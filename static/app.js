// Initialize map centered on Miami-Dade
const map = L.map("map", {
    center: [25.76, -80.19],
    zoom: 12,
    zoomControl: true,
});

L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19,
}).addTo(map);

// State
let marker = null;
let radiusCircle = null;
let contamMarkers = [];

const searchForm = document.getElementById("search-form");
const addressInput = document.getElementById("address-input");
const searchBtn = document.getElementById("search-btn");
const sidebar = document.getElementById("sidebar");
const loading = document.getElementById("loading");
const riskCard = document.getElementById("risk-card");
const closeSidebar = document.getElementById("close-sidebar");

// Search by address
searchForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const address = addressInput.value.trim();
    if (!address) return;

    searchBtn.disabled = true;
    searchBtn.textContent = "...";

    try {
        const geoRes = await fetch(`/api/geocode?address=${encodeURIComponent(address)}`);
        const geoData = await geoRes.json();

        if (geoData.error) {
            alert(geoData.error);
            return;
        }

        await queryRisk(geoData.lat, geoData.lon, address);
    } catch (err) {
        alert("Error geocoding address. Please try again.");
        console.error(err);
    } finally {
        searchBtn.disabled = false;
        searchBtn.textContent = "Search";
    }
});

// Click on map
map.on("click", async (e) => {
    const { lat, lng } = e.latlng;
    await queryRisk(lat, lng);
});

// Close sidebar
closeSidebar.addEventListener("click", () => {
    sidebar.classList.add("hidden");
});

async function queryRisk(lat, lon, address) {
    // Show sidebar and loading
    sidebar.classList.remove("hidden");
    loading.classList.remove("hidden");
    riskCard.classList.add("hidden");

    // Place marker
    clearMap();
    marker = L.marker([lat, lon], {
        icon: L.divIcon({
            className: "custom-marker",
            html: '<div style="width:14px;height:14px;background:#e63946;border:2px solid #fff;border-radius:50%;box-shadow:0 0 8px rgba(230,57,70,0.6);"></div>',
            iconSize: [14, 14],
            iconAnchor: [7, 7],
        }),
    }).addTo(map);

    // Draw 1-mile radius
    radiusCircle = L.circle([lat, lon], {
        radius: 1609,
        color: "#e63946",
        fillColor: "#e63946",
        fillOpacity: 0.05,
        weight: 1,
        dashArray: "5,5",
    }).addTo(map);

    map.setView([lat, lon], 14);

    // Query risk API
    const params = new URLSearchParams({ lat, lon });
    if (address) params.set("address", address);

    try {
        const res = await fetch(`/api/risk?${params}`);
        const data = await res.json();

        if (data.error) {
            riskCard.innerHTML = `<div class="risk-section"><p style="color:#e63946;">${data.error}</p></div>`;
        } else {
            renderRiskCard(data);
            plotContamination(data.contamination);
        }
    } catch (err) {
        riskCard.innerHTML = '<div class="risk-section"><p style="color:#e63946;">Error fetching risk data.</p></div>';
        console.error(err);
    } finally {
        loading.classList.add("hidden");
        riskCard.classList.remove("hidden");
    }
}

function clearMap() {
    if (marker) map.removeLayer(marker);
    if (radiusCircle) map.removeLayer(radiusCircle);
    contamMarkers.forEach((m) => map.removeLayer(m));
    contamMarkers = [];
}

function plotContamination(contam) {
    if (!contam || !contam.sites) return;

    contam.sites.forEach((site) => {
        if (site.lat == null || site.lon == null) return;
        const m = L.circleMarker([site.lat, site.lon], {
            radius: 5,
            color: "#f4a261",
            fillColor: "#f4a261",
            fillOpacity: 0.7,
            weight: 1,
        })
            .bindPopup(
                `<b>${site.name}</b><br>${site.address}<br>` +
                `<span style="color:#888;">${site.program} — ${site.site_status}</span><br>` +
                `${site.distance_ft ? site.distance_ft.toLocaleString() + " ft away" : ""}`
            )
            .addTo(map);
        contamMarkers.push(m);
    });
}

function renderRiskCard(data) {
    const flood = data.flood || {};
    const elev = data.elevation || {};
    const slr = data.sea_level_rise || {};
    const contam = data.contamination || {};
    const fb = data.freeboard || {};

    // Flood zone risk coloring
    const zoneClass = getZoneClass(flood.zone);
    const fbClass = fb.value_ft != null ? (fb.value_ft < 0 ? "danger" : "safe") : "";

    // SLR bar
    const levels = slr.levels_checked || {};
    let slrBarHTML = '<div class="slr-bar">';
    for (let i = 1; i <= 6; i++) {
        const key = `${i}ft`;
        const val = levels[key];
        const cls = val === true ? "wet" : val === false ? "dry" : "unknown";
        slrBarHTML += `<div class="slr-level ${cls}">${i}ft</div>`;
    }
    slrBarHTML += "</div>";

    // Contamination list
    let contamHTML = "";
    if (contam.total_count > 0) {
        const byProgram = contam.by_program || {};
        contamHTML = '<ul class="contam-list">';
        for (const [program, count] of Object.entries(byProgram)) {
            contamHTML += `<li><span class="contam-badge active">${count}</span> ${program}</li>`;
        }
        contamHTML += "</ul>";
        if (contam.nearest) {
            contamHTML += `<p style="margin-top:8px;font-size:12px;color:#888;">Nearest: ${contam.nearest.name} (${contam.nearest.distance_ft ? contam.nearest.distance_ft.toLocaleString() + " ft" : "distance unknown"})</p>`;
        }
    } else {
        contamHTML = '<p style="color:#2a9d8f;font-size:13px;">No cleanup sites found within 1 mile.</p>';
    }

    riskCard.innerHTML = `
        <div class="risk-header">
            <h2>Ground Truth</h2>
            <div class="address">${data.address || "Unknown address"}</div>
        </div>

        ${data.ai_summary ? `
        <div class="ai-summary">
            <h3>Plain English Summary</h3>
            <p>${data.ai_summary}</p>
        </div>` : ""}

        <div class="risk-section">
            <h3>Flood Zone</h3>
            <div class="risk-row">
                <span class="risk-label">FEMA Zone</span>
                <span class="risk-value ${zoneClass}">${flood.zone || "Unknown"} ${flood.risk_level ? "(" + flood.risk_level + ")" : ""}</span>
            </div>
            <div class="risk-row">
                <span class="risk-label">Base Flood Elevation</span>
                <span class="risk-value">${flood.base_flood_elevation != null ? flood.base_flood_elevation + " ft NAVD88" : "N/A"}</span>
            </div>
            <div class="risk-row">
                <span class="risk-label">Property Elevation</span>
                <span class="risk-value">${elev.elevation_ft != null ? elev.elevation_ft + " ft" : "N/A"}</span>
            </div>
            <div class="risk-row">
                <span class="risk-label">Freeboard</span>
                <span class="risk-value ${fbClass}">${fb.value_ft != null ? fb.value_ft + " ft (" + fb.status.toUpperCase() + " BFE)" : "N/A"}</span>
            </div>
        </div>

        <div class="risk-section">
            <h3>Sea Level Rise</h3>
            <div class="risk-row">
                <span class="risk-label">Inundated at</span>
                <span class="risk-value ${slr.first_inundation_ft ? "warning" : "safe"}">${slr.first_inundation_ft ? "+" + slr.first_inundation_ft + " ft" : "Not within 6ft"}</span>
            </div>
            <div class="risk-row">
                <span class="risk-label">Projected year</span>
                <span class="risk-value">${slr.projected_year || "N/A"}</span>
            </div>
            ${slrBarHTML}
        </div>

        <div class="risk-section">
            <h3>Contamination (within 1 mile)</h3>
            <div class="risk-row" style="margin-bottom:8px;">
                <span class="risk-label">Total sites</span>
                <span class="risk-value ${contam.total_count > 0 ? "warning" : "safe"}">${contam.total_count}</span>
            </div>
            ${contamHTML}
        </div>

        <div style="text-align:center;padding:8px 0;">
            <span style="color:#444;font-size:11px;">Data: FEMA &middot; FL DEP &middot; USGS &middot; NOAA &middot; AI: Anthropic Claude</span>
        </div>
    `;
}

function getZoneClass(zone) {
    if (!zone) return "";
    if (zone.startsWith("V")) return "danger";
    if (zone.startsWith("A")) return "danger";
    if (zone === "X" || zone === "C") return "safe";
    return "warning";
}
