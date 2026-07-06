from tests.conftest import FakeAppContext


def _parse_sse(text: str) -> list[tuple[str, str]]:
    events = []
    for block in text.strip().split("\n\n"):
        if not block:
            continue
        lines = block.splitlines()
        event = next(line.removeprefix("event: ") for line in lines if line.startswith("event: "))
        data = next(line.removeprefix("data: ") for line in lines if line.startswith("data: "))
        events.append((event, data))
    return events


def test_chat_streams_tokens_then_done(fake_app: FakeAppContext) -> None:
    with fake_app.client.stream(
        "POST", "/chat", json={"question": "what color is the sky"}
    ) as response:
        events = _parse_sse(response.read().decode())

    token_events = [e for e in events if e[0] == "token"]
    done_events = [e for e in events if e[0] == "done"]

    assert len(token_events) > 0
    assert len(done_events) == 1
    assert "sources" in done_events[0][1]


def test_chat_general_route_has_no_sources(fake_app: FakeAppContext) -> None:
    fake_app.llm._route = "general"

    with fake_app.client.stream(
        "POST", "/chat", json={"question": "what's 2 + 2"}
    ) as response:
        events = _parse_sse(response.read().decode())

    done_events = [e for e in events if e[0] == "done"]
    assert done_events[0][1] == '{"sources": []}'
