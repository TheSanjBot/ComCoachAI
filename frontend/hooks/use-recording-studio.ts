"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { RecordingModeSlug } from "@/lib/mode-config";
import {
  analyzeRecording,
  formatElapsedTime,
  pickSupportedRecordingMimeType,
  type FaceDetectionState,
  type RecordingAnalysisResult,
  type RecordingUploadReceipt,
  uploadRecording
} from "@/lib/recording";

type RecordingStudioStatus =
  | "idle"
  | "requesting-permissions"
  | "ready"
  | "recording"
  | "recorded"
  | "uploading"
  | "analyzing"
  | "uploaded"
  | "analyzed"
  | "partial"
  | "error";

type FaceDetectorInstance = {
  detect: (input: ImageBitmapSource) => Promise<Array<unknown>>;
};

type FaceDetectorConstructor = new (options?: {
  fastMode?: boolean;
  maxDetectedFaces?: number;
}) => FaceDetectorInstance;

type BrowserWindow = Window & {
  FaceDetector?: FaceDetectorConstructor;
};

type UseRecordingStudioArgs = {
  mode: RecordingModeSlug;
  token: string;
};

function useStableEvent<TArgs extends unknown[], TReturn>(
  handler: (...args: TArgs) => TReturn
) {
  const handlerRef = useRef(handler);

  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  return useCallback((...args: TArgs) => handlerRef.current(...args), []);
}

