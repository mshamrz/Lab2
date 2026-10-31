variable "region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type = string
}

variable "cognito_domain_prefix" {
  type        = string
  description = "Prefix of the Cognito hosted domain"
}

variable "app_domain" {
  type        = string
  description = "Domain of the deployed site, used in Cognito callback URLs"
}

variable "google_client_id" {
  type        = string
  description = "OAuth client id of the Google project from Lab 4"
}

variable "google_client_secret" {
  type        = string
  sensitive   = true
  description = "OAuth client secret of the Google project from Lab 4"
}
