"""Add DeletionPolicy/UpdateReplacePolicy: Retain to every resource of a
deployed CloudFormation stack and update the stack, so that the stack can be
deleted afterwards without deleting the resources.

The template is read back from AWS, not from the repository, so the update
changes nothing but the two policies. Parameters keep their previous values.

Usage: python scripts\\retain_stack.py <stack-name> <region>
"""
import sys

POLICIES = ["    DeletionPolicy: Retain", "    UpdateReplacePolicy: Retain"]


def add_retain(template: str) -> tuple[str, int]:
    """Insert the two policies after the Type line of every resource."""
    out, section, added = [], None, 0
    lines = template.split("\n")
    for i, line in enumerate(lines):
        out.append(line)
        if line and not line.startswith((" ", "#", "\t")) and line.endswith(":"):
            section = line[:-1]
        if section == "Resources" and line.startswith("    Type: "):
            following = "\n".join(lines[i + 1:i + 4])
            if "DeletionPolicy" not in following:
                out.extend(POLICIES)
                added += 1
    return "\n".join(out), added


def main() -> None:
    import boto3
    from botocore.exceptions import ClientError

    stack, region = sys.argv[1], sys.argv[2]
    cf = boto3.client("cloudformation", region_name=region)

    body = cf.get_template(StackName=stack, TemplateStage="Original")["TemplateBody"]
    if not isinstance(body, str):
        sys.exit("This stack uses a JSON template, which this script does not handle.")

    new_body, added = add_retain(body)
    print(f"Stack {stack} in {region}: {added} resources get Retain.")
    if input("Type yes to update the stack: ").strip().lower() != "yes":
        sys.exit("Nothing was changed.")

    params = cf.describe_stacks(StackName=stack)["Stacks"][0].get("Parameters", [])
    try:
        cf.update_stack(
            StackName=stack,
            TemplateBody=new_body,
            Parameters=[{"ParameterKey": p["ParameterKey"], "UsePreviousValue": True} for p in params],
            Capabilities=["CAPABILITY_NAMED_IAM"],
        )
    except ClientError as e:
        sys.exit(f"update_stack failed: {e}")

    print("Updating, this takes a minute...")
    cf.get_waiter("stack_update_complete").wait(StackName=stack)

    check = cf.get_template(StackName=stack, TemplateStage="Original")["TemplateBody"]
    print("DeletionPolicy: Retain lines in the stack now:", check.count("DeletionPolicy: Retain"))


if __name__ == "__main__":
    main()
