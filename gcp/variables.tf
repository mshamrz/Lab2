variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "spry-auth"
}

variable "region" {
  description = "The Google Cloud region to deploy resources into"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Name of the Cloud Run API service"
  type        = string
  default     = "spry-api"
}

variable "db_instance_name" {
  description = "Name prefix for the Cloud SQL PostgreSQL instance"
  type        = string
  default     = "spry-db"
}

variable "db_name" {
  description = "Database name inside Cloud SQL"
  type        = string
  default     = "spry"
}

variable "db_user" {
  description = "Database user for Spry"
  type        = string
  default     = "spry"
}
