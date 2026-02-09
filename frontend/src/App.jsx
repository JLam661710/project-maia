import { useEffect, useState, useRef } from 'react'
import MaiaCanvas from './components/MaiaCanvas'
import { AudioStreamPlayer } from './utils/audioStreamPlayer'
import { AudioRecorder } from './utils/audioRecorder'
import './App.css'

function App() {
  const [status, setStatus] = useState("Connecting...")
  const [asrText, setAsrText] = useState("")
  const [isRecording, setIsRecording] = useState(false)
  
  const playerRef = useRef(new AudioStreamPlayer())
  const recorderRef = useRef(new AudioRecorder())
  
  // Two WebSockets: one for TTS, one for ASR
  const ttsWsRef = useRef(null)
  const asrWsRef = useRef(null)

  useEffect(() => {
    // 1. Connect TTS WebSocket
    const ttsWs = new WebSocket("ws://localhost:8000/ws/tts")
    ttsWsRef.current = ttsWs
    ttsWs.binaryType = "arraybuffer"

    ttsWs.onopen = () => {
      setStatus("TTS Connected. Ready.")
    }

    ttsWs.onmessage = async (event) => {
      if (event.data instanceof ArrayBuffer) {
        playerRef.current.playChunk(event.data)
        setStatus("Maia Speaking...")
      } else {
        try {
            const msg = JSON.parse(event.data)
            if(msg.type === 'status' && msg.content === 'done') {
                setStatus("Finished speaking.")
            }
        } catch (e) {
            void e
        }
      }
    }

    ttsWs.onclose = () => console.log("TTS Disconnected")
    
    // Cleanup
    return () => {
      ttsWs.close()
      if(asrWsRef.current) asrWsRef.current.close()
    }
  }, [])

  // Toggle Recording (ASR)
  const toggleRecording = async (e) => {
    e.stopPropagation(); // Prevent triggering background click

    if (isRecording) {
      // STOP Recording
      setIsRecording(false)
      setStatus("Processing...")
      
      // Stop Recorder
      recorderRef.current.stop()
      
      // Send STOP signal to backend
      if (asrWsRef.current && asrWsRef.current.readyState === WebSocket.OPEN) {
        asrWsRef.current.send("STOP")
      }

    } else {
      // START Recording
      try {
        // Ensure Audio Context (for playback) is ready
        playerRef.current.init()

        // Init ASR WebSocket
        const asrWs = new WebSocket("ws://localhost:8000/ws/asr")
        asrWsRef.current = asrWs
        asrWs.binaryType = "arraybuffer" // Although we receive text results mostly

        asrWs.onopen = async () => {
           console.log("ASR Connected")
           setStatus("Listening...")
           setIsRecording(true)
           setAsrText("") // Clear previous text

           // Start Mic
           await recorderRef.current.start((pcmData) => {
               // Send PCM chunks
               if (asrWs.readyState === WebSocket.OPEN) {
                   asrWs.send(pcmData.buffer)
               }
           })
        }

        asrWs.onmessage = (event) => {
           // We expect text results (JSON strings)
           try {
               const data = JSON.parse(event.data)
               // Format: { result: { text: "...", utterances: [...] } }
               if (data.result && data.result.text) {
                   setAsrText(data.result.text)
               }
           } catch (e) {
               console.error("ASR Parse Error", e)
           }
        }

        asrWs.onclose = () => {
            console.log("ASR Closed")
            setIsRecording(false)
            setStatus("ASR Session Ended")
        }
        
        asrWs.onerror = (e) => {
            console.error("ASR Error", e)
            setStatus("ASR Error")
            setIsRecording(false)
        }

      } catch (e) {
        console.error("Failed to start recording", e)
        setStatus("Mic Error: " + e.message)
      }
    }
  }

  // TTS Test (Click background)
  const handleTestTTS = () => {
    if (isRecording) return; // Don't speak while listening
    
    if (ttsWsRef.current && ttsWsRef.current.readyState === WebSocket.OPEN) {
      const text = "你好，我是 Maia。点击下方按钮，告诉我你想聊什么。"
      ttsWsRef.current.send(JSON.stringify({ text, format: "pcm" }))
      setStatus("Requesting TTS...")
      playerRef.current.init()
    }
  }

  const getAudioData = () => {
      return playerRef.current.getAudioData();
  }

  return (
    <div className="app-container" onClick={handleTestTTS}>
      <MaiaCanvas getAudioData={getAudioData} />
      
      <div className="ui-overlay">
        <h1 className="title">Maia</h1>
        <p className="status">{status}</p>
        
        {/* ASR Result Display */}
        {asrText && (
            <div className="asr-result">
                &quot;{asrText}&quot;
            </div>
        )}

        {/* Mic Button */}
        <button 
            className={`mic-button ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
        >
            {isRecording ? "Stop" : "Speak"}
        </button>
      </div>
    </div>
  )
}

export default App
