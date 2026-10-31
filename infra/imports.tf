# Adopt the agenda-parser resources that CloudFormation let go of.
# Delete this file after the first successful apply.

import {
  to = aws_s3_bucket.code
  id = "spry-agenda-code-438424053032"
}

import {
  to = aws_iam_role.parser
  id = "spry-agenda-parser-role"
}

import {
  to = aws_iam_role_policy_attachment.parser_logs
  id = "spry-agenda-parser-role/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

import {
  to = aws_iam_role_policy.invoke_claude
  id = "spry-agenda-parser-role:InvokeClaude"
}

import {
  to = aws_lambda_function.parser
  id = "spry-agenda-parser"
}

import {
  to = aws_lambda_function_url.parser
  id = "spry-agenda-parser"
}

import {
  to = aws_lambda_permission.parser_url
  id = "spry-agenda-parser/spry-ai-ParserUrlPermission-XZv7HRkJCtM8"
}

import {
  to = aws_lambda_permission.parser_invoke
  id = "spry-agenda-parser/spry-ai-ParserInvokePermission-SKrZhINGpYeF"
}
