import { describe, expect, it } from 'vitest'

import {
  ToolQueue,
  buildSessionUpdate,
  decodePcm16,
  encodePcm16,
  isToolCall,
} from './voiceProtocol'

const CONFIG = {
  system_prompt: 'Tu es VoiceOps',
  greeting: 'Bonjour',
  output: { voice: 'ivy' },
  tools: [{ name: 'check_vlan', description: 'd', parameters: {} }],
}

describe('buildSessionUpdate', () => {
  it('construit un session.update conforme au protocole AssemblyAI', () => {
    const update = buildSessionUpdate(CONFIG) as {
      type: string
      session: unknown
    }
    expect(update.type).toBe('session.update')
    expect(update.session).toBe(CONFIG)
  })
})

describe('ToolQueue', () => {
  it('accumule et draine les résultats au reply.done', () => {
    const queue = new ToolQueue()
    const call = {
      type: 'tool.call',
      call_id: 'c1',
      name: 'check_vlan',
      arguments: { device: 'PC-B204' },
    } as const

    queue.add(call, { status: 'mismatch' })
    expect(queue.size).toBe(1)

    const drained = queue.flush(false)
    expect(drained).toHaveLength(1)
    expect(drained[0].call_id).toBe('c1')
    expect(queue.size).toBe(0)
  })

  it('écarte les résultats intermédiaires en cas de barge-in', () => {
    const queue = new ToolQueue()
    const call = {
      type: 'tool.call',
      call_id: 'c1',
      name: 'ping_host',
      arguments: {},
    } as const
    queue.add(call, { ok: true })

    const drained = queue.flush(true)
    expect(drained).toHaveLength(0)
    expect(queue.size).toBe(0)
  })
})

describe('PCM16 encode/decode', () => {
  it('fait un aller-retour propre', () => {
    const samples = Float32Array.from([0, -1, 1, 0.5, -0.5, 0.25])
    const b64 = encodePcm16(samples)
    const round = decodePcm16(b64)
    expect(round.length).toBe(samples.length)
    expect(Math.abs(round[0])).toBeLessThan(1 / 32768)
    expect(Math.abs(round[1] + 1)).toBeLessThan(0.001)
    expect(Math.abs(round[2] - 1)).toBeLessThan(0.001)
  })
})

describe('isToolCall', () => {
  it('détecte un événement tool.call', () => {
    expect(
      isToolCall({ type: 'tool.call', call_id: 'a', name: 'x', arguments: {} }),
    ).toBe(true)
    expect(isToolCall({ type: 'reply.done' })).toBe(false)
    expect(isToolCall(null)).toBe(false)
  })
})