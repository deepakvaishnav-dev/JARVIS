import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../hooks/useWebSocket';

// Mock WebSockets globally
class MockWebSocket {
  url: string;
  readyState: number = 0;
  onmessage: ((event: unknown) => void) | null = null;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      this.readyState = 1;
      if (this.onopen) this.onopen();
    }, 10);
  }
}

global.WebSocket = MockWebSocket as unknown as typeof WebSocket;

describe('useWebSocket Hook', () => {
  it('connects to URL and initializes state', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:test'));
    
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isGenerating).toBe(false);
    expect(result.current.messages).toEqual([]);
    
    // Wait for the mock open to fire
    await act(async () => {
      await new Promise(r => setTimeout(r, 20));
    });
    
    expect(result.current.isConnected).toBe(true);
  });
});
