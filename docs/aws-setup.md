# AWS setup — one-time, do this by hand once

Everything here is created once, manually, with the AWS CLI. After this, the
Makefile and `deploy.yml` only *update* these resources — they never create
them. Replace `<...>` placeholders with your own values.

Prereqs: AWS account, MFA on root, an IAM user for yourself, `aws configure`
run locally, a domain you control in Route 53 (or another DNS provider that
lets you add CNAME records).

## 0. Variables (fill these in, reuse below)

```bash
export AWS_REGION=eu-central-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export DOMAIN=yourdomain.com
```

## 1. ECR — where backend images live

```bash
aws ecr create-repository --repository-name spry-backend --region $AWS_REGION
```

## 2. RDS — Postgres for the deployed backend

Simplest for a lab: a small `db.t4g.micro` instance, not Aurora, not
Multi-AZ (that's a year-1-scale decision, not a lab decision).

```bash
aws rds create-db-instance \
  --db-instance-identifier spry-db \
  --db-instance-class db.t4g.micro \
  --engine postgres --engine-version 16 \
  --master-username spry --master-user-password '<choose a real password>' \
  --allocated-storage 20 \
  --publicly-accessible false \
  --vpc-security-group-ids <sg-id-allowing-5432-from-ecs-only>
```

Note the endpoint once it's up (`aws rds describe-db-instances`) — you'll put
it in the ECS task definition's `DATABASE_URL`.

## 3. S3 + CloudFront — the frontend

```bash
aws s3 mb s3://spry-frontend-<something-unique>
```

Keep the bucket private; create a CloudFront distribution with Origin
Access Control pointing at it (console is easiest for the OAC + bucket
policy step — the CLI version is verbose). Note the distribution id and
domain name.

## 4. ACM certificate (validation CNAME)

```bash
aws acm request-certificate \
  --domain-name app.$DOMAIN --subject-alternative-names api.$DOMAIN \
  --validation-method DNS --region $AWS_REGION
```

`aws acm describe-certificate` gives you a CNAME name/value pair per domain —
publish those in your DNS. The certificate moves to `ISSUED` once they
resolve; this can take minutes.

## 5. ECS cluster, ALB, target group, service

```bash
aws ecs create-cluster --cluster-name spry-cluster

aws elbv2 create-load-balancer --name spry-alb \
  --subnets <public-subnet-1> <public-subnet-2> \
  --security-groups <sg-allowing-80-443>

aws elbv2 create-target-group --name spry-backend-tg \
  --protocol HTTP --port 8000 --vpc-id <vpc-id> --target-type ip \
  --health-check-path /health
```

Attach the ACM cert to an HTTPS (443) listener on the ALB pointing at the
target group; add an HTTP (80) listener that redirects to 443.

Register the first task definition from the template, once, by hand:

```bash
# fill in infra/task-definition.template.json first, then:
aws ecs register-task-definition --cli-input-json file://infra/task-definition.template.json

aws ecs create-service \
  --cluster spry-cluster --service-name spry-backend \
  --task-definition spry-backend --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<private-subnet-ids>],securityGroups=[<sg-allowing-8000-from-alb>],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=<target-group-arn>,containerName=spry-backend,containerPort=8000"
```

The health check is what makes this safe: ECS only sends traffic to a task
once `/health` returns 200, and replaces a task that stops answering.

## 6. DNS — routing (not validation)

```
app.yourdomain.com   CNAME/ALIAS  -> <cloudfront-distribution-domain>
api.yourdomain.com   CNAME/ALIAS  -> <alb-dns-name>
```

## 7. GitHub OIDC — no long-lived keys

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

aws iam create-role --role-name spry-deploy-role \
  --assume-role-policy-document file://infra/oidc-trust-policy.json
# then attach a policy scoped to: this ECR repo, this ECS cluster/service,
# this S3 bucket, this CloudFront distribution — not AdministratorAccess.
```

Fill in `<ACCOUNT_ID>` and `<YOUR_GITHUB_USER>` in
`infra/oidc-trust-policy.json` before creating the role. Set these as
repository **variables** in GitHub (not secrets, they aren't sensitive,
except the account id which can be either): `AWS_ACCOUNT_ID`, `AWS_REGION`,
`ECS_CLUSTER`, `ECS_SERVICE`, `S3_BUCKET`, `CLOUDFRONT_DIST_ID`, `API_URL`.

## Teardown (do this when the lab is graded)

```bash
aws ecs update-service --cluster spry-cluster --service spry-backend --desired-count 0
aws ecs delete-service --cluster spry-cluster --service spry-backend
aws elbv2 delete-load-balancer --load-balancer-arn <alb-arn>
aws rds delete-db-instance --db-instance-identifier spry-db --skip-final-snapshot
aws cloudfront delete-distribution --id <dist-id>   # must be disabled first
aws s3 rb s3://spry-frontend-<something-unique> --force
```

NAT gateways, ALBs and RDS bill by the hour whether or not anyone visits —
tear down as soon as the screenshots and URLs are captured for submission.
