from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import io
import tempfile
import os
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr
from typing import Optional
import base64
from utils.logger import agent_logger
from config import config
import json
import wave
from vosk import Model, KaldiRecognizer

app = FastAPI(title="Voice Agent", description="Handles speech-to-text and text-to-speech")

class TTSRequest(BaseModel):
    text: str
    language: str = "en"
    slow: bool = False

class VoiceAgent:
    """Agent responsible for voice processing operations."""
    
    def __init__(self):
        # Initialize Vosk model for speech recognition
        model_path = self.download_vosk_model(config.VOSK_MODEL)
        self.vosk_model = Model(model_path)
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        agent_logger.info("Voice Agent initialized with Vosk")
    
    def download_vosk_model(self, model_size="small"):
        """Download Vosk model if not already present."""
        import os
        import urllib.request
        import zipfile
        
        # Define model paths and URLs
        model_urls = {
            "small": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "medium": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            "large": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.42.zip"
        }
        
        model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f"vosk-model-{model_size}")
        
        # Check if model already exists
        if os.path.exists(model_path):
            return model_path
        
        # Download and extract model
        agent_logger.info(f"Downloading Vosk {model_size} model...")
        zip_path = os.path.join(model_dir, f"vosk-model-{model_size}.zip")
        
        urllib.request.urlretrieve(model_urls[model_size], zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        
        # Rename extracted folder to standard name
        extracted_dir = os.path.join(model_dir, os.path.basename(model_urls[model_size]).replace(".zip", ""))
        if os.path.exists(extracted_dir) and extracted_dir != model_path:
            os.rename(extracted_dir, model_path)
        
        # Clean up zip file
        os.remove(zip_path)
        
        agent_logger.info(f"Vosk {model_size} model downloaded and extracted to {model_path}")
        return model_path
    
    async def speech_to_text(self, audio_file: bytes) -> str:
        """Convert speech to text using Vosk."""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_file)
                temp_file_path = temp_file.name
            
            try:
                # Convert to proper format for Vosk if needed
                wf = wave.open(temp_file_path, "rb")
                
                # Check if we need to convert the audio
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                    # Convert to mono 16-bit PCM
                    audio = AudioSegment.from_wav(temp_file_path)
                    audio = audio.set_channels(1)
                    audio = audio.set_frame_rate(16000)
                    audio.export(temp_file_path, format="wav")
                    wf = wave.open(temp_file_path, "rb")
                
                # Process with Vosk
                rec = KaldiRecognizer(self.vosk_model, wf.getframerate())
                
                results = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        part_result = json.loads(rec.Result())
                        results.append(part_result.get('text', ''))
                
                # Get final result
                part_result = json.loads(rec.FinalResult())
                results.append(part_result.get('text', ''))
                
                transcription = ' '.join(results).strip()
                
                agent_logger.info(f"Transcribed: {transcription[:100]}...")
                return transcription
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            agent_logger.error(f"Error in speech-to-text: {e}")
            return ""
    
    async def text_to_speech(self, text: str, language: str = "en", slow: bool = False) -> bytes:
        """Convert text to speech using gTTS."""
        try:
            # Create TTS object
            tts = gTTS(text=text, lang=language, slow=slow)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                tts.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Read the audio file
                with open(temp_file_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                agent_logger.info(f"Generated TTS for text: {text[:50]}...")
                return audio_data
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            agent_logger.error(f"Error in text-to-speech: {e}")
            return b""
    
    async def process_voice_input(self, audio_file: bytes) -> dict:
        """Process voice input and return transcription with metadata."""
        try:
            transcription = await self.speech_to_text(audio_file)
            
            if not transcription:
                return {
                    "transcription": "",
                    "success": False,
                    "error": "Could not transcribe audio"
                }
            
            # Analyze the transcription for intent
            intent = self.analyze_intent(transcription)
            
            return {
                "transcription": transcription,
                "intent": intent,
                "success": True,
                "confidence": 0.9  # Placeholder confidence score
            }
            
        except Exception as e:
            agent_logger.error(f"Error processing voice input: {e}")
            return {
                "transcription": "",
                "success": False,
                "error": str(e)
            }
    
    def analyze_intent(self, text: str) -> dict:
        """Analyze the intent of the transcribed text."""
        text_lower = text.lower()
        
        # Simple intent classification
        if any(word in text_lower for word in ["risk", "exposure", "portfolio"]):
            return {"type": "risk_analysis", "confidence": 0.8}
        elif any(word in text_lower for word in ["earnings", "surprise", "beat", "miss"]):
            return {"type": "earnings_analysis", "confidence": 0.8}
        elif any(word in text_lower for word in ["market", "brief", "update", "news"]):
            return {"type": "market_brief", "confidence": 0.8}
        elif any(word in text_lower for word in ["asia", "tech", "technology"]):
            return {"type": "sector_analysis", "confidence": 0.7}
        else:
            return {"type": "general_query", "confidence": 0.5}
    
    async def create_voice_response(self, text: str) -> bytes:
        """Create a voice response from text."""
        try:
            # Clean up text for better TTS
            cleaned_text = self.clean_text_for_tts(text)
            
            # Generate speech
            audio_data = await self.text_to_speech(cleaned_text)
            
            return audio_data
            
        except Exception as e:
            agent_logger.error(f"Error creating voice response: {e}")
            return b""
    
    def clean_text_for_tts(self, text: str) -> str:
        """Clean text to make it more suitable for TTS."""
        # Remove markdown formatting
        text = text.replace("**", "").replace("*", "")
        
        # Replace symbols with words
        text = text.replace("%", " percent")
        text = text.replace("$", " dollars")
        text = text.replace("&", " and")
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        return text

# Initialize agent
voice_agent = VoiceAgent()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "Voice Agent"}

@app.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """Convert uploaded audio to text."""
    try:
        audio_data = await audio_file.read()
        result = await voice_agent.process_voice_input(audio_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text-to-speech")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech."""
    try:
        audio_data = await voice_agent.text_to_speech(
            request.text, 
            request.language, 
            request.slow
        )
        
        # Encode audio data as base64 for JSON response
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "text": request.text,
            "language": request.language
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-voice")
async def process_voice(audio_file: UploadFile = File(...)):
    """Process voice input and return transcription with intent."""
    try:
        audio_data = await audio_file.read()
        result = await voice_agent.process_voice_input(audio_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-response")
async def create_voice_response(request: TTSRequest):
    """Create a voice response from text."""
    try:
        audio_data = await voice_agent.create_voice_response(request.text)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "audio_data": audio_base64,
            "original_text": request.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.VOICE_AGENT_PORT)
