class FlowVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.linesPerBar = 4; // Standard hip-hop bar = 4 lines
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        if (!this.canvas) return;
        this.canvas.width = this.canvas.parentElement.clientWidth;
        this.canvas.height = 100;
        this.draw([]);
    }

    update(lines) {
        this.draw(lines);
    }

    draw(lines) {
        if (!this.ctx) return;

        const w = this.canvas.width;
        const h = this.canvas.height;
        const ctx = this.ctx;

        ctx.clearRect(0, 0, w, h);

        if (!lines || lines.length === 0) {
            this.drawEmptyState(ctx, w, h);
            return;
        }

        // Group lines into bars (4 lines = 1 bar)
        const bars = this.groupIntoBars(lines);

        const barWidth = Math.max((w / Math.max(bars.length, 1)) - 4, 20);
        const maxSyllables = Math.max(...bars.map(b => b.totalSyllables), 48); // 4 bars * ~12 syllables

        bars.forEach((bar, index) => {
            const x = index * ((w / Math.max(bars.length, 1))) + 2;
            const barHeight = (bar.totalSyllables / maxSyllables) * (h - 20);
            const y = h - barHeight - 10;

            // Color based on density category
            const color = this.getDensityColor(bar.avgSyllables);

            // Draw bar
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.roundRect(x, y, barWidth, barHeight, 4);
            ctx.fill();

            // Draw bar number
            ctx.fillStyle = 'rgba(255,255,255,0.7)';
            ctx.font = 'bold 11px system-ui';
            ctx.textAlign = 'center';
            ctx.fillText(`${bar.avgSyllables}`, x + barWidth / 2, h - 2);
        });

        // Draw legend
        this.drawLegend(ctx, w);
    }

    groupIntoBars(lines) {
        const bars = [];
        for (let i = 0; i < lines.length; i += this.linesPerBar) {
            const barLines = lines.slice(i, i + this.linesPerBar);
            const totalSyllables = barLines.reduce((sum, l) => sum + (l.syllable_count || 0), 0);
            const avgSyllables = Math.round(totalSyllables / barLines.length);
            bars.push({
                lines: barLines,
                totalSyllables,
                avgSyllables,
                lineCount: barLines.length
            });
        }
        return bars;
    }

    getDensityColor(avgSyllables) {
        if (avgSyllables <= 8) return '#22c55e';  // Green - sparse/laid back
        if (avgSyllables <= 12) return '#8b5cf6'; // Purple - medium flow
        if (avgSyllables <= 16) return '#f59e0b'; // Orange - dense
        return '#ef4444'; // Red - chopper/double time
    }

    drawLegend(ctx, w) {
        const legendItems = [
            { color: '#22c55e', label: 'Chill' },
            { color: '#8b5cf6', label: 'Flow' },
            { color: '#f59e0b', label: 'Dense' },
            { color: '#ef4444', label: 'Chopper' }
        ];

        let x = w - 180;
        ctx.font = '10px system-ui';

        legendItems.forEach(item => {
            ctx.fillStyle = item.color;
            ctx.fillRect(x, 5, 12, 12);
            ctx.fillStyle = 'rgba(255,255,255,0.6)';
            ctx.fillText(item.label, x + 16, 14);
            x += 45;
        });
    }

    drawEmptyState(ctx, w, h) {
        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.font = '14px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText('Start writing to see your flow visualization', w / 2, h / 2);
    }
}
