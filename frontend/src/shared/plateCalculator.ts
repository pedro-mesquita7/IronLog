export interface PlateResult {
  perSide: number[];
  totalWeight: number;
  remainder: number;
}

export function calculatePlates(
  targetWeight: number,
  barWeight: number,
  availablePlates: { weight_kg: number; quantity: number }[]
): PlateResult {
  const loadPerSide = (targetWeight - barWeight) / 2;
  if (loadPerSide <= 0) {
    return { perSide: [], totalWeight: barWeight, remainder: 0 };
  }

  const sorted = [...availablePlates]
    .filter((p) => p.weight_kg > 0 && p.quantity >= 2)
    .sort((a, b) => b.weight_kg - a.weight_kg);

  const perSide: number[] = [];
  let remaining = loadPerSide;

  for (const plate of sorted) {
    const maxPairs = Math.floor(plate.quantity / 2);
    const count = Math.min(maxPairs, Math.floor(remaining / plate.weight_kg));
    for (let i = 0; i < count; i++) {
      perSide.push(plate.weight_kg);
      remaining -= plate.weight_kg;
    }
  }

  const actualLoad = perSide.reduce((sum, p) => sum + p, 0) * 2;
  return {
    perSide,
    totalWeight: barWeight + actualLoad,
    remainder: Math.round((loadPerSide - (actualLoad / 2)) * 100) / 100,
  };
}
