def _call_generate_any_method(client):
    for m in ("post", "get", "put"):
        resp = getattr(client, m)("/api/report/generate")
        if resp.status_code != 405:
            return resp
    return resp


def _mock_html_generation(monkeypatch, tmp_path):
    import reports

    def fake_generate(self):
        out_dir = tmp_path / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "detailed_report_TEST.html"
        p.write_text("<html><body>TEST</body></html>", encoding="utf-8")
        return str(p)

    monkeypatch.setattr(reports.ReportGenerator, "generate_detailed_html_report", fake_generate, raising=True)


def _mock_csv_generation(monkeypatch, tmp_path):
    import reports

    def fake_generate(self):
        out_dir = tmp_path / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "course_report_TEST.csv"
        p.write_text("a,b\n1,2\n", encoding="utf-8")
        return str(p)

    monkeypatch.setattr(reports.ReportGenerator, "generate_full_report", fake_generate, raising=True)


def test_api_report_generate_csv(client, monkeypatch, tmp_path):
    _mock_csv_generation(monkeypatch, tmp_path)

    resp = _call_generate_any_method(client)
    assert resp.status_code == 200

    # Если endpoint отдаёт JSON
    if resp.is_json:
        data = resp.get_json()
        assert data.get("status") == "success"
    else:
        # Если endpoint отдаёт файл
        ct = resp.headers.get("Content-Type", "")
        assert ("text/csv" in ct) or ("application/octet-stream" in ct)


def test_api_report_view_html(client, monkeypatch, tmp_path):
    _mock_html_generation(monkeypatch, tmp_path)

    resp = client.get("/api/report/view-html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("Content-Type", "")
    assert "<html" in resp.get_data(as_text=True).lower()


def test_api_report_download_html(client, monkeypatch, tmp_path):
    _mock_html_generation(monkeypatch, tmp_path)

    resp = client.get("/api/report/download-html")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("Content-Type", "")
    cd = resp.headers.get("Content-Disposition", "")
    assert "attachment" in cd.lower()
    assert ".html" in cd.lower()


def test_api_report_recommendations(client):
    resp = client.get("/api/report/recommendations")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "title" in data[0]
    assert "description" in data[0]
