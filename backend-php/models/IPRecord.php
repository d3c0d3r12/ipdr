<?php
/**
 * IP Record Model
 */

class IPRecord {
    private $conn;
    private $table = 'ip_records';
    
    public $id;
    public $timestamp;
    public $ip;
    public $country;
    public $region;
    public $city;
    public $isp;
    public $source_file;
    public $created_at;
    
    public function __construct($db) {
        $this->conn = $db;
    }
    
    /**
     * Create new IP record
     */
    public function create() {
        $query = "INSERT INTO " . $this->table . " 
                  (timestamp, ip, country, region, city, isp, source_file) 
                  VALUES (:timestamp, :ip, :country, :region, :city, :isp, :source_file)
                  RETURNING id";
        
        $stmt = $this->conn->prepare($query);
        
        // Bind parameters
        $stmt->bindParam(':timestamp', $this->timestamp);
        $stmt->bindParam(':ip', $this->ip);
        $stmt->bindParam(':country', $this->country);
        $stmt->bindParam(':region', $this->region);
        $stmt->bindParam(':city', $this->city);
        $stmt->bindParam(':isp', $this->isp);
        $stmt->bindParam(':source_file', $this->source_file);
        
        if ($stmt->execute()) {
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            return $row['id'];
        }
        
        return false;
    }
    
    /**
     * Get all records with pagination
     */
    public function getAll($limit = 100, $offset = 0) {
        $query = "SELECT * FROM " . $this->table . " 
                  ORDER BY created_at DESC 
                  LIMIT :limit OFFSET :offset";
        
        $stmt = $this->conn->prepare($query);
        $stmt->bindParam(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindParam(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();
        
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
    
    /**
     * Get total count
     */
    public function getCount() {
        $query = "SELECT COUNT(*) as total FROM " . $this->table;
        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        return $row['total'];
    }
    
    /**
     * Get statistics
     */
    public function getStats() {
        $query = "SELECT 
                    COUNT(*) as total,
                    COUNT(DISTINCT country) as countries,
                    COUNT(DISTINCT city) as cities
                  FROM " . $this->table;
        
        $stmt = $this->conn->prepare($query);
        $stmt->execute();
        
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }
    
    /**
     * Bulk insert from CSV
     */
    public function bulkInsertFromCSV($csvPath, $sourcefile) {
        if (!file_exists($csvPath)) {
            return false;
        }
        
        $handle = fopen($csvPath, 'r');
        $header = fgetcsv($handle); // Skip header
        
        $inserted = 0;
        while (($data = fgetcsv($handle)) !== false) {
            $this->timestamp = $data[0] ?? '';
            $this->ip = $data[1] ?? '';
            $this->country = $data[2] ?? null;
            $this->region = $data[3] ?? null;
            $this->city = $data[4] ?? null;
            $this->isp = $data[5] ?? null;
            $this->source_file = $sourcefile;
            
            if ($this->create()) {
                $inserted++;
            }
        }
        
        fclose($handle);
        return $inserted;
    }
}
