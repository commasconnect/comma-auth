/**
 * Vue 3 Composable for Comma Central Auth
 * Copy this to each CMYK Vue/Nuxt project
 */

import { ref, computed } from 'vue'

interface UserInfo {
  email: string
  name: string
  picture?: string
  domain: string
  provider: string
}

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  requires_2fa: boolean
}

interface CommaAuthConfig {
  authUrl: string
  redirectUrl?: string
}

const authUrl = ref('https://auth.comma.cm')  // Production
// const authUrl = ref('http://localhost:8000')  // Development

const accessToken = ref<string | null>(localStorage.getItem('comma_access_token'))
const refreshToken = ref<string | null>(localStorage.getItem('comma_refresh_token'))
const userInfo = ref<UserInfo | null>(null)
const requires2FA = ref(false)

export function useCommaAuth(config?: CommaAuthConfig) {
  if (config?.authUrl) {
    authUrl.value = config.authUrl
  }

  const isAuthenticated = computed(() => !!accessToken.value && !requires2FA.value)
  const isPartiallyAuthenticated = computed(() => !!accessToken.value && requires2FA.value)

  // Initialize auth state from localStorage
  if (accessToken.value) {
    verifyToken()
  }

  async function initiateLogin(redirectUrl?: string) {
    try {
      const response = await fetch(`${authUrl.value}/auth/google`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        // Store redirect URL for after auth
        if (redirectUrl) {
          localStorage.setItem('comma_auth_redirect', redirectUrl)
        }
        // Redirect to Google OAuth
        window.location.href = data.authorization_url
      }
    } catch (error) {
      console.error('Failed to initiate login:', error)
    }
  }

  async function handleAuthCallback(token: string, requires2fa?: boolean) {
    accessToken.value = token
    requires2FA.value = requires2fa || false
    
    localStorage.setItem('comma_access_token', token)
    
    await verifyToken()
    
    // Redirect to original URL if stored
    const redirectUrl = localStorage.getItem('comma_auth_redirect')
    if (redirectUrl) {
      localStorage.removeItem('comma_auth_redirect')
      window.location.href = redirectUrl
    }
  }

  async function verifyToken() {
    if (!accessToken.value) return false

    try {
      const response = await fetch(`${authUrl.value}/auth/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken.value}`,
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        const data = await response.json()
        if (data.valid) {
          userInfo.value = data.user_info
          requires2FA.value = data.user_info?.requires_2fa || false
          return true
        }
      }
      
      // Token invalid, clear auth
      logout()
      return false
    } catch (error) {
      console.error('Token verification failed:', error)
      logout()
      return false
    }
  }

  async function sendOTP(phoneNumber: string) {
    if (!accessToken.value) throw new Error('Not authenticated')

    try {
      const response = await fetch(`${authUrl.value}/auth/otp/send`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken.value}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      })

      if (!response.ok) {
        throw new Error('Failed to send OTP')
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to send OTP:', error)
      throw error
    }
  }

  async function verifyOTP(phoneNumber: string, code: string) {
    if (!accessToken.value) throw new Error('Not authenticated')

    try {
      const response = await fetch(`${authUrl.value}/auth/otp/verify`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken.value}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          phone_number: phoneNumber, 
          code: code 
        }),
      })

      if (response.ok) {
        const data: TokenResponse = await response.json()
        accessToken.value = data.access_token
        refreshToken.value = data.refresh_token
        requires2FA.value = false
        
        localStorage.setItem('comma_access_token', data.access_token)
        localStorage.setItem('comma_refresh_token', data.refresh_token)
        
        await verifyToken()
        return true
      }
      
      return false
    } catch (error) {
      console.error('OTP verification failed:', error)
      return false
    }
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    userInfo.value = null
    requires2FA.value = false
    
    localStorage.removeItem('comma_access_token')
    localStorage.removeItem('comma_refresh_token')
    localStorage.removeItem('comma_auth_redirect')
  }

  function getAuthHeaders() {
    if (!accessToken.value) return {}
    
    return {
      'Authorization': `Bearer ${accessToken.value}`,
    }
  }

  return {
    // State
    isAuthenticated,
    isPartiallyAuthenticated,
    userInfo,
    requires2FA,
    
    // Methods
    initiateLogin,
    handleAuthCallback,
    verifyToken,
    sendOTP,
    verifyOTP,
    logout,
    getAuthHeaders,
  }
}