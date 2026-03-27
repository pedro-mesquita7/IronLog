resource "aws_api_gateway_rest_api" "ironlog" {
  name        = "${local.project}-api"
  description = "IronLog Gym Tracker API"
}

resource "aws_api_gateway_gateway_response" "cors_4xx" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  response_type = "DEFAULT_4XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  }
}

resource "aws_api_gateway_gateway_response" "cors_5xx" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  response_type = "DEFAULT_5XX"

  response_parameters = {
    "gatewayresponse.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
    "gatewayresponse.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "gatewayresponse.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  }
}

# --- Resource hierarchy ---

resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_rest_api.ironlog.root_resource_id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "login" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "login"
}

resource "aws_api_gateway_resource" "equipment" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "equipment"
}

resource "aws_api_gateway_resource" "equipment_id" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.equipment.id
  path_part   = "{id}"
}

# --- POST /api/auth/login ---

resource "aws_api_gateway_method" "login_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.login.id
  http_method             = aws_api_gateway_method.login_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.auth.invoke_arn
}

# --- GET /api/equipment ---

resource "aws_api_gateway_method" "equipment_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.equipment.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "equipment_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.equipment.id
  http_method             = aws_api_gateway_method.equipment_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.equipment.invoke_arn
}

# --- POST /api/equipment ---

resource "aws_api_gateway_method" "equipment_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.equipment.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "equipment_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.equipment.id
  http_method             = aws_api_gateway_method.equipment_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.equipment.invoke_arn
}

# --- PUT /api/equipment/{id} ---

resource "aws_api_gateway_method" "equipment_id_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.equipment_id.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "equipment_id_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.equipment_id.id
  http_method             = aws_api_gateway_method.equipment_id_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.equipment.invoke_arn
}

# --- DELETE /api/equipment/{id} ---

resource "aws_api_gateway_method" "equipment_id_delete" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.equipment_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "equipment_id_delete" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.equipment_id.id
  http_method             = aws_api_gateway_method.equipment_id_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.equipment.invoke_arn
}

# --- CORS OPTIONS methods ---

# OPTIONS /api/auth/login
resource "aws_api_gateway_method" "login_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "login_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "login_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login_options.http_method
  status_code = aws_api_gateway_method_response.login_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# OPTIONS /api/equipment
resource "aws_api_gateway_method" "equipment_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.equipment.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "equipment_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.equipment.id
  http_method = aws_api_gateway_method.equipment_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "equipment_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.equipment.id
  http_method = aws_api_gateway_method.equipment_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "equipment_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.equipment.id
  http_method = aws_api_gateway_method.equipment_options.http_method
  status_code = aws_api_gateway_method_response.equipment_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# OPTIONS /api/equipment/{id}
resource "aws_api_gateway_method" "equipment_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.equipment_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "equipment_id_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.equipment_id.id
  http_method = aws_api_gateway_method.equipment_id_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "equipment_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.equipment_id.id
  http_method = aws_api_gateway_method.equipment_id_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "equipment_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.equipment_id.id
  http_method = aws_api_gateway_method.equipment_id_options.http_method
  status_code = aws_api_gateway_method_response.equipment_id_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# === EXERCISES ===

resource "aws_api_gateway_resource" "exercises" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "exercises"
}

resource "aws_api_gateway_resource" "exercises_id" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.exercises.id
  path_part   = "{id}"
}

# GET /api/exercises
resource "aws_api_gateway_method" "exercises_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.exercises.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "exercises_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.exercises.id
  http_method             = aws_api_gateway_method.exercises_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.exercises.invoke_arn
}

# POST /api/exercises
resource "aws_api_gateway_method" "exercises_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.exercises.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "exercises_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.exercises.id
  http_method             = aws_api_gateway_method.exercises_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.exercises.invoke_arn
}

# PUT /api/exercises/{id}
resource "aws_api_gateway_method" "exercises_id_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.exercises_id.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "exercises_id_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.exercises_id.id
  http_method             = aws_api_gateway_method.exercises_id_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.exercises.invoke_arn
}

