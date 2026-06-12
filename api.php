<?php
// Read credentials from database.txt
$db_config = file_get_contents('database.txt');
if (!$db_config) {
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Database configuration not found']);
    exit;
}

$lines = explode("\n", $db_config);
$config = [];
foreach ($lines as $line) {
    if (strpos($line, ':') !== false) {
        list($key, $val) = explode(':', $line, 2);
        $config[trim($key)] = trim($val);
    }
}

$host = $config['Connect'] ?? 'localhost';
$db   = $config['Name_db'] ?? '';
$user = $config['Name_db'] ?? ''; // In this environment, user is often same as DB name
$pass = $config['Pass'] ?? '';
$charset = 'utf8mb4';

$dsn = "mysql:host=$host;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
     $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
     header('Content-Type: application/json');
     echo json_encode(['error' => 'Connection failed: ' . $e->getMessage()]);
     exit;
}

// Ensure table exists
$pdo->exec("CREATE TABLE IF NOT EXISTS site_data (
    id VARCHAR(50) PRIMARY KEY,
    content LONGTEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)");

header('Content-Type: application/json');

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET') {
    $stmt = $pdo->prepare("SELECT content FROM site_data WHERE id = 'scores'");
    $stmt->execute();
    $row = $stmt->fetch();
    if ($row) {
        echo $row['content'];
    } else {
        echo json_encode(['scores' => []]);
    }
} elseif ($method === 'POST') {
    $input = file_get_contents('php://input');
    // Verify JSON
    $data = json_decode($input);
    if (json_last_error() === JSON_ERROR_NONE) {
        $stmt = $pdo->prepare("INSERT INTO site_data (id, content) VALUES ('scores', ?) ON DUPLICATE KEY UPDATE content = VALUES(content)");
        $stmt->execute([$input]);
        echo json_encode(['success' => true]);
    } else {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON']);
    }
}
