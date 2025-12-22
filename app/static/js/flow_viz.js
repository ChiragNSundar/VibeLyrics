class FlowVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        if (!this.canvas) return;
        this.canvas.width = this.canvas.parentElement.clientWidth;
        this.canvas.height = 100; // Fixed height for the strip
        this.draw([]);
    }

    update(lines) {
        // lines is array of {syllable_count: number}
        this.draw(lines);
    }

    draw(lines) {
        if (!this.ctx) return;

        const w = this.canvas.width;
        const h = this.canvas.height;
        const ctx = this.ctx;

        ctx.clearRect(0, 0, w, h);

        if (!lines || lines.length === 0) return;

        const barWidth = (w / lines.length) - 2;
        const maxSyllables = Math.max(...lines.map(l => l.syllable_count || 0), 16); // Scale based on max or at least 16

        lines.forEach((line, index) => {
            const count = line.syllable_count || 0;
            const barHeight = (count / maxSyllables) * h;
            const x = index * ((w / lines.length));
            const y = h - barHeight;

            // Gradient based on density
            const gradient = ctx.createLinearGradient(0, y, 0, h);
            gradient.addColorStop(0, '#8b5cf6');
            gradient.addColorStop(1, '#06b6d4');

            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Optional: Draw text
            if (barWidth > 20) {
                ctx.fillStyle = '#fff';
                ctx.font = '10px monospace';
                ctx.fillText(count, x + (barWidth / 2) - 3, h - 5);
            }
        });
    }
}
