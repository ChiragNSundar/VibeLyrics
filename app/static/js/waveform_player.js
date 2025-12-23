/**
 * Waveform Player - Wavesurfer.js Integration
 * Provides waveform visualization, A-B looping, and speed control
 */

class WaveformPlayer {
    constructor(containerId, audioUrl) {
        this.containerId = containerId;
        this.audioUrl = audioUrl;
        this.wavesurfer = null;
        this.loopRegion = null;
        this.isLooping = false;
        this.loopStart = null;
        this.loopEnd = null;

        this.init();
    }

    init() {
        // Initialize Wavesurfer
        this.wavesurfer = WaveSurfer.create({
            container: `#${this.containerId}`,
            waveColor: 'rgba(138, 43, 226, 0.5)',
            progressColor: '#8a2be2',
            cursorColor: '#ff6b6b',
            barWidth: 2,
            barGap: 1,
            barRadius: 2,
            height: 80,
            responsive: true,
            normalize: true,
            backend: 'WebAudio'
        });

        // Load audio
        if (this.audioUrl) {
            this.wavesurfer.load(this.audioUrl);
        }

        // Handle loop playback
        this.wavesurfer.on('audioprocess', () => {
            if (this.isLooping && this.loopEnd !== null) {
                const currentTime = this.wavesurfer.getCurrentTime();
                if (currentTime >= this.loopEnd) {
                    this.wavesurfer.seekTo(this.loopStart / this.wavesurfer.getDuration());
                }
            }
        });

        // Ready event
        this.wavesurfer.on('ready', () => {
            console.log('Waveform ready');
            this.updateTimeDisplay();
        });

        this.wavesurfer.on('audioprocess', () => this.updateTimeDisplay());
        this.wavesurfer.on('seek', () => this.updateTimeDisplay());
    }

    play() {
        this.wavesurfer.play();
    }

    pause() {
        this.wavesurfer.pause();
    }

    playPause() {
        this.wavesurfer.playPause();
    }

    setSpeed(rate) {
        this.wavesurfer.setPlaybackRate(rate);
    }

    // A-B Loop functionality
    setLoopStart() {
        this.loopStart = this.wavesurfer.getCurrentTime();
        this.updateLoopDisplay();
    }

    setLoopEnd() {
        this.loopEnd = this.wavesurfer.getCurrentTime();
        if (this.loopStart !== null && this.loopEnd > this.loopStart) {
            this.isLooping = true;
        }
        this.updateLoopDisplay();
    }

    clearLoop() {
        this.loopStart = null;
        this.loopEnd = null;
        this.isLooping = false;
        this.updateLoopDisplay();
    }

    updateLoopDisplay() {
        const loopInfo = document.getElementById('loop-info');
        if (loopInfo) {
            if (this.loopStart !== null && this.loopEnd !== null) {
                loopInfo.textContent = `Loop: ${this.formatTime(this.loopStart)} - ${this.formatTime(this.loopEnd)}`;
                loopInfo.classList.add('active');
            } else if (this.loopStart !== null) {
                loopInfo.textContent = `Loop A: ${this.formatTime(this.loopStart)} (set B point)`;
                loopInfo.classList.remove('active');
            } else {
                loopInfo.textContent = '';
                loopInfo.classList.remove('active');
            }
        }
    }

    updateTimeDisplay() {
        const timeDisplay = document.getElementById('waveform-time');
        if (timeDisplay && this.wavesurfer) {
            const current = this.wavesurfer.getCurrentTime();
            const duration = this.wavesurfer.getDuration();
            timeDisplay.textContent = `${this.formatTime(current)} / ${this.formatTime(duration)}`;
        }
    }

    formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    destroy() {
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
        }
    }
}

// Global instance
let waveformPlayer = null;

function initWaveformPlayer(containerId, audioUrl) {
    if (waveformPlayer) {
        waveformPlayer.destroy();
    }
    waveformPlayer = new WaveformPlayer(containerId, audioUrl);
    return waveformPlayer;
}
