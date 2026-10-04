import React, { createContext, useContext, useEffect, useState } from 'react'
import {
  api,
  getAuthToken,
  getStoredUser,
  removeAuthToken,
  setAuthToken,
  setStoredUser,
} from '../api'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => getStoredUser())
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true

    const restoreSession = async () => {
      if (!getAuthToken()) {
        if (active) setIsLoading(false)
        return
      }

      try {
        const currentUser = await api.getMe()
        if (active) {
          setStoredUser(currentUser)
          setUser(currentUser)
        }
      } catch {
        removeAuthToken()
        if (active) setUser(null)
      } finally {
        if (active) setIsLoading(false)
      }
    }

    restoreSession()
    return () => { active = false }
  }, [])

  const login = async (email, password) => {
    let tokenResponse
    try {
      tokenResponse = await api.login(email, password)
    } catch (primaryError) {
      try {
        tokenResponse = await api.componentLogin(email, password)
      } catch {
        throw primaryError
      }
    }

    setAuthToken(tokenResponse.access_token)
    try {
      const currentUser = await api.getMe()
      setStoredUser(currentUser)
      setUser(currentUser)
      return currentUser
    } catch (error) {
      removeAuthToken()
      throw error
    }
  }

  const logout = () => {
    setUser(null)
    removeAuthToken()
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
