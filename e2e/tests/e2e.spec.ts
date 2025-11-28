import { test, expect } from '@playwright/test';

test('login and create job via admin UI', async ({ page }) => {
  await page.goto('/');
  // login (there is no real password)
  await page.fill('input[placeholder="username"]', 'e2e-user');
  await page.click('button:has-text("Login")');
  // wait for admin to load
  await page.waitForSelector('h2:has-text("Admin")');
  // create job
  await page.fill('input[placeholder="Job name"]', 'E2E Job');
  await page.click('button:has-text("Create")');
  // expect item visible
  await expect(page.locator('li')).toContainText('E2E Job');
});
