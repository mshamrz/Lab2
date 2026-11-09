resource "google_artifact_registry_repository" "backend_repo" {
  depends_on    = [google_project_service.enabled_services]
  location      = var.region
  repository_id = "spry-repo"
  description   = "Docker repository for Spry backend container images"
  format        = "DOCKER"
}
