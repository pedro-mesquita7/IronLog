resource "random_password" "auth_token" {
  length  = 64
  special = false
}

resource "random_password" "jwt_secret" {
  length  = 32
  special = false
}

resource "aws_ssm_parameter" "auth_token" {
  name  = "/ironlog/auth-token"
  type  = "SecureString"
  value = random_password.auth_token.result

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/ironlog/jwt-secret"
  type  = "SecureString"
  value = random_password.jwt_secret.result

  lifecycle {
    ignore_changes = [value]
  }
}

# --- WHOOP OAuth tokens (user fills via aws ssm put-parameter) ---

resource "aws_ssm_parameter" "whoop_client_id" {
  name  = "/ironlog/whoop-client-id"
  type  = "SecureString"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "whoop_client_secret" {
  name  = "/ironlog/whoop-client-secret"
  type  = "SecureString"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "whoop_access_token" {
  name  = "/ironlog/whoop-access-token"
  type  = "SecureString"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "whoop_refresh_token" {
  name  = "/ironlog/whoop-refresh-token"
  type  = "SecureString"
  value = "placeholder"

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "whoop_refresh_token_expiry" {
  name  = "/ironlog/whoop-refresh-token-expiry"
  type  = "String"
  value = "2099-01-01T00:00:00Z"

  lifecycle {
    ignore_changes = [value]
  }
}
