    <?php
session_start();

$username = $_POST["username"];
$password = $_POST["password"];

/* Demo credentials */
$valid_user = "admin";
$valid_pass = "admin";

if ($username === $valid_user && $password === $valid_pass) {

    $_SESSION["user"] = $username;
    $_SESSION["login_time"] = time();

    header("Location: index.php");
    exit();

} else {

    echo "Invalid username or password";
}
?>