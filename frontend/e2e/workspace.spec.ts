import { test, expect } from '@playwright/test';

test.describe('Workspace Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should load workspace page', async ({ page }) => {
        await expect(page).toHaveTitle(/VibeLyrics/);
        await expect(page.locator('h1')).toContainText('Your Sessions');
    });

    test('should show new session button', async ({ page }) => {
        const newSessionButton = page.getByRole('button', { name: /New Session/i });
        await expect(newSessionButton).toBeVisible();
    });

    test('should open new session form on button click', async ({ page }) => {
        await page.getByRole('button', { name: /New Session/i }).click();
        await expect(page.locator('.new-session-form')).toBeVisible();
    });

    test('should open new session form with Ctrl+N', async ({ page }) => {
        await page.keyboard.press('Control+n');
        await expect(page.locator('.new-session-form')).toBeVisible();
    });

    test('should close form with Escape', async ({ page }) => {
        await page.getByRole('button', { name: /New Session/i }).click();
        await expect(page.locator('.new-session-form')).toBeVisible();
        await page.keyboard.press('Escape');
        await expect(page.locator('.new-session-form')).not.toBeVisible();
    });

    test('should create a new session', async ({ page }) => {
        await page.getByRole('button', { name: /New Session/i }).click();

        // Fill form
        await page.getByPlaceholder('Untitled Track').fill('Test Session');
        await page.getByRole('button', { name: 'Create Session' }).click();

        // Should navigate to session page
        await expect(page).toHaveURL(/\/session\/\d+/);
    });

    test('should display session cards when sessions exist', async ({ page }) => {
        // Create a session first
        await page.getByRole('button', { name: /New Session/i }).click();
        await page.getByPlaceholder('Untitled Track').fill('E2E Test Session');
        await page.getByRole('button', { name: 'Create Session' }).click();

        // Go back to workspace
        await page.goto('/');

        // Check session card exists
        await expect(page.locator('.session-card')).toBeVisible();
        await expect(page.locator('.session-card h3')).toContainText('E2E Test Session');
    });
});
