resource "aws_iam_user" "ci" {
  name = "${local.project}-ci"
}

resource "aws_iam_policy" "ci" {
  name = "${local.project}-ci-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Lambda"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "lambda:GetFunction",
          "lambda:ListFunctions",
          "lambda:ListVersionsByFunction",
          "lambda:DeleteFunction",
          "lambda:AddPermission",
          "lambda:RemovePermission",
          "lambda:InvokeFunction",
          "lambda:GetPolicy",
          "lambda:CreateEventSourceMapping",
          "lambda:DeleteEventSourceMapping",
          "lambda:GetEventSourceMapping",
          "lambda:ListEventSourceMappings",
          "lambda:UpdateEventSourceMapping",
          "lambda:PublishLayerVersion",
          "lambda:GetLayerVersion",
          "lambda:DeleteLayerVersion",
          "lambda:ListLayerVersions",
          "lambda:ListTags",
          "lambda:TagResource",
        ]
        Resource = "*"
      },
      {
        Sid    = "IAM"
        Effect = "Allow"
        Action = [
          "iam:PassRole",
          "iam:GetRole",
          "iam:GetPolicy",
          "iam:GetPolicyVersion",
          "iam:GetRolePolicy",
          "iam:ListRolePolicies",
          "iam:ListAttachedRolePolicies",
          "iam:ListAttachedUserPolicies",
          "iam:CreatePolicy",
          "iam:CreatePolicyVersion",
          "iam:DeletePolicyVersion",
          "iam:AttachRolePolicy",
          "iam:DetachRolePolicy",
          "iam:PutRolePolicy",
          "iam:ListInstanceProfilesForRole",
          "iam:GetUser",
          "iam:GetUserPolicy",
          "iam:PutUserPolicy",
        ]
        Resource = [
          "arn:aws:iam::${local.account_id}:role/${local.project}-*",
          "arn:aws:iam::${local.account_id}:policy/${local.project}-*",
          "arn:aws:iam::${local.account_id}:user/${local.project}-*",
        ]
      },
      {
        Sid      = "APIGateway"
        Effect   = "Allow"
        Action   = ["apigateway:GET", "apigateway:POST", "apigateway:PUT", "apigateway:DELETE", "apigateway:PATCH"]
        Resource = "arn:aws:apigateway:${data.aws_region.current.name}::*"
      },
      {
        Sid    = "S3"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket", "s3:GetBucket*", "s3:GetEncryptionConfiguration", "s3:GetAccelerateConfiguration", "s3:GetLifecycleConfiguration", "s3:GetReplicationConfiguration"]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*",
          "arn:aws:s3:::ironlog-terraform-state",
          "arn:aws:s3:::ironlog-terraform-state/*",
        ]
      },
      {
        Sid    = "SSM"
        Effect = "Allow"
        Action = ["ssm:GetParameter", "ssm:GetParameters", "ssm:PutParameter", "ssm:AddTagsToResource"]
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${local.account_id}:parameter/ironlog/*"
      },
      {
        Sid      = "SSMGlobal"
        Effect   = "Allow"
        Action   = ["ssm:DescribeParameters", "ssm:ListTagsForResource"]
        Resource = "*"
      },
      {
        Sid      = "DynamoDB"
        Effect   = "Allow"
        Action   = ["dynamodb:DescribeTable", "dynamodb:DescribeContinuousBackups", "dynamodb:DescribeTimeToLive", "dynamodb:ListTagsOfResource"]
        Resource = aws_dynamodb_table.ironlog.arn
      },
      {
        Sid      = "SNS"
        Effect   = "Allow"
        Action   = ["sns:GetTopicAttributes", "sns:ListSubscriptionsByTopic", "sns:GetSubscriptionAttributes", "sns:ListTagsForResource"]
        Resource = aws_sns_topic.alerts.arn
      },
      {
        Sid      = "SQS"
        Effect   = "Allow"
        Action   = ["sqs:GetQueueAttributes", "sqs:GetQueueUrl", "sqs:ListQueueTags"]
        Resource = aws_sqs_queue.cdc_dlq.arn
      },
      {
        Sid      = "CloudWatch"
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:DescribeLogGroups", "logs:PutRetentionPolicy", "cloudwatch:DescribeAlarms", "cloudwatch:PutMetricAlarm", "cloudwatch:DeleteAlarms", "cloudwatch:ListTagsForResource"]
        Resource = "*"
      },
      {
        Sid      = "AthenaGlue"
        Effect   = "Allow"
        Action   = ["athena:GetWorkGroup", "athena:CreateWorkGroup", "athena:UpdateWorkGroup", "athena:DeleteWorkGroup", "athena:ListTagsForResource", "glue:GetDatabase", "glue:CreateDatabase", "glue:UpdateDatabase", "glue:DeleteDatabase", "glue:GetTable", "glue:CreateTable", "glue:UpdateTable", "glue:DeleteTable", "glue:GetTables", "glue:BatchCreatePartition", "glue:GetPartitions", "glue:GetTags"]
        Resource = "*"
      },
      {
        Sid      = "EventBridge"
        Effect   = "Allow"
        Action   = ["events:DescribeRule", "events:PutRule", "events:DeleteRule", "events:PutTargets", "events:RemoveTargets", "events:ListTargetsByRule", "events:ListTagsForResource"]
        Resource = "arn:aws:events:${data.aws_region.current.name}:${local.account_id}:rule/${local.project}-*"
      },
    ]
  })
}

resource "aws_iam_user_policy_attachment" "ci" {
  user       = aws_iam_user.ci.name
  policy_arn = aws_iam_policy.ci.arn
}
