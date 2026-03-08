from app.domain.bt_run.compare import build_note


def test_build_note_ok() -> None:
    assert build_note(0, 0) == "BT und RUN sind im Toleranzbereich."