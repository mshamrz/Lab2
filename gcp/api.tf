resource "google_service_account" "api_sa" {
  account_id   = "spry-api-sa"
  display_name = "Service Account for Spry Cloud Run API"
}

resource "google_project_iam_member" "cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.db_password_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_cloud_run_v2_service" "spry_api" {
  depends_on = [
    google_project_service.enabled_services,
    google_sql_database_instance.postgres,
    google_sql_database.spry_db,
    google_sql_user.spry_user
  ]

  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.api_sa.email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}/spry-backend:latest"

      ports {
        container_port = 8000
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql+psycopg2://${google_sql_user.spry_user.name}:${random_password.db_password.result}@/spry?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }
}

# Allow unauthenticated invocation so the frontend / public can query the API
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = google_cloud_run_v2_service.spry_api.project
  location = google_cloud_run_v2_service.spry_api.location
  name     = google_cloud_run_v2_service.spry_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
