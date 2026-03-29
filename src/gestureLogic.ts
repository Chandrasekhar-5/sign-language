import { GESTURES, HandLandmark } from "./types";

/**
 * Heuristic-based gesture recognition logic.
 * Calculates distances and relative positions of hand landmarks to predict gestures.
 */
export function recognizeGesture(landmarks: HandLandmark[]): string {
  if (!landmarks || landmarks.length < 21) return GESTURES.NONE;

  // Helper to check if a finger is extended
  const isExtended = (tipIdx: number, pipIdx: number) => {
    return landmarks[tipIdx].y < landmarks[pipIdx].y;
  };

  const indexExtended = isExtended(8, 6);
  const middleExtended = isExtended(12, 10);
  const ringExtended = isExtended(16, 14);
  const pinkyExtended = isExtended(20, 18);
  
  // Distance helper
  const getDist = (p1: number, p2: number) => {
    return Math.sqrt(
      Math.pow(landmarks[p1].x - landmarks[p2].x, 2) + 
      Math.pow(landmarks[p1].y - landmarks[p2].y, 2)
    );
  };

  // 1. THUMBS UP: Thumb extended, others folded
  const thumbUp = landmarks[4].y < landmarks[3].y && 
                  landmarks[8].y > landmarks[6].y && 
                  landmarks[12].y > landmarks[10].y &&
                  landmarks[16].y > landmarks[14].y;
  if (thumbUp) return GESTURES.THUMBS_UP;

  // 2. POINT: Index extended, others folded
  if (indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
    return GESTURES.POINT;
  }

  // 3. PEACE: Index and Middle extended, others folded
  if (indexExtended && middleExtended && !ringExtended && !pinkyExtended) {
    return GESTURES.PEACE;
  }

  // 4. OK: Thumb and Index tips are close, others extended
  const distThumbIndex = getDist(4, 8);
  if (distThumbIndex < 0.05 && middleExtended && ringExtended && pinkyExtended) {
    return GESTURES.OK;
  }

  // 5. NO: Index and Middle extended but close to thumb (pinching motion)
  if (indexExtended && middleExtended && !ringExtended && !pinkyExtended && distThumbIndex < 0.1) {
    return GESTURES.NO;
  }

  // 6. YES (Fist): All fingers folded
  if (!indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
    return GESTURES.YES;
  }

  // 7. THANK YOU: Fingers together, hand slightly tilted (simplified for static)
  // Often represented as a flat hand near the mouth, but here we'll use a specific flat hand pose
  const fingersTogether = getDist(8, 12) < 0.05 && getDist(12, 16) < 0.05 && getDist(16, 20) < 0.05;
  if (indexExtended && middleExtended && ringExtended && pinkyExtended && fingersTogether) {
    // Distinguish between HELLO and STOP
    // STOP: Fingers together, palm flat
    // HELLO: Fingers spread
    return GESTURES.STOP;
  }

  if (indexExtended && middleExtended && ringExtended && pinkyExtended && !fingersTogether) {
    return GESTURES.HELLO;
  }

  // 8. THANK YOU (Alternative pose: flat hand tilted)
  if (indexExtended && middleExtended && ringExtended && pinkyExtended && landmarks[4].y > landmarks[3].y) {
     // If thumb is tucked in and fingers are flat, we can call it Thank You for this demo
     return GESTURES.THANK_YOU;
  }

  return GESTURES.NONE;
}
