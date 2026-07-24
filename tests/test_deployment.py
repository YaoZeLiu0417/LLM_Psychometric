import pytest

from psychometric_v2.deployment import DeploymentMode, DeploymentSettings


def test_deployment_defaults_to_public_demo(monkeypatch) -> None:
    monkeypatch.delenv("WORKBENCH_DEPLOYMENT", raising=False)
    monkeypatch.delenv("PUBLIC_DEMO_GENERATION_LIMIT", raising=False)

    settings = DeploymentSettings.from_env()

    assert settings.mode is DeploymentMode.PUBLIC_DEMO
    assert settings.public_demo_generation_limit == 3


def test_deployment_accepts_explicit_research_mode(monkeypatch) -> None:
    monkeypatch.setenv("WORKBENCH_DEPLOYMENT", "research")

    assert DeploymentSettings.from_env().mode is DeploymentMode.RESEARCH


def test_deployment_accepts_explicit_public_limit(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_DEMO_GENERATION_LIMIT", "5")

    assert DeploymentSettings.from_env().public_demo_generation_limit == 5


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("WORKBENCH_DEPLOYMENT", "production"),
        ("PUBLIC_DEMO_GENERATION_LIMIT", "0"),
        ("PUBLIC_DEMO_GENERATION_LIMIT", "four"),
    ),
)
def test_deployment_rejects_invalid_values(
    monkeypatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError, match="deployment configuration"):
        DeploymentSettings.from_env()