# DELETE /api/exercises/{id}
resource "aws_api_gateway_method" "exercises_id_delete" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.exercises_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "exercises_id_delete" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.exercises_id.id
  http_method             = aws_api_gateway_method.exercises_id_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.exercises.invoke_arn
}

# OPTIONS /api/exercises
resource "aws_api_gateway_method" "exercises_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.exercises.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "exercises_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.exercises.id
  http_method = aws_api_gateway_method.exercises_options.http_method
  type        = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "exercises_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.exercises.id
  http_method = aws_api_gateway_method.exercises_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "exercises_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.exercises.id
  http_method = aws_api_gateway_method.exercises_options.http_method
  status_code = aws_api_gateway_method_response.exercises_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# OPTIONS /api/exercises/{id}
resource "aws_api_gateway_method" "exercises_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.exercises_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "exercises_id_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.exercises_id.id
  http_method = aws_api_gateway_method.exercises_id_options.http_method
  type        = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "exercises_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.exercises_id.id
  http_method = aws_api_gateway_method.exercises_id_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "exercises_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.exercises_id.id
  http_method = aws_api_gateway_method.exercises_id_options.http_method
  status_code = aws_api_gateway_method_response.exercises_id_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# === PLANS ===

resource "aws_api_gateway_resource" "plans" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "plans"
}

resource "aws_api_gateway_resource" "plans_id" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.plans.id
  path_part   = "{id}"
}

resource "aws_api_gateway_resource" "plans_id_activate" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.plans_id.id
  path_part   = "activate"
}

# GET /api/plans
resource "aws_api_gateway_method" "plans_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.plans.id
  http_method             = aws_api_gateway_method.plans_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.plans.invoke_arn
}

# POST /api/plans
resource "aws_api_gateway_method" "plans_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.plans.id
  http_method             = aws_api_gateway_method.plans_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.plans.invoke_arn
}

# GET /api/plans/{id}
resource "aws_api_gateway_method" "plans_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans_id.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_id_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.plans_id.id
  http_method             = aws_api_gateway_method.plans_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.plans.invoke_arn
}

# PUT /api/plans/{id}
resource "aws_api_gateway_method" "plans_id_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans_id.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_id_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.plans_id.id
  http_method             = aws_api_gateway_method.plans_id_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.plans.invoke_arn
}

# DELETE /api/plans/{id}
resource "aws_api_gateway_method" "plans_id_delete" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_id_delete" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.plans_id.id
  http_method             = aws_api_gateway_method.plans_id_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.plans.invoke_arn
}

# PUT /api/plans/{id}/activate
resource "aws_api_gateway_method" "plans_id_activate_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans_id_activate.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_id_activate_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.plans_id_activate.id
  http_method             = aws_api_gateway_method.plans_id_activate_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.plans.invoke_arn
}

# OPTIONS /api/plans
resource "aws_api_gateway_method" "plans_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans.id
  http_method = aws_api_gateway_method.plans_options.http_method
  type        = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "plans_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans.id
  http_method = aws_api_gateway_method.plans_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "plans_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans.id
  http_method = aws_api_gateway_method.plans_options.http_method
  status_code = aws_api_gateway_method_response.plans_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# OPTIONS /api/plans/{id}
resource "aws_api_gateway_method" "plans_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_id_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans_id.id
  http_method = aws_api_gateway_method.plans_id_options.http_method
  type        = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "plans_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans_id.id
  http_method = aws_api_gateway_method.plans_id_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "plans_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans_id.id
  http_method = aws_api_gateway_method.plans_id_options.http_method
  status_code = aws_api_gateway_method_response.plans_id_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# OPTIONS /api/plans/{id}/activate
