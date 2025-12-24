/**
 * Enhanced Flow Visualizer
 * Premium visualization of lyric flow patterns with gradients, animations, and details
 */
class FlowVisualizer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.linesPerBar = 4;
        this.animationProgress = 0;
        this.bars = [];
        this.hoveredBar = -1;

        // Enhanced color palette with gradients
        this.colors = {
            chill: { start: '#10b981', end: '#059669', glow: 'rgba(16, 185, 129, 0.3)' },
            flow: { start: '#8b5cf6', end: '#7c3aed', glow: 'rgba(139, 92, 246, 0.3)' },
            dense: { start: '#f59e0b', end: '#d97706', glow: 'rgba(245, 158, 11, 0.3)' },
            chopper: { start: '#ef4444', end: '#dc2626', glow: 'rgba(239, 68, 68, 0.3)' }
        };

        this.resize();
        window.addEventListener('resize', () => this.resize());

        // Mouse interaction
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseleave', () => { this.hoveredBar = -1; this.draw(this.bars); });
    }

    resize() {
        if (!this.canvas) return;
        this.canvas.width = this.canvas.parentElement.clientWidth;
        this.canvas.height = 120; // Taller for better visuals
        this.draw(this.bars);
    }

    update(lines) {
        this.bars = this.groupIntoBars(lines);
        this.animateIn();
    }

    animateIn() {
        this.animationProgress = 0;
        const animate = () => {
            this.animationProgress = Math.min(1, this.animationProgress + 0.08);
            this.draw(this.bars);
            if (this.animationProgress < 1) {
                requestAnimationFrame(animate);
            }
        };
        animate();
    }

    draw(bars) {
        if (!this.ctx) return;

        const w = this.canvas.width;
        const h = this.canvas.height;
        const ctx = this.ctx;

        // Clear with gradient background
        const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
        bgGrad.addColorStop(0, 'rgba(15, 15, 30, 0.9)');
        bgGrad.addColorStop(1, 'rgba(25, 25, 45, 0.9)');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, w, h);

        if (!bars || bars.length === 0) {
            this.drawEmptyState(ctx, w, h);
            return;
        }

        const padding = 20;
        const barGap = 6;
        const availableWidth = w - (padding * 2);
        const barWidth = Math.max((availableWidth / bars.length) - barGap, 30);
        const maxSyllables = Math.max(...bars.map(b => b.totalSyllables), 48);
        const maxHeight = h - 40;

        // Draw grid lines
        this.drawGrid(ctx, w, h, maxHeight);

        bars.forEach((bar, index) => {
            const x = padding + index * (barWidth + barGap);
            const targetHeight = (bar.totalSyllables / maxSyllables) * maxHeight;
            const barHeight = targetHeight * this.animationProgress;
            const y = h - barHeight - 20;

            const colorSet = this.getColorSet(bar.avgSyllables);
            const isHovered = this.hoveredBar === index;

            // Draw glow effect
            if (isHovered || bar.avgSyllables > 14) {
                ctx.shadowColor = colorSet.glow;
                ctx.shadowBlur = isHovered ? 20 : 10;
            }

            // Create gradient for bar
            const barGrad = ctx.createLinearGradient(x, y + barHeight, x, y);
            barGrad.addColorStop(0, colorSet.end);
            barGrad.addColorStop(1, colorSet.start);

            // Draw bar with rounded corners
            ctx.fillStyle = barGrad;
            ctx.beginPath();
            this.roundRect(ctx, x, y, barWidth, barHeight, 6);
            ctx.fill();

            // Reset shadow
            ctx.shadowBlur = 0;

            // Draw shine effect on top
            const shineGrad = ctx.createLinearGradient(x, y, x + barWidth, y);
            shineGrad.addColorStop(0, 'rgba(255,255,255,0.2)');
            shineGrad.addColorStop(0.5, 'rgba(255,255,255,0.05)');
            shineGrad.addColorStop(1, 'rgba(255,255,255,0.1)');
            ctx.fillStyle = shineGrad;
            ctx.beginPath();
            this.roundRect(ctx, x, y, barWidth, Math.min(barHeight, 15), 6);
            ctx.fill();

            // Draw bar number label
            ctx.fillStyle = 'rgba(255,255,255,0.9)';
            ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`${index + 1}`, x + barWidth / 2, h - 5);

            // Draw syllable count on bar if hovered or tall enough
            if (isHovered || barHeight > 40) {
                ctx.fillStyle = 'rgba(255,255,255,0.95)';
                ctx.font = 'bold 12px system-ui';
                ctx.fillText(`${bar.avgSyllables}`, x + barWidth / 2, y + 18);

                if (isHovered) {
                    ctx.font = '10px system-ui';
                    ctx.fillStyle = 'rgba(255,255,255,0.7)';
                    ctx.fillText('syl/line', x + barWidth / 2, y + 30);
                }
            }

            // Draw mini line indicators at bottom of bar
            this.drawLineIndicators(ctx, bar, x, y + barHeight - 8, barWidth);
        });

        // Draw legend and stats
        this.drawLegend(ctx, w);
        this.drawStats(ctx, w, bars);
    }

    drawGrid(ctx, w, h, maxHeight) {
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 1;

        // Horizontal grid lines
        for (let i = 0; i <= 4; i++) {
            const y = h - 20 - (maxHeight * i / 4);
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(w, y);
            ctx.stroke();
        }
    }

    drawLineIndicators(ctx, bar, x, y, barWidth) {
        const dotSize = 4;
        const gap = 6;
        const startX = x + (barWidth - (bar.lineCount * (dotSize + gap) - gap)) / 2;

        for (let i = 0; i < bar.lineCount; i++) {
            ctx.fillStyle = 'rgba(255,255,255,0.5)';
            ctx.beginPath();
            ctx.arc(startX + i * (dotSize + gap) + dotSize / 2, y, dotSize / 2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    drawStats(ctx, w, bars) {
        if (bars.length < 2) return;

        const totalSyl = bars.reduce((sum, b) => sum + b.totalSyllables, 0);
        const avgPerLine = Math.round(totalSyl / (bars.length * this.linesPerBar));

        ctx.fillStyle = 'rgba(139, 92, 246, 0.8)';
        ctx.font = 'bold 10px system-ui';
        ctx.textAlign = 'left';
        ctx.fillText(`Avg: ${avgPerLine} syl/line`, 10, 15);

        // Flow rating
        let flowRating = 'Standard';
        if (avgPerLine <= 8) flowRating = 'Laid Back';
        else if (avgPerLine <= 10) flowRating = 'Smooth';
        else if (avgPerLine <= 14) flowRating = 'Technical';
        else flowRating = 'Rapid Fire';

        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.fillText(`Flow: ${flowRating}`, 10, 28);
    }

    groupIntoBars(lines) {
        const bars = [];
        for (let i = 0; i < lines.length; i += this.linesPerBar) {
            const barLines = lines.slice(i, i + this.linesPerBar);
            const totalSyllables = barLines.reduce((sum, l) => sum + (l.syllable_count || 0), 0);
            const avgSyllables = barLines.length > 0 ? Math.round(totalSyllables / barLines.length) : 0;
            bars.push({
                lines: barLines,
                totalSyllables,
                avgSyllables,
                lineCount: barLines.length
            });
        }
        return bars;
    }

    getColorSet(avgSyllables) {
        if (avgSyllables <= 8) return this.colors.chill;
        if (avgSyllables <= 12) return this.colors.flow;
        if (avgSyllables <= 16) return this.colors.dense;
        return this.colors.chopper;
    }

    roundRect(ctx, x, y, width, height, radius) {
        if (height < 0) return;
        radius = Math.min(radius, height / 2, width / 2);
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.arcTo(x + width, y, x + width, y + radius, radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.arcTo(x + width, y + height, x + width - radius, y + height, radius);
        ctx.lineTo(x + radius, y + height);
        ctx.arcTo(x, y + height, x, y + height - radius, radius);
        ctx.lineTo(x, y + radius);
        ctx.arcTo(x, y, x + radius, y, radius);
    }

    drawLegend(ctx, w) {
        const legendItems = [
            { color: this.colors.chill.start, label: '≤8 Chill' },
            { color: this.colors.flow.start, label: '9-12 Flow' },
            { color: this.colors.dense.start, label: '13-16 Dense' },
            { color: this.colors.chopper.start, label: '17+ Chopper' }
        ];

        let x = w - 260;
        ctx.font = '9px system-ui';

        legendItems.forEach(item => {
            // Draw colored dot
            ctx.fillStyle = item.color;
            ctx.beginPath();
            ctx.arc(x + 5, 10, 5, 0, Math.PI * 2);
            ctx.fill();

            // Draw label
            ctx.fillStyle = 'rgba(255,255,255,0.6)';
            ctx.textAlign = 'left';
            ctx.fillText(item.label, x + 14, 13);
            x += 65;
        });
    }

    drawEmptyState(ctx, w, h) {
        // Animated pulse effect
        const pulse = Math.sin(Date.now() / 500) * 0.1 + 0.4;

        ctx.fillStyle = `rgba(139, 92, 246, ${pulse})`;
        ctx.font = '14px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText('🎤 Start writing to see your flow visualization', w / 2, h / 2);

        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.font = '11px system-ui';
        ctx.fillText('Each bar shows 4 lines • Colors indicate syllable density', w / 2, h / 2 + 20);
    }

    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;

        const padding = 20;
        const barGap = 6;
        const availableWidth = this.canvas.width - (padding * 2);
        const barWidth = Math.max((availableWidth / Math.max(this.bars.length, 1)) - barGap, 30);

        const hoveredIndex = Math.floor((mouseX - padding) / (barWidth + barGap));

        if (hoveredIndex >= 0 && hoveredIndex < this.bars.length && this.hoveredBar !== hoveredIndex) {
            this.hoveredBar = hoveredIndex;
            this.draw(this.bars);
        } else if (hoveredIndex < 0 || hoveredIndex >= this.bars.length) {
            if (this.hoveredBar !== -1) {
                this.hoveredBar = -1;
                this.draw(this.bars);
            }
        }
    }
}
