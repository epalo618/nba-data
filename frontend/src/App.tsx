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

            {/* Soccer's URLs carry an extra :league segment, so they need their
                own routes rather than falling through to the generic /:sport/*
                ones below (which only ever match a single path segment). */}
            <Route path="/soccer" element={<Navigate to="/soccer/epl" replace />} />
            <Route path="/soccer/:league" element={<Dashboard />} />
            <Route path="/soccer/:league/teams" element={<Teams />} />
            <Route path="/soccer/:league/players" element={<Players />} />
            <Route path="/soccer/:league/games" element={<Games />} />
            <Route path="/soccer/:league/games/:homeId/vs/:awayId" element={<GameMatchup />} />
            <Route path="/soccer/:league/predictions" element={<Predictions />} />
            <Route path="/soccer/:league/yesterday" element={<Yesterday />} />

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
