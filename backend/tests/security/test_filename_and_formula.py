from app.utils.filename import sanitize_filename
from app.utils.formula_injection import escape_csv_formula
from app.utils.text_normalization import normalize_identifier


def test_sanitize_filename_strips_path_and_unsafe_chars() -> None:
    assert sanitize_filename("../../etc/passwd.log") == "passwd.log"
    assert sanitize_filename('bad<>:"|?*.txt') == "bad_______.txt"
    assert sanitize_filename("") == "upload"


def test_sanitize_filename_truncates_long_names() -> None:
    long_name = "a" * 300 + ".log"
    sanitized = sanitize_filename(long_name, max_length=20)
    assert len(sanitized) <= 20
    assert sanitized.endswith(".log")


def test_escape_csv_formula_prefixes_dangerous_values() -> None:
    assert escape_csv_formula("=1+1") == "'=1+1"
    assert escape_csv_formula("+123") == "'+123"
    assert escape_csv_formula("-123") == "'-123"
    assert escape_csv_formula("@SUM(A1)") == "'@SUM(A1)"
    assert escape_csv_formula("safe text") == "safe text"


def test_normalize_identifier_uses_nfkc() -> None:
    assert normalize_identifier(" Ａｌｉｃｅ ") == "Alice"
    assert normalize_identifier("café") == "café"
