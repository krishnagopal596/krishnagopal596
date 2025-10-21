package com.insurance.policy;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.EnableEurekaClient;
import org.springframework.kafka.annotation.EnableKafka;

/**
 * Policy Service - Core microservice for insurance policy management
 * 
 * Features:
 * - Policy CRUD operations
 * - Policy validation and business rules
 * - Integration with billing and claims services
 * - Real-time policy updates via Kafka
 * 
 * @author Krishna Gopal Madhavaram
 * @version 1.0
 */
@SpringBootApplication
@EnableEurekaClient
@EnableKafka
public class PolicyServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(PolicyServiceApplication.class, args);
    }
}
