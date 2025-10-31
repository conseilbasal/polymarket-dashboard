import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import TraderDetail from './pages/TraderDetail'
import Leaderboard from './pages/Leaderboard'
import AllTrades from './pages/AllTrades'
import CopyTrading from './pages/CopyTrading'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/copy-trading" replace />} />
          <Route path="/copy-trading" element={<CopyTrading />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/trader/:address" element={<TraderDetail />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/trades" element={<AllTrades />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
