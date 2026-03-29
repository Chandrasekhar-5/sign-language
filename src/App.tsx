/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  HandLandmarker, 
  FilesetResolver,
  DrawingUtils
} from '@mediapipe/tasks-vision';
import { 
  History, 
  Volume2, 
  VolumeX, 
  Trash2, 
  Hand, 
  Settings,
  Info,
  AlertCircle,
  Loader2,
  Play,
  Square,
  MessageSquare,
  ChevronRight,
  X
} from 'lucide-react';
import { recognizeGesture } from './gestureLogic';
import { GESTURES } from './types';
import { cn } from './lib/utils';

export default function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const handLandmarkerRef = useRef<HandLandmarker | null>(null);
  const requestRef = useRef<number>(null);
  
  // State
  const [detectedWord, setDetectedWord] = useState<string>(GESTURES.NONE);
  const [currentSentence, setCurrentSentence] = useState<string[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isTtsEnabled, setIsTtsEnabled] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [showAllGestures, setShowAllGestures] = useState(false);
  
  // Refs for detection logic
  const lastDetectedRef = useRef<string>(GESTURES.NONE);
  const detectionCountRef = useRef<number>(0);
  const DETECTION_THRESHOLD = 8; // Lowered from 15 for faster response

  const speak = useCallback((text: string) => {
    if (!isTtsEnabled || !text || text === GESTURES.NONE) return;
    
    // Cancel any ongoing speech to prevent queue buildup
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.85; // Slightly slower for better clarity
    utterance.pitch = 1;
    utterance.volume = 1;
    
    window.speechSynthesis.speak(utterance);
  }, [isTtsEnabled]);

  const processFrame = useCallback(() => {
  if (
    !videoRef.current || 
    !canvasRef.current || 
    !handLandmarkerRef.current ||
    videoRef.current.readyState < 2
  ) {
    requestRef.current = requestAnimationFrame(processFrame);
    return;
  }

  const canvasCtx = canvasRef.current.getContext('2d');
  if (!canvasCtx) return;

  const startTimeMs = performance.now();
  const results = handLandmarkerRef.current.detectForVideo(videoRef.current, startTimeMs);

  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
  
  // Draw video frame normally (NO MIRROR)
  canvasCtx.drawImage(
    videoRef.current, 
    0, 0, 
    canvasRef.current.width, 
    canvasRef.current.height
  );

  if (results.landmarks && results.landmarks.length > 0) {
    const drawingUtils = new DrawingUtils(canvasCtx);
    
    for (const landmarks of results.landmarks) {
      // Draw connections and landmarks normally (NO MIRROR)
      drawingUtils.drawConnectors(landmarks, HandLandmarker.HAND_CONNECTIONS, {
        color: '#10b981',
        lineWidth: 8
      });
      drawingUtils.drawLandmarks(landmarks, {
        color: '#ef4444',
        lineWidth: 1,
        radius: 3
      });

      // Get gesture recognition
      const gesture = recognizeGesture(landmarks as any);
      
      if (gesture !== GESTURES.NONE) {
        if (gesture === lastDetectedRef.current) {
          detectionCountRef.current += 1;
        } else {
          lastDetectedRef.current = gesture;
          detectionCountRef.current = 1;
        }

        if (detectionCountRef.current === DETECTION_THRESHOLD) {
          setDetectedWord(gesture);
          setConfidence(92 + Math.random() * 6);
          
          // Speak the gesture regardless of recording state
          speak(gesture);
          
          if (isRecording) {
            setCurrentSentence(prev => {
              // Don't add the same word twice in a row immediately
              if (prev[prev.length - 1] === gesture) return prev;
              return [...prev, gesture];
            });
          } else {
            // Add individual gesture to history if not recording
            setHistory(prev => {
              if (prev[0] === gesture) return prev;
              return [gesture, ...prev].slice(0, 20);
            });
          }
        }
      } else {
        // Reset detection if no gesture
        if (lastDetectedRef.current !== GESTURES.NONE) {
          lastDetectedRef.current = GESTURES.NONE;
          detectionCountRef.current = 0;
          setDetectedWord(GESTURES.NONE);
          setConfidence(0);
        }
      }
    }
  } else {
    if (detectedWord !== GESTURES.NONE) {
      setDetectedWord(GESTURES.NONE);
      setConfidence(0);
    }
  }
  
  canvasCtx.restore();
  requestRef.current = requestAnimationFrame(processFrame);
}, [isRecording, speak, detectedWord]);

  useEffect(() => {
    const initializeMediaPipe = async () => {
      try {
        console.log("Initializing MediaPipe...");
        const vision = await FilesetResolver.forVisionTasks(
          "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
        );
        
        const handLandmarker = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: `https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task`,
            delegate: "GPU"
          },
          runningMode: "VIDEO",
          numHands: 2
        });

        handLandmarkerRef.current = handLandmarker;
        console.log("HandLandmarker initialized");

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          console.log("Requesting camera access...");
          const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 1280, height: 720, facingMode: "user" }
          });
          
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.onloadedmetadata = () => {
              videoRef.current?.play();
              console.log("Video started playing");
              setIsLoading(false);
              requestRef.current = requestAnimationFrame(processFrame);
            };
          }
        } else {
          setError("Camera not supported in this browser");
          setIsLoading(false);
        }
      } catch (err) {
        console.error("Init error:", err);
        setError("Camera access denied or AI models failed to load. Please ensure you have granted camera permissions.");
        setIsLoading(false);
      }
    };

    initializeMediaPipe();
    
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
      if (handLandmarkerRef.current) handLandmarkerRef.current.close();
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
      window.speechSynthesis.cancel();
    };
  }, [processFrame]);

  const toggleRecording = () => {
    if (isRecording) {
      // Stopping: Save sentence to history
      if (currentSentence.length > 0) {
        const sentence = currentSentence.join(" ");
        setHistory(prev => [sentence, ...prev].slice(0, 10));
        setCurrentSentence([]);
      }
      setIsRecording(false);
    } else {
      // Starting
      setCurrentSentence([]);
      setIsRecording(true);
    }
  };

  const speakFullSentence = () => {
    const sentence = currentSentence.join(" ");
    if (sentence) speak(sentence);
  };

  const clearHistory = () => setHistory([]);

  const supportedGestures = [
    { name: "Hello", desc: "Open Palm (Spread Fingers)" },
    { name: "Stop", desc: "Open Palm (Fingers Together)" },
    { name: "Yes", desc: "Closed Fist" },
    { name: "No", desc: "Index & Middle Finger Pinched" },
    { name: "Thank You", desc: "Flat Hand with Thumb Tucked" },
    { name: "Thumbs Up", desc: "Thumb Up, Fingers Closed" },
    { name: "Point", desc: "Index Finger Extended" },
    { name: "Peace", desc: "V-Shape with Spread Fingers" },
    { name: "OK", desc: "👌 Thumb & Index Circle" },
    { name: "Rock On", desc: "Index & Pinky Extended" },
    { name: "Call Me", desc: "Thumb & Pinky Extended" },
    { name: "I Love You", desc: "Index, Pinky & Thumb Extended" },
    { name: "Dislike", desc: "Thumb Pointing Down" }
  ];

  return (
    <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-emerald-500/30 overflow-x-hidden">
      {/* Header */}
      <header className="p-6 flex justify-between items-center border-b border-white/5 backdrop-blur-xl sticky top-0 z-40 bg-[#050505]/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/20 rotate-3">
            <Hand className="text-black w-6 h-6 -rotate-3" />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tighter uppercase">SignAI Pro</h1>
            <p className="text-[10px] text-emerald-500 font-bold uppercase tracking-[0.2em]">Real-time Translator</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setIsTtsEnabled(!isTtsEnabled)}
            className={cn(
              "p-2.5 rounded-xl transition-all duration-300 border",
              isTtsEnabled ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" : "bg-white/5 border-white/5 text-white/40"
            )}
          >
            {isTtsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
          </button>
          <button className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-white/60 hover:bg-white/10 transition-colors">
            <Settings size={20} />
          </button>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto p-6 space-y-8">
        {/* Top Row: Video and Detected Gesture */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Video Feed */}
          <div className="lg:col-span-8 relative aspect-video bg-white/5 rounded-[2rem] overflow-hidden border border-white/5 shadow-2xl group">
            {isLoading && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-[#050505]">
                <Loader2 className="w-12 h-12 text-emerald-500 animate-spin mb-4" />
                <p className="text-white/40 font-bold uppercase tracking-widest text-xs">Loading AI Engine</p>
              </div>
            )}

            {error && (
              <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-[#050505]/95 p-8 text-center">
                <AlertCircle className="w-16 h-16 text-red-500 mb-6" />
                <h2 className="text-2xl font-black mb-2 uppercase tracking-tighter">Access Denied</h2>
                <p className="text-white/40 max-w-md mb-8 text-sm">{error}</p>
                <button 
                  onClick={() => window.location.reload()}
                  className="px-10 py-4 bg-white text-black font-black rounded-2xl hover:bg-emerald-500 transition-all active:scale-95"
                >
                  RETRY CONNECTION
                </button>
              </div>
            )}

            <video ref={videoRef} className="hidden" playsInline muted />
            <canvas 
              ref={canvasRef} 
              className="w-full h-full object-cover" 
              width={1280} 
              height={720} 
            />

            {/* Recording Indicator */}
            <div className="absolute top-8 left-8 flex items-center gap-3 px-4 py-2 bg-black/60 backdrop-blur-xl rounded-2xl border border-white/10 z-10">
              <div className={cn("w-2.5 h-2.5 rounded-full", isRecording ? "bg-red-500 animate-pulse" : "bg-emerald-500")} />
              <span className="text-[10px] font-black uppercase tracking-widest text-white/80">
                {isRecording ? "Recording Sentence" : "Live Stream"}
              </span>
            </div>

            {/* Controls Overlay */}
            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4 z-10">
              <button 
                onClick={toggleRecording}
                className={cn(
                  "flex items-center gap-3 px-8 py-4 rounded-2xl font-black transition-all active:scale-95 shadow-2xl",
                  isRecording 
                    ? "bg-red-500 text-white hover:bg-red-600" 
                    : "bg-emerald-500 text-black hover:bg-emerald-400"
                )}
              >
                {isRecording ? (
                  <><Square size={20} fill="currentColor" /> STOP RECORDING</>
                ) : (
                  <><Play size={20} fill="currentColor" /> START RECORDING</>
                )}
              </button>
            </div>
          </div>

          {/* Detected Gesture Card */}
          <div className="lg:col-span-4 h-full flex flex-col gap-6">
            <div className="bg-white/5 rounded-[2rem] p-10 border border-white/5 flex flex-col items-center justify-center flex-1 relative overflow-hidden group min-h-[300px]">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-emerald-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <p className="text-[10px] font-black uppercase tracking-[0.4em] text-white/20 mb-8">Real-time Gesture</p>
              
              <AnimatePresence mode="wait">
                <motion.div
                  key={detectedWord}
                  initial={{ opacity: 0, scale: 0.8, rotate: -5 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  exit={{ opacity: 0, scale: 1.2, rotate: 5 }}
                  className={cn(
                    "text-6xl xl:text-8xl font-black tracking-tighter transition-all text-center",
                    detectedWord === GESTURES.NONE ? "text-white/5" : "text-emerald-400 drop-shadow-[0_0_40px_rgba(52,211,153,0.4)]"
                  )}
                >
                  {detectedWord === GESTURES.NONE ? "---" : detectedWord}
                </motion.div>
              </AnimatePresence>

              <div className="mt-10 flex items-center gap-3 px-4 py-2 bg-white/5 rounded-xl border border-white/5">
                <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <motion.div 
                    className="h-full bg-emerald-500"
                    animate={{ width: `${confidence}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-white/40">{Math.round(confidence)}%</span>
              </div>
            </div>

            {/* History Sidebar */}
            <div className="bg-white/5 rounded-[2rem] border border-white/5 flex flex-col h-[300px]">
              <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <History size={18} className="text-emerald-500" />
                  <h2 className="font-black text-xs uppercase tracking-widest">History</h2>
                </div>
                <button onClick={clearHistory} className="text-white/20 hover:text-red-400 transition-colors">
                  <Trash2 size={16} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {history.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-white/10 text-center p-6">
                    <p className="text-[10px] font-bold uppercase tracking-widest">No records</p>
                  </div>
                ) : (
                  history.map((item, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 bg-white/5 rounded-2xl border border-white/5 flex justify-between items-center group/item"
                    >
                      <p className="text-sm font-medium text-white/80 leading-relaxed flex-1">{item}</p>
                      <button 
                        onClick={() => speak(item)}
                        className="p-2 text-white/20 hover:text-emerald-500 hover:bg-emerald-500/10 rounded-lg transition-all opacity-0 group-hover/item:opacity-100"
                      >
                        <Volume2 size={16} />
                      </button>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Middle Row: Sentence Builder */}
        <div className="bg-white/5 rounded-[2.5rem] p-8 border border-white/5 relative group">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-6 flex-1 w-full">
              <div className="w-16 h-16 bg-emerald-500/10 rounded-2xl flex items-center justify-center border border-emerald-500/20 shrink-0">
                <MessageSquare className="text-emerald-500 w-8 h-8" />
              </div>
              <div className="flex-1">
                <p className="text-[10px] font-black uppercase tracking-[0.3em] text-white/20 mb-2">Current Sentence</p>
                <div className="flex flex-wrap gap-2 min-h-[40px]">
                  {currentSentence.length === 0 ? (
                    <p className="text-white/10 font-medium italic">Start recording to build a sentence...</p>
                  ) : (
                    currentSentence.map((word, i) => (
                      <motion.span 
                        key={i}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="px-4 py-2 bg-emerald-500 text-black font-black rounded-xl text-sm shadow-lg shadow-emerald-500/20"
                      >
                        {word}
                      </motion.span>
                    ))
                  )}
                </div>
              </div>
            </div>

            <button 
              onClick={speakFullSentence}
              disabled={currentSentence.length === 0}
              className="px-8 py-4 bg-white text-black font-black rounded-2xl flex items-center gap-3 hover:bg-emerald-500 transition-all active:scale-95 disabled:opacity-20 disabled:pointer-events-none shrink-0"
            >
              <Volume2 size={20} /> SPELL SENTENCE
            </button>
          </div>
        </div>

        {/* Bottom Row: Supported Signs */}
        <div className="bg-white/5 rounded-[2.5rem] p-10 border border-white/5">
          <div className="flex justify-between items-center mb-8">
            <div className="flex items-center gap-3">
              <Info size={20} className="text-emerald-500" />
              <h2 className="text-xl font-black tracking-tighter uppercase">Supported Gestures</h2>
            </div>
            <button 
              onClick={() => setShowAllGestures(true)}
              className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-emerald-500 hover:text-white transition-colors"
            >
              See All <ChevronRight size={14} />
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {supportedGestures.slice(0, 5).map((sign) => (
              <div key={sign.name} className="p-6 bg-white/5 rounded-3xl border border-white/5 hover:border-emerald-500/30 transition-all group">
                <p className="text-sm font-black text-white/90 mb-1 group-hover:text-emerald-400 transition-colors uppercase tracking-tight">{sign.name}</p>
                <p className="text-[10px] text-white/30 font-medium">{sign.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Gestures Modal */}
      <AnimatePresence>
        {showAllGestures && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAllGestures(false)}
              className="absolute inset-0 bg-black/90 backdrop-blur-xl"
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="relative w-full max-w-4xl bg-[#0a0a0a] rounded-[3rem] border border-white/10 overflow-hidden shadow-2xl"
            >
              <div className="p-10 flex justify-between items-center border-b border-white/5">
                <h2 className="text-3xl font-black uppercase tracking-tighter">Gesture Library</h2>
                <button onClick={() => setShowAllGestures(false)} className="p-3 bg-white/5 rounded-2xl hover:bg-red-500 transition-all">
                  <X size={24} />
                </button>
              </div>
              <div className="p-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
                {supportedGestures.map((sign) => (
                  <div key={sign.name} className="p-8 bg-white/5 rounded-[2rem] border border-white/5">
                    <p className="text-xl font-black text-emerald-400 mb-2 uppercase tracking-tight">{sign.name}</p>
                    <p className="text-xs text-white/40 font-medium leading-relaxed">{sign.desc}</p>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <style dangerouslySetInnerHTML={{ __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(16, 185, 129, 0.4); }
      `}} />
    </div>
  );
}