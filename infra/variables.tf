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

variable "parser_model" {
  type    = string
  default = "us.anthropic.claude-sonnet-4-6"
}

variable "parser_code_key" {
  type        = string
  default     = "agenda-parser.zip"
  description = "S3 key of the parser zip in the code bucket"
}

# ---- The weekly report (Lab 5) ----

variable "builder_image_uri" {
  type    = string
  default = "438424053032.dkr.ecr.eu-central-1.amazonaws.com/spry-backend:latest"
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "database_url" {
  type        = string
  sensitive   = true
  description = "Connection string of the Aurora database, for report-builder"
}

variable "recipient_email" {
  type        = string
  description = "Verified SES address that receives the weekly report"
}
