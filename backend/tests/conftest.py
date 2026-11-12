import pathlib
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import require_admin
from app.db.models import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
RESULTS_PATH = pathlib.Path(__file__).parent / "test_results.md"


# ---------------------------------------------------------------------------
# DB / client fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def engine():
    e = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Admin auth mock
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=False)
def fake_admin(client):
    """Override require_admin so endpoints don't need a live Clerk JWT."""
    async def _fake():
        return "test-clerk-user"

    app.dependency_overrides[require_admin] = _fake
    yield
    app.dependency_overrides.pop(require_admin, None)


# ---------------------------------------------------------------------------
# Markdown results reporter
# ---------------------------------------------------------------------------

_results: list[tuple[str, str, str | None]] = []  # (nodeid, outcome, longrepr)


def pytest_runtest_logreport(report):
    if report.when == "call":
        longrepr = None
        if report.failed:
            longrepr = str(report.longrepr).split("\n")[-1][:120]
        _results.append((report.nodeid, report.outcome, longrepr))


def pytest_sessionfinish(session, exitstatus):
    passed = [r for r in _results if r[1] == "passed"]
    failed = [r for r in _results if r[1] == "failed"]
    skipped = [r for r in _results if r[1] == "skipped"]

    lines = [
        "# Test Results",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "| Total | Passed | Failed | Skipped |",
        "|-------|--------|--------|---------|",
        f"| {len(_results)} | {len(passed)} | {len(failed)} | {len(skipped)} |",
        "",
        "## Results",
        "",
        "| Status | Test |",
        "|--------|------|",
    ]

    for nodeid, outcome, _ in sorted(_results, key=lambda r: r[1]):
        icon = "✅" if outcome == "passed" else ("❌" if outcome == "failed" else "⏭️")
        lines.append(f"| {icon} {outcome.upper()} | `{nodeid}` |")

    if failed:
        lines += ["", "## Failures", ""]
        for nodeid, outcome, longrepr in _results:
            if outcome == "failed" and longrepr:
                lines += [f"### `{nodeid}`", "", "```", longrepr, "```", ""]

    RESULTS_PATH.write_text("\n".join(lines) + "\n")
