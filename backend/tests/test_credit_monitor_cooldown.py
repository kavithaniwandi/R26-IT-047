"""Credit cooldown tests use only temporary JSON state and a mocked clock."""
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfoNotFoundError

import pytest

from app.services import credit_monitor as cm


@pytest.fixture
def clock(monkeypatch, tmp_path):
    times = [datetime(2026, 10, 16, 4, 22, tzinfo=timezone.utc)]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return times[0].astimezone(tz) if tz else times[0].replace(tzinfo=None)

    monkeypatch.setattr(cm, 'datetime', Clock)
    monkeypatch.setattr(cm, 'STATE_FILE', tmp_path / 'credit.json')
    monkeypatch.setattr(cm, '_key_state', {})
    return times


@pytest.mark.parametrize(('exhausted_at', 'deadline'), [
    ('2026-10-16T04:22:00+00:00', '2026-10-16T07:00:00+00:00'),
    ('2026-03-08T08:30:00+00:00', '2026-03-09T07:00:00+00:00'),
    ('2026-11-01T07:30:00+00:00', '2026-11-02T08:00:00+00:00'),
])
def test_expires_at_next_los_angeles_midnight_across_dst(clock, exhausted_at, deadline):
    state = {'exhausted': True, 'exhausted_at': exhausted_at, 'calls': 9, 'failures': 2}
    cm._key_state['gemini_key_1'] = state
    end = datetime.fromisoformat(deadline)
    clock[0] = end - timedelta(seconds=1)
    assert cm.is_exhausted('gemini_key_1')
    clock[0] = end
    assert not cm.is_exhausted('gemini_key_1')
    assert state == {'exhausted': False, 'exhausted_at': None, 'calls': 9, 'failures': 2}
    assert json.loads(cm.STATE_FILE.read_text())['gemini_key_1'] == state


def test_timezone_failure_uses_twenty_four_hours(clock, monkeypatch):
    def missing_zone(name):
        raise ZoneInfoNotFoundError(name)
    monkeypatch.setattr(cm, 'ZoneInfo', missing_zone)
    start = clock[0]
    cm.mark_exhausted('gemini_key_1')
    clock[0] = start + timedelta(hours=24) - timedelta(seconds=1)
    assert cm.is_exhausted('gemini_key_1')
    clock[0] = start + timedelta(hours=24)
    assert not cm.is_exhausted('gemini_key_1')


def test_restart_reloads_timestamp_and_status_clears_expired_key(clock):
    cm._key_state['gemini_key_1'] = {
        'exhausted': True, 'exhausted_at': '2026-10-16T04:22:00+00:00',
        'calls': 9, 'failures': 2,
    }
    cm._save_state()
    cm._key_state.clear()
    cm._load_state()
    assert cm.is_exhausted('gemini_key_1')
    clock[0] = datetime(2026, 10, 16, 7, tzinfo=timezone.utc)
    status = cm.get_status()
    key = next(p for p in status['providers'] if p['provider'] == 'GEMINI_KEY_1')
    assert not key['exhausted']
    assert key['calls_today'] == 9
    assert key['failures'] == 2


@pytest.mark.parametrize('timestamp', [None, 'invalid'])
def test_legacy_state_gets_finite_cooldown(clock, timestamp):
    cm._key_state['gemini_key_1'] = {'exhausted': True, 'exhausted_at': timestamp}
    assert cm.is_exhausted('gemini_key_1')
    assert cm._key_state['gemini_key_1']['exhausted_at'] == clock[0].isoformat()
    clock[0] = datetime(2026, 10, 16, 7, tzinfo=timezone.utc)
    assert not cm.is_exhausted('gemini_key_1')


def test_unseen_keys_do_not_create_state(clock):
    assert not cm.is_exhausted('gemini_key_11')
    assert cm._key_state == {}
    assert not cm.STATE_FILE.exists()
