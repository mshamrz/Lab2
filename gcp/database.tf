resource "random_id" "db_suffix" {
  byte_length = 4
}

resource "random_password" "db_password" {
  length  = 24
  special = false
}

resource "google_sql_database_instance" "postgres" {
  depends_on          = [google_project_service.enabled_services]
  name                = "${var.db_instance_name}-${random_id.db_suffix.hex}"
  database_version    = "POSTGRES_15"
  region              = var.region
  deletion_protection = false

  settings {
    tier              = "db-f1-micro"
    disk_size         = 10
    disk_type         = "PD_SSD"
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled = true
    }

    backup_configuration {
      enabled = false
    }
  }
}

resource "google_sql_database" "spry_db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "spry_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Store database password in Google Secret Manager
resource "google_secret_manager_secret" "db_password_secret" {
  depends_on = [google_project_service.enabled_services]
  secret_id  = "spry-db-password"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password_version" {
  secret      = google_secret_manager_secret.db_password_secret.id
  secret_data = random_password.db_password.result
}
