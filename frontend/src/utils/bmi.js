/** Compute BMI from height (cm) and weight (kg). Returns null if inputs invalid. */
export function computeBmi(heightCm, weightKg) {
  if (heightCm == null || weightKg == null || heightCm <= 0) return null
  const heightM = heightCm / 100
  const bmi = weightKg / (heightM * heightM)
  return Math.round(bmi * 10) / 10
}

export function bmiCategory(bmi) {
  if (bmi == null) return null
  if (bmi < 18.5) return 'underweight'
  if (bmi < 25) return 'normal'
  if (bmi < 30) return 'overweight'
  return 'obese'
}

export function bmiLabel(bmi) {
  const cat = bmiCategory(bmi)
  if (!cat) return '—'
  return `${bmi} (${cat})`
}
