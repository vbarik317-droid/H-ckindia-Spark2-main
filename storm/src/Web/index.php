<?php
require "session_check.php";

date_default_timezone_set("Asia/Kolkata");

$csv_path = "forecast/output_pred.csv";
$storm_value = "N/A";
$last_updated = "N/A";

if (file_exists($csv_path)) {
    $data = array_map('str_getcsv', file($csv_path));
    if (count($data) > 1) {
        $storm_value = $data[1][0];
        $last_updated = date("d M Y h:i A") . " IST";

    }
}

function getStatus($value) {
    if (!is_numeric($value)) return "Unknown";
    if ($value < -100) return "Extreme Storm";
    if ($value < -50) return "Strong Storm";
    if ($value < -20) return "Moderate Activity";
    return "Quiet Conditions";
}

$status = getStatus($storm_value);
?>
<!DOCTYPE html>
<html>
<head>
    <title>Storm Prophet Dashboard</title>
    <base href="/storm/src/Web/">
    <link rel="stylesheet" href="style.css">
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
</head>

<body>

<div class="header">
    <a href="logout.php">Logout</a>
    <h1>Storm Prophet</h1>
    <p>Real-Time Geomagnetic Storm Forecast</p>
</div>

<div class="info-panel">
    <!-- HISTORY COLUMN -->
    <div class="history-column">
        <h3>History</h3>
        <div id="historyContent"></div>
    </div>

    <div class="card">
        <h2>Storm Value</h2>
        <p class="value"><?php echo $storm_value; ?> nT</p>
    </div> 
    <div class="card">
        <h2>Latest Solar Wind Data</h2>
        <p>Speed: <span id="solarWindSpeed">--</span> km/s</p>
        <p>Density: <span id="solarDensity">--</span> p/cm³</p>
        <p>Bz Magnetic Field: <span id="solarBz">--</span> nT</p>
    </div>
    <div class="card">
        <h2>Status</h2>
        <p><?php echo $status; ?></p>
    </div>
    <div class="card">
        <h2>Last Updated</h2>
        <p id="lastUpdated"><?php echo $last_updated; ?></p>

    </div>

    <!-- NEW DETAILS BOX -->
    <div class="details-box">
        <h3>Storm Scale</h3>

        <div class="scale-item quiet">Quiet: > -20 nT</div>
        <div class="scale-item minor">Minor: -20 to -50 nT</div>
        <div class="scale-item moderate">Moderate: -50 to -100 nT</div>
        <div class="scale-item strong">Strong: < -100 nT</div>

    </div>

    
</div>

<div class="buttons">
    <button id="updateBtn">Update Forecast</button>
	<span id="loader" style="display:none;"> Updating... ⏳</span>
    <button onclick="viewCSV()">View Raw Data</button>
</div>
<div id="backendConsole" class="console">
    <div class="console-header">Backend Log</div>
    <pre id="consoleOutput">Click "Update Forecast" to run model...</pre>
</div>

<div class="impact-wrapper">

    <div class="impact-header">
        <h2>Space Weather Risk Assessment</h2>

        <select id="impactMode" onchange="switchImpactMode()">
        <option value="india">India Impact View</option>
        <option value="global">Global Impact View</option>
        </select>
    </div>

    <div class="impact-grid">

        <div class="impact-card">
            <h3>Infrastructure Risk</h3>
            <p id="powerRisk">Calculating...</p>
            <p id="satRisk">Calculating...</p>
            <p id="gpsRisk">Calculating...</p>
        </div>

        <div class="impact-card">
            <h3>Geomagnetic Storm Forecast</h3>
            <p id="stormTrend">Analyzing...</p>
            <p id="stormForecast">Analyzing...</p>
        </div>

        <div class="impact-card">
            <h3>Anomaly Detection</h3>
            <p id="anomalyStatus">Analyzing...</p>
        </div>

        <div class="impact-card">
            <h3>Monitoring Region</h3>
            <p id="regionInfo">India </p>
            <p id="geomagneticZone">Zone: Mid Latitude</p>
        </div>

        <div class="impact-card">
            <h3>AI Model Status</h3>
            <p>LSTM Neural Network</p>
            <p>Data Window: 72 Hours</p>
            <p id="confidence">Confidence: --</p>
        </div>

    </div>
</div>

<div id="cesiumContainer"></div>

<script>


function viewCSV() {
    window.open("forecast/output_pred.csv", "_blank");
}

// Cesium globe
Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIyMmM3ZWJkOS0zZWRiLTQ3YWItYjI4NC0wNzRjZjVmYmUzNzQiLCJpZCI6MzkxMzQwLCJpYXQiOjE3NzEzMjY5Mjl9.RplI6WBDrTOsTTqUPIZE_p3j9JdNtn6iIjTZ4ytvJ-U';
var viewer = new Cesium.Viewer('cesiumContainer', {
    animation: false,
    timeline: false
});

</script>
<script src="script.js"></script>

</body>
</html>
