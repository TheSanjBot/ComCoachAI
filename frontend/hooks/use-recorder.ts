"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface RecorderState {
  stream: MediaStream | null;
  previewUrl: string | null;
  isRecording: boolean;
  duration: number;
  faceDetected: boolean;
  error: string | null;
}

export function useRecorder() {
  const [state, setState] = useState<RecorderState>({
    stream: null,
    previewUrl: null,
    isRecording: false,
    duration: 0,
    faceDetected: false,
    error: null
  });
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const clearStream = useCallback(() => {
    setState((current) => {
      current.stream?.getTracks().forEach((track) => track.stop());
      return { ...current, stream: null, isRecording: false, faceDetected: false };
    });
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      const mediaRecorder = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        setState((current) => ({
          ...current,
          previewUrl: url,
          isRecording: false
        }));
      };

      mediaRecorder.start(1000);
      mediaRecorderRef.current = mediaRecorder;
      setState({
        stream,
        previewUrl: null,
        isRecording: true,
        duration: 0,
        faceDetected: true,
        error: null
      });

      timerRef.current = window.setInterval(() => {
        setState((current) => ({
          ...current,
          duration: current.duration + 1,
          faceDetected: current.stream?.active ?? false
        }));
      }, 1000);
    } catch (error) {
      setState((current) => ({
        ...current,
        error:
          error instanceof Error
            ? error.message
            : "Unable to access webcam and microphone."
      }));
    }
  }, []);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    clearStream();
  }, [clearStream]);

  useEffect(() => {
    return () => {
      clearStream();
      if (state.previewUrl) {
        URL.revokeObjectURL(state.previewUrl);
      }
    };
  }, [clearStream, state.previewUrl]);

  return {
    ...state,
    startRecording,
    stopRecording
  };
}

