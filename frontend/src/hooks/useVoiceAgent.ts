import { useCallback, useEffect, useRef, useState } from 'react'

import { api } from '../services/api'
import {
  ToolQueue,
  buildSessionUpdate,
  decodePcm16,
  isToolCall,
} from '../services/voiceProtocol'

export type AgentStatus =
  | 'idle'
  | 'starting'
  | 'listening'
  | 'speaking'
  | 'error'

export interface TranscriptItem {
  role: 'user' | 'agent'
  text: string
}

export interface ToolCallItem {
  name: string
  status: 'running' | 'done' | 'error'
}

const WS_URL = 'wss://agents.assemblyai.com/v1/ws'

function isVoiceSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    typeof window.WebSocket === 'function' &&
    typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices?.getUserMedia &&
    (typeof window.AudioContext === 'function' ||
      typeof (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext === 'function')
  )
}

function audioContext(): AudioContext {
  const Ctor =
    window.AudioContext ??
    (window as unknown as { webkitAudioContext: typeof AudioContext })
      .webkitAudioContext
  return new Ctor({ sampleRate: 24000 })
}

function playPcm16(context: AudioContext, b64: string): void {
  const samples = decodePcm16(b64)
  const buffer = context.createBuffer(1, samples.length, 24000)
  buffer.copyToChannel(samples, 0)
  const source = context.createBufferSource()
  source.buffer = buffer
  source.connect(context.destination)
  source.start()
}

export function useVoiceAgent() {
  const [status, setStatus] = useState<AgentStatus>('idle')
  const [transcript, setTranscript] = useState<TranscriptItem[]>([])
  const [toolCalls, setToolCalls] = useState<ToolCallItem[]>([])

  const socketRef = useRef<WebSocket | null>(null)
  const contextRef = useRef<AudioContext | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const workletRef = useRef<AudioWorkletNode | null>(null)
  const queueRef = useRef(new ToolQueue())
  const activeRef = useRef(false)

  const pushTranscript = useCallback((role: TranscriptItem['role'], text: string) => {
    setTranscript((prev) => [...prev, { role, text }])
  }, [])

  const pushTool = useCallback((name: string, state: ToolCallItem['status']) => {
    setToolCalls((prev) => [...prev, { name, status: state }])
  }, [])

  const handleReplyAudio = useCallback((context: AudioContext, data: unknown) => {
    if (typeof data !== 'string') return
    playPcm16(context, data)
  }, [])

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      const raw = typeof event.data === 'string' ? event.data : ''
      if (!raw) return
      let msg: Record<string, unknown>
      try {
        msg = JSON.parse(raw) as Record<string, unknown>
      } catch {
        return
      }

      const type = msg['type']
      if (type === 'session.ready') {
        setStatus('listening')
      } else if (type === 'transcript.user' && typeof msg['text'] === 'string') {
        pushTranscript('user', msg['text'] as string)
      } else if (type === 'transcript.agent' && typeof msg['text'] === 'string') {
        pushTranscript('agent', msg['text'] as string)
      } else if (type === 'reply.started' || type === 'reply.audio') {
        if (status === 'listening' || status === 'idle') setStatus('speaking')
        if (type === 'reply.audio' && contextRef.current) {
          handleReplyAudio(contextRef.current, msg['data'])
        }
      } else if (type === 'input.speech.started') {
        setStatus('listening')
      } else if (isToolCall(msg)) {
        pushTool(msg.name, 'running')
        const socket = socketRef.current
        void api
          .runTool(msg.name, msg.arguments)
          .then((result) => {
            queueRef.current.add(msg, result)
            pushTool(msg.name, 'done')
            if (!socket) return
            const pending = queueRef.current.flush(false)
            for (const item of pending) {
              socket.send(
                JSON.stringify({
                  type: 'tool.result',
                  call_id: item.call_id,
                  result: JSON.stringify(item.result),
                }),
              )
            }
          })
          .catch(() => {
            pushTool(msg.name, 'error')
            queueRef.current.flush(true)
          })
      } else if (type === 'reply.done') {
        const interrupted = msg['status'] === 'interrupted'
        const pending = queueRef.current.flush(interrupted)
        const socket = socketRef.current
        if (socket && !interrupted) {
          for (const item of pending) {
            socket.send(
              JSON.stringify({
                type: 'tool.result',
                call_id: item.call_id,
                result: JSON.stringify(item.result),
              }),
            )
          }
        }
        if (!interrupted) setStatus('listening')
      } else if (type === 'session.error') {
        setStatus('error')
      } else if (type === 'session.ended') {
        activeRef.current = false
        setStatus('idle')
      }
    },
    [handleReplyAudio, pushTool, pushTranscript, status],
  )

  const stop = useCallback(() => {
    activeRef.current = false
    socketRef.current?.close()
    workletRef.current?.port.postMessage({ type: 'stop' })
    sourceRef.current?.disconnect()
    workletRef.current?.disconnect()
    streamRef.current?.getTracks().forEach((track) => track.stop())
    if (contextRef.current) void contextRef.current.close()
    socketRef.current = null
    workletRef.current = null
    sourceRef.current = null
    streamRef.current = null
    contextRef.current = null
    setStatus('idle')
  }, [])

  const start = useCallback(async () => {
    if (activeRef.current) return
    if (!isVoiceSupported()) {
      setStatus('error')
      return
    }
    activeRef.current = true
    setStatus('starting')
    try {
      const tokenResponse = await api.getVoiceToken()
      const context = audioContext()
      contextRef.current = context
      const socket = new WebSocket(`${WS_URL}?token=${tokenResponse.token}`)
      socketRef.current = socket
      socket.onopen = () => {
        socket.send(JSON.stringify(buildSessionUpdate(tokenResponse.config)))
      }
      socket.onmessage = handleMessage
      socket.onerror = () => {
        setStatus('error')
        activeRef.current = false
      }
      socket.onclose = () => {
        if (activeRef.current) {
          activeRef.current = false
          setStatus('idle')
        }
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      })
      streamRef.current = stream
      await context.audioWorklet.addModule('/pcm-worklet.js')
      const source = context.createMediaStreamSource(stream)
      sourceRef.current = source
      const worklet = new AudioWorkletNode(context, 'voiceops-pcm-processor', {
        processorOptions: { targetRate: 24000, chunkSize: 8192 },
      })
      workletRef.current = worklet
      worklet.port.onmessage = (event) => {
        const audio = event.data?.audio
        if (audio && socket.readyState === WebSocket.OPEN && activeRef.current) {
          socket.send(JSON.stringify({ type: 'input.audio', audio }))
        }
      }
      const mute = context.createGain()
      mute.gain.value = 0
      source.connect(worklet)
      worklet.connect(mute)
      mute.connect(context.destination)
      setStatus('listening')
    } catch {
      activeRef.current = false
      setStatus('error')
    }
  }, [handleMessage])

  useEffect(() => {
    return () => {
      activeRef.current = false
      socketRef.current?.close()
    }
  }, [])

  return {
    status,
    transcript,
    toolCalls,
    start,
    stop,
    supported: isVoiceSupported(),
  }
}