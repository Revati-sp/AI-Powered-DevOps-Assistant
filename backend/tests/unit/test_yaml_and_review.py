from app.schemas.generators import KubernetesRequest
from app.services.kubernetes_generator import _build_manifests
from app.services.security_review_service import run_static_checks
from app.services.yaml_validator import dumps_multidoc, validate_yaml_documents


def test_kubernetes_yaml_validation() -> None:
    payload = KubernetesRequest(
        application_name="payment-api",
        image="payment-api:1.0.0",
        replicas=2,
        include_ingress=True,
        include_configmap=True,
        include_hpa=True,
    )
    docs = _build_manifests(payload)
    content = dumps_multidoc(docs)
    parsed = validate_yaml_documents(content)
    kinds = {doc["kind"] for doc in parsed}
    assert {
        "Deployment",
        "Service",
        "ConfigMap",
        "Ingress",
        "HorizontalPodAutoscaler",
    } <= kinds


def test_review_static_checks_detect_root_and_secrets() -> None:
    content = "FROM alpine\nUSER root\nENV API_KEY=supersecretvalue\n"
    findings = run_static_checks("dockerfile", content)
    titles = {f.title for f in findings}
    assert "Explicit root user" in titles
    assert "Possible hardcoded secret" in titles
