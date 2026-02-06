export class AudioStreamPlayer {
    constructor(sampleRate = 24000) {
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.nextStartTime = 0;
        this.sampleRate = sampleRate;
        this.queue = [];
        this.isPlaying = false;
    }

    init() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: this.sampleRate,
            });
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.analyser.connect(this.audioContext.destination);
        }
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
    }

    // Process raw PCM bytes (Int16)
    playChunk(arrayBuffer) {
        this.init();
        
        // Convert Int16 (2 bytes) to Float32 (-1.0 to 1.0)
        const int16Data = new Int16Array(arrayBuffer);
        const float32Data = new Float32Array(int16Data.length);
        
        for (let i = 0; i < int16Data.length; i++) {
            // Normalize 16-bit integer (-32768 to 32767) to float (-1.0 to 1.0)
            float32Data[i] = int16Data[i] / 32768.0;
        }

        // Create AudioBuffer
        const audioBuffer = this.audioContext.createBuffer(
            1, // Mono
            float32Data.length,
            this.sampleRate
        );
        
        audioBuffer.copyToChannel(float32Data, 0);
        
        // Schedule playback
        const source = this.audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(this.analyser);
        
        const currentTime = this.audioContext.currentTime;
        // Ensure we schedule in the future, but contiguous if possible
        if (this.nextStartTime < currentTime) {
            this.nextStartTime = currentTime + 0.05; // small buffer for first chunk
        }
        
        source.start(this.nextStartTime);
        this.nextStartTime += audioBuffer.duration;
    }

    getAudioData() {
        if (this.analyser) {
            this.analyser.getByteFrequencyData(this.dataArray);
            return this.dataArray; // Returns Uint8Array [0-255]
        }
        return new Uint8Array(0);
    }
}
