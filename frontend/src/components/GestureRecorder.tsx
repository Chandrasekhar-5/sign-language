import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, Square, Play, Trash2, Save, Download, Upload, Clock } from 'lucide-react';
import { cn } from '../lib/utils';

interface RecordedSequence {
  id: string;
  name: string;
  gestures: string[];
  timestamp: number;
  duration: number;
}

interface GestureRecorderProps {
  onSequenceRecorded?: (sequence: string[]) => void;
  onSequencePlayback?: (gesture: string) => void;
}

export const GestureRecorder: React.FC<GestureRecorderProps> = ({ 
  onSequenceRecorded, 
  onSequencePlayback 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedGestures, setRecordedGestures] = useState<string[]>([]);
  const [savedSequences, setSavedSequences] = useState<RecordedSequence[]>([]);
  const [recordingStartTime, setRecordingStartTime] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedSequence, setSelectedSequence] = useState<RecordedSequence | null>(null);
  
  const playbackInterval = useRef<NodeJS.Timeout | null>(null);
  
  const startRecording = useCallback(() => {
    setRecordedGestures([]);
    setIsRecording(true);
    setRecordingStartTime(Date.now());
  }, []);
  
  const stopRecording = useCallback(() => {
    setIsRecording(false);
    const duration = (Date.now() - recordingStartTime) / 1000;
    
    if (recordedGestures.length > 0 && onSequenceRecorded) {
      onSequenceRecorded(recordedGestures);
    }
    
    // Save to local storage
    const newSequence: RecordedSequence = {
      id: Date.now().toString(),
      name: `Sequence ${savedSequences.length + 1}`,
      gestures: [...recordedGestures],
      timestamp: Date.now(),
      duration: duration
    };
    
    setSavedSequences(prev => [newSequence, ...prev].slice(0, 20));
    localStorage.setItem('gesture_sequences', JSON.stringify([newSequence, ...savedSequences]));
  }, [recordedGestures, recordingStartTime, savedSequences, onSequenceRecorded]);
  
  const addGesture = useCallback((gesture: string) => {
    if (isRecording && gesture !== 'None') {
      setRecordedGestures(prev => {
        // Don't add duplicate consecutive gestures
        if (prev[prev.length - 1] === gesture) return prev;
        return [...prev, gesture];
      });
    }
  }, [isRecording]);
  
  const playSequence = useCallback((sequence: RecordedSequence) => {
    if (isPlaying) return;
    
    setIsPlaying(true);
    setSelectedSequence(sequence);
    
    let index = 0;
    playbackInterval.current = setInterval(() => {
      if (index >= sequence.gestures.length) {
        clearInterval(playbackInterval.current!);
        setIsPlaying(false);
        setSelectedSequence(null);
        return;
      }
      
      if (onSequencePlayback) {
        onSequencePlayback(sequence.gestures[index]);
      }
      index++;
    }, 800); // Play each gesture every 800ms
  }, [isPlaying, onSequencePlayback]);
  
  const stopPlayback = useCallback(() => {
    if (playbackInterval.current) {
      clearInterval(playbackInterval.current);
      playbackInterval.current = null;
    }
    setIsPlaying(false);
    setSelectedSequence(null);
  }, []);
  
  const deleteSequence = useCallback((id: string) => {
    setSavedSequences(prev => prev.filter(s => s.id !== id));
    localStorage.setItem('gesture_sequences', JSON.stringify(savedSequences.filter(s => s.id !== id)));
  }, [savedSequences]);
  
  const exportSequences = useCallback(() => {
    const data = JSON.stringify(savedSequences, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gesture_sequences_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [savedSequences]);
  
  const importSequences = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const sequences = JSON.parse(e.target?.result as string);
        setSavedSequences(prev => [...sequences, ...prev].slice(0, 20));
        localStorage.setItem('gesture_sequences', JSON.stringify([...sequences, ...savedSequences]));
      } catch (error) {
        console.error('Error importing sequences:', error);
      }
    };
    reader.readAsText(file);
  }, [savedSequences]);
  
  // Listen for gesture detections
  React.useEffect(() => {
    const handleGestureDetected = (event: CustomEvent) => {
      if (isRecording) {
        addGesture(event.detail.gesture);
      }
    };
    
    window.addEventListener('gestureDetected', handleGestureDetected as EventListener);
    return () => {
      window.removeEventListener('gestureDetected', handleGestureDetected as EventListener);
    };
  }, [isRecording, addGesture]);
  
  return (
    <div className="bg-white/5 rounded-4xl p-6 border border-white/5">
      <h3 className="text-lg font-black mb-4 flex items-center gap-2">
        <Mic size={18} className="text-emerald-500" />
        Gesture Recorder
      </h3>
      
      {/* Recording Controls */}
      <div className="flex gap-3 mb-6">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex-1 py-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-500 font-black flex items-center justify-center gap-2 hover:bg-red-500/30 transition-all"
          >
            <Mic size={18} /> Start Recording
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="flex-1 py-3 bg-red-500 rounded-xl text-white font-black flex items-center justify-center gap-2 animate-pulse"
          >
            <Square size={18} fill="currentColor" /> Stop Recording
          </button>
        )}
        
        <button
          onClick={exportSequences}
          className="px-4 py-3 bg-white/10 rounded-xl hover:bg-white/20 transition-all"
          title="Export sequences"
        >
          <Download size={18} />
        </button>
        
        <label className="px-4 py-3 bg-white/10 rounded-xl hover:bg-white/20 transition-all cursor-pointer">
          <Upload size={18} />
          <input type="file" accept=".json" onChange={importSequences} className="hidden" />
        </label>
      </div>
      
      {/* Recording Status */}
      {isRecording && (
        <div className="mb-6 p-4 bg-red-500/10 rounded-2xl border border-red-500/20">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-mono text-red-500">Recording...</span>
            <span className="text-xs font-mono text-white/40">
              {Math.floor((Date.now() - recordingStartTime) / 1000)}s
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {recordedGestures.map((gesture, i) => (
              <span key={i} className="px-2 py-1 bg-red-500/20 rounded-lg text-xs font-mono">
                {gesture}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Saved Sequences */}
      <div className="space-y-3 max-h-96 overflow-y-auto custom-scrollbar">
        {savedSequences.length === 0 ? (
          <div className="text-center py-8 text-white/40 text-sm">
            No saved sequences. Record your first gesture sequence!
          </div>
        ) : (
          savedSequences.map((sequence) => (
            <motion.div
              key={sequence.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "p-4 bg-white/5 rounded-2xl border transition-all",
                selectedSequence?.id === sequence.id && isPlaying
                  ? "border-emerald-500 bg-emerald-500/10"
                  : "border-white/5 hover:border-white/10"
              )}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-black text-sm">{sequence.name}</h4>
                  <div className="flex items-center gap-2 text-xs text-white/40 mt-1">
                    <Clock size={12} />
                    <span>{sequence.duration.toFixed(1)}s</span>
                    <span>•</span>
                    <span>{sequence.gestures.length} gestures</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => playSequence(sequence)}
                    disabled={isPlaying}
                    className="p-2 bg-emerald-500/20 rounded-lg hover:bg-emerald-500/30 transition-all disabled:opacity-50"
                  >
                    <Play size={14} />
                  </button>
                  <button
                    onClick={() => deleteSequence(sequence.id)}
                    className="p-2 bg-red-500/20 rounded-lg hover:bg-red-500/30 transition-all"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {sequence.gestures.slice(0, 5).map((gesture, i) => (
                  <span key={i} className="px-2 py-0.5 bg-white/10 rounded text-xs">
                    {gesture}
                  </span>
                ))}
                {sequence.gestures.length > 5 && (
                  <span className="px-2 py-0.5 text-xs text-white/40">
                    +{sequence.gestures.length - 5}
                  </span>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>
      
      {/* Playback Status */}
      {isPlaying && selectedSequence && (
        <div className="fixed bottom-8 right-8 z-50 p-4 bg-black/90 backdrop-blur-xl rounded-2xl border border-emerald-500/30 shadow-2xl">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-sm font-mono">Playing: {selectedSequence.name}</span>
            <button onClick={stopPlayback} className="p-1 hover:bg-white/10 rounded">
              <Square size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};