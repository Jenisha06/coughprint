'use client'
import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { predictCough } from '../services/mockApi'

export default function Recorder() {
  const router = useRouter()
  const [status, setStatus] = useState('idle') 
  const [coughCount, setCoughCount] = useState(0)
  const [error, setError] = useState(null)

  const canvasRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const streamRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const animFrameRef = useRef(null)
  const coughCountRef = useRef(0)
  const lastCoughTimeRef = useRef(0)

  const COUGH_THRESHOLD = 0.15
  const COUGH_COOLDOWN_MS = 1500
  const TARGET_COUGHS = 3

  function drawWaveform(analyser) {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const bufferLength = analyser.fftSize
    const dataArray = new Float32Array(bufferLength)

    function draw() {
      animFrameRef.current = requestAnimationFrame(draw)
      analyser.getFloatTimeDomainData(dataArray)

      ctx.fillStyle = '#030712'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

     
      let sum = 0
      for (let i = 0; i < bufferLength; i++) sum += dataArray[i] ** 2
      const rms = Math.sqrt(sum / bufferLength)

      const now = Date.now()
      if (
        rms > COUGH_THRESHOLD &&
        now - lastCoughTimeRef.current > COUGH_COOLDOWN_MS &&
        coughCountRef.current < TARGET_COUGHS
      ) {
        lastCoughTimeRef.current = now
        coughCountRef.current += 1
        setCoughCount(coughCountRef.current)
      }

      // Draw waveform
      const isCoughing = rms > COUGH_THRESHOLD
      ctx.lineWidth = 2
      ctx.strokeStyle = isCoughing ? '#10b981' : '#6b7280'
      ctx.beginPath()

      const sliceWidth = canvas.width / bufferLength
      let x = 0
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i]
        const y = (v + 1) / 2 * canvas.height
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
        x += sliceWidth
      }
      ctx.stroke()
    }
    draw()
  }

  async function startRecording() {
    try {
      setError(null)
      coughCountRef.current = 0
      setCoughCount(0)
      chunksRef.current = []

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 2048
      source.connect(analyser)
      analyserRef.current = analyser

      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.ondataavailable = e => chunksRef.current.push(e.data)
      mediaRecorder.start()

      setStatus('recording')
      drawWaveform(analyser)
    } catch (err) {
      setError('Microphone access denied. Please allow microphone and try again.')
    }
  }

async function stopAndAnalyse() {
    setStatus('processing')
    cancelAnimationFrame(animFrameRef.current)

    const mediaRecorder = mediaRecorderRef.current
    mediaRecorder.stop()
    streamRef.current.getTracks().forEach(t => t.stop())
    
    
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
    }

    mediaRecorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
      try {
        const result = await predictCough(blob)
        sessionStorage.setItem('coughResult', JSON.stringify(result))
        router.push('/results')
      } catch (err) {
        setError('Analysis failed. Please try again.')
        setStatus('idle')
      }
    }
  }

  
  useEffect(() => {
    if (coughCount >= TARGET_COUGHS && status === 'recording') {
      setTimeout(() => stopAndAnalyse(), 800)
    }
  }, [coughCount, status])


useEffect(() => {
    return () => {
      cancelAnimationFrame(animFrameRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
    }
  }, [])

  return (
    <div className="flex flex-col items-center gap-8 w-full max-w-xl mx-auto px-4 py-12">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-2">Record Your Cough</h1>
        <p className="text-gray-400 text-sm">We need 3 cough sounds to analyse your respiratory health</p>
      </div>

      {/* Cough counter */}
      <div className="flex gap-4">
        {[1, 2, 3].map(n => (
          <div
            key={n}
            className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold border-2 transition-all duration-300 ${
              coughCount >= n
                ? 'bg-emerald-500 border-emerald-500 text-white scale-110'
                : 'border-gray-600 text-gray-600'
            }`}
          >
            {coughCount >= n ? '✓' : n}
          </div>
        ))}
      </div>

      {/* Waveform canvas */}
      <canvas
        ref={canvasRef}
        width={500}
        height={120}
        className="w-full rounded-xl bg-gray-950 border border-gray-800"
      />

      {/* Status text */}
      <p className="text-sm text-gray-400 h-6">
        {status === 'idle' && 'Press the button and cough 3 times'}
        {status === 'recording' && coughCount < 3 && `Listening... cough detected: ${coughCount}/3`}
        {status === 'recording' && coughCount >= 3 && 'Got all 3! Analysing...'}
        {status === 'processing' && '🔬 Analysing your cough pattern...'}
      </p>

      {/* Error */}
      {error && <p className="text-red-400 text-sm text-center">{error}</p>}

      {/* Button */}
      {status === 'idle' && (
        <button
          onClick={startRecording}
          className="w-24 h-24 rounded-full bg-emerald-500 hover:bg-emerald-400 text-white text-4xl shadow-lg shadow-emerald-500/30 transition-all hover:scale-105 active:scale-95"
        >
          🎙️
        </button>
      )}

      {status === 'recording' && (
        <button
          onClick={stopAndAnalyse}
          className="w-24 h-24 rounded-full bg-red-500 hover:bg-red-400 text-white text-4xl shadow-lg shadow-red-500/30 transition-all animate-pulse"
        >
          ⏹️
        </button>
      )}

      {status === 'processing' && (
        <div className="w-24 h-24 rounded-full bg-gray-800 flex items-center justify-center">
          <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"/>
        </div>
      )}
    </div>
  )
}