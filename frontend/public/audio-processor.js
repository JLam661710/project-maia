// AudioWorkletProcessor for downsampling audio from ~48kHz to 16kHz
class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096;
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
        this._bytesWritten = 0;
    }

    process(inputs) {
        const input = inputs[0];

        // Input is Float32Array[] (channels)
        if (input.length > 0) {
            const inputChannel = input[0]; // Mono
            
            // Just pass through audio to output (optional, for monitoring)
            // for (let i = 0; i < inputChannel.length; i++) {
            //     output[0][i] = inputChannel[i];
            // }

            // Post data to main thread
            // We can send every chunk (128 samples usually) or buffer it
            // Sending every 128 samples (approx 2.6ms at 48k) is fine for low latency
            this.port.postMessage(inputChannel);
        }

        return true;
    }
}

registerProcessor('audio-processor', AudioProcessor);