export function useRecordingStudio({ mode, token }: UseRecordingStudioArgs) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const detectionRef = useRef<number | null>(null);
  const previewUrlRef = useRef<string | null>(null);
  const detectorInstanceRef = useRef<FaceDetectorInstance | null>(null);
  const isCheckingFaceRef = useRef(false);
  const isRecordingRef = useRef(false);
  const discardNextStopRef = useRef(false);

  const [status, setStatus] = useState<RecordingStudioStatus>("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [faceDetectionState, setFaceDetectionState] = useState<FaceDetectionState>("waiting");
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState("video/webm");
  const [hasCamera, setHasCamera] = useState(false);
  const [hasMicrophone, setHasMicrophone] = useState(false);
  const [savedRecording, setSavedRecording] = useState<RecordingUploadReceipt | null>(null);
  const [analysisResult, setAnalysisResult] = useState<RecordingAnalysisResult | null>(null);
  const [faceDetectedSamples, setFaceDetectedSamples] = useState(0);
  const [faceMissingSamples, setFaceMissingSamples] = useState(0);

  const clearTimer = useStableEvent(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  });

  const clearFaceLoop = useStableEvent(() => {
    if (detectionRef.current !== null) {
      window.clearInterval(detectionRef.current);
      detectionRef.current = null;
    }
  });

  const revokePreviewUrl = useStableEvent(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }
  });

  const stopTracks = useStableEvent(() => {
    clearFaceLoop();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setHasCamera(false);
    setHasMicrophone(false);
    setFaceDetectionState("waiting");
  });

  const cleanupRecorderState = useStableEvent(() => {
    clearTimer();
    isRecordingRef.current = false;
    recorderRef.current = null;
  });

  const detectFace = useStableEvent(async () => {
    const activeVideo = videoRef.current;
    if (!activeVideo || activeVideo.readyState < 2) {
      setFaceDetectionState("checking");
      return;
    }

    const browserWindow = window as BrowserWindow;
    if (!browserWindow.FaceDetector) {
      setFaceDetectionState("unsupported");
      clearFaceLoop();
      return;
    }

    if (isCheckingFaceRef.current) {
      return;
    }

    isCheckingFaceRef.current = true;

    try {
      detectorInstanceRef.current ??= new browserWindow.FaceDetector({
        fastMode: true,
        maxDetectedFaces: 2
      });

      const faces = await detectorInstanceRef.current.detect(activeVideo as unknown as ImageBitmapSource);
      const nextState: FaceDetectionState = faces.length > 0 ? "detected" : "not-detected";
      setFaceDetectionState(nextState);

      if (isRecordingRef.current) {
        if (nextState === "detected") {
          setFaceDetectedSamples((current) => current + 1);
        } else {
          setFaceMissingSamples((current) => current + 1);
        }
      }
    } catch {
      setFaceDetectionState("unsupported");
      clearFaceLoop();
    } finally {
      isCheckingFaceRef.current = false;
    }
  });

  const startFaceLoop = useStableEvent(() => {
    clearFaceLoop();
    void detectFace();
    detectionRef.current = window.setInterval(() => {
      void detectFace();
    }, 1500);
  });

  const requestPermissions = useStableEvent(async () => {
    setPermissionError(null);
    setActionError(null);
    setStatus("requesting-permissions");

    try {
      stopTracks();
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: true
      });

      streamRef.current = stream;
      setHasCamera(stream.getVideoTracks().length > 0);
      setHasMicrophone(stream.getAudioTracks().length > 0);

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
        void videoRef.current.play().catch(() => undefined);
      }

      setStatus("ready");
      setFaceDetectionState("checking");
      startFaceLoop();
    } catch (error) {
      setStatus("error");
      setPermissionError(
        error instanceof Error
          ? error.message
          : "Unable to access the webcam and microphone."
      );
    }
  });

  const resetCapture = useStableEvent(() => {
    revokePreviewUrl();
    setRecordingBlob(null);
    setRecordingUrl(null);
    setSavedRecording(null);
    setAnalysisResult(null);
    setElapsedSeconds(0);
    setFaceDetectedSamples(0);
    setFaceMissingSamples(0);
    setActionError(null);
    setStatus(streamRef.current ? "ready" : "idle");
  });

  const startRecording = useStableEvent(async () => {
    if (!streamRef.current) {
      await requestPermissions();
      if (!streamRef.current) {
        return;
      }
    }

    if (typeof MediaRecorder === "undefined") {
      setStatus("error");
      setActionError("This browser does not support in-browser recording.");
      return;
    }

    resetCapture();
    const supportedMimeType = pickSupportedRecordingMimeType();
    setMimeType(supportedMimeType);

    try {
      chunksRef.current = [];
      discardNextStopRef.current = false;
      const nextRecorder = new MediaRecorder(
        streamRef.current,
        supportedMimeType ? { mimeType: supportedMimeType } : undefined
      );
      recorderRef.current = nextRecorder;

      nextRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      nextRecorder.onerror = () => {
        cleanupRecorderState();
        setStatus("error");
        setActionError("Recording failed. Please try again.");
      };

      nextRecorder.onstop = () => {
        cleanupRecorderState();
        if (discardNextStopRef.current) {
          discardNextStopRef.current = false;
          chunksRef.current = [];
          return;
        }
        const capturedBlob = new Blob(chunksRef.current, { type: supportedMimeType });
        if (capturedBlob.size === 0) {
          setStatus("error");
          setActionError("No recording data was captured. Please try again.");
          return;
        }
        const nextUrl = URL.createObjectURL(capturedBlob);
        previewUrlRef.current = nextUrl;
        setRecordingBlob(capturedBlob);
        setRecordingUrl(nextUrl);
        setStatus("recorded");
      };

      isRecordingRef.current = true;
      setElapsedSeconds(0);
      setFaceDetectedSamples(0);
      setFaceMissingSamples(0);
      setSavedRecording(null);
      setAnalysisResult(null);
      setStatus("recording");
      nextRecorder.start();

      clearTimer();
      timerRef.current = window.setInterval(() => {
        setElapsedSeconds((current) => current + 1);
      }, 1000);
    } catch {
      cleanupRecorderState();
      setStatus("error");
      setActionError("Unable to start the recording session.");
    }
  });

  const stopRecording = useStableEvent(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
  });

  const uploadCapturedRecording = useStableEvent(async () => {
    if (savedRecording) {
      return savedRecording;
    }
    if (!recordingBlob) {
      return null;
    }

    setStatus("uploading");
    setActionError(null);

    try {
      const receipt = await uploadRecording({
        token,
        mode,
        blob: recordingBlob,
        durationSeconds: elapsedSeconds,
        mimeType,
        faceDetectionState,
        faceDetectedSamples,
        faceMissingSamples
      });
      setSavedRecording(receipt);
      setStatus("uploaded");
      return receipt;
    } catch (error) {
      setStatus("error");
      setActionError(
        error instanceof Error ? error.message : "Unable to upload the recording."
      );
      return null;
    }
  });

  const submitRecordingForAnalysis = useStableEvent(async () => {
    const uploadedRecording = (await uploadCapturedRecording()) ?? savedRecording;
    if (!uploadedRecording) {
      return null;
    }

    setStatus("analyzing");
    setActionError(null);

    try {
      const result = await analyzeRecording(token, uploadedRecording.recording_id);
      setAnalysisResult(result);
      setStatus(result.processing_status === "analyzed" ? "analyzed" : "partial");
      return {
        recording: uploadedRecording,
        analysis: result,
      };
    } catch (error) {
      setStatus("error");
      setActionError(
        error instanceof Error ? error.message : "Unable to analyze the recording."
      );
      return null;
    }
  });

  const releaseDevices = useStableEvent(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      discardNextStopRef.current = true;
      recorderRef.current.stop();
    }
    cleanupRecorderState();
    stopTracks();
    resetCapture();
  });

  useEffect(() => {
    return () => {
      cleanupRecorderState();
      stopTracks();
      revokePreviewUrl();
    };
  }, [cleanupRecorderState, revokePreviewUrl, stopTracks]);

  return {
    videoRef,
    status,
    elapsedSeconds,
    formattedElapsedTime: formatElapsedTime(elapsedSeconds),
    faceDetectionState,
    permissionError,
    actionError,
    recordingUrl,
    recordingBlob,
    mimeType,
    hasCamera,
    hasMicrophone,
    savedRecording,
    analysisResult,
    faceDetectedSamples,
    faceMissingSamples,
    canStartRecording:
      status === "ready" ||
      status === "recorded" ||
      status === "uploaded" ||
      status === "analyzed" ||
      status === "partial",
    canStopRecording: status === "recording",
    canSubmitForAnalysis:
      Boolean(recordingBlob || savedRecording) &&
      [
        "recorded",
        "uploaded",
        "analyzed",
        "partial",
        "error"
      ].includes(status),
    requestPermissions,
    startRecording,
    stopRecording,
    uploadCapturedRecording,
    submitRecordingForAnalysis,
    resetCapture,
    releaseDevices
  };
}
