output "dynamodb_table_name" {
  value = aws_dynamodb_table.ironlog.name
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.ironlog.arn
}

output "dynamodb_stream_arn" {
  value = aws_dynamodb_table.ironlog.stream_arn
}

output "data_lake_bucket" {
  value = aws_s3_bucket.data_lake.bucket
}

output "api_gateway_id" {
  value = aws_api_gateway_rest_api.ironlog.id
}

output "api_gateway_root_resource_id" {
  value = aws_api_gateway_rest_api.ironlog.root_resource_id
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_exec.arn
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "api_gateway_invoke_url" {
  value = aws_api_gateway_stage.prod.invoke_url
}
