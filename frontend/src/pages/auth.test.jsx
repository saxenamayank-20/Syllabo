import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import api, { setToken } from '../api/client'
import { axiosError, renderAt } from '../test/utils'
import ForgotPassword from './ForgotPassword'
import Login from './Login'
import VerifyEmail from './VerifyEmail'

vi.mock('../api/client', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }
})

const session = {
  access_token: 'tok',
  user: { id: 1, name: 'Riya Shah', email: 'riya@gmail.com', email_verified: true, timezone: 'UTC' },
}

beforeEach(() => {
  vi.resetAllMocks()
  setToken(null)
})

describe('Login', () => {
  it('sends unverified users to the verify-email page', async () => {
    api.post.mockRejectedValueOnce(axiosError(403, { code: 'email_not_verified', message: 'Verify', email: 'riya@gmail.com' }))
    renderAt('/login', <Login />)
    await userEvent.type(screen.getByLabelText('Email'), 'riya@gmail.com')
    await userEvent.type(screen.getByLabelText('Password'), 'secret123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent('/verify-email?email=riya%40gmail.com'))
  })

  it('shows the error for a wrong password', async () => {
    api.post.mockRejectedValueOnce(axiosError(401, 'Incorrect email or password'))
    renderAt('/login', <Login />)
    await userEvent.type(screen.getByLabelText('Email'), 'riya@gmail.com')
    await userEvent.type(screen.getByLabelText('Password'), 'nope')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
  })
})

describe('VerifyEmail', () => {
  it('verifies the code and stores the session', async () => {
    api.post.mockResolvedValueOnce({ data: session })
    renderAt('/verify-email?email=riya%40gmail.com', <VerifyEmail />, { route: '/verify-email' })
    expect(screen.getByRole('button', { name: /resend code in/i })).toBeDisabled()
    await userEvent.type(screen.getByLabelText('Verification code'), '12a3456') // non-digits are dropped
    await userEvent.click(screen.getByRole('button', { name: 'Verify email' }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/auth/verify-email', { email: 'riya@gmail.com', code: '123456' }))
    await waitFor(() => expect(localStorage.getItem('studyai_token')).toBe('tok'))
  })
})

describe('ForgotPassword', () => {
  it('requests a code, then resets the password', async () => {
    api.post
      .mockResolvedValueOnce({ data: { email: 'riya@gmail.com', email_sent: true, message: 'sent' } })
      .mockResolvedValueOnce({ data: session })
    renderAt('/forgot-password', <ForgotPassword />)
    await userEvent.type(screen.getByLabelText('Email'), 'riya@gmail.com')
    await userEvent.click(screen.getByRole('button', { name: 'Send reset code' }))

    await userEvent.type(await screen.findByLabelText('Reset code'), '654321')
    await userEvent.type(screen.getByLabelText('New password'), 'newpass99')
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'different')
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('do not match')

    await userEvent.clear(screen.getByLabelText('Confirm new password'))
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newpass99')
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenLastCalledWith('/auth/reset-password', { email: 'riya@gmail.com', code: '654321', new_password: 'newpass99' }),
    )
  })
})
