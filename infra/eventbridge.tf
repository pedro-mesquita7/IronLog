# --- WHOOP daily sync schedule ---

resource "aws_cloudwatch_event_rule" "whoop_sync" {
  name                = "${local.project}-whoop-sync"
  description         = "Daily WHOOP data sync at 06:00 UTC"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "whoop_sync" {
  rule = aws_cloudwatch_event_rule.whoop_sync.name
  arn  = aws_lambda_function.whoop_sync.arn
}

resource "aws_lambda_permission" "whoop_sync_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.whoop_sync.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.whoop_sync.arn
}
