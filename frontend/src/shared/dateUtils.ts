const lisbonFormatter = new Intl.DateTimeFormat('pt-PT', {
  timeZone: 'Europe/Lisbon',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

const dateOnlyFormatter = new Intl.DateTimeFormat('pt-PT', {
  timeZone: 'Europe/Lisbon',
  year: 'numeric',
  month: 'short',
  day: 'numeric',
});

const timeOnlyFormatter = new Intl.DateTimeFormat('pt-PT', {
  timeZone: 'Europe/Lisbon',
  hour: '2-digit',
  minute: '2-digit',
});

export function formatDateTime(iso: string): string {
  return lisbonFormatter.format(new Date(iso));
}

export function formatDate(iso: string): string {
  return dateOnlyFormatter.format(new Date(iso));
}

export function formatTime(iso: string): string {
  return timeOnlyFormatter.format(new Date(iso));
}

export function toDateInputValue(iso: string): string {
  return iso.slice(0, 10);
}

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}
