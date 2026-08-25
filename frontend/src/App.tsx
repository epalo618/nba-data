import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Teams from './pages/Teams'
import Players from './pages/Players'
import Games from './pages/Games'
import GameMatchup from './pages/GameMatchup'
import Predictions from './pages/Predictions'
import Yesterday from './pages/Yesterday'
import ComingSoon from './pages/ComingSoon'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Navigate to="/nba" replace />} />

            {/* Soccer isn't wired up on the backend yet (Phase 6) — these literal
                routes outrank the generic /:sport/* routes below so they show a
                placeholder instead of hitting real pages that would 404. NFL was
                the same until Phase 5 (its backend landed in Phase 4); it now
                falls through to the real pages below like NBA does. */}
            <Route path="/soccer" element={<ComingSoon />} />
            <Route path="/soccer/:league" element={<ComingSoon />} />
            <Route path="/soccer/:league/teams" element={<ComingSoon />} />
            <Route path="/soccer/:league/players" element={<ComingSoon />} />
            <Route path="/soccer/:league/games" element={<ComingSoon />} />
            <Route path="/soccer/:league/games/:homeId/vs/:awayId" element={<ComingSoon />} />
            <Route path="/soccer/:league/predictions" element={<ComingSoon />} />
            <Route path="/soccer/:league/yesterday" element={<ComingSoon />} />

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
