import type { Level } from '@/lib/types';

const STYLES: Record<Level, string> = {
    high: 'bg-risk-critical/10 text-risk-critical',
    medium: 'bg-risk-elevated/10 text-risk-elevated',
    low: 'bg-subtle text-muted',
};

export default function LevelBadge({ level }: { level: Level }) {
    return (
        <span className={`inline-flex shrink-0 self-start items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize ${STYLES[level] ?? STYLES.low}`}>
            {level}
        </span>
    );
}
