<?php
/**
 * Data Controller
 */

require_once __DIR__ . '/../models/IPRecord.php';

class DataController {
    private $db;
    private $ipRecord;
    
    public function __construct() {
        $database = new Database();
        $this->db = $database->getConnection();
        $this->ipRecord = new IPRecord($this->db);
    }
    
    public function getRecords() {
        $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 100;
        $offset = isset($_GET['offset']) ? (int)$_GET['offset'] : 0;
        
        $records = $this->ipRecord->getAll($limit, $offset);
        $total = $this->ipRecord->getCount();
        
        http_response_code(200);
        echo json_encode([
            'count' => count($records),
            'total' => $total,
            'records' => $records
        ]);
    }
    
    public function getSummary() {
        $stats = $this->ipRecord->getStats();
        
        http_response_code(200);
        echo json_encode([
            'total' => (int)$stats['total'],
            'countries' => (int)$stats['countries'],
            'cities' => (int)$stats['cities'],
            'suspicious' => 0 // Placeholder
        ]);
    }
    
    public function storeFromCSV() {
        $data = json_decode(file_get_contents('php://input'), true);
        $csvPath = $data['csv_path'] ?? '';
        $sourceFile = $data['source_file'] ?? 'unknown';
        
        if (!file_exists($csvPath)) {
            http_response_code(404);
            echo json_encode(['error' => 'CSV file not found']);
            return;
        }
        
        $inserted = $this->ipRecord->bulkInsertFromCSV($csvPath, $sourceFile);
        
        http_response_code(200);
        echo json_encode([
            'message' => 'Data stored successfully',
            'inserted' => $inserted
        ]);
    }
}
