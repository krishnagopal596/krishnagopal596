# Cloud-Native DevOps Platform - AWS Infrastructure
# Author: Krishna Gopal Madhavaram
# Email: krishnagopal596@gmail.com

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "devops-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "krishnagopal596"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name               = "${var.project_name}-vpc"
  cidr               = var.vpc_cidr
  azs                = slice(data.aws_availability_zones.available.names, 0, 3)
  private_subnets    = var.private_subnet_cidrs
  public_subnets     = var.public_subnet_cidrs
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# EKS Cluster Module
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${var.project_name}-cluster"
  cluster_version = var.kubernetes_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Node groups
  node_groups = {
    general = {
      instance_types = var.node_instance_types
      min_size      = var.node_min_size
      max_size      = var.node_max_size
      desired_size  = var.node_desired_size
      
      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "general"
      }
    }
    
    spot = {
      instance_types = var.spot_instance_types
      min_size      = 0
      max_size      = 5
      desired_size  = 0
      
      k8s_labels = {
        Environment = var.environment
        NodeGroup   = "spot"
      }
      
      taints = {
        spot = {
          key    = "spot"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }
  
  # Add-ons
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }
  
  # Security groups
  cluster_security_group_additional_rules = {
    ingress_https_from_alb = {
      description = "HTTPS from ALB"
      protocol    = "tcp"
      from_port   = 443
      to_port     = 443
      type        = "ingress"
      cidr_blocks = [module.vpc.vpc_cidr_block]
    }
  }
}

# RDS Database
module "rds" {
  source = "./modules/rds"
  
  identifier = "${var.project_name}-database"
  
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.database_instance_class
  
  allocated_storage     = var.database_allocated_storage
  max_allocated_storage = var.database_max_allocated_storage
  storage_encrypted     = true
  
  db_name  = var.database_name
  username  = var.database_username
  password  = var.database_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment == "production" ? false : true
  
  tags = {
    Name = "${var.project_name}-database"
  }
}

# ElastiCache Redis
module "redis" {
  source = "./modules/redis"
  
  cluster_id = "${var.project_name}-redis"
  
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_cache_nodes
  parameter_group_name = "default.redis7"
  
  subnet_group_name = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "${var.project_name}-redis"
  }
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name = "${var.project_name}-alb"
  
  vpc_id          = module.vpc.vpc_id
  subnets         = module.vpc.public_subnets
  security_groups = [aws_security_group.alb.id]
  
  # Target groups
  target_groups = {
    frontend = {
      name_prefix      = "frontend-"
      protocol         = "HTTP"
      port             = 80
      protocol_version = "HTTP1"
      target_type      = "ip"
      
      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }
    }
    
    backend = {
      name_prefix      = "backend-"
      protocol         = "HTTP"
      port             = 8080
      protocol_version = "HTTP1"
      target_type      = "ip"
      
      health_check = {
        enabled             = true
        healthy_threshold   = 2
        interval            = 30
        matcher             = "200"
        path                = "/actuator/health"
        port                = "traffic-port"
        protocol            = "HTTP"
        timeout             = 5
        unhealthy_threshold = 2
      }
    }
  }
  
  # Listeners
  http_tcp_listeners = [
    {
      port        = 80
      protocol    = "HTTP"
      action_type = "redirect"
      redirect = {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  ]
  
  https_listeners = [
    {
      port               = 443
      protocol           = "HTTPS"
      certificate_arn    = aws_acm_certificate.main.arn
      target_group_index = 0
    }
  ]
  
  tags = {
    Name = "${var.project_name}-alb"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "application_logs" {
  bucket = "${var.project_name}-application-logs-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name = "${var.project_name}-application-logs"
  }
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-terraform-state-${random_id.bucket_suffix.hex}"
  
  tags = {
    Name = "${var.project_name}-terraform-state"
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "${var.project_name}-redis-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_name}-redis-sg"
  }
}

resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# Database Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = module.vpc.private_subnets
  
  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-cache-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

# ACM Certificate
resource "aws_acm_certificate" "main" {
  domain_name       = var.domain_name
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
  
  tags = {
    Name = "${var.project_name}-certificate"
  }
}

# Route53 Zone
resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0
  name  = var.domain_name
  
  tags = {
    Name = "${var.project_name}-route53-zone"
  }
}

# Random ID for bucket suffixes
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Outputs
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.redis.cluster_address
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.alb.lb_dns_name
}

output "alb_zone_id" {
  description = "Application Load Balancer zone ID"
  value       = module.alb.lb_zone_id
}
