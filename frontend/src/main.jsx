/**
 * Module   : App Bootstrap
 * Owner    : Frontend Lead
 * Purpose  : React root render entrypoint.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)