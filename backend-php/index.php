<?php
/**
 * Police Intelligence System - PHP Backend
 * Main entry point for API requests
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Load configuration
require_once 'config/database.php';
require_once 'config/config.php';

// Load controllers
require_once 'controllers/AuthController.php';
require_once 'controllers/UploadController.php';
require_once 'controllers/DataController.php';
require_once 'controllers/ProcessController.php';

// Simple router
$request_uri = $_SERVER['REQUEST_URI'];
$request_method = $_SERVER['REQUEST_METHOD'];

// Remove query string and base path
$path = parse_url($request_uri, PHP_URL_PATH);
$path = str_replace('/backend-php', '', $path);

// Route handling
switch (true) {
    // Health check
    case $path === '/' && $request_method === 'GET':
        echo json_encode(['status' => 'Police Intelligence API (PHP) is running']);
        break;
    
    // Authentication
    case $path === '/api/auth/login' && $request_method === 'POST':
        $controller = new AuthController();
        $controller->login();
        break;
    
    // Upload
    case $path === '/api/upload/' && $request_method === 'POST':
        $controller = new UploadController();
        $controller->upload();
        break;
    
    // Data endpoints
    case $path === '/api/data/' && $request_method === 'GET':
        $controller = new DataController();
        $controller->getRecords();
        break;
    
    case $path === '/api/data/summary' && $request_method === 'GET':
        $controller = new DataController();
        $controller->getSummary();
        break;
    
    // Process endpoints
    case $path === '/api/process/extract' && $request_method === 'GET':
        $controller = new ProcessController();
        $controller->extract();
        break;
    
    case $path === '/api/process/merge' && $request_method === 'POST':
        $controller = new ProcessController();
        $controller->merge();
        break;
    
    case $path === '/api/process/export' && $request_method === 'GET':
        $controller = new ProcessController();
        $controller->export();
        break;
    
    // 404 Not Found
    default:
        http_response_code(404);
        echo json_encode(['error' => 'Endpoint not found']);
        break;
}
