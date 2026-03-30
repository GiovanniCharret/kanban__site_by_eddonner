import { expect, test } from "@playwright/test";

test("loads board and supports core card flow", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Kanban Project Board" })).toBeVisible();
  await expect(page.locator(".column")).toHaveCount(5);

  await page.getByRole("button", { name: "+ Add card" }).first().click();
  const form = page.locator(".add-card-form").first();
  await form.getByLabel("Title", { exact: true }).fill("E2E task");
  await form.getByLabel("Details", { exact: true }).fill("Created in Playwright");
  await form.getByRole("button", { name: "Create" }).click();

  await expect(page.getByText("E2E task")).toBeVisible();

  const createdCard = page.locator("article").filter({ hasText: "E2E task" });
  await createdCard.getByRole("button", { name: "Delete" }).click();

  await expect(page.getByText("E2E task")).toHaveCount(0);
});
