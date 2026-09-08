import type { VoiceConfig } from './api'

export const PCM_SAMPLE_RATE = 24000

export function buildSessionUpdate(config: VoiceConfig): unknown {
  return { type: 'session.update', session: config }
}

export interface ToolCallEvent {
  type: 'tool.call'
  call_id: string
  name: string
  arguments: Record<string, unknown>
}

export function isToolCall(value: unknown): value is ToolCallEvent {
  if (typeof value !== 'object' || value === null) return false
  const event = value as Record<string, unknown>
  return (
    event['type'] === 'tool.call' &&
    typeof event['call_id'] === 'string' &&
    typeof event['name'] === 'string'
  )
}

export class ToolQueue {
  private pending: Array<{ call_id: string; result: unknown }> = []

  get size(): number {
    return this.pending.length
  }

  add(call: ToolCallEvent, result: unknown): void {
    this.pending.push({ call_id: call.call_id, result })
  }

  flush(interrupted: boolean): Array<{ call_id: string; result: unknown }> {
    if (interrupted) {
      this.pending = []
      return []
    }
    const drained = this.pending
    this.pending = []
    return drained
  }
}

export function encodePcm16(samples: Float32Array): string {
  const pcm = new Int16Array(samples.length)
  for (let i = 0; i < samples.length; i += 1) {
    const value = Math.max(-1, Math.min(1, samples[i] ?? 0))
    pcm[i] = value > 0 ? Math.round(value * 0x7fff) : Math.round(value * 0x8000)
  }
  const bytes = new Uint8Array(pcm.buffer)
  let binary = ''
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000))
  }
  return btoa(binary)
}

export function decodePcm16(b64: string): Float32Array<ArrayBuffer> {
  const binary = atob(b64)
  const pcm = new Int16Array(Math.floor(binary.length / 2))
  for (let i = 0; i < pcm.length; i += 1) {
    const lo = binary.charCodeAt(i * 2)
    const hi = binary.charCodeAt(i * 2 + 1)
    pcm[i] = ((hi << 8) | lo) << 16 >> 16
  }
  const samples = new Float32Array(pcm.length)
  for (let i = 0; i < pcm.length; i += 1) {
    samples[i] = pcm[i] / 32768
  }
  return samples
}