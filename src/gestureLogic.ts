import { GESTURES, HandLandmark } from "./types";

/**
 * Heuristic-based gesture recognition logic.
 * Calculates distances and relative positions of hand landmarks to predict gestures.
 */
export function recognizeGesture(landmarks: HandLandmark[]): string {
  if (!landmarks || landmarks.length < 21) return GESTURES.NONE;

  // Helper to check if a finger is extended (distance from wrist)
  const isExtended = (tipIdx: number, pipIdx: number) => {
    const distTip = Math.sqrt(
      Math.pow(landmarks[tipIdx].x - landmarks[0].x, 2) + 
      Math.pow(landmarks[tipIdx].y - landmarks[0].y, 2)
    );
    const distPip = Math.sqrt(
      Math.pow(landmarks[pipIdx].x - landmarks[0].x, 2) + 
      Math.pow(landmarks[pipIdx].y - landmarks[0].y, 2)
    );
    // Standard check: Tip is further from wrist than PIP joint
    // Also add a vertical check for upright hands
    const isUpright = landmarks[tipIdx].y < landmarks[pipIdx].y;
    return (distTip > distPip * 1.15) || isUpright;
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

  // 1. THUMBS UP: Thumb tip is highest and far from palm
  const thumbTip = landmarks[4];
  const thumbBase = landmarks[2];
  const thumbExtended = getDist(4, 0) > getDist(2, 0) * 1.1;
  const thumbUp = thumbTip.y < landmarks[2].y && thumbExtended && !indexExtended && !middleExtended;

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
  if (distThumbIndex < 0.08 && middleExtended && ringExtended && pinkyExtended) {
    return GESTURES.OK;
  }

  // 5. NO: Index and Middle extended but close to thumb (pinching motion)
  if (indexExtended && middleExtended && !ringExtended && !pinkyExtended && distThumbIndex < 0.15) {
    return GESTURES.NO;
  }

  // 6. YES (Fist): All fingers folded
  if (!indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
    return GESTURES.YES;
  }

  // 7. STOP: All fingers extended and together
  const fingersTogether = getDist(8, 12) < 0.1 && getDist(12, 16) < 0.1 && getDist(16, 20) < 0.1;
  if (indexExtended && middleExtended && ringExtended && pinkyExtended && fingersTogether) {
    return GESTURES.STOP;
  }

  // 8. HELLO: All fingers extended and spread
  if (indexExtended && middleExtended && ringExtended && pinkyExtended && !fingersTogether) {
    return GESTURES.HELLO;
  }

  // 9. THANK YOU: Flat hand, thumb tucked or slightly out
  if (indexExtended && middleExtended && ringExtended && pinkyExtended && landmarks[4].y > landmarks[8].y) {
     return GESTURES.THANK_YOU;
  }

  return GESTURES.NONE;
}
