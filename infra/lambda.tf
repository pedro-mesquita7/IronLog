# --- Lambda packaging ---

# Application code (handlers + shared)
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../backend"
  output_path = "${path.module}/../build/lambda.zip"
  excludes    = ["tests", "tests/**", "requirements.txt", "requirements-dev.txt", "__pycache__", "*.pyc", ".venv", ".pytest_cache"]
}

# PyJWT dependency layer — built via local-exec
resource "null_resource" "pip_layer" {
  triggers = {
    requirements = filemd5("${path.module}/../backend/requirements.txt")
  }

  provisioner "local-exec" {
    command     = "pip install PyJWT -t \"${path.module}/../build/layer/python\" --upgrade --no-deps --quiet"
    interpreter = ["bash", "-c"]
  }
}

data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "${path.module}/../build/layer"
  output_path = "${path.module}/../build/layer.zip"
  depends_on  = [null_resource.pip_layer]
}

resource "aws_lambda_layer_version" "deps" {
  filename            = data.archive_file.lambda_layer.output_path
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256
  layer_name          = "${local.project}-deps"
  compatible_runtimes = ["python3.13"]
}

# --- Lambda functions ---

resource "aws_lambda_function" "auth" {
  function_name    = "${local.project}-auth"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.auth.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "equipment" {
  function_name    = "${local.project}-equipment"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.equipment.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "exercises" {
  function_name    = "${local.project}-exercises"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.exercises.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "plans" {
  function_name    = "${local.project}-plans"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.plans.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "sessions" {
  function_name    = "${local.project}-sessions"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.sessions.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "sets" {
  function_name    = "${local.project}-sets"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.sets.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "corrections" {
  function_name    = "${local.project}-corrections"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.corrections.handler"
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

resource "aws_lambda_function" "seed" {
  function_name    = "${local.project}-seed"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.seed.handler"
  runtime          = "python3.13"
  timeout          = 30
  memory_size      = 128
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN    = local.cors_allowed_origins
    }
  }
}

# --- API Gateway permissions ---

resource "aws_lambda_permission" "auth_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "equipment_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.equipment.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "exercises_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.exercises.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "plans_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.plans.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "sessions_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sessions.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "sets_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.sets.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "corrections_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.corrections.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "seed_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.seed.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_function" "analytics" {
  function_name    = "${local.project}-analytics"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.analytics.handler"
  runtime          = "python3.13"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME         = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN     = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET     = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN        = local.cors_allowed_origins
      ATHENA_WORKGROUP     = aws_athena_workgroup.ironlog.name
      ATHENA_DATABASE      = aws_glue_catalog_database.ironlog.name
      ATHENA_GOLD_DATABASE = "gold"
      ATHENA_OUTPUT_BUCKET = aws_s3_bucket.data_lake.bucket
    }
  }
}

resource "aws_lambda_function" "export" {
  function_name    = "${local.project}-export"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.export.handler"
  runtime          = "python3.13"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      TABLE_NAME           = aws_dynamodb_table.ironlog.name
      SSM_AUTH_TOKEN       = aws_ssm_parameter.auth_token.name
      SSM_JWT_SECRET       = aws_ssm_parameter.jwt_secret.name
      CORS_ORIGIN          = local.cors_allowed_origins
      ATHENA_WORKGROUP     = aws_athena_workgroup.ironlog.name
      ATHENA_DATABASE      = aws_glue_catalog_database.ironlog.name
      ATHENA_GOLD_DATABASE = "gold"
      ATHENA_OUTPUT_BUCKET = aws_s3_bucket.data_lake.bucket
    }
  }
}

resource "aws_lambda_permission" "analytics_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.analytics.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

resource "aws_lambda_permission" "export_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.export.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.ironlog.execution_arn}/*/*"
}

# --- CDC Pipeline ---

resource "aws_sqs_queue" "cdc_dlq" {
  name                      = "${local.project}-cdc-dlq"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_lambda_function" "cdc" {
  function_name    = "${local.project}-cdc"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.cdc.handler"
  runtime          = "python3.13"
  timeout          = 60
  memory_size      = 256
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      DATA_LAKE_BUCKET = aws_s3_bucket.data_lake.bucket
    }
  }
}

# --- WHOOP Sync ---

resource "aws_lambda_function" "whoop_sync" {
  function_name    = "${local.project}-whoop-sync"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handlers.whoop_sync.handler"
  runtime          = "python3.13"
  timeout          = 60
  memory_size      = 256
  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      DATA_LAKE_BUCKET               = aws_s3_bucket.data_lake.bucket
      SSM_WHOOP_CLIENT_ID            = aws_ssm_parameter.whoop_client_id.name
      SSM_WHOOP_CLIENT_SECRET        = aws_ssm_parameter.whoop_client_secret.name
      SSM_WHOOP_ACCESS_TOKEN         = aws_ssm_parameter.whoop_access_token.name
      SSM_WHOOP_REFRESH_TOKEN        = aws_ssm_parameter.whoop_refresh_token.name
      SSM_WHOOP_REFRESH_TOKEN_EXPIRY = aws_ssm_parameter.whoop_refresh_token_expiry.name
      SNS_TOPIC_ARN                  = aws_sns_topic.alerts.arn
    }
  }
}

resource "aws_lambda_event_source_mapping" "cdc_stream" {
  event_source_arn  = aws_dynamodb_table.ironlog.stream_arn
  function_name     = aws_lambda_function.cdc.arn
  starting_position = "LATEST"
  batch_size        = 100

  maximum_batching_window_in_seconds = 60
  bisect_batch_on_function_error     = true
  maximum_retry_attempts             = 3
  maximum_record_age_in_seconds      = 86400

  destination_config {
    on_failure {
      destination_arn = aws_sqs_queue.cdc_dlq.arn
    }
  }
}
