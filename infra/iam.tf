resource "aws_iam_role" "lambda_exec" {
  name = "${local.project}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name = "${local.project}-lambda-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDB"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:BatchWriteItem",
        ]
        Resource = [
          aws_dynamodb_table.ironlog.arn,
          "${aws_dynamodb_table.ironlog.arn}/index/*",
        ]
      },
      {
        Sid    = "DynamoDBStreams"
        Effect = "Allow"
        Action = [
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:DescribeStream",
          "dynamodb:ListStreams",
        ]
        Resource = "${aws_dynamodb_table.ironlog.arn}/stream/*"
      },
      {
        Sid    = "SSMRead"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
        ]
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${local.account_id}:parameter/ironlog/*"
      },
      {
        Sid    = "SSMWriteWhoop"
        Effect = "Allow"
        Action = [
          "ssm:PutParameter",
        ]
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${local.account_id}:parameter/ironlog/whoop-*"
      },
      {
        Sid    = "SNSPublish"
        Effect = "Allow"
        Action = [
          "sns:Publish",
        ]
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Sid    = "S3"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/*"
      },
      {
        Sid    = "S3List"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
        ]
        Resource = aws_s3_bucket.data_lake.arn
      },
      {
        Sid    = "SQS"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
        ]
        Resource = aws_sqs_queue.cdc_dlq.arn
      },
      {
        Sid    = "Athena"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
        ]
        Resource = "arn:aws:athena:${data.aws_region.current.name}:${local.account_id}:workgroup/${local.project}"
      },
      {
        Sid    = "GlueRead"
        Effect = "Allow"
        Action = [
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetPartitions",
        ]
        Resource = [
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:catalog",
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:database/${local.project}",
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:database/gold",
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:database/silver",
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:table/${local.project}/*",
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:table/gold/*",
          "arn:aws:glue:${data.aws_region.current.name}:${local.account_id}:table/silver/*",
        ]
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${local.account_id}:*"
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}
