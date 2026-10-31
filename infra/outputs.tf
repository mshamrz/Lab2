output "user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  value = aws_cognito_user_pool_client.main.id
}

output "cognito_domain" {
  value = "${var.cognito_domain_prefix}.auth.${var.region}.amazoncognito.com"
}

output "parser_function_name" {
  value = aws_lambda_function.parser.function_name
}

output "parser_url" {
  value = aws_lambda_function_url.parser.function_url
}
