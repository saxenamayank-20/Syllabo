import { describe, expect, it } from 'vitest'
import { axiosError } from '../test/utils'
import { errorMessage, isEmailNotVerified } from './client'

describe('errorMessage', () => {
  it('reads string, object and validation-list details', () => {
    expect(errorMessage(axiosError(400, 'Incorrect code. 4 attempts left.'))).toBe('Incorrect code. 4 attempts left.')
    expect(errorMessage(axiosError(403, { code: 'email_not_verified', message: 'Please verify' }))).toBe('Please verify')
    expect(
      errorMessage(axiosError(422, [{ loc: ['body', 'email'], msg: 'value is not a valid email address' }])),
    ).toBe('email: value is not a valid email address')
  })

  it('explains network failures', () => {
    expect(errorMessage(new Error('Network Error'))).toMatch(/Cannot reach the server/)
  })

  it('detects unverified-email responses', () => {
    expect(isEmailNotVerified(axiosError(403, { code: 'email_not_verified' }))).toBe(true)
    expect(isEmailNotVerified(axiosError(403, 'Forbidden'))).toBe(false)
    expect(isEmailNotVerified(axiosError(401, 'Incorrect email or password'))).toBe(false)
  })
})
