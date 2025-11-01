<?php
/**
 * Process Controller
 */

class ProcessController {
    
    public function extract() {
        $runDir = $_GET['run_dir'] ?? '';
        
        if (!is_dir($runDir)) {
            http_response_code(404);
            echo json_encode(['error' => 'Run directory not found']);
            return;
        }
        
        // Find HTML files
        $htmlFiles = glob($runDir . '*.{html,htm}', GLOB_BRACE);
        
        if (empty($htmlFiles)) {
            http_response_code(400);
            echo json_encode(['error' => 'No HTML files found']);
            return;
        }
        
        http_response_code(200);
        echo json_encode([
            'status' => 'extracted',
            'html_file' => basename($htmlFiles[0]),
            'run_dir' => $runDir
        ]);
    }
    
    public function merge() {
        $data = json_decode(file_get_contents('php://input'), true);
        $runDir = $data['run_dir'] ?? $_GET['run_dir'] ?? '';
        
        if (!is_dir($runDir)) {
            http_response_code(404);
            echo json_encode(['error' => 'Run directory not found']);
            return;
        }
        
        // Find InfoByIP CSV files
        $csvFiles = glob($runDir . 'infobyip_batch_*.csv');
        
        if (empty($csvFiles)) {
            http_response_code(400);
            echo json_encode(['error' => 'No InfoByIP CSV files found']);
            return;
        }
        
        // Merge CSVs (simplified)
        $mergedPath = $runDir . 'ip_lookup_table.csv';
        $this->mergeCSVFiles($csvFiles, $mergedPath);
        
        http_response_code(200);
        echo json_encode([
            'message' => 'processed',
            'lookup' => $mergedPath,
            'csv_count' => count($csvFiles)
        ]);
    }
    
    public function export() {
        $runDir = $_GET['run_dir'] ?? '';
        
        if (!is_dir($runDir)) {
            http_response_code(404);
            echo json_encode(['error' => 'Run directory not found']);
            return;
        }
        
        $excelPath = $runDir . 'master_ip_data.xlsx';
        
        if (!file_exists($excelPath)) {
            http_response_code(404);
            echo json_encode(['error' => 'Excel file not found. Run processing first.']);
            return;
        }
        
        // Download file
        header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        header('Content-Disposition: attachment; filename="master_ip_data.xlsx"');
        header('Content-Length: ' . filesize($excelPath));
        readfile($excelPath);
        exit();
    }
    
    private function mergeCSVFiles($files, $outputPath) {
        $output = fopen($outputPath, 'w');
        $headerWritten = false;
        
        foreach ($files as $file) {
            $input = fopen($file, 'r');
            $header = fgetcsv($input);
            
            if (!$headerWritten) {
                fputcsv($output, $header);
                $headerWritten = true;
            }
            
            while (($row = fgetcsv($input)) !== false) {
                fputcsv($output, $row);
            }
            
            fclose($input);
        }
        
        fclose($output);
    }
}
