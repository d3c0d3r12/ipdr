import { useState } from 'react';

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
  message?: string;
}

export interface ValidationRules {
  [field: string]: ValidationRule | ValidationRule[];
}

export interface ValidationErrors {
  [field: string]: string;
}

/**
 * Form Validation Hook
 * Validates form fields against rules and returns validation state and errors
 * 
 * @param rules - Validation rules for each field
 * @returns { errors, validate, clearErrors, clearFieldError }
 */
export function useFormValidation(rules: ValidationRules) {
  const [errors, setErrors] = useState<ValidationErrors>({});

  const validate = (values: Record<string, any>): boolean => {
    const newErrors: ValidationErrors = {};

    for (const [field, rule] of Object.entries(rules)) {
      const value = values[field];
      const ruleArray = Array.isArray(rule) ? rule : [rule];

      for (const r of ruleArray) {
        // Required validation
        if (r.required && (!value || value.toString().trim() === '')) {
          newErrors[field] = r.message || `${field} is required`;
          break;
        }

        if (!value) continue; // Skip other validations if field is empty

        // Min length validation
        if (r.minLength && value.toString().length < r.minLength) {
          newErrors[field] =
            r.message || `${field} must be at least ${r.minLength} characters`;
          break;
        }

        // Max length validation
        if (r.maxLength && value.toString().length > r.maxLength) {
          newErrors[field] =
            r.message || `${field} must be no more than ${r.maxLength} characters`;
          break;
        }

        // Pattern validation
        if (r.pattern && !r.pattern.test(value)) {
          newErrors[field] = r.message || `${field} format is invalid`;
          break;
        }

        // Custom validation
        if (r.custom) {
          const customError = r.custom(value);
          if (customError) {
            newErrors[field] = customError;
            break;
          }
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const clearErrors = (): void => {
    setErrors({});
  };

  const clearFieldError = (field: string): void => {
    setErrors((prev) => {
      const updated = { ...prev };
      delete updated[field];
      return updated;
    });
  };

  const getFieldError = (field: string): string | undefined => {
    return errors[field];
  };

  const hasError = (field: string): boolean => {
    return !!errors[field];
  };

  return {
    errors,
    validate,
    clearErrors,
    clearFieldError,
    getFieldError,
    hasError,
  };
}

/**
 * Common validation patterns
 */
export const ValidationPatterns = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
  username: /^[a-zA-Z0-9_-]{3,20}$/,
  phone: /^[0-9]{10,15}$/,
  ipAddress:
    /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  url: /^https?:\/\/.+/,
};

/**
 * Common validation rules
 */
export const CommonValidations = {
  email: {
    required: true,
    pattern: ValidationPatterns.email,
    message: 'Please enter a valid email address',
  },
  password: {
    required: true,
    minLength: 8,
    pattern: ValidationPatterns.password,
    message:
      'Password must be at least 8 characters with uppercase, lowercase, number, and special character',
  },
  username: {
    required: true,
    pattern: ValidationPatterns.username,
    message: 'Username must be 3-20 characters with letters, numbers, underscore, or hyphen',
  },
  phone: {
    pattern: ValidationPatterns.phone,
    message: 'Please enter a valid phone number',
  },
  ipAddress: {
    pattern: ValidationPatterns.ipAddress,
    message: 'Please enter a valid IP address',
  },
};
