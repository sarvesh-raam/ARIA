// A random ID this browser creates for itself and sends with every request, so the backend only
// shows it the reports it uploaded. No sign-up; clearing site data starts a new, empty workspace.

const STORAGE_KEY = 'aria-workspace-id';
let fallbackId: string | null = null;

const newId = (): string => {
    if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    // Older browsers: 128 random bits as hex
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    return Array.from(bytes, (b: number) => b.toString(16).padStart(2, '0')).join('');
};

export function getWorkspaceId(): string {
    try {
        let id = localStorage.getItem(STORAGE_KEY);
        if (!id) {
            id = newId();
            localStorage.setItem(STORAGE_KEY, id);
        }
        return id;
    } catch {
        // Storage blocked (e.g. some private modes): keep an ID for this tab only
        fallbackId ??= newId();
        return fallbackId;
    }
}
