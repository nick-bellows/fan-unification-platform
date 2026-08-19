variable "region" {
  type    = string
  default = "us-east-1"
}

variable "name_prefix" {
  type    = string
  default = "fanuni"
}

variable "lake_bucket_name" {
  description = "Globally unique S3 bucket name for the lake."
  type        = string
  default     = "fanuni-lake-example" # override per account
}

variable "base_capacity_rpus" {
  description = "Redshift Serverless base capacity. 8 is the minimum — and the reason this module stays unapplied for a portfolio."
  type        = number
  default     = 8
}
