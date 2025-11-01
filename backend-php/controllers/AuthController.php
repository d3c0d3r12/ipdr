<?php
/**
 * Authentication Controller
 */

class AuthController {
    private $fake_users = [
        'inspector' => 'secure@123',
        'analyst' => 'an@123'
    ];
    
    public function login() {
        $data = json_decode(file_get_contents('php://input'), true);
        
        $username = $data['username'] ?? '';
        $password = $data['password'] ?? '';
        
        if (isset($this->fake_users[$username]) && $this->fake_users[$username] === $password) {
            $token = $this->generateJWT($username);
            
            http_response_code(200);
            echo json_encode([
                'token' => $token,
                'user' => $username
            ]);
        } else {
            http_response_code(401);
            echo json_encode(['error' => 'Invalid credentials']);
        }
    }
    
    private function generateJWT($username) {
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        $payload = json_encode([
            'user' => $username,
            'iat' => time(),
            'exp' => time() + (60 * 60 * 24) // 24 hours
        ]);
        
        $base64UrlHeader = $this->base64UrlEncode($header);
        $base64UrlPayload = $this->base64UrlEncode($payload);
        
        $signature = hash_hmac('sha256', $base64UrlHeader . "." . $base64UrlPayload, JWT_SECRET, true);
        $base64UrlSignature = $this->base64UrlEncode($signature);
        
        return $base64UrlHeader . "." . $base64UrlPayload . "." . $base64UrlSignature;
    }
    
    private function base64UrlEncode($data) {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
}
