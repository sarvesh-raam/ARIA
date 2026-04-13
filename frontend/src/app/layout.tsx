import type { Metadata, Viewport } from 'next'
import { Inter, Outfit } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' })

export const metadata: Metadata = {
    title: 'ARIA | Strategic Risk Intelligence',
    description: 'Autonomous AI ecosystem for forensic financial auditing and real-time market intelligence.',
    keywords: ['AI', 'Risk Analysis', 'Financial Audit', 'Forensic Intelligence', 'Llama 3.3'],
    authors: [{ name: 'sarvesh-raam' }],
    metadataBase: new URL('http://localhost:3000'),
}

export const viewport: Viewport = {
    themeColor: '#0f172a',
    width: 'device-width',
    initialScale: 1,
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
            <body className="antialiased min-h-screen bg-slate-950 font-sans">
                {children}
            </body>
        </html>
    )
}
