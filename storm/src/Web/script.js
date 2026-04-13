// ============================
// REAL-TIME FORECAST + HISTORY
// ============================
document.addEventListener("DOMContentLoaded", function() {

    const updateBtn = document.getElementById("updateBtn");
    const loader = document.getElementById("loader");
    const stormValueElement = document.querySelector(".value");
    const lastUpdatedElement = document.getElementById("lastUpdated");
    const consoleBox = document.getElementById("backendConsole");

    const historyContent = document.getElementById("historyContent");

    

    // -------------------------
    // LOAD HISTORY FUNCTION
    // -------------------------
    function loadHistory() {
        fetch("history.php")
            .then(res => res.text())
            .then(data => {
                if (historyContent) {
                    historyContent.innerHTML = data;
                }
            })
            .catch(err => {
                console.error("History load failed:", err);
            });
    }

    fetch("forecast/output_pred.csv")
        .then(response => response.text())
        .then(text => {
            const lines = text.split("\n");
            if(lines.length > 1){
                const values = lines[1].split(",");
                document.getElementById("solarWindSpeed").innerText =
                    values[1] + " km/s";
            }
        });

    // -------------------------
    // AUTO LOAD HISTORY ON PAGE OPEN
    // -------------------------
    loadHistory();

    function updateRiskAnalysis(stormValue) {

    const mode = document.getElementById("impactMode").value;

    const powerRisk = document.getElementById("powerRisk");
    const satRisk = document.getElementById("satRisk");
    const gpsRisk = document.getElementById("gpsRisk");

    let powerText = "";
    let satText = "";
    let gpsText = "";

    // INDIA MODE
    if (mode === "india") {

        if (stormValue > -20) {
            powerText = "India Grid: Stable";
            satText = "Indian Satellites: Nominal";
            gpsText = "NavIC / GPS: Normal";
        }
        else if (stormValue > -50) {
            powerText = "India Grid: Minor fluctuations possible";
            satText = "ISRO Satellites: Minor disturbance";
            gpsText = "Navigation: Minor drift possible";
        }
        else if (stormValue > -100) {
            powerText = "India Grid: Moderate transformer stress risk";
            satText = "Satellite drag increased";
            gpsText = "Navigation errors likely";
        }
        else {
            powerText = "India Grid: High transformer stress risk";
            satText = "Satellite anomaly risk high";
            gpsText = "Navigation disruption possible";
        }

    }

    // GLOBAL MODE
    else {

        if (stormValue > -20) {
            powerText = "Global Power Grid: Quiet";
            satText = "Global Satellites: Stable orbit";
            gpsText = "Global Navigation: Normal";
        }
        else if (stormValue > -50) {
            powerText = "High-latitude grids: Minor fluctuations";
            satText = "Satellite radiation: Slight increase";
            gpsText = "GPS drift possible in polar regions";
        }
        else if (stormValue > -100) {
            powerText = "Auroral zone grids under stress";
            satText = "Satellite drag and radiation elevated";
            gpsText = "Navigation degraded at high latitude";
        }
        else {
            powerText = "Severe grid disturbance possible globally";
            satText = "Satellite radiation hazard";
            gpsText = "Global navigation disruption possible";
        }

    }

    if (powerRisk) powerRisk.innerText = powerText;
    if (satRisk) satRisk.innerText = satText;
    if (gpsRisk) gpsRisk.innerText = gpsText;
}
const impactMode = document.getElementById("impactMode");

if (impactMode) {
    impactMode.addEventListener("change", function () {

        const currentValue = parseFloat(document.querySelector(".value").innerText);

        updateRiskAnalysis(currentValue);
        updateEarlyWarning(currentValue);
        updateRegionInfo();

    });
}

function switchImpactMode() {

    if (currentStormValue === null) return;

    const storm = currentStormValue;

    const powerRisk = document.getElementById("powerRisk");
    const satRisk = document.getElementById("satRisk");
    const gpsRisk = document.getElementById("gpsRisk");
    const stormTrend = document.getElementById("stormTrend");
    const stormForecast = document.getElementById("stormForecast");

    if (storm > -20) {
        powerRisk.innerText = "Power Grid: Safe";
        satRisk.innerText = "Satellite Operations: Nominal";
        gpsRisk.innerText = "GPS Accuracy: Normal";
        stormTrend.innerText = "Solar Activity: Quiet";
        stormForecast.innerText = "Next 24h: Quiet Conditions";
    }
    else if (storm <= -20 && storm > -50) {
        powerRisk.innerText = "Power Grid: Low Risk";
        satRisk.innerText = "Satellite Operations: Minor Disturbance";
        gpsRisk.innerText = "GPS Accuracy: Minor Drift";
        stormTrend.innerText = "Solar Activity: Increasing";
        stormForecast.innerText = "Next 24h: Minor Geomagnetic Storm";
    }
    else if (storm <= -50 && storm > -100) {
        powerRisk.innerText = "Power Grid: Moderate Risk";
        satRisk.innerText = "Satellite Operations: Elevated Risk";
        gpsRisk.innerText = "GPS Accuracy: Noticeable Errors";
        stormTrend.innerText = "Solar Activity: Active Storm";
        stormForecast.innerText = "Next 24h: Moderate Storm Expected";
    }
    else {
        powerRisk.innerText = "Power Grid: High Risk";
        satRisk.innerText = "Satellite Operations: Severe Radiation Risk";
        gpsRisk.innerText = "GPS Accuracy: Severe Disruption";
        stormTrend.innerText = "Solar Activity: Severe Geomagnetic Storm";
        stormForecast.innerText = "Next 24h: Strong Storm Conditions";
    }
}
window.switchImpactMode = switchImpactMode;


let currentStormValue = null;

document.addEventListener("DOMContentLoaded", function () {
    updateForecast();
});

function updateEarlyWarning(stormValue) {

    const stormTrend = document.getElementById("stormTrend");
    const stormForecast = document.getElementById("stormForecast");

    const mode = document.getElementById("impactMode").value;

    let trendText = "";
    let forecastText = "";

    if (mode === "india") {

        if (stormValue > -20) {
            trendText = "India Region: Quiet geomagnetic activity";
            forecastText = "No infrastructure impact expected in India.";
        }
        else if (stormValue > -50) {
            trendText = "Minor geomagnetic activity over Indian latitudes";
            forecastText = "Possible small navigation fluctuations.";
        }
        else if (stormValue > -100) {
            trendText = "Moderate storm reaching mid-latitudes";
            forecastText = "Indian satellites and GPS may experience disturbances.";
        }
        else {
            trendText = "Strong geomagnetic storm affecting mid-latitudes";
            forecastText = "Significant risk to power transformers and satellites.";
        }

    } else {

        if (stormValue > -20) {
            trendText = "Global geomagnetic conditions quiet";
            forecastText = "No major global disturbances expected.";
        }
        else if (stormValue > -50) {
            trendText = "Minor geomagnetic storm developing";
            forecastText = "Auroral regions may experience disturbances.";
        }
        else if (stormValue > -100) {
            trendText = "Moderate global geomagnetic storm";
            forecastText = "High-latitude grids and satellites affected.";
        }
        else {
            trendText = "Severe global geomagnetic storm";
            forecastText = "Polar power grids and satellites at high risk.";
        }

    }

    if (stormTrend) stormTrend.innerText = trendText;
    if (stormForecast) stormForecast.innerText = forecastText;
}

function updateRegionInfo() {

    const mode = document.getElementById("impactMode").value;

    const regionInfo = document.getElementById("regionInfo");
    const geomagneticZone = document.getElementById("geomagneticZone");

    if (mode === "india") {

        regionInfo.innerText = "India (Mid-Latitude Monitoring)";
        geomagneticZone.innerText = "Geomagnetic Zone: Mid Latitude";

    } else {

        regionInfo.innerText = "Global Monitoring Network";
        geomagneticZone.innerText = "Geomagnetic Zones: Polar + Mid Latitude";

    }
}
function updateSectorImpact(stormValue) {

    const selector = document.getElementById("sectorSelector");
    const sectorImpact = document.getElementById("sectorImpact");

    if (!selector || !sectorImpact) return;   // prevents crash

    const sector = selector.value;

    let message = "";

    if (sector === "power") {
        message = stormValue < -100
            ? "⚠ Transformer stress risk. Monitor grid stability."
            : "No major grid instability expected.";
    }

    if (sector === "aviation") {
        message = stormValue < -80
            ? "⚠ High-latitude flight communication disturbance possible."
            : "Normal aviation conditions.";
    }

    if (sector === "satellite") {
        message = stormValue < -70
            ? "⚠ Satellite attitude correction required."
            : "Nominal satellite operation.";
    }

    if (sector === "telecom") {
        message = stormValue < -60
            ? "⚠ Signal degradation possible at high frequencies."
            : "Stable telecom conditions.";
    }

    sectorImpact.innerText = message;
}
    const sectorSelector = document.getElementById("sectorSelector");

    if(sectorSelector){
    sectorSelector.addEventListener("change", function(){
        const currentValue = parseFloat(document.querySelector(".value").innerText);
        updateSectorImpact(currentValue);
    });
    }

    function updateAnomalyDetection(stormValue) {

    const anomalyStatus = document.getElementById("anomalyStatus");
    if (!anomalyStatus) return;

    if (stormValue < -100) {

        anomalyStatus.innerText =
            "Severe geomagnetic anomaly detected.";

    }
    else if (stormValue < -50) {

        anomalyStatus.innerText =
            "Moderate magnetic field disturbance.";

    }
    else {

        anomalyStatus.innerText =
            "No significant anomalies detected.";

    }
}

    function updateNationalImpact(stormValue) {

        const impactGrid = document.getElementById("impactGrid");
        const impactSatellite = document.getElementById("impactSatellite");
        const impactAviation = document.getElementById("impactAviation");
        const impactTelecom = document.getElementById("impactTelecom");

        let gridRisk = "";
        let satelliteRisk = "";
        let aviationRisk = "";
        let telecomRisk = "";

        if (stormValue > -20) {

            gridRisk = "Power Grid: No substations at risk.";
            satelliteRisk = "Satellites: Normal orbital operation.";
            aviationRisk = "Aviation: No rerouting required.";
            telecomRisk = "Telecom: Stable high-frequency communication.";

        } else if (stormValue > -50) {

            gridRisk = "Power Grid: 2–5 minor substations may experience voltage fluctuation.";
            satelliteRisk = "Satellites: Minor orbit correction required.";
            aviationRisk = "Aviation: Polar route disturbance probability ~10%.";
            telecomRisk = "Telecom: Minor HF signal instability possible.";

        } else if (stormValue > -100) {

            gridRisk = "Power Grid: 5–12 substations at moderate stress risk.";
            satelliteRisk = "Satellites: Increased drag; correction burn likely.";
            aviationRisk = "Aviation: 20–35% rerouting probability for high latitude flights.";
            telecomRisk = "Telecom: Short-duration signal degradation likely.";

        } else {

            gridRisk = "Power Grid: 12–25 substations under transformer stress risk.";
            satelliteRisk = "Satellites: High anomaly probability; attitude disturbance expected.";
            aviationRisk = "Aviation: 40–60% rerouting probability; radiation exposure risk.";
            telecomRisk = "Telecom: Major HF blackout possible in polar regions.";

        }

        impactGrid.innerHTML =
            `<div class="impact-item">${gridRisk}</div>`;

        impactSatellite.innerHTML =
            `<div class="impact-item">${satelliteRisk}</div>`;

        impactAviation.innerHTML =
            `<div class="impact-item">${aviationRisk}</div>`;

        impactTelecom.innerHTML =
            `<div class="impact-item">${telecomRisk}</div>`;
    }

    // -------------------------
    // UPDATE FORECAST BUTTON
    // -------------------------
    if (updateBtn) {
        updateBtn.addEventListener("click", function() {

            console.log("Update button clicked");

            updateBtn.disabled = true;
            updateBtn.innerText = "Updating...";
            if (loader) loader.style.display = "inline";

            fetch("./update_prediction.php")
                .then(res => res.json())
                .then(data => {

                    // Show backend logs
                    const consoleOutput = document.getElementById("consoleOutput");
                    if (consoleOutput) consoleOutput.innerText = data.logs;
                    document.getElementById("solarWindSpeed").innerText =
                        data.solar_wind_speed + " km/s";

                    // Update storm value
                    if (stormValueElement) {
                        stormValueElement.innerText = data.storm_value + " nT";
                    }
 
                    const confidenceBox = document.getElementById("confidence");
                    if (confidenceBox) {
                        confidenceBox.innerText = "Confidence: " + data.confidence + "%";
                    }
                    document.getElementById("solarWindSpeed").innerText = data.solar_wind_speed;

                    const densityBox = document.getElementById("solarDensity");
                    if (densityBox) densityBox.innerText = data.density;

                    const bzBox = document.getElementById("solarBz");
                    if (bzBox) bzBox.innerText = data.bz;
                    

                    const numericValue = parseFloat(data.storm_value);

                    updateRiskAnalysis(numericValue);
                    updateEarlyWarning(numericValue);
                    updateSectorImpact(numericValue);
                    updateAnomalyDetection(numericValue);
                    updateNationalImpact(numericValue);
                    updateRegionInfo();



                    

                    // Update time (IST)
                    const now = new Date();
                    if (lastUpdatedElement) {
                        lastUpdatedElement.innerText =
                            now.toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
                    }

                    // 🔥 IMPORTANT: refresh history AFTER update finishes
                    loadHistory();
                    const initialValue = numericValue;
                    updateRiskAnalysis(initialValue);
                    updateEarlyWarning(initialValue);
                    updateSectorImpact(initialValue);
                    updateAnomalyDetection(initialValue);
                    updateNationalImpact(initialValue);

                    updateBtn.disabled = false;
                    updateBtn.innerText = "Update Forecast";
                    if (loader) loader.style.display = "none";

                    // Auto scroll console
                    if (consoleBox) {
                        consoleBox.scrollTop = consoleBox.scrollHeight;
                    }
					const value = parseFloat(data.storm_value);

					document.querySelectorAll(".scale-item").forEach(item => {
    					item.style.opacity = "0.4";
					});

					if (value > -20) {
    					document.querySelector(".quiet").style.opacity = "1";
					}
					else if (value > -50) {
    					document.querySelector(".minor").style.opacity = "1";
					}
					else if (value > -100) {
    					document.querySelector(".moderate").style.opacity = "1";
					}
					else {
    					document.querySelector(".strong").style.opacity = "1";
					}

                })
                .catch(error => {
                    console.error("Update failed:", error);

                    updateBtn.disabled = false;
                    updateBtn.innerText = "Update Forecast";
                    if (loader) loader.style.display = "none";
                });
        });
    }
});
