<?php
/**
 * Application Configuration
 */

define('JWT_SECRET', getenv('JWT_SECRET') ?: 'supersecurekey');
define('UPLOAD_DIR', __DIR__ . '/../uploads/');
define('PROCESSED_DIR', __DIR__ . '/../processed/');
define('LOGS_DIR', __DIR__ . '/../logs/');

// Create directories if they don't exist
if (!file_exists(UPLOAD_DIR)) mkdir(UPLOAD_DIR, 0755, true);
if (!file_exists(PROCESSED_DIR)) mkdir(PROCESSED_DIR, 0755, true);
if (!file_exists(LOGS_DIR)) mkdir(LOGS_DIR, 0755, true);

// Timezone
date_default_timezone_set('Asia/Kolkata');
