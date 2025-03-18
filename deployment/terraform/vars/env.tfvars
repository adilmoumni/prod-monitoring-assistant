# Your Production Google Cloud project id
prod_project_id = "qwiklabs-gcp-03-98e7977f8112"

# Your Staging / Test Google Cloud project id
staging_project_id = "qwiklabs-gcp-02-d9d7b362e218"

# Your Google Cloud project ID that will be used to host the Cloud Build pipelines.
cicd_runner_project_id = "qwiklabs-gcp-03-98e7977f8112"

# Name of the host connection you created in Cloud Build
host_connection_name = "github-connection"

# Name of the repository you added to Cloud Build
repository_name = "prod-monitoring-assistant"

# The Google Cloud region you will use to deploy the infrastructure
region = "us-central1"
cloud_run_app_sa_name = "prod-monitoring-assistant-cr"

telemetry_bigquery_dataset_id = "telemetry_genai_app_sample_sink"
telemetry_sink_name = "telemetry_logs_genai_app_sample"
telemetry_logs_filter = "jsonPayload.attributes.\"traceloop.association.properties.log_type\"=\"tracing\" jsonPayload.resource.attributes.\"service.name\"=\"prod-monitoring-assistant\""

feedback_bigquery_dataset_id = "feedback_genai_app_sample_sink"
feedback_sink_name = "feedback_logs_genai_app_sample"
feedback_logs_filter = "jsonPayload.log_type=\"feedback\""

cicd_runner_sa_name = "cicd-runner"

suffix_bucket_name_load_test_results = "cicd-load-test-results"
repository_owner = "adilmoumni"
github_app_installation_id = "62862413"
github_pat_secret_id = "github-connection-github-oauthtoken-b351c2"
connection_exists = true
