import { afterEach, describe, expect, it } from 'vitest'
import { addDaysISO, formatDuration, formatTime, greeting, setActiveTimeZone, toISODate } from './date'

afterEach(() => setActiveTimeZone(null))

describe('date utils', () => {
  it('computes "today" in the active timezone', () => {
    const instant = new Date('2026-10-05T20:30:00Z')
    setActiveTimeZone('UTC')
    expect(toISODate(instant)).toBe('2026-10-05')
    setActiveTimeZone('Asia/Kolkata') // UTC+5:30 -> already the 6th
    expect(toISODate(instant)).toBe('2026-10-06')
    setActiveTimeZone('America/New_York')
    expect(toISODate(instant)).toBe('2026-10-05')
  })

  it('adds days across month ends', () => {
    expect(addDaysISO(1, '2026-10-31')).toBe('2026-11-01')
    expect(addDaysISO(6, '2026-12-28')).toBe('2027-01-03')
  })

  it('greets based on the hour in the active timezone', () => {
    const instant = new Date('2026-10-05T06:00:00Z')
    setActiveTimeZone('UTC')
    expect(greeting(instant)).toBe('Good Morning')
    setActiveTimeZone('Asia/Tokyo') // 15:00
    expect(greeting(instant)).toBe('Good Afternoon')
    setActiveTimeZone('Pacific/Auckland') // 19:00
    expect(greeting(instant)).toBe('Good Evening')
  })

  it('formats times and durations', () => {
    expect(formatTime('14:05:00')).toBe('2:05 PM')
    expect(formatTime('00:30')).toBe('12:30 AM')
    expect(formatTime(null)).toBe('')
    expect(formatDuration(45)).toBe('45 mins')
    expect(formatDuration(60)).toBe('1 hour')
    expect(formatDuration(150)).toBe('2h 30m')
  })
})
