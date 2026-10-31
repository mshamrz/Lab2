# Adopt the weekly-report resources that CloudFormation let go of.
# Delete this file after the first successful apply.

import {
  to       = aws_s3_bucket.reports
  provider = aws.eu
  id       = "spry-reports-438424053032"
}

import {
  to       = aws_s3_bucket_public_access_block.reports
  provider = aws.eu
  id       = "spry-reports-438424053032"
}

import {
  to       = aws_s3_bucket_lifecycle_configuration.reports
  provider = aws.eu
  id       = "spry-reports-438424053032"
}

import {
  to       = aws_s3_bucket_notification.reports
  provider = aws.eu
  id       = "spry-reports-438424053032"
}

import {
  to       = aws_sqs_queue.report_requests_dlq
  provider = aws.eu
  id       = "https://sqs.eu-central-1.amazonaws.com/438424053032/spry-report-requests-dlq"
}

import {
  to       = aws_sqs_queue.report_requests
  provider = aws.eu
  id       = "https://sqs.eu-central-1.amazonaws.com/438424053032/spry-report-requests"
}

import {
  to       = aws_iam_role.builder
  provider = aws.eu
  id       = "spry-report-builder-role"
}

import {
  to       = aws_iam_role_policy_attachment.builder_vpc
  provider = aws.eu
  id       = "spry-report-builder-role/arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

import {
  to       = aws_iam_role_policy.builder
  provider = aws.eu
  id       = "spry-report-builder-role:BuilderPermissions"
}

import {
  to       = aws_lambda_function.builder
  provider = aws.eu
  id       = "spry-report-builder"
}

import {
  to       = aws_lambda_event_source_mapping.builder
  provider = aws.eu
  id       = "d5752b18-bc56-44d5-8c4f-aebeee178b03"
}

import {
  to       = aws_iam_role.scheduler
  provider = aws.eu
  id       = "spry-report-scheduler-role"
}

import {
  to       = aws_iam_role_policy.scheduler
  provider = aws.eu
  id       = "spry-report-scheduler-role:SendSQS"
}

import {
  to       = aws_scheduler_schedule.weekly
  provider = aws.eu
  id       = "default/spry-weekly-report-schedule"
}

import {
  to       = aws_iam_role.mailer
  provider = aws.eu
  id       = "spry-report-mailer-role"
}

import {
  to       = aws_iam_role_policy_attachment.mailer_logs
  provider = aws.eu
  id       = "spry-report-mailer-role/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

import {
  to       = aws_iam_role_policy.mailer
  provider = aws.eu
  id       = "spry-report-mailer-role:MailerPermissions"
}

import {
  to       = aws_lambda_function.mailer
  provider = aws.eu
  id       = "spry-report-mailer"
}

import {
  to       = aws_lambda_permission.mailer_s3
  provider = aws.eu
  id       = "spry-report-mailer/spry-reports-MailerLambdaPermission-6MUalDR4ZnGS"
}
