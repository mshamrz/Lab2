# ADR 0007: Infrastructure as Code with Terraform and HCP Terraform

Status: accepted. Date: 2026-10-31.

## Context

In Labs 4-6 the infrastructure was written as CloudFormation templates
(`auth.yml`, `reports.yml`, `ai.yml`) and deployed from a laptop with
`aws cloudformation deploy`. Three problems showed up along the way:

- Some resources were never written down. The S3 bucket that holds the parser
  zip was created with `aws s3 mb`, and nothing in Git described it.
- Who creates the infrastructure was a person with admin keys on a laptop.
  Nothing reviewed the change before it reached AWS.
- The project already reaches outside AWS (a Google OAuth client, GitHub) and
  will need a second environment, which CloudFormation cannot cover in one plan.

## Decision

The infrastructure lives in `infra/*.tf` (one root module) and is applied by
HCP Terraform, workspace `spry-dev`, connected to this repository.

- A pull request gets a speculative plan as a check. A person reads it. A merge
  to `main` starts a run that waits for **Confirm & Apply**. Auto-apply is off.
- HCP Terraform reaches AWS with dynamic credentials (OIDC) through the role
  `hcp-terraform-ooad-mshamrz`. No AWS keys are stored anywhere.
- The Cognito user pool, its client, domain, Google provider and branding, and
  the agenda parser (role, function, function URL, permissions and the code
  bucket) were moved from CloudFormation by importing them. CloudFormation was
  told to let go first (`DeletionPolicy: Retain`), the stacks were deleted, and
  `import` blocks adopted the real resources. Nothing was re-created, so the
  four users in the user pool survived.
- The first plan of each import was read for `-/+` and `destroy` lines before
  merging. One of them caught a replacement of the user pool client, which was
  fixed in the code and never applied.

## Alternatives considered

- **Stay on CloudFormation.** Free, and AWS keeps the state. It stops at the
  edge of one AWS account and cannot manage the Google or GitHub parts.
- **AWS CDK.** Real programming languages on top of CloudFormation. It adds a
  build step and a bootstrap stack, and keeps the same AWS-only limit.
- **OpenTofu.** The same files and commands, an open-source licence. Terraform
  was chosen because HCP Terraform, which gives remote state, locking, plans on
  pull requests and OIDC to AWS, is built around it.
- **Delete the stacks and apply the Terraform.** Rejected: it would delete the
  user pool with every registered account.

## Consequences

- **Who can change the infrastructure.** Anyone who can open a pull request can
  propose a change. Only a person with apply rights in HCP Terraform can
  confirm it, after reading the plan. A change made by hand in the console shows
  up as drift in the next plan and is reverted by the next apply, so an
  emergency fix has to be written back into the code.
- **Secrets.** The Google client secret is a sensitive Terraform variable in the
  workspace, not a file in Git. It is still stored in the Terraform state, which
  lives in HCP Terraform and is readable by members of the organization, and in
  the local `.env`. During the import the old secret appeared in plain text in
  a plan log, so it was rotated before the first apply.
- **State.** We now keep the state. Losing it would make Terraform want to create
  everything again. HCP Terraform stores and locks it and keeps every version.
- **If HCP Terraform is down.** The running system is not affected, because
  Cognito and the Lambda function do not depend on it. Only changes to the
  infrastructure wait. In an emergency, the same files can be applied from a
  laptop with the workspace in local execution mode.
- **The AWS role is broad.** `hcp-terraform-ooad-mshamrz` has
  `AdministratorAccess`, and its trust allows any workspace of the organization.
  That is acceptable for a class project. A team would narrow both.
- **Not migrated: `reports.yml`.** The Lab 5 stack (weekly report) does not exist
  in this AWS account any more, because the database and VPC it depended on
  were removed. There is nothing to import, and a `reports.tf` cannot be
  applied without them. The template stays in the repository as documentation
  until that part is rebuilt.
- **The parser zip.** The code bucket is managed by Terraform, but the zip is
  built and uploaded by `scripts/build_parser_zip.py` and `aws s3 cp`. Terraform
  does not notice a new zip by itself.
