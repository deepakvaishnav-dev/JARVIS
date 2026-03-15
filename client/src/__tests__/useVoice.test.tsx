import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVoice } from '../hooks/useVoice';

vi.mock('react-hot-toast', () => ({
  default: {
    error: vi.fn(),
    success: vi.fn()
  }
}));

// Mock globals for browser APIs
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockRejectedValue(new Error("Permission Denied"))
  },
  writable: true
});

describe('useVoice Hook', () => {
  it('initializes with correct default states', () => {
    const { result } = renderHook(() => useVoice());
    
    expect(result.current.isRecording).toBe(false);
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.isSpeaking).toBe(false);
  });

  it('triggers toast error on mic permission failure', async () => {
    const { result } = renderHook(() => useVoice());
    
    await act(async () => {
      await result.current.startRecording();
    });
    
    // Expect React Hot Toast default.error to have been called because of the mock rejection
    const toastMock = await import('react-hot-toast');
    expect(toastMock.default.error).toHaveBeenCalledWith("Microphone access denied or unavailable.");
  });
});