resource "aws_api_gateway_method" "plans_id_activate_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.plans_id_activate.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "plans_id_activate_options" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans_id_activate.id
  http_method = aws_api_gateway_method.plans_id_activate_options.http_method
  type        = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "plans_id_activate_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans_id_activate.id
  http_method = aws_api_gateway_method.plans_id_activate_options.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "plans_id_activate_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.plans_id_activate.id
  http_method = aws_api_gateway_method.plans_id_activate_options.http_method
  status_code = aws_api_gateway_method_response.plans_id_activate_options_200.status_code
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${local.cors_origin}'"
  }
}

# === SESSIONS ===

resource "aws_api_gateway_resource" "sessions" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "sessions"
}

resource "aws_api_gateway_resource" "sessions_id" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.sessions.id
  path_part   = "{id}"
}

resource "aws_api_gateway_resource" "sessions_id_complete" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.sessions_id.id
  path_part   = "complete"
}

resource "aws_api_gateway_resource" "sessions_id_sets" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.sessions_id.id
  path_part   = "sets"
}

resource "aws_api_gateway_resource" "sessions_id_sets_sid" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.sessions_id_sets.id
  path_part   = "{sid}"
}

resource "aws_api_gateway_resource" "sessions_id_notes" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.sessions_id.id
  path_part   = "notes"
}

# POST /api/sessions
resource "aws_api_gateway_method" "sessions_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions.id
  http_method             = aws_api_gateway_method.sessions_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# GET /api/sessions
resource "aws_api_gateway_method" "sessions_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions.id
  http_method             = aws_api_gateway_method.sessions_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# GET /api/sessions/{id}
resource "aws_api_gateway_method" "sessions_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id.id
  http_method             = aws_api_gateway_method.sessions_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# PUT /api/sessions/{id}
resource "aws_api_gateway_method" "sessions_id_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id.id
  http_method   = "PUT"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id.id
  http_method             = aws_api_gateway_method.sessions_id_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# PUT /api/sessions/{id}/complete
resource "aws_api_gateway_method" "sessions_id_complete_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_complete.id
  http_method   = "PUT"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_complete_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id_complete.id
  http_method             = aws_api_gateway_method.sessions_id_complete_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# POST /api/sessions/{id}/sets
resource "aws_api_gateway_method" "sessions_id_sets_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_sets.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_sets_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id_sets.id
  http_method             = aws_api_gateway_method.sessions_id_sets_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sets.invoke_arn
}

# PUT /api/sessions/{id}/sets/{sid}
resource "aws_api_gateway_method" "sessions_id_sets_sid_put" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method   = "PUT"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_sets_sid_put" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method             = aws_api_gateway_method.sessions_id_sets_sid_put.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sets.invoke_arn
}

# DELETE /api/sessions/{id}/sets/{sid}
resource "aws_api_gateway_method" "sessions_id_sets_sid_delete" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method   = "DELETE"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_sets_sid_delete" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method             = aws_api_gateway_method.sessions_id_sets_sid_delete.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sets.invoke_arn
}

# POST /api/sessions/{id}/notes
resource "aws_api_gateway_method" "sessions_id_notes_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_notes.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_notes_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id_notes.id
  http_method             = aws_api_gateway_method.sessions_id_notes_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# GET /api/sessions/{id}/notes
resource "aws_api_gateway_method" "sessions_id_notes_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_notes.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_notes_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.sessions_id_notes.id
  http_method             = aws_api_gateway_method.sessions_id_notes_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.sessions.invoke_arn
}

# === CORRECTIONS ===

resource "aws_api_gateway_resource" "corrections" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "corrections"
}

# POST /api/corrections
resource "aws_api_gateway_method" "corrections_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.corrections.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "corrections_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.corrections.id
  http_method             = aws_api_gateway_method.corrections_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.corrections.invoke_arn
}

# GET /api/corrections
resource "aws_api_gateway_method" "corrections_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.corrections.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "corrections_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.corrections.id
  http_method             = aws_api_gateway_method.corrections_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.corrections.invoke_arn
}

