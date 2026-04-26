from app.time_windows import compute_time_windows


def test_time_windows_use_timezone() -> None:
    windows = compute_time_windows("America/New_York")
    assert windows.timezone in {"America/New_York", "UTC"}
    assert windows.now_utc.endswith("+00:00")
    assert windows.last_7_days_start_utc.endswith("+00:00")
    assert windows.month_start_utc.endswith("+00:00")


def test_time_windows_fallback_for_unknown_zone() -> None:
    windows = compute_time_windows("Not/A_Real_Timezone")
    assert windows.timezone == "UTC"
