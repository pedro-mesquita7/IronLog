terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket  = "ironlog-terraform-state"
    key     = "ironlog/terraform.tfstate"
    region  = "eu-west-3"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  project     = "ironlog"
  environment = "prod"
  account_id  = data.aws_caller_identity.current.account_id
  cors_origin          = "*"
  cors_allowed_origins = "https://pedro-mesquita7.github.io,http://localhost:5173"

  common_tags = {
    Project     = "ironlog"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}
