# Was infra/reports.yml (Lab 5): the weekly report.
# S3 bucket, SQS + DLQ, report-builder Lambda (in the VPC), a weekly schedule
# and the report-mailer Lambda. Everything here is in eu-central-1.

locals {
  reports_bucket = "${var.project_name}-reports-${data.aws_caller_identity.current.account_id}"
}

# ---- 1. The private bucket -------------------------------------------------

resource "aws_s3_bucket" "reports" {
  provider = aws.eu
  bucket   = local.reports_bucket
}

resource "aws_s3_bucket_public_access_block" "reports" {
  provider = aws.eu
  bucket   = aws_s3_bucket.reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  provider = aws.eu
  bucket   = aws_s3_bucket.reports.id

  rule {
    id     = "ExpireAfter90Days"
    status = "Enabled"

    filter {}

    expiration {
      days = 90
    }
  }
}

# In CloudFormation the bucket and the Lambda permission pointed at each other
# (Lab 5's circular dependency). Here they are three separate resources, and
# the notification simply waits for the permission.
resource "aws_s3_bucket_notification" "reports" {
  provider = aws.eu
  bucket   = aws_s3_bucket.reports.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.mailer.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "reports/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.mailer_s3]
}

# ---- 2. SQS queues (DLQ + main) -------------------------------------------

resource "aws_sqs_queue" "report_requests_dlq" {
  provider = aws.eu
  name     = "${var.project_name}-report-requests-dlq"
}

resource "aws_sqs_queue" "report_requests" {
  provider                   = aws.eu
  name                       = "${var.project_name}-report-requests"
  visibility_timeout_seconds = 360

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.report_requests_dlq.arn
    maxReceiveCount     = 3
  })
}

# ---- 3. report-builder (in the VPC) ----------------------------------------

resource "aws_iam_role" "builder" {
  provider = aws.eu
  name     = "${var.project_name}-report-builder-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "builder_vpc" {
  provider   = aws.eu
  role       = aws_iam_role.builder.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "builder" {
  provider = aws.eu
  name     = "BuilderPermissions"
  role     = aws_iam_role.builder.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "arn:aws:s3:::${local.reports_bucket}/reports/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = aws_sqs_queue.report_requests.arn
      },
    ]
  })
}

resource "aws_lambda_function" "builder" {
  provider      = aws.eu
  function_name = "${var.project_name}-report-builder"
  role          = aws_iam_role.builder.arn
  package_type  = "Image"
  image_uri     = var.builder_image_uri
  timeout       = 60
  memory_size   = 512

  image_config {
    entry_point = ["python", "-m", "awslambdaric"]
    command     = ["app.reports.lambda_handler.handler"]
  }

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      REPORTS_BUCKET = local.reports_bucket
      DATABASE_URL   = var.database_url
    }
  }
}

# ---- 4. SQS -> builder ------------------------------------------------------

resource "aws_lambda_event_source_mapping" "builder" {
  provider         = aws.eu
  event_source_arn = aws_sqs_queue.report_requests.arn
  function_name    = aws_lambda_function.builder.arn
  batch_size       = 1
}

# ---- 5. EventBridge Scheduler -> SQS ---------------------------------------

resource "aws_iam_role" "scheduler" {
  provider = aws.eu
  name     = "${var.project_name}-report-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler" {
  provider = aws.eu
  name     = "SendSQS"
  role     = aws_iam_role.scheduler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.report_requests.arn
    }]
  })
}

resource "aws_scheduler_schedule" "weekly" {
  provider                     = aws.eu
  name                         = "${var.project_name}-weekly-report-schedule"
  schedule_expression          = "cron(0 7 ? * MON *)"
  schedule_expression_timezone = "Europe/Kyiv"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sqs_queue.report_requests.arn
    role_arn = aws_iam_role.scheduler.arn
    input    = "{\"source\": \"schedule\", \"week\": null}"
  }
}

# ---- 6. report-mailer (outside the VPC) -------------------------------------

resource "aws_iam_role" "mailer" {
  provider = aws.eu
  name     = "${var.project_name}-report-mailer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "mailer_logs" {
  provider   = aws.eu
  role       = aws_iam_role.mailer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "mailer" {
  provider = aws.eu
  name     = "MailerPermissions"
  role     = aws_iam_role.mailer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "arn:aws:s3:::${local.reports_bucket}/reports/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      },
    ]
  })
}

# The code used to sit inline in the CloudFormation template. Now it is a
# file, mailer/index.py, zipped by Terraform.
data "archive_file" "mailer" {
  type        = "zip"
  source_file = "${path.module}/mailer/index.py"
  output_path = "${path.module}/mailer.zip"
}

resource "aws_lambda_function" "mailer" {
  provider         = aws.eu
  function_name    = "${var.project_name}-report-mailer"
  role             = aws_iam_role.mailer.arn
  runtime          = "python3.11"
  handler          = "index.handler"
  timeout          = 30
  filename         = data.archive_file.mailer.output_path
  source_code_hash = data.archive_file.mailer.output_base64sha256

  environment {
    variables = {
      RECIPIENT_EMAIL = var.recipient_email
    }
  }
}

# The statement id is the one CloudFormation generated, kept so that the
# existing permission can be imported and not re-created.
resource "aws_lambda_permission" "mailer_s3" {
  provider       = aws.eu
  statement_id   = "spry-reports-MailerLambdaPermission-6MUalDR4ZnGS"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.mailer.function_name
  principal      = "s3.amazonaws.com"
  source_account = data.aws_caller_identity.current.account_id
  source_arn     = "arn:aws:s3:::${local.reports_bucket}"
}
