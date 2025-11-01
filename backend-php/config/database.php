<?php
/**
 * Database Configuration and Connection
 */

class Database {
    private $host = 'localhost';
    private $db_name = 'police_data';
    private $username = 'police_user';
    private $password = 'StrongPass';
    private $conn;
    
    public function __construct() {
        // Load from environment if available
        if (getenv('DB_HOST')) $this->host = getenv('DB_HOST');
        if (getenv('DB_NAME')) $this->db_name = getenv('DB_NAME');
        if (getenv('DB_USER')) $this->username = getenv('DB_USER');
        if (getenv('DB_PASS')) $this->password = getenv('DB_PASS');
    }
    
    public function getConnection() {
        $this->conn = null;
        
        try {
            $this->conn = new PDO(
                "pgsql:host=" . $this->host . ";dbname=" . $this->db_name,
                $this->username,
                $this->password
            );
            $this->conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        } catch(PDOException $e) {
            echo json_encode(['error' => 'Connection failed: ' . $e->getMessage()]);
            exit();
        }
        
        return $this->conn;
    }
}
