package com.insurance.policy.controller;

import com.insurance.policy.dto.PolicyDto;
import com.insurance.policy.dto.PolicyResponseDto;
import com.insurance.policy.service.PolicyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/**
 * REST Controller for Policy Management
 * 
 * Provides comprehensive API endpoints for policy operations including:
 * - Policy creation and updates
 * - Policy retrieval with advanced filtering
 * - Policy status management
 * - Integration with billing and claims systems
 * 
 * Security: OAuth2 + JWT authentication with role-based access control
 * 
 * @author Krishna Gopal Madhavaram
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/policies")
@RequiredArgsConstructor
@Tag(name = "Policy Management", description = "API for insurance policy operations")
@SecurityRequirement(name = "bearerAuth")
public class PolicyController {

    private final PolicyService policyService;

    @Operation(summary = "Create new policy", description = "Creates a new insurance policy with validation")
    @PostMapping
    @PreAuthorize("hasRole('AGENT') or hasRole('ADMIN')")
    public ResponseEntity<PolicyResponseDto> createPolicy(@Valid @RequestBody PolicyDto policyDto) {
        log.info("Creating new policy for customer: {}", policyDto.getCustomerId());
        
        PolicyResponseDto response = policyService.createPolicy(policyDto);
        
        log.info("Policy created successfully with ID: {}", response.getPolicyId());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @Operation(summary = "Get policy by ID", description = "Retrieves a specific policy by its unique identifier")
    @GetMapping("/{policyId}")
    @PreAuthorize("hasRole('AGENT') or hasRole('ADMIN') or hasRole('CUSTOMER')")
    public ResponseEntity<PolicyResponseDto> getPolicy(@PathVariable String policyId) {
        log.debug("Retrieving policy: {}", policyId);
        
        PolicyResponseDto policy = policyService.getPolicyById(policyId);
        return ResponseEntity.ok(policy);
    }

    @Operation(summary = "Get policies with filtering", description = "Retrieves policies with advanced filtering and pagination")
    @GetMapping
    @PreAuthorize("hasRole('AGENT') or hasRole('ADMIN')")
    public ResponseEntity<Page<PolicyResponseDto>> getPolicies(
            @RequestParam(required = false) String customerId,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String policyType,
            Pageable pageable) {
        
        log.debug("Retrieving policies with filters - customerId: {}, status: {}, policyType: {}", 
                 customerId, status, policyType);
        
        Page<PolicyResponseDto> policies = policyService.getPolicies(customerId, status, policyType, pageable);
        return ResponseEntity.ok(policies);
    }

    @Operation(summary = "Update policy", description = "Updates an existing policy with validation")
    @PutMapping("/{policyId}")
    @PreAuthorize("hasRole('AGENT') or hasRole('ADMIN')")
    public ResponseEntity<PolicyResponseDto> updatePolicy(
            @PathVariable String policyId,
            @Valid @RequestBody PolicyDto policyDto) {
        
        log.info("Updating policy: {}", policyId);
        
        PolicyResponseDto response = policyService.updatePolicy(policyId, policyDto);
        
        log.info("Policy updated successfully: {}", policyId);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Cancel policy", description = "Cancels an active policy")
    @PatchMapping("/{policyId}/cancel")
    @PreAuthorize("hasRole('AGENT') or hasRole('ADMIN')")
    public ResponseEntity<PolicyResponseDto> cancelPolicy(@PathVariable String policyId) {
        log.info("Cancelling policy: {}", policyId);
        
        PolicyResponseDto response = policyService.cancelPolicy(policyId);
        
        log.info("Policy cancelled successfully: {}", policyId);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Get policy analytics", description = "Retrieves analytics data for policies")
    @GetMapping("/analytics")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Object> getPolicyAnalytics(
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate) {
        
        log.debug("Retrieving policy analytics for period: {} to {}", startDate, endDate);
        
        Object analytics = policyService.getPolicyAnalytics(startDate, endDate);
        return ResponseEntity.ok(analytics);
    }
}
