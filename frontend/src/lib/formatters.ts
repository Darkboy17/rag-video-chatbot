/**
 * Format nullable counts for compact metric display.
 */
export function formatNumber(value?: number | null): string {
  if (value === null || value === undefined) {
    return "Unavailable";
  }

  return new Intl.NumberFormat("en", {
    notation: value >= 100_000 ? "compact" : "standard",
    maximumFractionDigits: 1,
  }).format(value);
}

/**
 * Format backend engagement-rate percentages.
 */
export function formatPercent(value?: number | null): string {
  if (value === null || value === undefined) {
    return "Unavailable";
  }

  return `${value.toFixed(2)}%`;
}

/**
 * Convert duration seconds into a concise card label.
 */
export function formatDuration(seconds?: number | null): string {
  if (seconds === null || seconds === undefined) {
    return "Unavailable";
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (minutes === 0) {
    return `${remainingSeconds}s`;
  }

  return `${minutes}m ${remainingSeconds}s`;
}

/**
 * Display yt-dlp upload dates, including YYYYMMDD strings.
 */
export function formatUploadDate(value?: string | null): string {
  if (!value) {
    return "Unavailable";
  }

  if (/^\d{8}$/.test(value)) {
    const year = value.slice(0, 4);
    const month = value.slice(4, 6);
    const day = value.slice(6, 8);

    return `${day}/${month}/${year}`;
  }

  return value;
}
