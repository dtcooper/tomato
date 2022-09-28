
// TODO: timeout on fetch

const ping = async (address, accessToken = null) => {
  let data, response
  const headers = {}

  if (accessToken) { headers['X-Access-Token'] = accessToken }

  try {
    response = await fetch(`${address}ping/`, { headers })
    data = await response.json()
  } catch (error) {
    console.error(error)
    return { success: false, error: 'Invalid handshake. Are you sure this address is correct?' }
  }

  return data
}

const login = async (address, username, password) => {
  let response, data

  try {
    response = await fetch(`${address}auth/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    data = await response.json()
  } catch (error) {
    console.error(error)
    return { success: false, error: 'Server error while logging in' }
  }

  return data
}

export { login, ping }
