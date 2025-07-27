from datetime import datetime
import slack_summary_bot as bot


def test_format_messages():
    messages = [
        {"type": "message", "user": "U1", "text": "Hello", "ts": "100"},
        {"type": "message", "user": "U2", "subtype": "bot_message", "text": "Bot", "ts": "101"},
        {"type": "message", "user": "BOT", "text": "skip", "ts": "102"},
        {"type": "message", "user": "U3", "text": "Thread", "ts": "103", "thread_ts": "103"},
        {"type": "message", "user": "U4", "text": "Reply", "ts": "104", "thread_ts": "103"},
        {"type": "file_share", "user": "U5", "text": "file", "ts": "105"},
    ]
    formatted = bot.format_messages(messages, "BOT")
    assert formatted == [
        {"user": "U1", "text": "Hello", "ts": "100", "thread_ts": ""},
        {"user": "U3", "text": "Thread", "ts": "103", "thread_ts": "103"},
        {"user": "U4", "text": "Reply", "ts": "104", "thread_ts": "103"},
    ]


def test_update_message_list():
    message_list = [
        {"user": "U1", "text": "Hi", "ts": "100"},
        {"user": "U2", "text": "Parent", "ts": "101", "thread_ts": "101"},
        {"user": "U3", "text": "Later", "ts": "106"},
    ]
    threaded = [
        {"user": "U4", "text": "R1", "ts": "103"},
        {"user": "U5", "text": "R0", "ts": "102"},
    ]
    result = bot.update_message_list(message_list[:], threaded, "101")
    assert [m["ts"] for m in result] == [
        "100",
        "101",
        "102",
        "103",
        "106",
    ]


class FixedDateTime(datetime):
    fixed_now = datetime(2024, 4, 8, 12, 0, 0)

    @classmethod
    def now(cls):
        return cls.fixed_now


def test_get_time_range_daily(monkeypatch):
    monkeypatch.setattr(bot, "RUN_DAILY", True)
    monkeypatch.setattr(bot, "datetime", FixedDateTime)
    start, end = bot.get_time_range()
    assert end == FixedDateTime.fixed_now
    assert start == FixedDateTime.fixed_now - bot.timedelta(days=1)


def test_get_time_range_weekend_skip(monkeypatch):
    weekend = FixedDateTime.fixed_now
    weekend = weekend - bot.timedelta(days=weekend.weekday() - 5)  # set to Saturday
    class WeekEndDT(FixedDateTime):
        fixed_now = weekend
    monkeypatch.setattr(bot, "RUN_DAILY", False)
    monkeypatch.setattr(bot, "datetime", WeekEndDT)
    start, end = bot.get_time_range()
    assert start is None and end is None


def test_get_time_range_weekstart(monkeypatch):
    monday = FixedDateTime.fixed_now
    monday = monday - bot.timedelta(days=monday.weekday())  # set to Monday
    class MondayDT(FixedDateTime):
        fixed_now = monday
    monkeypatch.setattr(bot, "RUN_DAILY", False)
    monkeypatch.setattr(bot, "datetime", MondayDT)
    start, end = bot.get_time_range()
    assert end == monday
    assert start == monday - bot.timedelta(days=3)

