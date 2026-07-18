import type { components } from "@/lib/api/generated-types";

/** Keep in sync with backend `ReviewConfigType` / ReviewRequest.type. */
export type ReviewType =
  | "dockerfile"
  | "kubernetes"
  | "terraform"
  | "github-actions"
  | "gitlab-ci"
  | "jenkins";

export type ReviewRequest = Omit<components["schemas"]["ReviewRequest"], "type"> & {
  type: ReviewType;
};
export type ReviewResponse = components["schemas"]["ReviewResponse"];
export type ReviewFinding = components["schemas"]["ReviewFinding"];
export type FindingSource = ReviewFinding["source"];
export type FindingSeverity = ReviewFinding["severity"];

export const FINDING_SOURCE_LABELS: Record<FindingSource, string> = {
  static: "Deterministic (static)",
  organization_policy: "Organization policy",
  llm: "AI-assisted (llm)",
};

export const REVIEW_TYPE_LABELS: Record<ReviewType, string> = {
  dockerfile: "Dockerfile",
  kubernetes: "Kubernetes",
  terraform: "Terraform",
  "github-actions": "GitHub Actions",
  "gitlab-ci": "GitLab CI",
  jenkins: "Jenkins",
};

export const REVIEW_TYPE_HINTS: Record<ReviewType, string> = {
  dockerfile: "Paste a Dockerfile (e.g. Dockerfile).",
  kubernetes: "Paste Kubernetes YAML manifests.",
  terraform: "Paste Terraform HCL (.tf).",
  "github-actions": "Paste a GitHub Actions workflow YAML.",
  "gitlab-ci": "Paste .gitlab-ci.yml or .gitlab-ci.yaml.",
  jenkins: "Paste a Jenkinsfile or Groovy pipeline.",
};

export const REVIEW_TYPE_SAMPLES: Record<ReviewType, string> = {
  dockerfile: "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nCMD [\"python\", \"-m\", \"app\"]\n",
  kubernetes:
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: demo\nspec:\n  replicas: 1\n",
  terraform: 'resource "aws_s3_bucket" "demo" {\n  bucket = "example"\n}\n',
  "github-actions":
    "name: ci\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n",
  "gitlab-ci":
    "stages:\n  - test\n\ntest:\n  stage: test\n  image: python:3.12-slim\n  script:\n    - pip install -r requirements.txt\n    - pytest\n",
  jenkins:
    "pipeline {\n  agent any\n  stages {\n    stage('Test') {\n      steps {\n        sh 'pytest'\n      }\n    }\n  }\n}\n",
};
