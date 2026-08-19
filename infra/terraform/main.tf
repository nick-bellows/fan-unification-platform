# The real-AWS deployment this repo emulates locally (ADR 0002): S3 lake,
# Redshift Serverless warehouse, and the IAM role Redshift assumes for COPY.
# Validated in CI (init -backend=false && validate); never applied — applying
# would cost real money and the portfolio runs at $0.

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "lake" {
  bucket = var.lake_bucket_name
}

resource "aws_s3_bucket_public_access_block" "lake" {
  bucket                  = aws_s3_bucket.lake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  bucket = aws_s3_bucket.lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

data "aws_iam_policy_document" "redshift_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["redshift.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lake_read" {
  statement {
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.lake.arn, "${aws_s3_bucket.lake.arn}/*"]
  }
}

resource "aws_iam_role" "redshift_copy" {
  name               = "${var.name_prefix}-redshift-copy"
  assume_role_policy = data.aws_iam_policy_document.redshift_assume.json
}

resource "aws_iam_role_policy" "redshift_copy_lake_read" {
  name   = "lake-read"
  role   = aws_iam_role.redshift_copy.id
  policy = data.aws_iam_policy_document.lake_read.json
}

resource "aws_redshiftserverless_namespace" "warehouse" {
  namespace_name        = "${var.name_prefix}-ns"
  db_name               = "fanuni"
  iam_roles             = [aws_iam_role.redshift_copy.arn]
  manage_admin_password = true # credentials live in Secrets Manager, not code
}

resource "aws_redshiftserverless_workgroup" "warehouse" {
  workgroup_name      = "${var.name_prefix}-wg"
  namespace_name      = aws_redshiftserverless_namespace.warehouse.namespace_name
  base_capacity       = var.base_capacity_rpus
  publicly_accessible = false
}
