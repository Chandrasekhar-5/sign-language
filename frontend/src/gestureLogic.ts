import { GESTURES, HandLandmark } from "./types";

export function recognizeGesture(landmarks: HandLandmark[]): string {
  if (!landmarks || landmarks.length < 21) return GESTURES.NONE;

  const getDist = (p1: number, p2: number) => {
    return Math.sqrt(
      Math.pow(landmarks[p1].x - landmarks[p2].x, 2) + 
      Math.pow(landmarks[p1].y - landmarks[p2].y, 2)
    );
  };

  const getFingerState = (tipIdx: number, pipIdx: number, mcpIdx: number): boolean => {
    const tipToWrist = getDist(tipIdx, 0);
    const mcpToWrist = getDist(mcpIdx, 0);
    return tipToWrist > mcpToWrist * 1.15;
  };

  const isThumbExtended = (): boolean => {
    const tipToWrist = getDist(4, 0);
    const mcpToWrist = getDist(2, 0);
    return tipToWrist > mcpToWrist * 1.25;
  };

  const thumbExtended = isThumbExtended();
  const indexExtended = getFingerState(8, 6, 5);
  const middleExtended = getFingerState(12, 10, 9);
  const ringExtended = getFingerState(16, 14, 13);
  const pinkyExtended = getFingerState(20, 18, 17);

  // Special checks for OK gesture
  const thumbTip = landmarks[4];
  const indexTip = landmarks[8];
  const thumbIndexDistance = Math.hypot(thumbTip.x - indexTip.x, thumbTip.y - indexTip.y);
  
  // Special check for Rock vs Love
  const rockPosition = !thumbExtended && indexExtended && !middleExtended && !ringExtended && pinkyExtended;
  const lovePosition = thumbExtended && indexExtended && !middleExtended && !ringExtended && pinkyExtended;

  // 1. OK GESTURE - Fixed: Thumb and index circle
  if (thumbIndexDistance < 0.08) {
    return GESTURES.OK;
  }

  // 2. ROCK ON - Index and pinky only (no thumb)
  if (rockPosition) {
    return GESTURES.ROCK;
  }

  // 3. THUMBS UP
  if (thumbExtended && !indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
    if (landmarks[4].y < landmarks[2].y) {
      return GESTURES.THUMBS_UP;
    }
    if (landmarks[4].y > landmarks[2].y) {
      return GESTURES.DISLIKE;
    }
  }

  // 4. POINT
  if (!thumbExtended && indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
    return GESTURES.POINT;
  }

  // 5. PEACE
  if (indexExtended && middleExtended && !ringExtended && !pinkyExtended) {
    const spread = Math.abs(landmarks[8].x - landmarks[12].x);
    if (spread > 0.05) {
      return GESTURES.PEACE;
    }
    if (spread < 0.04) {
      return GESTURES.NO;
    }
  }

  // 6. YES (Fist)
  if (!thumbExtended && !indexExtended && !middleExtended && !ringExtended && !pinkyExtended) {
    return GESTURES.YES;
  }

  // 7. STOP vs HELLO
  if (thumbExtended && indexExtended && middleExtended && ringExtended && pinkyExtended) {
    const spread = Math.abs(landmarks[8].x - landmarks[20].x);
    if (spread < 0.07) {
      return GESTURES.STOP;
    }
    if (spread >= 0.07) {
      return GESTURES.HELLO;
    }
  }

  // 8. THANK YOU
  if (!thumbExtended && indexExtended && middleExtended && ringExtended && pinkyExtended) {
    return GESTURES.THANK_YOU;
  }

  // 9. CALL ME
  if (thumbExtended && !indexExtended && !middleExtended && !ringExtended && pinkyExtended) {
    return GESTURES.CALL_ME;
  }

  return GESTURES.NONE;
}