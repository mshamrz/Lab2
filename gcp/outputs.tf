output "cloud_run_url" {
  description = "Public URL of the Spry API deployed on Cloud Run"
  value       = google_cloud_run_v2_service.spry_api.uri
}

output "artifact_registry_repo" {
  description = "Docker repository URI for pushing the backend image"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}"
}

output "cloud_sql_connection_name" {
  description = "Connection name of the Cloud SQL PostgreSQL instance"
  value       = google_sql_database_instance.postgres.connection_name
}

output "cloud_sql_public_ip" {
  description = "Public IPv4 address of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.public_ip_address
}
