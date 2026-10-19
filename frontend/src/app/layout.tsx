import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
    title: 'ARIA | Financial Risk Analysis',
    description: 'Upload a financial report and get a risk score built from its statements and recent news.',
    keywords: ['AI', 'Risk Analysis', 'Financial Audit', 'Forensic Intelligence', 'RAG', 'Groq', 'Quantitative Finance'],
    authors: [{ name: 'Sarvesh Raam' }],
    metadataBase: new URL('https://aria-intelligence.vercel.app'),
    openGraph: {
        title: 'ARIA | Financial Risk Analysis',
        description: 'Financial risk analysis combining document RAG, recent news and Groq-hosted LLMs.',
        url: 'https://aria-intelligence.vercel.app',
        siteName: 'ARIA Intelligence',
        locale: 'en_US',
        type: 'website',
    },
    twitter: {
        card: 'summary_large_image',
        title: 'ARIA | Financial Risk Analysis',
        description: 'Upload a financial report and get a risk score built from its statements and recent news.',
    }
}

export const viewport: Viewport = {
    themeColor: [
        { media: '(prefers-color-scheme: light)', color: '#f7f8fa' },
        { media: '(prefers-color-scheme: dark)', color: '#0b0d12' },
    ],
    width: 'device-width',
    initialScale: 1,
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" className={inter.variable}>
            <body className="min-h-screen">
                {children}
            </body>
        </html>
    )
}
