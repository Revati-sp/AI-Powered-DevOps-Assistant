from app.utils.command_risk import classify_command_risk


def test_critical_rm_rf() -> None:
    result = classify_command_risk("rm -rf /")
    assert result.risk_level == "critical"
    assert result.requires_confirmation is True


def test_high_chmod() -> None:
    result = classify_command_risk("chmod -R 777 /var/www")
    assert result.risk_level == "high"


def test_low_safe_command() -> None:
    result = classify_command_risk("ls -la /var/log")
    assert result.risk_level == "low"
    assert result.requires_confirmation is False
