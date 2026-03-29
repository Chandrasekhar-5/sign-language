import { GESTURES, HandLandmark } from "./types";

/**
 * Data-driven gesture recognition.
 * Instead of hardcoding logic for every sign, we define "Signatures"
 * which are patterns of which fingers are extended.
 */

interface GestureTemplate {
  name: string;
  signature: string; // 5-bit string: Thumb, Index, Middle, Ring, Pinky (1=Up, 0=Down)
  specialCheck?: (landmarks: HandLandmark[], dists: any) => boolean;
}

export function recognizeGesture(landmarks: HandLandmark[]): { gesture: string, signature: string } {
  if (!landmarks || landmarks.length < 21) return { gesture: GESTURES.NONE, signature: "00000" };

  // Distance helper
  const getDist = (p1: number, p2: number) => {
    return Math.sqrt(
      Math.pow(landmarks[p1].x - landmarks[p2].x, 2) + 
      Math.pow(landmarks[p1].y - landmarks[p2].y, 2)
    );
  };

  // 1. Calculate finger states (1 = Extended, 0 = Folded)
  // We compare tip distance from wrist vs pip distance from wrist
  const isExtended = (tipIdx: number, pipIdx: number) => {
    const distTip = getDist(tipIdx, 0);
    const distPip = getDist(pipIdx, 0);
    return distTip > distPip * 1.15;
  };

  // Thumb is special (horizontal distance from palm center)
  const thumbExtended = getDist(4, 0) > getDist(2, 0) * 1.3;
  
  const states = [
    thumbExtended ? "1" : "0",
    isExtended(8, 6) ? "1" : "0",
    isExtended(12, 10) ? "1" : "0",
    isExtended(16, 14) ? "1" : "0",
    isExtended(20, 18) ? "1" : "0"
  ];

  const signature = states.join("");

  // 2. Define the Library
  const GESTURE_LIBRARY: GestureTemplate[] = [
    { 
      name: GESTURES.THUMBS_UP, 
      signature: "10000",
      specialCheck: (l) => l[4].y < l[2].y // Thumb must be pointing up
    },
    { name: GESTURES.POINT, signature: "01000" },
    { 
      name: GESTURES.PEACE, 
      signature: "01100",
      specialCheck: (l) => getDist(8, 12) > 0.08 // Fingers must be spread
    },
    { 
      name: GESTURES.NO, 
      signature: "01100",
      specialCheck: (l) => getDist(8, 12) < 0.05 // Fingers must be close (pinching)
    },
    { 
      name: GESTURES.OK, 
      signature: "01111",
      specialCheck: (l) => getDist(4, 8) < 0.06 // Thumb and Index touching
    },
    { name: GESTURES.YES, signature: "00000" }, // Fist
    { 
      name: GESTURES.STOP, 
      signature: "11111",
      specialCheck: (l) => getDist(8, 12) < 0.05 // Fingers together
    },
    { 
      name: GESTURES.HELLO, 
      signature: "11111",
      specialCheck: (l) => getDist(8, 12) >= 0.05 // Fingers spread
    },
    { 
      name: GESTURES.THANK_YOU, 
      signature: "01111",
      specialCheck: (l) => getDist(4, 8) >= 0.06 // Flat hand, thumb tucked
    }
  ];

  // 3. Match against library
  for (const template of GESTURE_LIBRARY) {
    if (template.signature === signature) {
      if (!template.specialCheck || template.specialCheck(landmarks, {})) {
        return { gesture: template.name, signature };
      }
    }
  }

  return { gesture: GESTURES.NONE, signature };
}
