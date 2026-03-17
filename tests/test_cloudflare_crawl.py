import json
from unittest.mock import MagicMock, patch

import pytest

import cloudflare_crawl


def make_response(data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setattr(cloudflare_crawl, "account_id", "test-account")
    monkeypatch.setattr(cloudflare_crawl, "token", "test-token")


def test_start_crawl_returns_job_id():
    resp = make_response({"success": True, "result": "job-abc123"})
    with patch.object(cloudflare_crawl.https, "post", return_value=resp) as mock_post:
        job_id = cloudflare_crawl.start_crawl("https://example.com")

    assert job_id == "job-abc123"
    mock_post.assert_called_once_with(
        "https://api.cloudflare.com/client/v4/accounts/test-account/browser-rendering/crawl",
        headers=cloudflare_crawl.headers,
        json={"url": "https://example.com", "formats": ["html", "markdown"], "limit": 5000},
    )


def test_start_crawl_raises_on_http_error():
    resp = make_response({}, status_code=500)
    resp.raise_for_status.side_effect = Exception("HTTP 500")
    with patch.object(cloudflare_crawl.https, "post", return_value=resp):
        with pytest.raises(Exception, match="HTTP 500"):
            cloudflare_crawl.start_crawl("https://example.com")


def test_start_crawl_raises_when_success_false():
    resp = make_response({"success": False, "errors": ["bad request"]})
    with patch.object(cloudflare_crawl.https, "post", return_value=resp):
        with pytest.raises(Exception):
            cloudflare_crawl.start_crawl("https://example.com")


def test_get_job_returns_job_dict():
    job_data = {
        "success": True,
        "result": {"status": "complete", "total": 10, "finished": 10, "skipped": 0},
    }
    resp = make_response(job_data)
    with patch.object(cloudflare_crawl.https, "get", return_value=resp):
        result = cloudflare_crawl.get_job("job-abc123")

    assert result == job_data


def test_get_job_raises_on_http_error():
    resp = make_response({}, status_code=404)
    resp.raise_for_status.side_effect = Exception("HTTP 404")
    with patch.object(cloudflare_crawl.https, "get", return_value=resp):
        with pytest.raises(Exception, match="HTTP 404"):
            cloudflare_crawl.get_job("job-abc123")


def test_wait_for_job_returns_immediately_when_not_running():
    job_data = {"result": {"status": "complete", "total": 5, "finished": 5, "skipped": 0}}
    with patch("cloudflare_crawl.get_job", return_value=job_data) as mock_get_job:
        status = cloudflare_crawl.wait_for_job("job-abc123")

    assert status == "complete"
    mock_get_job.assert_called_once_with("job-abc123", params={"limit": 1})


def test_wait_for_job_polls_until_complete():
    running = {"result": {"status": "running", "total": 10, "finished": 3, "skipped": 0}}
    done = {"result": {"status": "complete", "total": 10, "finished": 10, "skipped": 0}}

    with patch("cloudflare_crawl.get_job", side_effect=[running, done]) as mock_get_job:
        with patch("cloudflare_crawl.time.sleep") as mock_sleep:
            status = cloudflare_crawl.wait_for_job("job-abc123", sleep_secs=1)

    assert status == "complete"
    assert mock_get_job.call_count == 2
    mock_sleep.assert_called_once_with(1)


def test_wait_for_job_returns_failed_status():
    job_data = {"result": {"status": "failed", "total": 5, "finished": 2, "skipped": 0}}
    with patch("cloudflare_crawl.get_job", return_value=job_data):
        status = cloudflare_crawl.wait_for_job("job-abc123")

    assert status == "failed"


def test_write_results_single_page(tmp_path):
    result_data = {
        "result": {
            "status": "complete",
            "records": [{"url": "https://example.com", "content": "hello"}],
        }
    }
    resp = make_response(result_data)
    with patch.object(cloudflare_crawl.https, "get", return_value=resp):
        cloudflare_crawl.write_results("job-abc123", tmp_path)

    output_file = tmp_path / "job-abc123-001.json"
    assert output_file.exists()
    written = json.loads(output_file.read_text())
    assert written == result_data


def test_write_results_multiple_pages(tmp_path):
    page1 = {"result": {"records": [{"url": "https://example.com/1"}], "cursor": "cursor1"}}
    page2 = {"result": {"records": [{"url": "https://example.com/2"}]}}

    responses = [make_response(page1), make_response(page2)]
    with patch.object(cloudflare_crawl.https, "get", side_effect=responses) as mock_get:
        cloudflare_crawl.write_results("job-abc123", tmp_path)

    assert (tmp_path / "job-abc123-001.json").exists()
    assert (tmp_path / "job-abc123-002.json").exists()

    second_call_params = mock_get.call_args_list[1][1]["params"]
    assert second_call_params["cursor"] == "cursor1"


def test_write_results_creates_download_dir(tmp_path):
    new_dir = tmp_path / "new_subdir"
    result_data = {"result": {"records": []}}
    resp = make_response(result_data)
    with patch.object(cloudflare_crawl.https, "get", return_value=resp):
        cloudflare_crawl.write_results("job-abc123", new_dir)

    assert new_dir.is_dir()


def test_write_results_defaults_to_current_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result_data = {"result": {"records": []}}
    resp = make_response(result_data)
    with patch.object(cloudflare_crawl.https, "get", return_value=resp):
        cloudflare_crawl.write_results("job-abc123", None)

    assert (tmp_path / "job-abc123-001.json").exists()


def test_write_results_stops_when_cursor_unchanged(tmp_path):
    page = {"result": {"records": [], "cursor": "same-cursor"}}
    responses = [make_response(page), make_response(page)]
    with patch.object(cloudflare_crawl.https, "get", side_effect=responses):
        cloudflare_crawl.write_results("job-abc123", tmp_path)

    assert (tmp_path / "job-abc123-001.json").exists()
    assert (tmp_path / "job-abc123-002.json").exists()
    assert not (tmp_path / "job-abc123-003.json").exists()
