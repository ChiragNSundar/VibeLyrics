// VibeLyrics Alpine.js Components

document.addEventListener('alpine:init', () => {
    // Dropdown Component using x-data="dropdown"
    Alpine.data('dropdown', () => ({
        open: false,
        toggle() {
            this.open = !this.open;
        },
        close() {
            this.open = false;
        }
    }));

    // Sidebar Panel Component
    Alpine.data('sidebarPanel', () => ({
        activeTab: 'ai',

        switchTab(tabName) {
            this.activeTab = tabName;
            // Also ensure panel is open if switching tabs
            if (!Alpine.store('aiPanel').open) {
                Alpine.store('aiPanel').open = true;
            }
        },

        isActive(tabName) {
            return this.activeTab === tabName;
        }
    }));
});
