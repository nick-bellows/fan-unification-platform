import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openRenderedPage(page: Page, route: string) {
  const consoleErrors: string[] = [];
  const httpErrors: string[] = [];
  const pageErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) httpErrors.push(`${response.status()} ${response.url()}`);
  });

  const deployedRoute = `/fan-unification-platform${route === "/" ? "/" : route}`;
  await page.goto(deployedRoute, { waitUntil: "networkidle" });
  await expect(page.locator(".noresults:visible")).toHaveCount(0);
  expect(pageErrors, `page errors on ${route}`).toEqual([]);
  expect(httpErrors, `HTTP errors on ${route}`).toEqual([]);
  expect(consoleErrors, `console errors on ${route}`).toEqual([]);
}

test("lineage tour renders source, warehouse, fact, and mart evidence", async ({ page }) => {
  await openRenderedPage(page, "/start");
  await expect(page.getByRole("heading", { name: "Start Here — One Record's Lineage" })).toBeVisible();
  await expect(
    page.getByText(/evidence|probabilistic score met|deterministic cluster edge/).first(),
  ).toBeVisible();
  await expect(page.locator("table:visible")).toHaveCount(5);
  expect(await page.locator("table:visible td").count()).toBeGreaterThanOrEqual(7);
  // The featured cluster must be truth-verified as ONE person, and the
  // false-merge anatomy must be present and labeled (external-review fix).
  await expect(page.getByText(/true\s+identity/i).first()).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Anatomy of a false merge" }),
  ).toBeVisible();
});

for (const check of [
  { route: "/unification", tables: 2, text: "deterministic", selector: "td:visible" },
  { route: "/ops", tables: 3, text: "Data-quality gates", selector: "a:visible" },
  { route: "/revenue", tables: 2, text: "Ticket → merch cohorts", selector: "a:visible" },
]) {
  test(`${check.route} renders its claim-bearing data`, async ({ page }) => {
    await openRenderedPage(page, check.route);
    await expect(page.locator(check.selector).filter({ hasText: check.text }).first()).toBeVisible();
    expect(await page.locator("table:visible").count()).toBeGreaterThanOrEqual(check.tables);
    expect(await page.locator("table:visible td").count()).toBeGreaterThan(check.tables);
  });
}

test("reviewer routes have no automated WCAG A/AA violations", async ({ page }) => {
  for (const route of ["/", "/start", "/unification", "/ops", "/revenue"]) {
    await openRenderedPage(page, route);
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations, `${route} accessibility violations`).toEqual([]);
  }
});
