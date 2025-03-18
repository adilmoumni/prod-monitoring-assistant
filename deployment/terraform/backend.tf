terraform {
  backend "gcs" {
    bucket = "qwiklabs-gcp-03-98e7977f8112-terraform-state"
    prefix = "prod"
  }
}
