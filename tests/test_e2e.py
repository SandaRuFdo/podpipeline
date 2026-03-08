"""
PodPipeline — Playwright E2E Test Suite
Frameworks: pytest + playwright (chromium)
Coverage: Full UI flow testing
"""
import re
import pytest
from playwright.sync_api import Page, expect

BASE = "http://localhost:5000"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}


# ── TC-E2E-01: Dashboard ──────────────────────────────────────────────────────
class TestDashboard:
    def test_page_loads(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        expect(page.locator("h1")).to_contain_text("Dashboard")

    def test_stat_cards_present(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        # Stats cards exist (Episodes, Sources, etc.)
        cards = page.locator(".stat-card, .metric-card, .card")
        assert cards.count() >= 1

    def test_sidebar_visible(self, page: Page):
        page.goto(BASE)
        nav = page.locator(".sidebar, nav")
        expect(nav.first).to_be_visible()

    def test_title_correct(self, page: Page):
        page.goto(BASE)
        expect(page).to_have_title(re.compile("PodPipeline", re.IGNORECASE))

    def test_server_status_dot_visible(self, page: Page):
        page.goto(BASE)
        dot = page.locator(".status-dot")
        expect(dot).to_be_visible()


# ── TC-E2E-02: Sidebar Navigation ────────────────────────────────────────────
class TestSidebarNavigation:
    def test_episodes_page(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='episodes']").click()
        page.wait_for_timeout(500)
        expect(page.locator("h1")).to_contain_text("Episode")

    def test_new_episode_page(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='new-episode']").click()
        page.wait_for_timeout(500)
        expect(page.locator("h1")).to_contain_text("New Episode")

    def test_analytics_page(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='analytics']").click()
        page.wait_for_timeout(500)
        expect(page.locator("h1")).to_contain_text("Analytics")

    def test_memory_page(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='memory']").click()
        page.wait_for_timeout(500)
        expect(page.locator("h1")).to_contain_text("Memory")

    def test_active_class_applied(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        active = page.locator(".nav-link.active")
        expect(active).to_be_visible()


# ── TC-E2E-03: Language Picker ────────────────────────────────────────────────
class TestLanguagePicker:
    def goto_new_episode(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='new-episode']").click()
        page.wait_for_timeout(800)

    def test_dropdown_opens(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#lang-selected").click()
        dropdown = page.locator("#lang-dropdown")
        expect(dropdown).not_to_have_class(re.compile("hidden"))

    def test_search_filters_languages(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#lang-selected").click()
        page.locator("#lang-search-input").fill("Spa")
        page.wait_for_timeout(300)
        options = page.locator(".lang-option")
        assert options.count() >= 1, "Should show at least 1 language matching 'Spa'"

    def test_language_selection_updates_button(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#lang-selected").click()
        page.locator("#lang-search-input").fill("Spa")
        page.wait_for_timeout(300)
        page.locator(".lang-option").first.click()
        page.wait_for_timeout(300)
        text = page.locator("#lang-selected").inner_text()
        assert "Spanish" in text or "es" in text.lower(), f"Language button should show Spanish, got: {text}"

    def test_dropdown_closes_after_selection(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#lang-selected").click()
        page.locator(".lang-option").first.click()
        page.wait_for_timeout(200)
        dropdown = page.locator("#lang-dropdown")
        assert "hidden" in (dropdown.get_attribute("class") or ""), "Dropdown should close after selection"


# ── TC-E2E-04: Audience Cards ─────────────────────────────────────────────────
class TestAudienceCards:
    def goto_new_episode(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='new-episode']").click()
        page.wait_for_timeout(800)

    def test_audience_cards_render(self, page: Page):
        self.goto_new_episode(page)
        cards = page.locator(".audience-card")
        assert cards.count() == 5, f"Expected 5 audience cards, got {cards.count()}"

    def test_first_card_selected_by_default(self, page: Page):
        self.goto_new_episode(page)
        selected = page.locator(".audience-card.selected")
        assert selected.count() == 1, "Exactly one card should be pre-selected"

    def test_clicking_card_selects_it(self, page: Page):
        self.goto_new_episode(page)
        # Click Gen Z card
        gen_z = page.locator("#aud-card-gen_z")
        gen_z.click()
        page.wait_for_timeout(300)
        expect(gen_z).to_have_class(re.compile("selected"))

    def test_only_one_card_selected_at_time(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#aud-card-gen_z").click()
        page.wait_for_timeout(300)
        selected = page.locator(".audience-card.selected")
        assert selected.count() == 1, "Only one card should be selected at a time"

    def test_hidden_input_updates_on_selection(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#aud-card-millennials").click()
        page.wait_for_timeout(300)
        val = page.locator("#target-audience-input").get_attribute("value") or \
              page.evaluate("document.getElementById('target-audience-input').value")
        assert "millennials" in val.lower(), f"Hidden input should contain 'millennials', got: {val}"


# ── TC-E2E-05: Skill Profile Badge ───────────────────────────────────────────
class TestSkillProfileBadge:
    def goto_new_episode(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='new-episode']").click()
        page.wait_for_timeout(1000)

    def test_badge_is_visible(self, page: Page):
        self.goto_new_episode(page)
        badge = page.locator("#skill-profile-status")
        expect(badge).to_be_visible()

    def test_badge_updates_on_audience_change(self, page: Page):
        self.goto_new_episode(page)
        page.locator("#aud-card-gen_z").click()
        page.wait_for_timeout(800)
        badge = page.locator("#skill-profile-status")
        expect(badge).to_be_visible()
        text = badge.inner_text()
        assert len(text.strip()) > 0, "Badge should have content after audience change"


# ── TC-E2E-06: Search Overlay ─────────────────────────────────────────────────
class TestSearchOverlay:
    def test_opens_on_slash_key(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.keyboard.press("/")
        page.wait_for_timeout(300)
        overlay = page.locator("#search-overlay")
        expect(overlay).not_to_have_class(re.compile("hidden"))

    def test_closes_on_escape(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.keyboard.press("/")
        page.wait_for_timeout(300)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        overlay = page.locator("#search-overlay")
        assert "hidden" in (overlay.get_attribute("class") or ""), "Search should close on Escape"

    def test_search_input_visible_after_open(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.keyboard.press("/")
        page.wait_for_timeout(300)
        inp = page.locator("#search-input")
        expect(inp).to_be_visible()


# ── TC-E2E-07: Form Validation ────────────────────────────────────────────────
class TestNewEpisodeForm:
    def goto_new_episode(self, page: Page):
        page.goto(BASE)
        page.wait_for_load_state("networkidle")
        page.locator("[data-page='new-episode']").click()
        page.wait_for_timeout(800)

    def test_form_exists(self, page: Page):
        self.goto_new_episode(page)
        form = page.locator("#new-episode-form")
        expect(form).to_be_visible()

    def test_season_input_exists(self, page: Page):
        self.goto_new_episode(page)
        expect(page.locator("input[name='season']")).to_be_visible()

    def test_episode_input_exists(self, page: Page):
        self.goto_new_episode(page)
        expect(page.locator("input[name='episode']")).to_be_visible()

    def test_submit_button_exists(self, page: Page):
        self.goto_new_episode(page)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        btn = page.locator("button[type='submit'], .btn-primary, #submit-btn").first
        expect(btn).to_be_visible()
