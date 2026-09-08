/* VoiceOps PCM worklet : convertit l'audio micro en PCM16 24 kHz (base64). */
class VoiceOpsPcmProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super()
    const opts = (options && options.processorOptions) || {}
    this.targetRate = opts.targetRate || 24000
    this.chunkSize = opts.chunkSize || 8192
    this.step = this.sampleRate / this.targetRate
    this.cursor = 0
    this.buffer = new Int16Array(this.chunkSize)
    this.len = 0
    this.running = true
    this.port.onmessage = (event) => {
      if (event.data && event.data.type === 'stop') {
        this.running = false
      }
    }
  }

  toBase64(array) {
    const bytes = new Uint8Array(array.buffer)
    let binary = ''
    for (let i = 0; i < bytes.length; i += 0x8000) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000))
    }
    return btoa(binary)
  }

  process(inputs) {
    if (!this.running) return false
    const channel = inputs[0] && inputs[0][0]
    if (!channel) return true
    for (let i = 0; i < channel.length; i += 1) {
      this.cursor += 1
      if (this.cursor >= this.step) {
        this.cursor = 0
        const sample = Math.max(-1, Math.min(1, channel[i]))
        this.buffer[this.len] = sample > 0 ? sample * 0x7fff : sample * 0x8000
        this.len += 1
        if (this.len === this.buffer.length) {
          this.port.postMessage({ audio: this.toBase64(this.buffer) })
          this.len = 0
        }
      }
    }
    return true
  }
}

registerProcessor('voiceops-pcm-processor', VoiceOpsPcmProcessor)