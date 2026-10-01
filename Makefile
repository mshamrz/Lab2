# Deploy contract. CI runs these same targets — nothing it does is a secret
# recipe you cannot run yourself.
#
# Required environment variables (set locally in your shell, or as
# repository variables/secrets in CI):
#   AWS_REGION            e.g. eu-central-1
#   S3_BUCKET             frontend bucket name
#   CLOUDFRONT_DIST_ID    CloudFront distribution id
#   ECR_REPOSITORY        e.g. 123456789012.dkr.ecr.eu-central-1.amazonaws.com/spry-backend
#   ECS_CLUSTER           e.g. spry-cluster
#   ECS_SERVICE           e.g. spry-backend
#   API_URL               e.g. https://api.yourdomain.com  (baked into the frontend build)

IMAGE_TAG ?= $(shell git rev-parse --short HEAD)

.PHONY: deploy-frontend deploy-backend

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
