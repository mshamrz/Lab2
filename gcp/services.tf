locals {
  services = [
    "run.googleapis.com",              # Cloud Run
    "sqladmin.googleapis.com",         # Cloud SQL Admin
    "artifactregistry.googleapis.com", # Artifact Registry
    "secretmanager.googleapis.com",    # Secret Manager
    "iam.googleapis.com",              # Identity and Access Management
    "cloudresourcemanager.googleapis.com"
  ]
}

resource "google_project_service" "enabled_services" {
  for_each = toset(local.services)

  service            = each.key
  disable_on_destroy = false
}
