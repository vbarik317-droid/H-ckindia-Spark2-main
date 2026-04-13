<?php
session_start();

/* session timeout (15 minutes) */
$timeout = 900;

if (!isset($_SESSION["user"])) {

    header("Location: login.php");
    exit();

}

if (isset($_SESSION["login_time"])) {

    if (time() - $_SESSION["login_time"] > $timeout) {

        session_destroy();

        header("Location: login.php?timeout=1");
        exit();

    }
}

/* refresh session time */
$_SESSION["login_time"] = time();
?>