import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
    title: 'ARIA | Autonomous Risk Intelligence Agent',
    description: 'AI-powered financial risk analysis and intelligence',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    )
}