resource "aws_api_gateway_resource" "seed" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "seed"
}

# POST /api/seed
resource "aws_api_gateway_method" "seed_post" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.seed.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "seed_post" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.seed.id
  http_method             = aws_api_gateway_method.seed_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.seed.invoke_arn
}

# === CORS OPTIONS for sessions/sets/corrections/seed ===

# OPTIONS /api/sessions
resource "aws_api_gateway_method" "sessions_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.sessions.id
  http_method       = aws_api_gateway_method.sessions_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "sessions_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.sessions_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "sessions_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions.id
  http_method = aws_api_gateway_method.sessions_options.http_method
  status_code = aws_api_gateway_method_response.sessions_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/sessions/{id}
resource "aws_api_gateway_method" "sessions_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.sessions_id.id
  http_method       = aws_api_gateway_method.sessions_id_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "sessions_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id.id
  http_method = aws_api_gateway_method.sessions_id_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "sessions_id_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id.id
  http_method = aws_api_gateway_method.sessions_id_options.http_method
  status_code = aws_api_gateway_method_response.sessions_id_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/sessions/{id}/complete
resource "aws_api_gateway_method" "sessions_id_complete_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_complete.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_complete_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.sessions_id_complete.id
  http_method       = aws_api_gateway_method.sessions_id_complete_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "sessions_id_complete_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_complete.id
  http_method = aws_api_gateway_method.sessions_id_complete_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "sessions_id_complete_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_complete.id
  http_method = aws_api_gateway_method.sessions_id_complete_options.http_method
  status_code = aws_api_gateway_method_response.sessions_id_complete_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/sessions/{id}/sets
resource "aws_api_gateway_method" "sessions_id_sets_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_sets.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_sets_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.sessions_id_sets.id
  http_method       = aws_api_gateway_method.sessions_id_sets_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "sessions_id_sets_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_sets.id
  http_method = aws_api_gateway_method.sessions_id_sets_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "sessions_id_sets_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_sets.id
  http_method = aws_api_gateway_method.sessions_id_sets_options.http_method
  status_code = aws_api_gateway_method_response.sessions_id_sets_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/sessions/{id}/sets/{sid}
resource "aws_api_gateway_method" "sessions_id_sets_sid_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_sets_sid_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method       = aws_api_gateway_method.sessions_id_sets_sid_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "sessions_id_sets_sid_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method = aws_api_gateway_method.sessions_id_sets_sid_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "sessions_id_sets_sid_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_sets_sid.id
  http_method = aws_api_gateway_method.sessions_id_sets_sid_options.http_method
  status_code = aws_api_gateway_method_response.sessions_id_sets_sid_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/sessions/{id}/notes
resource "aws_api_gateway_method" "sessions_id_notes_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.sessions_id_notes.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "sessions_id_notes_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.sessions_id_notes.id
  http_method       = aws_api_gateway_method.sessions_id_notes_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "sessions_id_notes_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_notes.id
  http_method = aws_api_gateway_method.sessions_id_notes_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "sessions_id_notes_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.sessions_id_notes.id
  http_method = aws_api_gateway_method.sessions_id_notes_options.http_method
  status_code = aws_api_gateway_method_response.sessions_id_notes_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/corrections
resource "aws_api_gateway_method" "corrections_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.corrections.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "corrections_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.corrections.id
  http_method       = aws_api_gateway_method.corrections_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "corrections_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.corrections.id
  http_method = aws_api_gateway_method.corrections_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "corrections_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.corrections.id
  http_method = aws_api_gateway_method.corrections_options.http_method
  status_code = aws_api_gateway_method_response.corrections_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/seed
resource "aws_api_gateway_method" "seed_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.seed.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "seed_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.seed.id
  http_method       = aws_api_gateway_method.seed_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "seed_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.seed.id
  http_method = aws_api_gateway_method.seed_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "seed_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.seed.id
  http_method = aws_api_gateway_method.seed_options.http_method
  status_code = aws_api_gateway_method_response.seed_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# === Analytics + Export resources ===

