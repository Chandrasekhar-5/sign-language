export type Gesture = {
  name: string;
  confidence: number;
};

export type HandLandmark = {
  x: number;
  y: number;
  z: number;
};

export const GESTURES = {
  HELLO: "Hello",
  STOP: "Stop",
  YES: "Yes",
  NO: "No",
  THANK_YOU: "Thank You",
  THUMBS_UP: "Thumbs Up",
  POINT: "Point",
  PEACE: "Peace",
  OK: "OK",
  ROCK: "Rock On",
  CALL_ME: "Call Me",
  DISLIKE: "Dislike",
  NONE: "None",
};