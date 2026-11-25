from __future__ import annotations

from playwright.sync_api import Page, expect


def test_navigation_real_clock_and_patient_registration(page: Page, live_url: str) -> None:
    page.goto(live_url)
    expect(page.get_by_role("heading", name="Visão geral", exact=True)).to_be_visible()

    first_clock = page.locator("#real-clock").inner_text()
    page.wait_for_timeout(1100)
    expect(page.locator("#real-clock")).not_to_have_text(first_clock)

    page.get_by_role("link", name="Pacientes", exact=True).click()
    expect(page).to_have_url(f"{live_url}/patients")
    expect(page.get_by_role("heading", name="Pacientes", exact=True)).to_be_visible()
    expect(page.get_by_text("Distribuição por prioridade")).to_have_count(0)

    page.get_by_role("button", name="Novo paciente").click()
    page.locator("#patient-name").fill("Paciente Playwright")
    page.locator("#patient-complaint").fill("Avaliação automatizada")
    page.locator("#patient-priority-input").select_option("2")
    page.get_by_role("button", name="Cadastrar paciente").click()

    patient_row = page.locator("#patients-table tr").filter(has_text="Paciente Playwright")
    expect(patient_row).to_be_visible()
    expect(patient_row.get_by_text("P2 · Muito urgente", exact=True)).to_be_visible()
