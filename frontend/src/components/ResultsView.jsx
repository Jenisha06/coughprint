'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const DISEASE_COLORS = {
  TB: '#ef4444',
  pneumonia: '#f97316',
  asthma: '#eab308',
  COPD: '#8b5cf6',
  'COVID-19': '#3b82f6',
  healthy: '#10b981',
}

const SEVERITY_CONFIG = {
  mild: { color: 'text-green-400', bg: 'bg-green-400/10 border-green-400/30', icon: '🟢' },
  moderate: { color: 'text-yellow-400', bg: 'bg-yellow-400/10 border-yellow-400/30', icon: '🟡' },
  severe: { color: 'text-red-400', bg: 'bg-red-400/10 border-red-400/30', icon: '🔴' },
}

export default function ResultsView() {
  const router = useRouter()
  const [result, setResult] = useState(null)

  useEffect(() => {
    const stored = sessionStorage.getItem('coughResult')
    if (!stored) {
      router.push('/')
      return
    }
    setResult(JSON.parse(stored))
  }, [])

  if (!result) return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  const topDisease = Object.entries(result.predictions).sort((a, b) => b[1] - a[1])[0]
  const severity = SEVERITY_CONFIG[result.severity]

  
  const predictionChart = {
    labels: Object.keys(result.predictions),
    datasets: [{
      label: 'Probability',
      data: Object.values(result.predictions).map(v => Math.round(v * 100)),
      backgroundColor: Object.keys(result.predictions).map(d => DISEASE_COLORS[d] + '99'),
      borderColor: Object.keys(result.predictions).map(d => DISEASE_COLORS[d]),
      borderWidth: 2,
      borderRadius: 6,
    }]
  }


  const shapChart = {
    labels: result.top_features.map(f => f.name),
    datasets: [{
      label: 'Feature Importance',
      data: result.top_features.map(f => Math.round(f.value * 100)),
      backgroundColor: '#6366f199',
      borderColor: '#6366f1',
      borderWidth: 2,
      borderRadius: 6,
    }]
  }

  const chartOptions = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
      y: { ticks: { color: '#9ca3af' }, grid: { color: '#1f2937' } },
    },
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 flex flex-col gap-8">

      
      <div className="text-center">
        <h1 className="text-3xl font-bold text-white mb-1">Analysis Complete</h1>
        <p className="text-gray-400 text-sm">Based on your 3 cough recordings</p>
      </div>

     
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-3">
        <p className="text-gray-400 text-sm uppercase tracking-widest">Primary Detection</p>
        <div className="flex items-center justify-between">
          <span
            className="text-4xl font-bold"
            style={{ color: DISEASE_COLORS[topDisease[0]] }}
          >
            {topDisease[0]}
          </span>
          <span className="text-2xl font-bold text-white">
            {Math.round(topDisease[1] * 100)}%
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-1000"
            style={{
              width: `${Math.round(topDisease[1] * 100)}%`,
              backgroundColor: DISEASE_COLORS[topDisease[0]]
            }}
          />
        </div>
        <p className="text-gray-400 text-sm">
          Confidence: <span className="text-white font-medium">{Math.round(result.confidence * 100)}%</span>
        </p>
      </div>

     
      <div className={`border rounded-2xl p-5 flex items-center gap-4 ${severity.bg}`}>
        <span className="text-3xl">{severity.icon}</span>
        <div>
          <p className="text-gray-400 text-sm uppercase tracking-widest">Severity</p>
          <p className={`text-xl font-bold capitalize ${severity.color}`}>{result.severity}</p>
        </div>
      </div>

      
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-5">
        <p className="text-gray-400 text-sm uppercase tracking-widest mb-1">Triage Recommendation</p>
        <p className="text-white font-medium">{result.triage}</p>
      </div>

     
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <h2 className="text-white font-semibold mb-4">Disease Probabilities</h2>
        <Bar data={predictionChart} options={chartOptions} />
      </div>

  
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
        <h2 className="text-white font-semibold mb-1">Why This Prediction?</h2>
        <p className="text-gray-400 text-xs mb-4">Top acoustic features driving the result</p>
        <Bar data={shapChart} options={{ ...chartOptions, indexAxis: 'y' }} />
        <div className="mt-4 flex flex-col gap-2">
          {result.top_features.map(f => (
            <div key={f.name} className="flex items-start gap-2 text-sm">
              <span className="text-indigo-400 font-medium min-w-[120px]">{f.name}</span>
              <span className="text-gray-400">{f.description}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={() => router.push('/')}
          className="flex-1 py-3 rounded-xl border border-gray-700 text-gray-300 hover:text-white hover:border-gray-500 transition-colors"
        >
          Record Again
        </button>
        <button
          onClick={() => alert('PDF coming Day 5!')}
          className="flex-1 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-medium transition-colors"
        >
          Download Report
        </button>
      </div>

    </div>
  )
}