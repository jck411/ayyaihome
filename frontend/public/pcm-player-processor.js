class PCMPlayerProcessor extends AudioWorkletProcessor {
    constructor() {
      super();
      this.sampleRate = 24000; // Ensure this matches the backend sample rate
      this.buffer = [];
      this.bufferSize = 2048; // Adjust buffer size as needed
  
      this.port.onmessage = (event) => {
        const arrayBuffer = event.data;
        const int16Array = new Int16Array(arrayBuffer);
        this.buffer.push(...int16Array);
      };
    }
  
    process(inputs, outputs) {
      const output = outputs[0];
      const outputChannel = output[0];
  
      if (this.buffer.length >= this.bufferSize) {
        for (let i = 0; i < outputChannel.length; i++) {
          if (this.buffer.length > 0) {
            const sample = this.buffer.shift();
            outputChannel[i] = sample / 32768; // Convert Int16 to Float32
          } else {
            outputChannel[i] = 0;
          }
        }
      } else {
        // Not enough data, output silence
        outputChannel.fill(0);
      }
  
      return true; // Keep processor alive
    }
  }
  
  registerProcessor('pcm-player', PCMPlayerProcessor);
  