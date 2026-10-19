export type Tone = 'stable' | 'elevated' | 'critical';

// Same bands as the backend (risk_agent.py): >70 critical, >40 elevated
export const scoreTone = (score: number): Tone => (score > 70 ? 'critical' : score > 40 ? 'elevated' : 'stable');

// "Medium Risk [ELEVATED]" -> "Medium risk"
export const ratingLabel = (rating: string) => {
    const label = rating.replace(/\s*\[.*\]\s*/, '').trim();
    return label.charAt(0).toUpperCase() + label.slice(1).toLowerCase();
};

// Older records were saved without a timezone. The server runs on UTC, so read them as UTC
// (otherwise the browser treats them as local time and shows the wrong hour)
const parseServerDate = (iso: string) => new Date(/(Z|[+-]\d\d:\d\d)$/.test(iso) ? iso : `${iso}Z`);

export const formatDateTime = (iso?: string | null) => {
    if (!iso) return '';
    const date = parseServerDate(iso);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
};

export const formatDate = (iso?: string | null) => {
    if (!iso) return '';
    const date = parseServerDate(iso);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString(undefined, { dateStyle: 'medium' });
};
