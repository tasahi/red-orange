import os
import numpy as np
from PIL import Image
import xarray as xr
import scipy.ndimage as ndimage

from typing import Any

from ..headless_widget import HeadlessWidget
from ..schemas import SignalDesc

class HLImageLoader(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return []
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: Any) -> None:
        pass
        
        
    def handle_new_signals(self) -> None:
        file_path = self.settings.get("file_path", "")
        if not file_path or not os.path.exists(file_path):
            self.send("Image", None)
            return
            
        try:
            # Load image and convert to numpy array
            with Image.open(file_path) as img:
                # Convert to RGB if it's not already
                img = img.convert('RGB')
                arr = np.array(img)
                
            # Convert to xarray.DataArray
            da = xr.DataArray(arr, dims=["y", "x", "channel"], name="image")
            self.send("Image", da)
        except Exception as e:
            self.send("Image", None)
            raise RuntimeError(f"Failed to load image: {e}")


class HLImageFilters1D(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if not hasattr(self, 'image') or self.image is None:
            self.send("Image", None)
            return
            
        filter_type = self.settings.get("filter_type", "gaussian_filter1d")
        axis = int(self.settings.get("axis", -1))
        arr = self.image.values
        result_arr = np.zeros_like(arr)
        
        try:
            for c in range(arr.shape[2]):
                if filter_type == "gaussian_filter1d":
                    sigma = float(self.settings.get("sigma", 2.0))
                    result_arr[:, :, c] = ndimage.gaussian_filter1d(arr[:, :, c], sigma=sigma, axis=axis)
                elif filter_type == "maximum_filter1d":
                    size = int(self.settings.get("size", 3))
                    result_arr[:, :, c] = ndimage.maximum_filter1d(arr[:, :, c], size=size, axis=axis)
                elif filter_type == "minimum_filter1d":
                    size = int(self.settings.get("size", 3))
                    result_arr[:, :, c] = ndimage.minimum_filter1d(arr[:, :, c], size=size, axis=axis)
                elif filter_type == "uniform_filter1d":
                    size = int(self.settings.get("size", 3))
                    result_arr[:, :, c] = ndimage.uniform_filter1d(arr[:, :, c], size=size, axis=axis)
                else:
                    result_arr[:, :, c] = arr[:, :, c]
                    
            da = xr.DataArray(result_arr, dims=["y", "x", "channel"], name="filtered_image")
            self.send("Image", da)
        except Exception as e:
            self.send("Image", None)
            raise RuntimeError(f"Failed to apply 1D filter: {e}")

class HLImageFilters2D(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if not hasattr(self, 'image') or self.image is None:
            self.send("Image", None)
            return
            
        filter_type = self.settings.get("filter_type", "gaussian")
        arr = self.image.values
        result_arr = arr
        
        try:
            if filter_type == "gaussian":
                sigma = float(self.settings.get("sigma", 2.0))
                result_arr = np.zeros_like(arr)
                for c in range(arr.shape[2]):
                    result_arr[:, :, c] = ndimage.gaussian_filter(arr[:, :, c], sigma=sigma)
            elif filter_type == "median":
                size = int(self.settings.get("size", 3))
                result_arr = np.zeros_like(arr)
                for c in range(arr.shape[2]):
                    result_arr[:, :, c] = ndimage.median_filter(arr[:, :, c], size=size)
            elif filter_type == "sobel":
                result_arr = np.zeros_like(arr, dtype=np.float32)
                for c in range(arr.shape[2]):
                    sx = ndimage.sobel(arr[:, :, c], axis=0, mode='constant')
                    sy = ndimage.sobel(arr[:, :, c], axis=1, mode='constant')
                    result_arr[:, :, c] = np.hypot(sx, sy)
            elif filter_type == "maximum":
                size = int(self.settings.get("size", 3))
                result_arr = np.zeros_like(arr)
                for c in range(arr.shape[2]):
                    result_arr[:, :, c] = ndimage.maximum_filter(arr[:, :, c], size=size)
            elif filter_type == "minimum":
                size = int(self.settings.get("size", 3))
                result_arr = np.zeros_like(arr)
                for c in range(arr.shape[2]):
                    result_arr[:, :, c] = ndimage.minimum_filter(arr[:, :, c], size=size)
            elif filter_type == "uniform":
                size = int(self.settings.get("size", 3))
                result_arr = np.zeros_like(arr)
                for c in range(arr.shape[2]):
                    result_arr[:, :, c] = ndimage.uniform_filter(arr[:, :, c], size=size)
            elif filter_type == "percentile":
                size = int(self.settings.get("size", 3))
                percentile = float(self.settings.get("percentile", 50))
                result_arr = np.zeros_like(arr)
                for c in range(arr.shape[2]):
                    result_arr[:, :, c] = ndimage.percentile_filter(arr[:, :, c], percentile=percentile, size=size)
            elif filter_type == "prewitt":
                result_arr = np.zeros_like(arr, dtype=np.float32)
                for c in range(arr.shape[2]):
                    sx = ndimage.prewitt(arr[:, :, c], axis=0, mode='constant')
                    sy = ndimage.prewitt(arr[:, :, c], axis=1, mode='constant')
                    result_arr[:, :, c] = np.hypot(sx, sy)
            else:
                pass
                
            da = xr.DataArray(result_arr, dims=["y", "x", "channel"], name="filtered_image")
            self.send("Image", da)
        except Exception as e:
            self.send("Image", None)
            raise RuntimeError(f"Failed to apply 2D filter: {e}")

class HLImageFourier(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if not hasattr(self, 'image') or self.image is None:
            self.send("Image", None)
            return
            
        filter_type = self.settings.get("filter_type", "fourier_gaussian")
        arr = self.image.values
        result_arr = np.zeros_like(arr, dtype=np.float32)
        
        try:
            for c in range(arr.shape[2]):
                fft_arr = np.fft.fftn(arr[:, :, c])
                if filter_type == "fourier_gaussian":
                    sigma = float(self.settings.get("sigma", 2.0))
                    filtered_fft = ndimage.fourier_gaussian(fft_arr, sigma=sigma)
                elif filter_type == "fourier_uniform":
                    size = float(self.settings.get("size", 3.0))
                    filtered_fft = ndimage.fourier_uniform(fft_arr, size=size)
                elif filter_type == "fourier_ellipsoid":
                    size = float(self.settings.get("size", 3.0))
                    filtered_fft = ndimage.fourier_ellipsoid(fft_arr, size=size)
                elif filter_type == "fourier_shift":
                    shift = float(self.settings.get("shift", 1.0))
                    filtered_fft = ndimage.fourier_shift(fft_arr, shift=shift)
                else:
                    filtered_fft = fft_arr
                    
                result_arr[:, :, c] = np.real(np.fft.ifftn(filtered_fft))
                
            da = xr.DataArray(result_arr, dims=["y", "x", "channel"], name="filtered_image")
            self.send("Image", da)
        except Exception as e:
            self.send("Image", None)
            raise RuntimeError(f"Failed to apply Fourier filter: {e}")

class HLImageInterpolation(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if not hasattr(self, 'image') or self.image is None:
            self.send("Image", None)
            return
            
        filter_type = self.settings.get("filter_type", "zoom")
        arr = self.image.values
        
        try:
            if filter_type == "zoom":
                zoom_factor = float(self.settings.get("zoom_factor", 0.5))
                result_arr = ndimage.zoom(arr, (zoom_factor, zoom_factor, 1), order=1)
            elif filter_type == "rotate":
                angle = float(self.settings.get("angle", 45.0))
                reshape = self.settings.get("reshape", True)
                result_arr = ndimage.rotate(arr, angle, axes=(0, 1), reshape=reshape)
            elif filter_type == "shift":
                shift_y = float(self.settings.get("shift_y", 10.0))
                shift_x = float(self.settings.get("shift_x", 10.0))
                result_arr = ndimage.shift(arr, (shift_y, shift_x, 0))
            elif filter_type == "extract_r":
                result_arr = arr[:, :, 0:1]
            elif filter_type == "extract_g":
                result_arr = arr[:, :, 1:2] if arr.shape[2] > 1 else arr[:, :, 0:1]
            elif filter_type == "extract_b":
                result_arr = arr[:, :, 2:3] if arr.shape[2] > 2 else arr[:, :, 0:1]
            else:
                result_arr = arr
                
            da = xr.DataArray(result_arr, dims=["y", "x", "channel"], name="interpolated_image")
            self.send("Image", da)
        except Exception as e:
            self.send("Image", None)
            raise RuntimeError(f"Failed to apply Interpolation: {e}")

class HLImageMorphology(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if not hasattr(self, 'image') or self.image is None:
            self.send("Image", None)
            return
            
        filter_type = self.settings.get("filter_type", "binary_dilation")
        iterations = int(self.settings.get("iterations", 1))
        
        arr = self.image.values
        result_arr = np.zeros_like(arr)
        
        try:
            for c in range(arr.shape[2]):
                channel_data = arr[:, :, c]
                if filter_type == "binary_dilation":
                    result_arr[:, :, c] = ndimage.binary_dilation(channel_data, iterations=iterations)
                elif filter_type == "binary_erosion":
                    result_arr[:, :, c] = ndimage.binary_erosion(channel_data, iterations=iterations)
                elif filter_type == "binary_opening":
                    result_arr[:, :, c] = ndimage.binary_opening(channel_data, iterations=iterations)
                elif filter_type == "binary_closing":
                    result_arr[:, :, c] = ndimage.binary_closing(channel_data, iterations=iterations)
                elif filter_type == "morphological_gradient":
                    result_arr[:, :, c] = ndimage.morphological_gradient(channel_data, size=(3, 3))
                else:
                    result_arr[:, :, c] = channel_data
                    
            da = xr.DataArray(result_arr, dims=["y", "x", "channel"], name="morphology_image")
            self.send("Image", da)
        except Exception as e:
            self.send("Image", None)
            raise RuntimeError(f"Failed to apply Morphology: {e}")

class HLImageMeasurements(HeadlessWidget):
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Measurements", type="dict")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if not hasattr(self, 'image') or self.image is None:
            self.send("Measurements", None)
            return
            
        filter_type = self.settings.get("filter_type", "mean")
        arr = self.image.values
        
        try:
            result = {}
            for c in range(arr.shape[2]):
                channel_data = arr[:, :, c]
                if filter_type == "sum":
                    result[f"channel_{c}"] = float(ndimage.sum(channel_data))
                elif filter_type == "mean":
                    result[f"channel_{c}"] = float(ndimage.mean(channel_data))
                elif filter_type == "variance":
                    result[f"channel_{c}"] = float(ndimage.variance(channel_data))
                elif filter_type == "standard_deviation":
                    result[f"channel_{c}"] = float(ndimage.standard_deviation(channel_data))
                elif filter_type == "extrema":
                    ex = ndimage.extrema(channel_data)
                    result[f"channel_{c}"] = {"min": float(ex[0]), "max": float(ex[1])}
                elif filter_type == "center_of_mass":
                    com = ndimage.center_of_mass(channel_data)
                    result[f"channel_{c}"] = [float(com[0]), float(com[1])]
                    
            self.send("Measurements", result)
        except Exception as e:
            self.send("Measurements", None)
            raise RuntimeError(f"Failed to measure: {e}")

class HLImageViewer(HeadlessWidget):
    def __init__(self, node_id: str, orchestrator):
        super().__init__(node_id, orchestrator)
        self.image = None
        
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        # Emits the image back out so it can be chained if necessary
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        if self.image is not None:
            self.send("Image", self.image)
        else:
            self.send("Image", None)

class HLImageSaver(HeadlessWidget):
    def __init__(self, node_id: str, orchestrator):
        super().__init__(node_id, orchestrator)
        self.image = None
        
    def get_input_signals(self) -> list[SignalDesc]:
        return [SignalDesc(name="Image", type="xarray.DataArray")]
        
    def get_output_signals(self) -> list[SignalDesc]:
        return []
        
    def receive(self, input_name: str, value: xr.DataArray | None) -> None:
        if input_name == "Image":
            self.image = value
            
    def handle_new_signals(self) -> None:
        file_path = self.settings.get("file_path", "")
        if self.image is None or not file_path:
            return
            
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(os.path.abspath(file_path))
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            arr = self.image.values
            if arr.dtype != np.uint8:
                # Normalize and scale
                if arr.ptp() > 0:
                    arr = (255.0 * (arr - arr.min()) / arr.ptp()).astype(np.uint8)
                else:
                    arr = arr.astype(np.uint8)
                    
            img = Image.fromarray(arr)
            img.save(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to save image: {e}")
