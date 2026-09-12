import os
import numpy as np
import xarray as xr
from scipy.io import wavfile

from typing import Any

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc

class HLAudioLoader(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return []
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Audio", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: Any) -> None:
        pass
        
    def handle_new_signals(self) -> None:
        file_path = self.settings.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            self.send("Audio", None)
            return
            
        try:
            samplerate, data = wavfile.read(file_path)
            
            # Ensure data is 2D (time, channel)
            if data.ndim == 1:
                data = data[:, np.newaxis]
                
            # Convert to xarray.DataArray
            da = xr.DataArray(
                data, 
                dims=["time", "channel"], 
                name="audio",
                attrs={"samplerate": samplerate}
            )
            self.send("Audio", da)
        except Exception as e:
            self.send("Audio", None)
            raise RuntimeError(f"Failed to load audio: {e}")

class HLAudioSaver(HeadlessWidget):
    def __init__(self, node_id: str, orchestrator):
        super().__init__(node_id, orchestrator)
        self.audio = None
        
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Audio", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return []
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Audio":
            self.audio = value
            
    def handle_new_signals(self) -> None:
        file_path = self.settings.get("file_path", "")
        if self.audio is None or not file_path:
            return
            
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(os.path.abspath(file_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            data = self.audio.values
            
            # scipy.io.wavfile expects (time, channels) or (time,)
            if data.ndim == 2 and data.shape[1] == 1:
                data = data.squeeze(axis=1)
                
            # Default to 44100 if samplerate is missing
            samplerate = self.audio.attrs.get("samplerate", 44100)
            
            wavfile.write(file_path, samplerate, data)
        except Exception as e:
            raise RuntimeError(f"Failed to save audio: {e}")
