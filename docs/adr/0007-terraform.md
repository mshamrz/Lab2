# ADR 0007: Infrastructure as Code with Terraform and HCP Terraform

Status: accepted. Date: 2026-10-31.

## Context

In Labs 4-6 the infrastructure was written as CloudFormation templates
(`auth.yml`, `reports.yml`, `ai.yml`) and deployed from a laptop with
`aws cloudformation deploy`. Three problems showed up along the way:

- Some things were never written down. The S3 bucket that holds the parser zip
  was created with `aws s3 mb`, and nothing in Git described it. The weekly
  report ran in Frankfurt (`eu-central-1`) while Cognito and the parser ran in
  `us-east-1`, and nothing said so.
- A template and the real resources drifted apart. `reports.yml` said the
  weekly report runs on Monday at 08:00. The deployed schedule said 07:00, and
  the generated reports confirmed it. Nobody had noticed.
- Who creates the infrastructure was a person with admin keys on a laptop.
  Nothing reviewed a change before it reached AWS.

The project also reaches outside AWS (a Google OAuth client, GitHub) and will
need a second environment, which CloudFormation cannot cover in one plan.

## Decision

The infrastructure lives in `infra/*.tf` (one root module) and is applied by
HCP Terraform, workspace `spry-dev`, connected to this repository.

- A pull request gets a speculative plan as a check, and a person reads it. A
  merge to `main` starts a run that waits for **Confirm & Apply**. Auto-apply is
  off, so nobody applies without reading the plan.
- HCP Terraform reaches AWS with dynamic credentials (OIDC) through the role
  `hcp-terraform-ooad-mshamrz`. No AWS keys are stored anywhere.
- All three templates were moved by import: 32 resources imported, none
  re-created. For each template CloudFormation was told to let go first
  (`DeletionPolicy: Retain`), the stack was deleted, and `import` blocks adopted
  the real resources. The four users of the Cognito user pool, the reports in
  the bucket and the weekly schedule survived.
- Every first plan was read for `-/+` and `destroy` lines before merging. This
  caught a planned replacement of the Cognito user pool client, which was fixed
  in the code and never applied, and the Monday 07:00 / 08:00 difference. In
  both cases the code was changed to match the real resource, not the other way
  round.
- Two AWS providers are configured: the default one for `us-east-1` and an alias
  `aws.eu` for the weekly report in `eu-central-1`.

## Alternatives considered

- **Stay on CloudFormation.** Free, and AWS keeps the state. It stops at the
  edge of one AWS account and cannot manage the Google or GitHub parts.
- **AWS CDK.** Real programming languages on top of CloudFormation. It adds a
  build step and a bootstrap stack, and keeps the same AWS-only limit.
- **OpenTofu.** The same files and commands, an open-source licence. Terraform
  was chosen because HCP Terraform, which gives remote state, locking, plans on
  pull requests and OIDC to AWS, is built around it.
- **Delete the stacks and apply the Terraform.** Rejected: it would delete the
  user pool with every registered account and the reports bucket with every
  report.

## Consequences

- **Who can change the infrastructure.** Anyone who can open a pull request can
  propose a change. Only a person with apply rights in HCP Terraform can
  confirm it, after reading the plan. A change made by hand in the console
  shows up as drift in the next plan and is reverted by the next apply, so an
  emergency fix has to be written back into the code.
- **Secrets.** The Google client secret and the database URL are sensitive
  Terraform variables in the workspace, not files in Git. They are still stored
  in the Terraform state, which lives in HCP Terraform and is readable by
  members of the organization, and in the local `.env`. During the import the
  old Google secret appeared in plain text in a plan log, so a new one was
  created before the first apply and the old one was deleted in Google Cloud.
- **State.** We now keep the state. Losing it would make Terraform want to
  create everything again. HCP Terraform stores and locks it and keeps every
  version.
- **If HCP Terraform is down.** The running system is not affected, because
  Cognito, the parser and the weekly report do not depend on it. Only changes
  to the infrastructure wait. In an emergency, the same files can be applied
  from a laptop with the workspace in local execution mode.
- **The AWS role is broad.** `hcp-terraform-ooad-mshamrz` has
  `AdministratorAccess`, and its trust allows any workspace of the
  organization. That is acceptable for a class project. A team would narrow
  both.
- **The parser zip.** The code bucket is managed by Terraform, but the zip is
  built and uploaded by `scripts/build_parser_zip.py` and `aws s3 cp`.
  Terraform does not notice a new zip by itself. The weekly report's mailer
  code now lives in `infra/mailer/index.py` and is zipped by Terraform.
- **Left alone on purpose.** The debug stack `spry-reports-debug4`
  (`debug.yml`), the empty stack `spry-reports-v2`, the empty bucket
  `spry-reports2-...`, the second Cognito stack in Frankfurt and the ECR
  repository are not part of the three templates of this lab. They are still
  outside Git and should be adopted or deleted in a later pass.
