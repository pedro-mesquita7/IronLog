resource "aws_iam_user" "ci" {
  name = "${local.project}-ci"
}

# Broad permissions for CI/CD — single-user hobby project.
# Terraform's AWS provider reads tags, code signing, versions etc. on refresh,
# requiring many implicit permissions. Using service-level wildcards avoids
# chasing individual actions every time the provider adds a new API call.
resource "aws_iam_policy" "ci" {
  name = "${local.project}-ci-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "Lambda"
        Effect   = "Allow"
        Action   = "lambda:*"
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
        Action   = "apigateway:*"
        Resource = "arn:aws:apigateway:${data.aws_region.current.name}::*"
      },
      {
        Sid    = "S3"
        Effect = "Allow"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*",
          "arn:aws:s3:::ironlog-terraform-state",
          "arn:aws:s3:::ironlog-terraform-state/*",
        ]
      },
      {
        Sid      = "SSM"
        Effect   = "Allow"
        Action   = "ssm:*"
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
        Action   = "sns:*"
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
        Action   = ["logs:*", "cloudwatch:*"]
        Resource = "*"
      },
      {
        Sid      = "AthenaGlue"
        Effect   = "Allow"
        Action   = ["athena:*", "glue:*"]
        Resource = "*"
      },
      {
        Sid      = "EventBridge"
        Effect   = "Allow"
        Action   = "events:*"
        Resource = "arn:aws:events:${data.aws_region.current.name}:${local.account_id}:rule/${local.project}-*"
      },
    ]
  })
}

resource "aws_iam_user_policy_attachment" "ci" {
  user       = aws_iam_user.ci.name
  policy_arn = aws_iam_policy.ci.arn
}
