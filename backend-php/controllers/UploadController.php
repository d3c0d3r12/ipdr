<?php
/**
 * Upload Controller
 */

require_once __DIR__ . '/../utils/HTMLParser.php';

class UploadController {
    
    public function upload() {
        if (!isset($_FILES['file']) || !isset($_POST['fir'])) {
            http_response_code(400);
            echo json_encode(['error' => 'File and FIR number required']);
            return;
        }
        
        $file = $_FILES['file'];
        $firNo = $_POST['fir'];
        
        // Validate file type
        $fileExt = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        if (!in_array($fileExt, ['html', 'htm'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Only HTML files are allowed']);
            return;
        }
        
        // Create run directory
        $timestamp = date('Ymd_His');
        $safeFir = preg_replace('/[^a-z0-9_-]+/i', '-', $firNo);
        $safeFir = substr($safeFir, 0, 64) ?: 'FIR';
        $runDir = PROCESSED_DIR . $timestamp . '_' . $safeFir . '/';
        
        if (!file_exists($runDir)) {
            mkdir($runDir, 0755, true);
        }
        
        // Save uploaded file
        $uploadPath = UPLOAD_DIR . $file['name'];
        move_uploaded_file($file['tmp_name'], $uploadPath);
        
        // Copy to run directory
        copy($uploadPath, $runDir . $file['name']);
        
        // Extract IP activity
        $htmlContent = file_get_contents($uploadPath);
        $parser = new HTMLParser();
        $rows = $parser->extractIPActivity($htmlContent);
        
        if (empty($rows)) {
            http_response_code(400);
            echo json_encode(['error' => 'No IP ACTIVITY rows found']);
            return;
        }
        
        // Save to CSV
        $csvPath = $runDir . 'original_log.csv';
        $this->saveToCSV($rows, $csvPath);
        
        // Create batches
        $batches = $this->createBatches($rows, $runDir);
        
        http_response_code(200);
        echo json_encode([
            'status' => 'uploaded',
            'filename' => $file['name'],
            'run_dir' => $runDir,
            'original_csv' => $csvPath,
            'count_rows' => count($rows),
            'batches' => count($batches)
        ]);
    }
    
    private function saveToCSV($rows, $path) {
        $fp = fopen($path, 'w');
        fputcsv($fp, ['row_index', 'timestamp_original', 'ip_original', 'activity']);
        
        foreach ($rows as $index => $row) {
            fputcsv($fp, [
                $index + 1,
                $row['timestamp'],
                $row['ip'],
                $row['activity'] ?? ''
            ]);
        }
        
        fclose($fp);
    }
    
    private function createBatches($rows, $runDir, $batchSize = 100) {
        $batches = [];
        $ips = array_column($rows, 'ip');
        $chunks = array_chunk($ips, $batchSize);
        
        foreach ($chunks as $index => $chunk) {
            $batchNum = str_pad($index + 1, 3, '0', STR_PAD_LEFT);
            $batchPath = $runDir . 'batch_' . $batchNum . '.txt';
            file_put_contents($batchPath, implode("\n", $chunk));
            $batches[] = $batchPath;
        }
        
        return $batches;
    }
}
