<?php

$path = "forecast/history.csv";

if (!file_exists($path)) {
    echo "<div class='history-entry'>No history available</div>";
    exit;
}

$lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);

$last3 = array_slice($lines, -3);

foreach (array_reverse($last3) as $line) {
    list($date, $value) = explode(",", $line);
    echo "<div class='history-entry'>
            <strong>$value nT</strong><br>
            <small>$date</small>
          </div>";
}
?>
