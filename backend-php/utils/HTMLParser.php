<?php
/**
 * HTML Parser Utility
 * Extracts IP activity from Google subscriber HTML files
 */

class HTMLParser {
    
    public function extractIPActivity($htmlContent) {
        $dom = new DOMDocument();
        @$dom->loadHTML($htmlContent, LIBXML_NOERROR);
        
        $xpath = new DOMXPath($dom);
        
        // Find "IP ACTIVITY" heading
        $h3Elements = $xpath->query('//h3');
        $targetTable = null;
        
        foreach ($h3Elements as $h3) {
            if (strtolower(trim($h3->textContent)) === 'ip activity') {
                // Find next table sibling
                $nextElement = $h3->nextSibling;
                while ($nextElement) {
                    if ($nextElement->nodeName === 'table') {
                        $targetTable = $nextElement;
                        break;
                    }
                    $nextElement = $nextElement->nextSibling;
                }
                break;
            }
        }
        
        // Fallback: use first table
        if (!$targetTable) {
            $tables = $xpath->query('//table');
            if ($tables->length > 0) {
                $targetTable = $tables->item(0);
            }
        }
        
        if (!$targetTable) {
            return [];
        }
        
        // Extract rows
        $rows = [];
        $trs = $xpath->query('.//tr', $targetTable);
        
        foreach ($trs as $index => $tr) {
            if ($index === 0) continue; // Skip header
            
            $tds = $xpath->query('.//td', $tr);
            if ($tds->length < 2) continue;
            
            $timestamp = trim($tds->item(0)->textContent);
            $ip = trim($tds->item(1)->textContent);
            $activity = $tds->length > 2 ? trim($tds->item(2)->textContent) : '';
            
            if (empty($timestamp) || empty($ip)) continue;
            if (!$this->isValidIP($ip)) continue;
            
            $rows[] = [
                'timestamp' => $timestamp,
                'ip' => $ip,
                'activity' => $activity
            ];
        }
        
        return $rows;
    }
    
    private function isValidIP($ip) {
        // IPv4
        if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4)) {
            return true;
        }
        
        // IPv6
        if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV6)) {
            return true;
        }
        
        return false;
    }
}
