# Was infra/auth.yml (Lab 4): Cognito with e-mail/password and Google.

resource "aws_cognito_user_pool" "main" {
  name                     = "${var.project_name}-user-pool"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  user_pool_tier           = "ESSENTIALS"

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  password_policy {
    minimum_length                   = 8
    require_uppercase                = true
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }
}

resource "aws_cognito_identity_provider" "google" {
  user_pool_id  = aws_cognito_user_pool.main.id
  provider_name = "Google"
  provider_type = "Google"

  # Cognito fills in the Google endpoints and the username mapping itself,
  # so they are written down here to make the plan match the real resource.
  provider_details = {
    client_id                     = var.google_client_id
    client_secret                 = var.google_client_secret
    authorize_scopes              = "openid email profile"
    attributes_url                = "https://people.googleapis.com/v1/people/me?personFields="
    attributes_url_add_attributes = "true"
    authorize_url                 = "https://accounts.google.com/o/oauth2/v2/auth"
    oidc_issuer                   = "https://accounts.google.com"
    token_request_method          = "POST"
    token_url                     = "https://www.googleapis.com/oauth2/v4/token"
  }

  attribute_mapping = {
    username       = "sub"
    email          = "email"
    email_verified = "email_verified"
  }
}

resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO", "Google"]

  callback_urls = [
    "https://${var.app_domain}/auth/callback/",
    "https://${var.app_domain}/",
    "http://localhost:5173/",
    "http://localhost:5173/auth/callback/",
  ]

  logout_urls = [
    "https://${var.app_domain}/",
    "http://localhost:5173/",
  ]

  depends_on = [aws_cognito_identity_provider.google]
}

resource "aws_cognito_user_pool_domain" "main" {
  domain                = var.cognito_domain_prefix
  user_pool_id          = aws_cognito_user_pool.main.id
  managed_login_version = 2
}

resource "aws_cognito_managed_login_branding" "main" {
  user_pool_id                = aws_cognito_user_pool.main.id
  client_id                   = aws_cognito_user_pool_client.main.id
  use_cognito_provided_values = true

  depends_on = [aws_cognito_user_pool_domain.main]
}
