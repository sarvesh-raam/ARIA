import type { Metadata, Viewport } from 'next'
import { Inter, Outfit } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' })

export const metadata: Metadata = {
    title: 'ARIA | Autonomous Risk Intelligence Agent',
    description: 'The industry-standard AI ecosystem for forensic financial auditing and multi-source market intelligence.',
    keywords: ['AI', 'Risk Analysis', 'Financial Audit', 'Forensic Intelligence', 'Llama 3.3', 'Quantitative Finance'],
    authors: [{ name: 'ARIA Institutional' }],
    metadataBase: new URL('https://aria-intelligence.vercel.app'),
    openGraph: {
        title: 'ARIA Professional Audit Interface',
        description: 'Next-generation forensic audit orchestration using Llama 3.3 and semantic search.',
        url: 'https://aria-intelligence.vercel.app',
        siteName: 'ARIA Intelligence',
        locale: 'en_US',
        type: 'website',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'ARIA Professional Audit Interface',
        description: 'Next-generation forensic audit orchestration.',
    }
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
