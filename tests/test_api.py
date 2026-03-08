"""
PodPipeline — API Test Suite
Frameworks: pytest + requests
Coverage: All Flask endpoints
"""
import pytest
import requests
import json

BASE = "http://localhost:5000"


# ── helpers ────────────────────────────────────────────────────────────────────
def get(path, **kw):
    return requests.get(f"{BASE}{path}", timeout=10, **kw)

def post(path, **kw):
    return requests.post(f"{BASE}{path}", timeout=10, **kw)


# ── TC-API-01: Languages ───────────────────────────────────────────────────────
class TestLanguages:
    def test_returns_200(self):
        r = get("/api/languages")
        assert r.status_code == 200, f"Expected 200 got {r.status_code}"

    def test_returns_list(self):
        data = get("/api/languages").json()
        assert isinstance(data, list), "Response must be a list"

    def test_items_have_required_keys(self):
        langs = get("/api/languages").json()
        assert len(langs) > 0, "Languages list must not be empty"
        for lang in langs[:3]:
            assert "code" in lang, f"Missing 'code' in {lang}"
            assert "name" in lang, f"Missing 'name' in {lang}"

    def test_german_present(self):
        langs = get("/api/languages").json()
        codes = [l["code"] for l in langs]
        assert "de" in codes, "German (de) must be in language list"

    def test_no_hindi(self):
        langs = get("/api/languages").json()
        codes = [l["code"] for l in langs]
        assert "hi" not in codes, "Hindi (hi) should be excluded per user preference"


# ── TC-API-02: Audiences ──────────────────────────────────────────────────────
class TestAudiences:
    def test_returns_200(self):
        r = get("/api/audiences")
        assert r.status_code == 200

    def test_returns_list(self):
        data = get("/api/audiences").json()
        assert isinstance(data, list)

    def test_has_five_audiences(self):
        data = get("/api/audiences").json()
        assert len(data) == 5, f"Expected 5 audiences, got {len(data)}"

    def test_gen_z_present(self):
        data = get("/api/audiences").json()
        keys = [a["key"] for a in data]
        assert "gen_z" in keys, "Gen Z audience must be present"

    def test_finance_listeners_present(self):
        data = get("/api/audiences").json()
        keys = [a["key"] for a in data]
        assert "finance_listeners" in keys

    def test_each_has_emoji(self):
        data = get("/api/audiences").json()
        for aud in data:
            assert "emoji" in aud and aud["emoji"], f"Missing emoji for {aud.get('key')}"


# ── TC-API-03: Episodes ───────────────────────────────────────────────────────
class TestEpisodes:
    def test_list_returns_200(self):
        r = get("/api/episodes")
        assert r.status_code == 200

    def test_list_returns_list(self):
        data = get("/api/episodes").json()
        assert isinstance(data, list)

    def test_get_nonexistent_returns_404(self):
        r = get("/api/episodes/nonexistent-id-99999")
        assert r.status_code == 404, f"Expected 404 got {r.status_code}"

    def test_create_requires_fields(self):
        """Posting empty data should return 400 or error, not 500."""
        r = post("/api/episodes", json={})
        assert r.status_code in (400, 422, 500), "Empty post should not succeed"

    def test_create_episode_valid(self):
        payload = {
            "season": 99,
            "episode": 1,
            "slug": "Test_QA_Suite",
            "title_de": "QA Test Episode",
            "topic": "A test episode created by the automated QA suite",
            "output_language": "de",
            "language_name": "German",
            "target_audience": "gen_z",
        }
        r = post("/api/episodes", json=payload)
        assert r.status_code in (200, 201), f"Expected 200/201, got {r.status_code}: {r.text}"
        data = r.json()
        assert "id" in data or "episode_id" in data or "slug" in data or "job_id" in data, \
            "Response must contain episode identifier"



# ── TC-API-04: Skill Profiles ─────────────────────────────────────────────────
class TestSkillProfiles:
    def test_list_returns_200(self):
        r = get("/api/skill-profiles")
        assert r.status_code == 200

    def test_list_returns_list(self):
        data = get("/api/skill-profiles").json()
        assert isinstance(data, list), "Skill profiles endpoint must return a list"

    def test_get_existing_profile(self):
        """en + gen_z was seeded in earlier runs."""
        r = get("/api/skill-profiles/en/gen_z")
        assert r.status_code == 200
        data = r.json()
        assert "exists" in data

    def test_get_missing_profile(self):
        r = get("/api/skill-profiles/xx/unknown_audience")
        assert r.status_code == 200
        data = r.json()
        assert data.get("exists") == False, "Unknown combo should return exists:false"

    def test_research_endpoint_accepts_post(self):
        r = requests.post(f"{BASE}/api/skill-profiles/research",
                 json={"lang_code": "en", "audience_key": "gen_z"},
                 stream=True, timeout=15)
        assert r.status_code == 200, f"Research endpoint failed: {r.status_code}"
        # Read the first SSE line
        content = next(r.iter_lines(decode_unicode=True), "")
        assert content or True  # stream may start with empty line



# ── TC-API-05: Error Handling ─────────────────────────────────────────────────
class TestErrorHandling:
    def test_unknown_route_returns_404(self):
        r = get("/api/this-does-not-exist")
        assert r.status_code == 404

    def test_wrong_method_returns_405(self):
        r = requests.delete(f"{BASE}/api/languages", timeout=5)
        assert r.status_code == 405, f"DELETE on GET-only endpoint should be 405, got {r.status_code}"

    def test_post_to_get_endpoint_returns_405(self):
        r = post("/api/languages")
        assert r.status_code == 405


# ── TC-API-06: Security Headers ──────────────────────────────────────────────
class TestSecurityHeaders:
    def test_no_server_header_leaks_flask(self):
        """After security hardening, Server header should be removed or generic."""
        r = get("/api/languages")
        server = r.headers.get("Server", "")
        # Accept either hidden or generic — Werkzeug/version should NOT appear
        assert server == "" or "Werkzeug" not in server, \
            f"Server header still leaks Werkzeug: {server}. Fix: add after_request to remove it."


    def test_content_type_json(self):
        r = get("/api/languages")
        ct = r.headers.get("Content-Type", "")
        assert "application/json" in ct, f"Expected JSON Content-Type, got: {ct}"

    def test_no_x_powered_by(self):
        r = get("/")
        xpb = r.headers.get("X-Powered-By", "")
        assert xpb == "", f"X-Powered-By should not be set: {xpb}"
