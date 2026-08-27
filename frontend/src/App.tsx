import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Teams from './pages/Teams'
import Players from './pages/Players'
import Games from './pages/Games'
import GameMatchup from './pages/GameMatchup'
import Predictions from './pages/Predictions'
import Yesterday from './pages/Yesterday'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Navigate to="/nba" replace />} />

            <Route path="/:sport" element={<Dashboard />} />
            <Route path="/:sport/teams" element={<Teams />} />
            <Route path="/:sport/players" element={<Players />} />
            <Route path="/:sport/games" element={<Games />} />
            <Route path="/:sport/games/:homeId/vs/:awayId" element={<GameMatchup />} />
            <Route path="/:sport/predictions" element={<Predictions />} />
            <Route path="/:sport/yesterday" element={<Yesterday />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
