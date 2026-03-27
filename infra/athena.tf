resource "aws_athena_workgroup" "ironlog" {
  name          = local.project
  force_destroy = true

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.bucket}/athena-results/"
    }
  }
}

resource "aws_glue_catalog_database" "ironlog" {
  name = local.project
}
