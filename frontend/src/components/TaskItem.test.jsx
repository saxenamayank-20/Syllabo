import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import TaskItem from './TaskItem'

const task = {
  id: 1, title: 'Revise optics', subject_name: 'Physics', duration_mins: 45,
  start_time: '17:00:00', status: 'pending', source: 'ai',
}

describe('TaskItem', () => {
  it('shows task details and the AI badge', () => {
    render(<ul><TaskItem task={task} onToggle={() => {}} /></ul>)
    expect(screen.getByText('Revise optics')).toBeInTheDocument()
    expect(screen.getByText('Physics')).toBeInTheDocument()
    expect(screen.getByText('5:00 PM')).toBeInTheDocument()
    expect(screen.getByText('AI')).toBeInTheDocument()
  })

  it('calls the toggle, edit and delete handlers', async () => {
    const onToggle = vi.fn(), onEdit = vi.fn(), onDelete = vi.fn()
    render(<ul><TaskItem task={task} onToggle={onToggle} onEdit={onEdit} onDelete={onDelete} /></ul>)
    await userEvent.click(screen.getByRole('checkbox'))
    await userEvent.click(screen.getByLabelText('Edit "Revise optics"'))
    await userEvent.click(screen.getByLabelText('Delete "Revise optics"'))
    expect(onToggle).toHaveBeenCalledWith(task)
    expect(onEdit).toHaveBeenCalledWith(task)
    expect(onDelete).toHaveBeenCalledWith(task)
  })
})
