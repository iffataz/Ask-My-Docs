from tests.conftest import FakeAppContext


def test_upload_txt_returns_chunk_count(fake_app: FakeAppContext) -> None:
    response = fake_app.client.post(
        "/documents", files={"file": ("note.txt", b"hello world", "text/plain")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "note.txt"
    assert body["chunk_count"] == 1
    assert body["document_id"]


def test_list_documents_after_upload(fake_app: FakeAppContext) -> None:
    fake_app.client.post(
        "/documents", files={"file": ("note.txt", b"hello world", "text/plain")}
    )

    response = fake_app.client.get("/documents")

    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "note.txt"


def test_delete_document_is_idempotent(fake_app: FakeAppContext) -> None:
    upload = fake_app.client.post(
        "/documents", files={"file": ("note.txt", b"hello world", "text/plain")}
    )
    document_id = upload.json()["document_id"]

    first = fake_app.client.delete(f"/documents/{document_id}")
    second = fake_app.client.delete(f"/documents/{document_id}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert fake_app.client.get("/documents").json() == []


def test_upload_unsupported_extension_returns_structured_400(fake_app: FakeAppContext) -> None:
    response = fake_app.client.post(
        "/documents", files={"file": ("virus.exe", b"MZ", "application/octet-stream")}
    )

    assert response.status_code == 400
    assert "detail" in response.json()
