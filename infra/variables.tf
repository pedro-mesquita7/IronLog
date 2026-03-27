variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "alert_phone" {
  description = "Phone number for SNS SMS alerts (E.164 format)"
  type        = string
  sensitive   = true
}
