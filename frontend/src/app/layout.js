import './globals.css'
import Navbar from '../components/Navbar'

export const metadata = {
  title: 'CoughPrint',
  description: 'AI-Powered Respiratory Disease Detection',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-950 text-white">
        <Navbar />
        {children}
      </body>
    </html>
  )
}