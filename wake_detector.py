import numpy as np
import pyaudio
from openwakeword.model import Model

class DetectorWakeWord:
    def __init__(self, modelo="hey_jarvis"):
        # openWakeWord incluye modelos como 'hey_jarvis', 'alexa', 'marvin', etc.
        self.model = Model(wakeword_models=[modelo], inference_framework="onnx")
        self.chunk_size = 1280
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000

    def esperar_activacion(self, umbral=0.5) -> bool:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        print("\n[Modo reposo: Esperando 'Hey JARVIS'...]")

        try:
            while True:
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)

                # Evaluar fragmento de audio
                prediction = self.model.predict(audio_data)

                for nombre_modelo, puntaje in prediction.items():
                    if puntaje >= umbral:
                        print("\n¡Palabra de activación detectada!")
                        stream.stop_stream()
                        stream.close()
                        audio.terminate()
                        return True
        except KeyboardInterrupt:
            stream.stop_stream()
            stream.close()
            audio.terminate()
            return False