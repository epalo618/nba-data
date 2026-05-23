import { BrowserRouter, Routes, Route } from 'react-router-dom'
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
            <Route path="/" element={<Dashboard />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/players" element={<Players />} />
            <Route path="/games" element={<Games />} />
            <Route path="/games/:homeId/vs/:awayId" element={<GameMatchup />} />
            <Route path="/predictions" element={<Predictions />} />
            <Route path="/yesterday" element={<Yesterday />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
