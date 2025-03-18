# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# a. Create PR checks trigger
resource "google_cloudbuild_trigger" "pr_checks" {
  name            = "pr-checks"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for PR checks"
  service_account = resource.google_service_account.cicd_runner_sa.id

  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
    pull_request {
      branch = "main"
    }
  }

  filename = "deployment/ci/pr_checks.yaml"
  included_files = [
    "app/**",
    "data_ingestion/**",
    "tests/**",
    "deployment/**",
    "uv.lock",
  ]
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services, google_cloudbuildv2_repository.repo]
}

# b. Create CD pipeline trigger
resource "google_cloudbuild_trigger" "cd_pipeline" {
  name            = "cd-pipeline"
  project         = var.cicd_runner_project_id
  location        = var.region
  service_account = resource.google_service_account.cicd_runner_sa.id
  description     = "Trigger for CD pipeline"

  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
    push {
      branch = "main"
    }
  }

  filename = "deployment/cd/staging.yaml"
  included_files = [
    "app/**",
    "data_ingestion/**",
    "tests/**",
    "deployment/**",
    "uv.lock"
  ]
  substitutions = {
    _STAGING_PROJECT_ID            = var.staging_project_id
    _BUCKET_NAME_LOAD_TEST_RESULTS = resource.google_storage_bucket.bucket_load_test_results.name
    _REGION                        = var.region
    _CONTAINER_NAME                = var.cloud_run_app_sa_name
    _ARTIFACT_REGISTRY_REPO_NAME   = var.artifact_registry_repo_name
    _CLOUD_RUN_APP_SA_NAME         = var.cloud_run_app_sa_name
    # Your other CD Pipeline substitutions
  }
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services, google_cloudbuildv2_repository.repo]

}

# c. Create Deploy to production trigger
resource "google_cloudbuild_trigger" "deploy_to_prod_pipeline" {
  name            = "deploy-to-prod-pipeline"
  project         = var.cicd_runner_project_id
  location        = var.region
  description     = "Trigger for deployment to production"
  service_account = resource.google_service_account.cicd_runner_sa.id
  repository_event_config {
    repository = google_cloudbuildv2_repository.repo.id
  }
  filename = "deployment/cd/deploy-to-prod.yaml"
  approval_config {
    approval_required = true
  }
  substitutions = {
    _PROD_PROJECT_ID             = var.prod_project_id
    _REGION                      = var.region
    _CONTAINER_NAME              = var.cloud_run_app_sa_name
    _ARTIFACT_REGISTRY_REPO_NAME = var.artifact_registry_repo_name
    _CLOUD_RUN_APP_SA_NAME       = var.cloud_run_app_sa_name
    # Your other Deploy to Prod Pipeline substitutions
  }
  depends_on = [resource.google_project_service.cicd_services, resource.google_project_service.shared_services, google_cloudbuildv2_repository.repo]

}
