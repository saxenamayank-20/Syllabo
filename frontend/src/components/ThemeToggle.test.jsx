import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it } from 'vitest'
import { THEME_KEY, ThemeProvider } from '../context/ThemeContext'
import ThemeToggle from './ThemeToggle'

const renderToggle = () =>
  render(
    <ThemeProvider>
      <ThemeToggle />
    </ThemeProvider>,
  )

afterEach(() => document.documentElement.classList.remove('dark'))

describe('ThemeToggle', () => {
  it('switches to dark mode and remembers the choice', async () => {
    renderToggle()
    expect(document.documentElement).not.toHaveClass('dark')

    await userEvent.click(screen.getByRole('button', { name: 'Switch to dark mode' }))
    expect(document.documentElement).toHaveClass('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')

    await userEvent.click(screen.getByRole('button', { name: 'Switch to light mode' }))
    expect(document.documentElement).not.toHaveClass('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('light')
  })

  it('starts from the saved theme', () => {
    localStorage.setItem(THEME_KEY, 'dark')
    renderToggle()
    expect(document.documentElement).toHaveClass('dark')
    expect(screen.getByRole('button', { name: 'Switch to light mode' })).toBeInTheDocument()
  })
})
