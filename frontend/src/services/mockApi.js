export async function predictCough(audioBlob) {
  await new Promise(r => setTimeout(r, 2000))
  return {
    predictions: {
      TB: 0.72,
      pneumonia: 0.12,
      asthma: 0.08,
      COPD: 0.04,
      "COVID-19": 0.02,
      healthy: 0.02,
    },
    confidence: 0.84,
    severity: "moderate",
    top_features: [
      { name: "MFCC-12", value: 0.34, description: "Mid-frequency resonance pattern" },
      { name: "Spectral Centroid", value: 0.28, description: "Brightness of cough sound" },
      { name: "Sub-band Energy 3", value: 0.21, description: "Energy in 1-2kHz range" },
      { name: "ZCR", value: 0.11, description: "Roughness of cough texture" },
      { name: "MFCC-5", value: 0.06, description: "Low-frequency vocal tract shape" },
    ],
    triage: "Refer to PHC within 48 hours",
  }
}

export async function submitEpidemio(district, predictions) {
  await new Promise(r => setTimeout(r, 500))
  return { status: "ok" }
}

export async function getHeatmapData() {
  await new Promise(r => setTimeout(r, 500))
  return {
    districts: [
      { name: "Mangaluru", lat: 12.9141, lng: 74.8560, dominant: "TB", count: 42 },
      { name: "Bengaluru", lat: 12.9716, lng: 77.5946, dominant: "pneumonia", count: 87 },
      { name: "Mysuru", lat: 12.2958, lng: 76.6394, dominant: "asthma", count: 31 },
      { name: "Hubballi", lat: 15.3647, lng: 75.1240, dominant: "TB", count: 55 },
      { name: "Belagavi", lat: 15.8497, lng: 74.4977, dominant: "COPD", count: 28 },
    ]
  }
}