resource "aws_api_gateway_resource" "analytics" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "analytics"
}

resource "aws_api_gateway_resource" "analytics_progression" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.analytics.id
  path_part   = "progression"
}

resource "aws_api_gateway_resource" "analytics_recovery_correlation" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.analytics.id
  path_part   = "recovery-correlation"
}

resource "aws_api_gateway_resource" "analytics_prs" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.analytics.id
  path_part   = "prs"
}

resource "aws_api_gateway_resource" "export" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "export"
}

# GET /api/analytics/progression
resource "aws_api_gateway_method" "analytics_progression_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.analytics_progression.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "analytics_progression_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.analytics_progression.id
  http_method             = aws_api_gateway_method.analytics_progression_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.analytics.invoke_arn
}

# GET /api/analytics/recovery-correlation
resource "aws_api_gateway_method" "analytics_recovery_correlation_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.analytics_recovery_correlation.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "analytics_recovery_correlation_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.analytics_recovery_correlation.id
  http_method             = aws_api_gateway_method.analytics_recovery_correlation_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.analytics.invoke_arn
}

# GET /api/analytics/prs
resource "aws_api_gateway_method" "analytics_prs_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.analytics_prs.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "analytics_prs_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.analytics_prs.id
  http_method             = aws_api_gateway_method.analytics_prs_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.analytics.invoke_arn
}

# GET /api/export
resource "aws_api_gateway_method" "export_get" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.export.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "export_get" {
  rest_api_id             = aws_api_gateway_rest_api.ironlog.id
  resource_id             = aws_api_gateway_resource.export.id
  http_method             = aws_api_gateway_method.export_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.export.invoke_arn
}

# OPTIONS /api/analytics/progression
resource "aws_api_gateway_method" "analytics_progression_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.analytics_progression.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "analytics_progression_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.analytics_progression.id
  http_method       = aws_api_gateway_method.analytics_progression_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "analytics_progression_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.analytics_progression.id
  http_method = aws_api_gateway_method.analytics_progression_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "analytics_progression_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.analytics_progression.id
  http_method = aws_api_gateway_method.analytics_progression_options.http_method
  status_code = aws_api_gateway_method_response.analytics_progression_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/analytics/recovery-correlation
resource "aws_api_gateway_method" "analytics_recovery_correlation_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.analytics_recovery_correlation.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "analytics_recovery_correlation_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.analytics_recovery_correlation.id
  http_method       = aws_api_gateway_method.analytics_recovery_correlation_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "analytics_recovery_correlation_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.analytics_recovery_correlation.id
  http_method = aws_api_gateway_method.analytics_recovery_correlation_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "analytics_recovery_correlation_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.analytics_recovery_correlation.id
  http_method = aws_api_gateway_method.analytics_recovery_correlation_options.http_method
  status_code = aws_api_gateway_method_response.analytics_recovery_correlation_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/analytics/prs
resource "aws_api_gateway_method" "analytics_prs_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.analytics_prs.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "analytics_prs_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.analytics_prs.id
  http_method       = aws_api_gateway_method.analytics_prs_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "analytics_prs_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.analytics_prs.id
  http_method = aws_api_gateway_method.analytics_prs_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "analytics_prs_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.analytics_prs.id
  http_method = aws_api_gateway_method.analytics_prs_options.http_method
  status_code = aws_api_gateway_method_response.analytics_prs_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# OPTIONS /api/export
