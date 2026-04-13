<?php

ob_start(); // prevent HTML warnings breaking JSON

$logs = shell_exec("python ../ml/live_predict.py 2>&1");

$csvPath = "forecast/output_pred.csv";

if (!file_exists($csvPath)) {
    echo json_encode([
        "storm_value" => "--",
        "solar_wind_speed" => "--",
        "confidence" => "--",
        "logs" => $logs
    ]);
    exit;
}

if (($handle = fopen($csvPath, "r")) !== FALSE) {

    $header = fgetcsv($handle);
    $data = fgetcsv($handle);

    if ($header && $data) {
        $row = array_combine($header, $data);
    } else {
        $row = ["storm_value"=>"--","solar_wind_speed"=>"--", "confidence"=>"--"];
    }

    fclose($handle);
}

echo json_encode([
    "storm_value" => $row["storm_value"] ?? "--",
    "solar_wind_speed" => $row["solar_wind_speed"] ?? "--",
    "density" => $row["density"] ?? "--",
    "bz" => $row["bz"] ?? "--",
    "confidence" => $row["confidence"] ?? "--",
    "logs" => $logs
]);

exit;
?>