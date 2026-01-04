import './globals.css'

export const metadata = {
  title: 'Plum OPD Claim Portal',
  description: 'AI-powered OPD insurance claim processing',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center">
                  <span className="text-2xl font-bold text-plum-600">Plum</span>
                  <span className="ml-2 text-gray-500 text-sm">OPD Claims</span>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <a href="/" className="text-gray-600 hover:text-plum-600 px-3 py-2 text-sm font-medium">
                  Submit Claim
                </a>
                <a href="/claims" className="text-gray-600 hover:text-plum-600 px-3 py-2 text-sm font-medium">
                  My Claims
                </a>
                <a href="/policy" className="text-gray-600 hover:text-plum-600 px-3 py-2 text-sm font-medium">
                  Policy Info
                </a>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}
