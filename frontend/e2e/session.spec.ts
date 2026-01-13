import { test, expect } from '@playwright/test';

test.describe('Session Page', () => {
    let sessionId: string;

    test.beforeAll(async ({ browser }) => {
        // Create a session to use in tests
        const page = await browser.newPage();
        await page.goto('/');
        await page.getByRole('button', { name: /New Session/i }).click();
        await page.getByPlaceholder('Untitled Track').fill('E2E Session Tests');
        await page.getByRole('button', { name: 'Create Session' }).click();

        // Get session ID from URL
        await page.waitForURL(/\/session\/\d+/);
        const url = page.url();
        sessionId = url.split('/session/')[1];

        await page.close();
    });

    test.beforeEach(async ({ page }) => {
        await page.goto(`/session/${sessionId}`);
    });

    test('should load session page', async ({ page }) => {
        await expect(page.locator('.session-page')).toBeVisible();
        await expect(page.locator('.session-title')).toContainText('E2E Session Tests');
    });

    test('should show lyrics editor', async ({ page }) => {
        await expect(page.locator('.lyrics-editor')).toBeVisible();
        await expect(page.locator('.line-input')).toBeVisible();
    });

    test('should add a new lyric line', async ({ page }) => {
        const input = page.locator('.line-input');
        await input.fill('This is a test line for E2E testing');
        await page.keyboard.press('Enter');

        // Line should appear in the editor
        await expect(page.locator('.line-row')).toBeVisible();
        await expect(page.locator('.line-text')).toContainText('This is a test line');
    });

    test('should show section dropdown', async ({ page }) => {
        const dropdown = page.locator('.section-dropdown');
        await expect(dropdown).toBeVisible();
        await expect(dropdown).toHaveValue('Verse');

        // Change section
        await dropdown.selectOption('Chorus');
        await expect(dropdown).toHaveValue('Chorus');
    });

    test('should navigate back to workspace', async ({ page }) => {
        await page.locator('.back-link').click();
        await expect(page).toHaveURL('/');
    });

    test('should display line count and date in header', async ({ page }) => {
        await expect(page.locator('.session-stats')).toBeVisible();
    });
});
