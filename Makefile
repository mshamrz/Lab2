-include .env
export

IMAGE_TAG ?= $(shell git rev-parse --short HEAD)

.PHONY: deploy-frontend deploy-backend infra-fmt infra-validate infra-plan llm-hello

# Infrastructure is described in infra/*.tf and applied by HCP Terraform
# after a merge to main. There is deliberately no "terraform apply" target here.
infra-fmt:
	cd infra && terraform fmt -check

infra-validate:
	cd infra && terraform init -backend=false && terraform validate

# A speculative plan in HCP Terraform (needs "terraform login" once).
infra-plan:
	cd infra && terraform init && terraform plan

deploy-frontend:
	cd frontend && npm ci && VITE_API_URL=$(API_URL) npm run build
	aws s3 sync frontend/dist s3://$(S3_BUCKET) --delete
	aws cloudfront create-invalidation --distribution-id $(CLOUDFRONT_DIST_ID) --paths "/*"

deploy-backend:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(shell echo $(ECR_REPOSITORY) | cut -d/ -f1)
	docker build -t $(ECR_REPOSITORY):$(IMAGE_TAG) ./backend
	docker push $(ECR_REPOSITORY):$(IMAGE_TAG)
	aws ecs describe-task-definition --task-definition spry-backend --query taskDefinition \
		> /tmp/current-task-def.json
	python3 infra/render_task_def.py /tmp/current-task-def.json $(ECR_REPOSITORY):$(IMAGE_TAG) > /tmp/new-task-def.json
	aws ecs register-task-definition --cli-input-json file:///tmp/new-task-def.json
	aws ecs update-service --cluster $(ECS_CLUSTER) --service $(ECS_SERVICE) --task-definition spry-backend --force-new-deployment

llm-hello:
	python scripts/llm_hello.py
