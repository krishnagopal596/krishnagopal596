package com.security.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;

/**
 * Secure Authentication Platform
 * 
 * A comprehensive security platform implementing advanced authentication,
 * authorization, and encryption mechanisms for enterprise-grade security.
 * 
 * Features:
 * - Multi-Factor Authentication (TOTP, SMS, Email, Biometric)
 * - OAuth2 & OpenID Connect
 * - Advanced encryption (AES-256, RSA-4096, ECC)
 * - JWT with refresh token rotation
 * - Zero-trust architecture
 * - Security monitoring and threat detection
 * - Compliance (GDPR, HIPAA, SOC2)
 * 
 * @author Krishna Gopal Madhavaram
 * @email krishnagopal596@gmail.com
 * @version 1.0
 */
@SpringBootApplication
@EnableWebSecurity
@EnableGlobalMethodSecurity(prePostEnabled = true, securedEnabled = true, jsr250Enabled = true)
public class SecureAuthApplication {

    public static void main(String[] args) {
        SpringApplication.run(SecureAuthApplication.class, args);
    }
}
