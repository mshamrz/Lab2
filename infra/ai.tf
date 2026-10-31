# Was infra/ai.yml (Lab 6): the agenda parser Lambda, outside the VPC,
# with a function URL. It calls Claude on Bedrock.

data "aws_caller_identity" "current" {}

locals {
  code_bucket = "${var.project_name}-agenda-code-${data.aws_caller_identity.current.account_id}"
}

# The bucket that holds the parser zip. It was created by hand with
# `aws s3 mb`, so it was never written down. Now it is.
resource "aws_s3_bucket" "code" {
  bucket = local.code_bucket
}

resource "aws_iam_role" "parser" {
  name = "${var.project_name}-agenda-parser-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "parser_logs" {
  role       = aws_iam_role.parser.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Converse through a cross-region inference profile needs the profile and
# the foundation model in the regions the profile routes to.
resource "aws_iam_role_policy" "invoke_claude" {
  name = "InvokeClaude"
  role = aws_iam_role.parser.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["bedrock:InvokeModel"]
      Resource = [
        "arn:aws:bedrock:${var.region}:${data.aws_caller_identity.current.account_id}:inference-profile/us.anthropic.claude-sonnet-4-6",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-6",
      ]
    }]
  })
}

# No vpc_config: this function needs no database.
resource "aws_lambda_function" "parser" {
  function_name = "${var.project_name}-agenda-parser"
  role          = aws_iam_role.parser.arn
  runtime       = "python3.12"
  handler       = "app.ai.agenda_lambda.handler"
  timeout       = 30
  memory_size   = 512

  s3_bucket = aws_s3_bucket.code.id
  s3_key    = var.parser_code_key

  environment {
    variables = {
      PARSER_MODEL = var.parser_model
      USER_POOL_ID = aws_cognito_user_pool.main.id
      CLIENT_ID    = aws_cognito_user_pool_client.main.id
    }
  }
}

resource "aws_lambda_function_url" "parser" {
  function_name      = aws_lambda_function.parser.function_name
  authorization_type = "NONE"

  cors {
    allow_headers = ["content-type", "authorization"]
    allow_methods = ["POST"]
    allow_origins = ["http://localhost:5173", "https://${var.app_domain}"]
    max_age       = 3600
  }
}

# Public URL permissions. The handler checks the Cognito token itself.
# The statement ids are the ones CloudFormation generated, kept so that
# the existing permissions can be imported and not re-created.
resource "aws_lambda_permission" "parser_url" {
  statement_id           = "spry-ai-ParserUrlPermission-XZv7HRkJCtM8"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.parser.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "parser_invoke" {
  statement_id             = "spry-ai-ParserInvokePermission-SKrZhINGpYeF"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.parser.function_name
  principal                = "*"
  invoked_via_function_url = true
}
