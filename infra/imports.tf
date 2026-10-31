# Adopt the Cognito resources that CloudFormation let go of.
# Delete this file after the first successful apply.

import {
  to = aws_cognito_user_pool.main
  id = "us-east-1_zous9WTDf"
}

import {
  to = aws_cognito_identity_provider.google
  id = "us-east-1_zous9WTDf:Google"
}

import {
  to = aws_cognito_user_pool_client.main
  id = "us-east-1_zous9WTDf/c76j5carht9ilqha454ioj3hm"
}

import {
  to = aws_cognito_user_pool_domain.main
  id = "spry-auth-mariana"
}

import {
  to = aws_cognito_managed_login_branding.main
  id = "us-east-1_zous9WTDf,b9435a49-9946-4d15-a486-f3e16bbdafae"
}