resource "aws_api_gateway_method" "export_options" {
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  resource_id   = aws_api_gateway_resource.export.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "export_options" {
  rest_api_id       = aws_api_gateway_rest_api.ironlog.id
  resource_id       = aws_api_gateway_resource.export.id
  http_method       = aws_api_gateway_method.export_options.http_method
  type              = "MOCK"
  request_templates = { "application/json" = "{\"statusCode\": 200}" }
}
resource "aws_api_gateway_method_response" "export_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.export.id
  http_method = aws_api_gateway_method.export_options.http_method
  status_code = "200"
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  "method.response.header.Access-Control-Allow-Origin" = true }
}
resource "aws_api_gateway_integration_response" "export_options_200" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id
  resource_id = aws_api_gateway_resource.export.id
  http_method = aws_api_gateway_method.export_options.http_method
  status_code = aws_api_gateway_method_response.export_options_200.status_code
  response_parameters = { "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
  "method.response.header.Access-Control-Allow-Origin" = "'${local.cors_origin}'" }
}

# --- Deployment + Stage ---

resource "aws_api_gateway_deployment" "prod" {
  rest_api_id = aws_api_gateway_rest_api.ironlog.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.api.id,
      aws_api_gateway_resource.login.id,
      aws_api_gateway_resource.equipment.id,
      aws_api_gateway_resource.equipment_id.id,
      aws_api_gateway_resource.exercises.id,
      aws_api_gateway_resource.exercises_id.id,
      aws_api_gateway_resource.plans.id,
      aws_api_gateway_resource.plans_id.id,
      aws_api_gateway_resource.plans_id_activate.id,
      aws_api_gateway_resource.sessions.id,
      aws_api_gateway_resource.sessions_id.id,
      aws_api_gateway_resource.sessions_id_complete.id,
      aws_api_gateway_resource.sessions_id_sets.id,
      aws_api_gateway_resource.sessions_id_sets_sid.id,
      aws_api_gateway_resource.sessions_id_notes.id,
      aws_api_gateway_resource.corrections.id,
      aws_api_gateway_resource.seed.id,
      aws_api_gateway_integration.login_post.id,
      aws_api_gateway_integration.equipment_get.id,
      aws_api_gateway_integration.equipment_post.id,
      aws_api_gateway_integration.equipment_id_put.id,
      aws_api_gateway_integration.equipment_id_delete.id,
      aws_api_gateway_integration.exercises_get.id,
      aws_api_gateway_integration.exercises_post.id,
      aws_api_gateway_integration.exercises_id_put.id,
      aws_api_gateway_integration.exercises_id_delete.id,
      aws_api_gateway_integration.plans_get.id,
      aws_api_gateway_integration.plans_post.id,
      aws_api_gateway_integration.plans_id_get.id,
      aws_api_gateway_integration.plans_id_put.id,
      aws_api_gateway_integration.plans_id_delete.id,
      aws_api_gateway_integration.plans_id_activate_put.id,
      aws_api_gateway_integration.sessions_post.id,
      aws_api_gateway_integration.sessions_get.id,
      aws_api_gateway_integration.sessions_id_get.id,
      aws_api_gateway_integration.sessions_id_put.id,
      aws_api_gateway_integration.sessions_id_complete_put.id,
      aws_api_gateway_integration.sessions_id_sets_post.id,
      aws_api_gateway_integration.sessions_id_sets_sid_put.id,
      aws_api_gateway_integration.sessions_id_sets_sid_delete.id,
      aws_api_gateway_integration.sessions_id_notes_post.id,
      aws_api_gateway_integration.sessions_id_notes_get.id,
      aws_api_gateway_integration.corrections_post.id,
      aws_api_gateway_integration.corrections_get.id,
      aws_api_gateway_integration.seed_post.id,
      aws_api_gateway_resource.analytics.id,
      aws_api_gateway_resource.analytics_progression.id,
      aws_api_gateway_resource.analytics_recovery_correlation.id,
      aws_api_gateway_resource.analytics_prs.id,
      aws_api_gateway_resource.export.id,
      aws_api_gateway_integration.analytics_progression_get.id,
      aws_api_gateway_integration.analytics_recovery_correlation_get.id,
      aws_api_gateway_integration.analytics_prs_get.id,
      aws_api_gateway_integration.export_get.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.prod.id
  rest_api_id   = aws_api_gateway_rest_api.ironlog.id
  stage_name    = "prod"
}
