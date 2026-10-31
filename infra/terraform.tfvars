project_name          = "spry"
cognito_domain_prefix = "spry-auth-mariana"
app_domain            = "d30mlui26iqxfd.cloudfront.net"
builder_image_uri     = "438424053032.dkr.ecr.eu-central-1.amazonaws.com/spry-backend:latest"
security_group_id     = "sg-0b9a5d039be46b2d5"
subnet_ids = [
  "subnet-0b191dfaed8bf2dbe",
  "subnet-0d1285298a2d6d032",
  "subnet-0636518edff8c4f4a",
]
