"""
Security Utilities
Input sanitization, validation, and security filters
"""

import re
import html
from typing import Any, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Comprehensive security validation and sanitization
    """
    
    # Dangerous patterns for SQL injection
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(;.*--)",
        r"(\bUNION\b.*\bSELECT\b)",
    ]
    
    # Dangerous patterns for XSS
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<applet",
    ]
    
    # Dangerous patterns for command injection
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r"\.\./",
        r"~",
        r"\x00",
    ]
    
    # Dangerous patterns for path traversal (including URL-encoded variants)
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",
        r"%2e%2e",        # URL-encoded ..
        r"%2e\.",         # Half-encoded ..
        r"\.%2e",         # Half-encoded ..
        r"%252e%252e",    # Double-encoded ..
        r"~",
        r"\x00",
        r"%00",           # URL-encoded null byte
        r"[;&|`$]",
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Trim whitespace
        value = value.strip()
        
        # Limit length
        if len(value) > max_length:
            logger.warning(f"String truncated from {len(value)} to {max_length} characters")
            value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        return value
    
    @staticmethod
    def validate_no_sql_injection(value: str) -> bool:
        """
        Check for SQL injection patterns (case-insensitive)

        Args:
            value: Input string

        Returns:
            True if safe, False if dangerous
        """
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"🚨 SQL injection attempt detected: {value}")
                return False

        return True
    
    @staticmethod
    def validate_no_xss(value: str) -> bool:
        """
        Check for XSS patterns
        
        Args:
            value: Input string
            
        Returns:
            True if safe, False if dangerous
        """
        for pattern in SecurityValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"🚨 XSS attempt detected: {value}")
                return False
        
        return True
    
    @staticmethod
    def validate_no_command_injection(value: str) -> bool:
        """
        Check for command injection patterns
        
        Args:
            value: Input string
            
        Returns:
            True if safe, False if dangerous
        """
        for pattern in SecurityValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                logger.warning(f"🚨 Command injection attempt detected: {value}")
                return False
        
        return True
    
    @staticmethod
    def validate_no_path_traversal(value: str) -> bool:
        """
        Check for path traversal patterns
        
        Args:
            value: Input string
            
        Returns:
            True if safe, False if dangerous
        """
        for pattern in SecurityValidator.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value):
                logger.warning(f"🚨 Path traversal attempt detected: {value}")
                return False
        
        return True
    
    @staticmethod
    def validate_alphanumeric(value: str, allow_dash: bool = True, allow_underscore: bool = True) -> bool:
        """
        Validate alphanumeric input
        
        Args:
            value: Input string
            allow_dash: Allow dash character
            allow_underscore: Allow underscore character
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9'
        if allow_dash:
            pattern += r'\-'
        if allow_underscore:
            pattern += r'_'
        pattern += r']+$'
        
        return bool(re.match(pattern, value))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        Validate IP address (IPv4 or IPv6)
        
        Args:
            ip: IP address string
            
        Returns:
            True if valid, False otherwise
        """
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        # IPv6 pattern (simplified)
        ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'
        
        if re.match(ipv4_pattern, ip):
            # Validate each octet
            octets = ip.split('.')
            return all(0 <= int(octet) <= 255 for octet in octets)
        
        return bool(re.match(ipv6_pattern, ip))
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename
        
        Args:
            filename: Input filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def validate_fir_number(fir: str) -> bool:
        """
        Validate FIR number format
        
        Args:
            fir: FIR number
            
        Returns:
            True if valid, False otherwise
        """
        # Allow alphanumeric, dash, underscore, slash
        pattern = r'^[a-zA-Z0-9\-_/]+$'
        
        if not re.match(pattern, fir):
            return False
        
        # Length check
        if len(fir) < 3 or len(fir) > 64:
            return False
        
        return True
    
    @staticmethod
    def comprehensive_validate(value: str, field_name: str = "input") -> str:
        """
        Comprehensive validation and sanitization
        
        Args:
            value: Input value
            field_name: Name of the field (for error messages)
            
        Returns:
            Sanitized value
            
        Raises:
            HTTPException: If validation fails
        """
        if not value or not isinstance(value, str):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: must be a non-empty string"
            )
        
        # Sanitize
        sanitized = SecurityValidator.sanitize_string(value)
        
        # Validate no SQL injection
        if not SecurityValidator.validate_no_sql_injection(sanitized):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: contains forbidden SQL patterns"
            )
        
        # Validate no XSS
        if not SecurityValidator.validate_no_xss(sanitized):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: contains forbidden script patterns"
            )
        
        # Validate no command injection
        if not SecurityValidator.validate_no_command_injection(sanitized):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: contains forbidden command patterns"
            )
        
        return sanitized


# Convenience functions
def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    return SecurityValidator.sanitize_string(value, max_length)


def validate_input(value: str, field_name: str = "input") -> str:
    """Comprehensive validation"""
    return SecurityValidator.comprehensive_validate(value, field_name)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename"""
    return SecurityValidator.sanitize_filename(filename)


def validate_fir_number(fir: str) -> bool:
    """Validate FIR number"""
    return SecurityValidator.validate_fir_number(fir)
