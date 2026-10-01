"""Take the currently registered ECS task definition, replace the container
image with the newly pushed tag, and print JSON ready for
`aws ecs register-task-definition --cli-input-json file://...`.

Usage: render_task_def.py <current-task-def.json> <new-image>
"""
import json
import sys

path, new_image = sys.argv[1], sys.argv[2]

with open(path) as f:
    task_def = json.load(f)

for field in (
    "taskDefinitionArn",
    "revision",
    "status",
    "requiresAttributes",
    "compatibilities",
    "registeredAt",
    "registeredBy",
):
    task_def.pop(field, None)

task_def["containerDefinitions"][0]["image"] = new_image

print(json.dumps(task_def))
