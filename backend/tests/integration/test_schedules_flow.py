import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="TODO")
async def test_create_schedule_then_poll_until_finished(database_url: str) -> None:
    """TODO: create a demand profile, templates and employees, POST /api/schedules, poll the
    job until succeeded, then check compliance is empty and kpi coverage is at least 0.98."""


@pytest.mark.integration
@pytest.mark.skip(reason="TODO")
async def test_stale_running_runs_are_failed_on_startup(database_url: str) -> None:
    """TODO: a run left running before restart is marked failed by recover_stale_runs."""
