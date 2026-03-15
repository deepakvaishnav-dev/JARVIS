import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock the Toaster so it doesn't complain about rendering outside of a DOM context sometimes in tests
vi.mock('react-hot-toast', () => ({
  Toaster: () => null,
  default: {
    error: vi.fn(),
    success: vi.fn(),
  }
}));

describe('App Component', () => {
  it('renders JARVIS OS title and layout', () => {
    render(<App />);
    const titles = screen.getAllByText(/JARVIS OS/i);
    expect(titles.length).toBeGreaterThan(0);
    
    // Check navigation items
    expect(screen.getByText('Workspace')).toBeInTheDocument();
    expect(screen.getByText('Voice Control')).toBeInTheDocument();
  });
});
