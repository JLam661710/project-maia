// Utility to handle Audio Recording and Resampling
export class AudioRecorder {
    constructor() {
        this.audioContext = null;
        this.workletNode = null;
        this.stream = null;
        this.onAudioData = null; // Callback(Int16Array)
        this.sampleRate = 16000; // Target sample rate
    }

    async start(onAudioData) {
        this.onAudioData = onAudioData;

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Load AudioWorklet
            await this.audioContext.audioWorklet.addModule('/audio-processor.js');

            const source = this.audioContext.createMediaStreamSource(this.stream);
            this.workletNode = new AudioWorkletNode(this.audioContext, 'audio-processor');

            // Handle data from worklet
            this.workletNode.port.onmessage = (event) => {
                const inputData = event.data; // Float32Array at context sample rate (e.g. 48000)
                const downsampled = this.downsampleBuffer(inputData, this.audioContext.sampleRate, this.sampleRate);
                if (this.onAudioData) {
                    this.onAudioData(downsampled);
                }
            };

            source.connect(this.workletNode);
            this.workletNode.connect(this.audioContext.destination); // Needed to keep worklet alive? Usually yes in Chrome

            // console.log(`AudioRecorder started. Input: ${this.audioContext.sampleRate}Hz, Output: ${this.sampleRate}Hz`);

        } catch (e) {
            console.error('Error starting AudioRecorder:', e);
            throw e;
        }
    }

    stop() {
        if (this.workletNode) {
            this.workletNode.disconnect();
            this.workletNode = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }

    // Simple Linear Interpolation Downsampling + Float32 to Int16 Conversion
    downsampleBuffer(buffer, sampleRate, outSampleRate) {
        if (outSampleRate === sampleRate) {
            return this.convertFloatToInt16(buffer);
        }
        
        const sampleRateRatio = sampleRate / outSampleRate;
        const newLength = Math.round(buffer.length / sampleRateRatio);
        const result = new Int16Array(newLength);
        
        let offsetResult = 0;
        let offsetBuffer = 0;
        
        while (offsetResult < result.length) {
            const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
            
            // Simple averaging (box filter) for downsampling to avoid aliasing
            let accum = 0;
            let count = 0;
            
            for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
                accum += buffer[i];
                count++;
            }
            
            if (count > 0) {
                const avg = accum / count;
                // Clip and convert
                const s = Math.max(-1, Math.min(1, avg));
                result[offsetResult] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            
            offsetResult++;
            offsetBuffer = nextOffsetBuffer;
        }
        
        return result;
    }

    convertFloatToInt16(buffer) {
        const l = buffer.length;
        const buf = new Int16Array(l);
        for (let i = 0; i < l; i++) {
            const s = Math.max(-1, Math.min(1, buffer[i]));
            buf[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return buf;
    }
}
