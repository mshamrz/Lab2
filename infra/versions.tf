terraform {
  required_version = ">= 1.10"

  cloud {
    organization = "ooad-mshamrz"

    workspaces {
      name = "spry-dev"
    }
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.7"
    }
  }
}

# Cognito and the agenda parser live in us-east-1.
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      PROJECT_NAME = var.project_name
      ManagedBy    = "terraform"
    }
  }
}

# The weekly report (Lab 5) was deployed in Frankfurt.
provider "aws" {
  alias  = "eu"
  region = "eu-central-1"

  default_tags {
    tags = {
      PROJECT_NAME = var.project_name
      ManagedBy    = "terraform"
    }
  }
}
