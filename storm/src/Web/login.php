<?php
session_start();

if (isset($_SESSION["user"])) {
    header("Location: index.php");
    exit();
}
?>

<!DOCTYPE html>
<html>
<head>
<title>Storm Prophet Login</title>
<base href="/storm/src/Web/">
<link rel="stylesheet" href="style.css">
</head>

<body class="login-body">

<div class="login-container">

<h1>Storm Prophet</h1>
<p>Geomagnetic Storm Forecast System</p>

<form method="POST" action="auth.php">

<input type="text" name="username" placeholder="Username" required>

<input type="password" name="password" placeholder="Password" required>

<button type="submit">Login</button>

</form>

</div>

</body>
</html>