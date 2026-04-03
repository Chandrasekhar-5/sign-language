<div align="center">
  
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/MediaPipe-00C853?style=for-the-badge&logo=google&logoColor=white" alt="MediaPipe" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Framer_Motion-0055FF?style=for-the-badge&logo=framer&logoColor=white" alt="Framer Motion" />
  
  <br />
  <br />
  
  <h1>🤟 SignAI Pro</h1>
  <h3>Real-Time Sign Language Translation System</h3>
  
  <p>
    <strong>Translate sign language gestures into natural speech instantly.</strong>
    🔗 GitHub Repository: https://github.com/Chandrasekhar-5/sign-language
  </p>
  
  <br />
  
  <img src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" alt="SignAI Pro Banner" width="800" />
  
  <br />
  <br />
  
  <a href="https://sign-language-psi.vercel.app/">
    <img src="https://img.shields.io/badge/Live_Demo-00C853?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Demo" />
  </a>
  
  <a href="#quick-start">
    <img src="https://img.shields.io/badge/Quick_Start-007ACC?style=for-the-badge&logo=github&logoColor=white" alt="Quick Start" />
  </a>
  
  <a href="#features">
    <img src="https://img.shields.io/badge/Features-FF6B6B?style=for-the-badge&logo=feature&logoColor=white" alt="Features" />
  </a>
  
</div>

---

## 🎯 Overview

**SignAI Pro** is a cutting-edge, real-time sign language translation system that bridges the communication gap between sign language users and the hearing world. Using advanced computer vision and machine learning, it recognizes hand gestures and converts them into natural, spoken sentences.

### Why SignAI Pro?

| Feature | Benefit |
|---------|---------|
| 🚀 **Real-Time Processing** | < 50ms latency - feels instant |
| 🎯 **12+ Gestures Recognized** | Comprehensive vocabulary for daily use |
| 🧠 **Smart Sentence Building** | Context-based sentence builder |
| 🔊 **Text-to-Speech** | Audible output for seamless communication |
| 💻 **Browser-Based** | No installation, works on any device |
| 🔒 **Privacy First** | All processing happens locally - no video uploads |

---

## ✨ Features

### Core Capabilities

<div align="center">
  
| Gesture | Meaning | Demo Sentence |
|---------|---------|---------------|
| 👋 | Hello | "Hello, how are you today?" |
| ✋ | Stop | "Stop right there." |
| ✊ | Yes | "Yes, absolutely!" |
| 🤌 | No | "No, thank you." |
| 🤚 | Thank You | "Thank you so much!" |
| 👍 | Thumbs Up | "Great job!" |
| ☝️ | Point | "Look over there." |
| ✌️ | Peace | "Peace out!" |
| 👌 | OK | "Okay, sounds good." |
| 🤘 | Rock On | "Rock on, you're awesome!" |
| 🤙 | Call Me | "Please give me a call." |
| 👎 | Dislike | "I don't like that." |

</div>

## ⚠️ Limitations

- Works best with single-hand gestures
- Sensitive to lighting conditions
- Limited gesture vocabulary (12+)
- No continuous sign language recognition yet

## 🚀 Future Improvements

- Deep learning model (LSTM / Transformer)
- Continuous sign recognition (not just static gestures)
- Multi-language speech output
- Mobile app version

### Advanced Features

- 🎬 **Gesture Recording** - Record and save gesture sequences
- 📝 **Sentence Builder** - Combine multiple gestures into natural sentences
- 🔄 **Smart Suggestions** - Predefined intelligent gesture combinations
- 📊 **Performance Metrics** - Real-time FPS and confidence scores
- 🎯 **Green Box Tracking** - Visual feedback for hand detection
- 🔊 **Adjustable Speech** - Toggle text-to-speech on/off
- 📜 **History Log** - Track all translated sentences

---

## 🎮 Live Demo Sentences

Try these impressive sentence combinations:
👋 + ☝️ + 👍 → "Hello, how are you today?"
🤚 + 👍 → "Thank you, I really appreciate that!"
👌 + 👍 → "Okay, that sounds great!"
✊ + 🤚 → "Yes, thank you very much!"
🤘 + 👍 → "Awesome, you're doing a fantastic job!"
🤙 + 👍 → "Please call me, that would be wonderful."


---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- npm or yarn
- A webcam

### Installation

```bash
# Clone the repository
git clone https://github.com/Chandrasekhar-5/sign-language.git

# Navigate to project
cd sign-language-translator

# Install dependencies
npm install

# Start development server
npm run dev

Open http://localhost:3000 and grant camera access.

Building for Production
bash
npm run build
The built files will be in the dist directory.

🏗️ Architecture

┌─────────────────────────────────────────────────────────────┐
│                         Browser                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Webcam    │→ │ MediaPipe   │→ │  Gesture Recognition│  │
│  │   Input     │  │Hand Tracking│  │(Rule based+landmark)│  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         ↓                ↓                    ↓             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Green Box  │  │ Landmark    │  │    NLP Sentence     │  │
│  │  Detection  │  │Visualization│  │      Builder        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         ↓                                ↓                  │
│  ┌─────────────┐                   ┌─────────────────────┐  │
│  │   Canvas    │                   │    Text-to-Speech   │  │
│  │   Render    │                   │       Output        │  │
│  └─────────────┘                   └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘


## Tech Stack 
Technology	        Purpose
React 19	         UI Framework
TypeScript	       Type Safety
MediaPipe	   Hand Landmark Detection
Tailwind CSS	      Styling
Framer Motion	     Animations
Web Speech API	   Text-to-Speech


📁 Project Structure
sign-language-translator/
├── src/
│   ├── App.tsx 
│   ├── gestureLogic.ts
│   ├── types.ts
│   ├── lib/
│   │   └── utils.ts
│   └── index.css
├── public/
│   └── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md

🎯 Gesture Recognition Logic
The system uses MediaPipe Hands for 21-point hand landmark detection and a rule-based algorithm for gesture classification:

// Example: Peace Sign Detection
if (indexExtended && middleExtended && !ringExtended && !pinkyExtended) {
  const spread = Math.abs(landmarks[8].x - landmarks[12].x);
  if (spread > 0.05) return "Peace";
}

Recognized Features
Finger extension states

Thumb position (up/down)

Finger distances and angles

Hand orientation

Inter-finger relationships


📊 Performance
Metric	Value
Frame Processing	< 50ms
Gesture Detection	30 FPS
Model Loading	< 2 seconds
Memory Usage	~150MB
Bundle Size	~2.5MB


📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
MediaPipe - Hand tracking technology

Google AI - Research and inspiration

Tailwind CSS - Styling framework

Framer Motion - Animations

<div align="center"> <img src="https://img.shields.io/github/stars/Chandrasekhar-5/sign-language?style=social" alt="GitHub stars" /> <img src="https://img.shields.io/github/forks/Chandrasekhar-5/sign-language?style=social" alt="GitHub forks" /> <br />
<sub>⭐ Star this repo if you find it useful!</sub>

</div>