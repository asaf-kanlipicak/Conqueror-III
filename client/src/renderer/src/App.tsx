import { useState } from 'react'

function App(): React.JSX.Element {
  const [message, setMessage] = useState<string>('')

  const fetchMessage = async (): Promise<void> => {
    try {
      const response = await fetch('http://0.0.0.0:8000')
      const data = await response.json()
      setMessage(data)
    } catch (error) {
      console.error('Error fetching message:', error)
      setMessage('Error fetching message')
    }
  }

  return (
    <div className="container">
      <h1>Conqueror III</h1>
      <div className="actions">
        <button onClick={fetchMessage}>
          Get Message
        </button>
      </div>
      {message && <div className="message">{message}</div>}
    </div>
  )
}

export default App
