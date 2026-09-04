"""_extract_answer 파싱 로직 단위 테스트.

샘플은 Phase 0 스파이크(2026-09-04)에서 실제로 관찰한 hermes CLI 출력 형태를
그대로 재현한다 — curried-percolating-ocean.md 참고.
"""
from webapp_bff.hermes_client import _extract_answer


def test_clean_output_without_reasoning_block():
    raw = (
        "↻ Resumed session 20260904_022140_67fb60 (1 user message, 8 total messages)\n"
        '방금 "오늘 영업시간이 몇시부터야?"라고 물어보셨어요. 특정 지점 알려주시면 바로 확인해 드릴게요.\n\n'
        "session_id: 20260904_022140_67fb60\n"
    )
    answer, session_id = _extract_answer(raw)
    assert session_id == "20260904_022140_67fb60"
    assert answer.startswith('방금 "오늘 영업시간이 몇시부터야?"')
    assert "session_id" not in answer


def test_output_with_reasoning_block_extracts_final_korean_answer():
    raw = (
        "**Clarifying refund policies**\n\n"
        "The file doesn't have a refund policy, so I should confirm with the manager.\n\n"
        "**Offering options for refunds**\n\n"
        "I should present the user with a couple of options in Korean.\n\n"
        "FAQ에서 환불 정책을 찾을 수 없습니다. 담당자 확인이 필요합니다.\n\n"
        "1) 담당자에게 확인해 드릴게요.\n"
        "2) 일반적인 환불 관행을 먼저 안내해 드릴게요.\n\n"
        "session_id: 20260904_013904_3ec714\n"
    )
    answer, session_id = _extract_answer(raw)
    assert session_id == "20260904_013904_3ec714"
    assert "FAQ에서 환불 정책을 찾을 수 없습니다" in answer
    assert "**" not in answer
    assert "session_id" not in answer


def test_session_id_appearing_before_the_answer_is_still_extracted():
    """실측(2026-09-04, webapp 컨테이너의 Docker SDK exec_run 호출)에서 session_id
    줄이 답변보다 앞에 나온 사례가 있었다 — docker compose exec로 확인한 순서와
    달랐다(정확한 원인은 미확인, 스트림 버퍼링 차이로 추정). 위치를 가정하지
    않고도 올바르게 분리되어야 한다."""
    raw = (
        "session_id: 20260904_030553_87dc97\n"
        "FAQ를 먼저 확인했습니다. 파일에 적힌 내용은 다음과 같습니다:\n\n"
        "- 매장 인근 공영주차장 이용, 1시간 무료\n\n"
        "확실한 확인이 필요하시면 담당자에게 확인해 드릴까요?"
    )
    answer, session_id = _extract_answer(raw)
    assert session_id == "20260904_030553_87dc97"
    assert "session_id" not in answer
    assert answer.startswith("FAQ를 먼저 확인했습니다")


def test_reasoning_leak_without_blank_line_separator_is_stripped():
    """실측(2026-09-04): reasoning 잔여물이 굵은 소제목도, 빈 줄 구분도 없이
    개행 하나(\\r\\n)만으로 답변에 바로 이어 붙어 나온 사례."""
    raw = (
        "It looks like I have an incorrect skill name. I'll have to call the "
        "function to read that file now.\r\n"
        "FAQ를 먼저 확인해봤습니다. 현재 FAQ에는 정기 휴무일이 명확히 적혀 있지 않습니다.\n\n"
        "어느 지점을 알려주시면 확인해 드릴까요?"
    )
    answer, _session_id = _extract_answer(raw)
    assert answer.startswith("FAQ를 먼저 확인해봤습니다")
    assert "incorrect skill name" not in answer


def test_missing_session_id_line_still_returns_body():
    raw = "그냥 평범한 답변입니다."
    answer, session_id = _extract_answer(raw)
    assert session_id is None
    assert answer == "그냥 평범한 답변입니다."
