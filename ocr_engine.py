"""
High-performance OCR engine leveraging native Windows WinRT (Windows.Media.Ocr).
Runs completely offline with zero external binary dependencies.
"""
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class WinRTOcrEngine:
    """Wrapper around Windows 10/11 built-in WinRT OCR API."""

    POWERSHELL_SCRIPT = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
})[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Media.Ocr,ContentType=WindowsRuntime] | Out-Null

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$imagePath = $args[0]
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imagePath)) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$ocr = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])

$lines = @()
foreach ($l in $ocr.Lines) {
    $lines += $l.Text
}

$outputObj = @{
    text = $ocr.Text
    lines = $lines
}

$outputObj | ConvertTo-Json -Depth 5 -Compress
"""

    BATCH_POWERSHELL_SCRIPT = """
param([string]$Dir, [string]$OutFile)
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
})[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Media.Ocr,ContentType=WindowsRuntime] | Out-Null

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$files = Get-ChildItem -Path "$Dir\\tx_*.png" | Sort-Object { [int]($_.BaseName -replace '\\D','') }

$results = @()
foreach ($f in $files) {
    try {
        $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName)) ([Windows.Storage.StorageFile])
        $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $ocr = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        
        $lines = @()
        foreach ($l in $ocr.Lines) {
            $lines += $l.Text
        }
        
        $results += [PSCustomObject]@{
            filename = $f.Name
            index = [int]($f.BaseName -replace '\\D','')
            text = $ocr.Text
            lines = $lines
        }
    } catch {
        Write-Warning "Error processing $($f.Name): $_"
    }
}

$results | ConvertTo-Json -Depth 5 | Set-Content -Path $OutFile -Encoding utf8
"""

    @classmethod
    def recognize_single(cls, image_path: Path) -> Dict[str, Any]:
        """Run OCR on a single image file."""
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False) as ps_file:
            ps_file.write(cls.POWERSHELL_SCRIPT)
            script_path = ps_file.name

        try:
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", script_path,
                str(image_path.resolve())
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(res.stdout.strip(), strict=False)
        finally:
            Path(script_path).unlink(missing_ok=True)

    @classmethod
    def recognize_batch(cls, images_dir: Path, output_json: Path) -> List[Dict[str, Any]]:
        """Run batch OCR on all images in a folder in a single high-speed execution."""
        logger.info(f"Running batch OCR on {images_dir}...")
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False) as ps_file:
            ps_file.write(cls.BATCH_POWERSHELL_SCRIPT)
            script_path = ps_file.name

        try:
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", script_path,
                "-Dir", str(images_dir.resolve()),
                "-OutFile", str(output_json.resolve())
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            with open(output_json, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            logger.info(f"Batch OCR complete! Processed {len(data)} images.")
            return data
        finally:
            Path(script_path).unlink(missing_ok=True)

    @staticmethod
    def crop_amount_region(image_path: Path, output_crop_path: Path) -> Path:
        """Crop the focal amount region (18% - 28% vertical span, offset from rupee glyph) for precise amount verification."""
        with Image.open(image_path) as im:
            w, h = im.size
            crop = im.crop((int(w * 0.22), int(h * 0.18), int(w * 0.88), int(h * 0.28)))
            crop_resized = crop.resize((crop.width * 2, crop.height * 2))
            crop_resized.save(output_crop_path)
            return output_crop_path
