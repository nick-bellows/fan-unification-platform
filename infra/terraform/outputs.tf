output "lake_bucket" {
  value = aws_s3_bucket.lake.bucket
}

output "redshift_workgroup_endpoint" {
  value = aws_redshiftserverless_workgroup.warehouse.endpoint
}

output "copy_role_arn" {
  description = "Pass to COPY ... IAM_ROLE when loading from the lake."
  value       = aws_iam_role.redshift_copy.arn
}
