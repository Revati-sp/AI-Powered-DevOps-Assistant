from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_artifact import ArtifactType
from app.models.user import User
from app.repositories.artifact_repository import ArtifactRepository
from app.schemas.generators import KubernetesRequest, KubernetesResponse
from app.services.yaml_validator import dumps_multidoc, validate_yaml_documents


def _labels(name: str) -> dict[str, str]:
    return {
        "app.kubernetes.io/name": name,
        "app.kubernetes.io/instance": name,
        "app.kubernetes.io/managed-by": "ai-devops-assistant",
    }


def _build_manifests(payload: KubernetesRequest) -> list[dict[str, Any]]:
    name = payload.application_name
    labels = _labels(name)
    docs: list[dict[str, Any]] = []

    if payload.include_configmap:
        docs.append(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": f"{name}-config", "labels": labels},
                "data": {
                    "APP_ENV": "production",
                    "LOG_LEVEL": "info",
                },
            }
        )

    docs.append(
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": name, "labels": labels},
            "spec": {
                "replicas": payload.replicas,
                "selector": {"matchLabels": {"app.kubernetes.io/name": name}},
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {"maxUnavailable": 0, "maxSurge": 1},
                },
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {
                        "securityContext": {
                            "runAsNonRoot": True,
                            "runAsUser": 1000,
                            "seccompProfile": {"type": "RuntimeDefault"},
                        },
                        "containers": [
                            {
                                "name": name,
                                "image": payload.image,
                                "imagePullPolicy": "IfNotPresent",
                                "ports": [
                                    {
                                        "name": "http",
                                        "containerPort": payload.container_port,
                                    }
                                ],
                                "envFrom": (
                                    [{"configMapRef": {"name": f"{name}-config"}}]
                                    if payload.include_configmap
                                    else []
                                ),
                                "resources": {
                                    "requests": {
                                        "cpu": payload.cpu_request,
                                        "memory": payload.memory_request,
                                    },
                                    "limits": {
                                        "cpu": payload.cpu_limit,
                                        "memory": payload.memory_limit,
                                    },
                                },
                                "securityContext": {
                                    "allowPrivilegeEscalation": False,
                                    "privileged": False,
                                    "readOnlyRootFilesystem": True,
                                    "capabilities": {"drop": ["ALL"]},
                                },
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/health",
                                        "port": "http",
                                    },
                                    "initialDelaySeconds": 20,
                                    "periodSeconds": 20,
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/ready",
                                        "port": "http",
                                    },
                                    "initialDelaySeconds": 10,
                                    "periodSeconds": 10,
                                },
                            }
                        ],
                    },
                },
            },
        }
    )

    docs.append(
        {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": name, "labels": labels},
            "spec": {
                "type": payload.service_type,
                "selector": {"app.kubernetes.io/name": name},
                "ports": [
                    {
                        "name": "http",
                        "port": payload.container_port,
                        "targetPort": "http",
                    }
                ],
            },
        }
    )

    if payload.include_ingress:
        docs.append(
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {
                    "name": f"{name}-ingress",
                    "labels": labels,
                    "annotations": {
                        "kubernetes.io/ingress.class": "nginx",
                    },
                },
                "spec": {
                    "rules": [
                        {
                            "host": f"{name}.example.com",
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": name,
                                                "port": {
                                                    "number": payload.container_port
                                                },
                                            }
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            }
        )

    if payload.include_hpa:
        docs.append(
            {
                "apiVersion": "autoscaling/v2",
                "kind": "HorizontalPodAutoscaler",
                "metadata": {"name": f"{name}-hpa", "labels": labels},
                "spec": {
                    "scaleTargetRef": {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "name": name,
                    },
                    "minReplicas": max(1, payload.replicas),
                    "maxReplicas": max(payload.replicas + 2, 5),
                    "metrics": [
                        {
                            "type": "Resource",
                            "resource": {
                                "name": "cpu",
                                "target": {
                                    "type": "Utilization",
                                    "averageUtilization": 70,
                                },
                            },
                        }
                    ],
                },
            }
        )

    return docs


class KubernetesGeneratorService:
    def __init__(self, session: AsyncSession) -> None:
        self.artifacts = ArtifactRepository(session)

    async def generate(
        self, user: User, payload: KubernetesRequest
    ) -> KubernetesResponse:
        docs = _build_manifests(payload)
        content = dumps_multidoc(docs)
        validate_yaml_documents(content)

        warnings: list[str] = []
        if payload.image.endswith(":latest") or ":" not in payload.image:
            warnings.append(
                "Image appears unpinned or uses 'latest'. Prefer immutable tags/digests."
            )
        if payload.service_type == "LoadBalancer":
            warnings.append(
                "LoadBalancer may expose the service publicly depending on cloud setup."
            )

        result = KubernetesResponse(
            content=content,
            explanation=[
                "Generated Deployment, Service, and optional ConfigMap/Ingress/HPA",
                "Includes non-root security context, probes, and resource limits",
                "Manifests are a preview only and were not applied to any cluster",
            ],
            warnings=warnings,
            best_practices=[
                "Pin image digests",
                "Restrict network policies",
                "Store secrets in Secret objects or an external secret manager",
            ],
        )

        await self.artifacts.create_artifact(
            user_id=user.id,
            artifact_type=ArtifactType.KUBERNETES,
            name=f"{payload.application_name}-manifests",
            content=result.content,
            metadata_json=result.model_dump(exclude={"content"}),
        )
        return result
