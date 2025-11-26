# backend/utils/audio_validation.py
"""
Audio file validation utilities for voice search
Provides comprehensive validation with security and performance considerations
"""

import os
import mimetypes
from typing import Tuple, List, Optional
from werkzeug.datastructures import FileStorage

class AudioValidator:
    """Comprehensive audio file validation for voice search"""
    
    # Supported audio formats and their MIME types
    SUPPORTED_FORMATS = {
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.m4a': 'audio/mp4',
        '.webm': 'audio/webm',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.aac': 'audio/aac'
    }
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_FILE_SIZE = 1024  # 1KB (to prevent empty files)
    
    # Audio quality constraints
    MAX_DURATION_SECONDS = 60  # 1 minute max
    MIN_DURATION_SECONDS = 1   # 1 second min
    
    def __init__(self, max_file_size: int = None):
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE
        
    def validate_audio_file(self, file: FileStorage) -> Tuple[bool, str, dict]:
        """
        Comprehensive audio file validation
        
        Args:
            file: FileStorage object from Flask request
            
        Returns:
            tuple: (is_valid: bool, message: str, metadata: dict)
        """
        if not file:
            return False, "No audio file provided", {}
        
        if not file.filename:
            return False, "Invalid filename", {}
        
        # Get file metadata
        metadata = self._extract_file_metadata(file)
        
        # Validate file size
        size_valid, size_message = self._validate_file_size(file, metadata)
        if not size_valid:
            return False, size_message, metadata
        
        # Validate file extension
        ext_valid, ext_message = self._validate_file_extension(file, metadata)
        if not ext_valid:
            return False, ext_message, metadata
        
        # Validate MIME type
        mime_valid, mime_message = self._validate_mime_type(file, metadata)
        if not mime_valid:
            return False, mime_message, metadata
        
        # Validate audio content (basic checks)
        content_valid, content_message = self._validate_audio_content(file, metadata)
        if not content_valid:
            return False, content_message, metadata
        
        return True, "Valid audio file", metadata
    
    def _extract_file_metadata(self, file: FileStorage) -> dict:
        """Extract file metadata"""
        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        expected_mime = self.SUPPORTED_FORMATS.get(file_ext, 'unknown')
        
        metadata = {
            'filename': file.filename,
            'file_extension': file_ext,
            'expected_mime_type': expected_mime,
            'content_type': file.content_type or 'unknown',
            'content_length': getattr(file, 'content_length', 0),
            'size_mb': getattr(file, 'content_length', 0) / (1024 * 1024)
        }
        
        return metadata
    
    def _validate_file_size(self, file: FileStorage, metadata: dict) -> Tuple[bool, str]:
        """Validate file size constraints"""
        content_length = metadata.get('content_length', 0)
        
        if content_length == 0:
            return False, "File appears to be empty"
        
        if content_length < self.MIN_FILE_SIZE:
            return False, f"File too small (minimum {self.MIN_FILE_SIZE} bytes)"
        
        if content_length > self.max_file_size:
            size_mb = content_length / (1024 * 1024)
            max_mb = self.max_file_size / (1024 * 1024)
            return False, f"File too large ({size_mb:.1f}MB, maximum {max_mb}MB)"
        
        return True, "File size valid"
    
    def _validate_file_extension(self, file: FileStorage, metadata: dict) -> Tuple[bool, str]:
        """Validate file extension"""
        file_ext = metadata.get('file_extension', '')
        
        if file_ext not in self.SUPPORTED_FORMATS:
            supported = ', '.join(sorted(self.SUPPORTED_FORMATS.keys()))
            return False, f"Unsupported file format '{file_ext}'. Supported formats: {supported}"
        
        return True, "File extension valid"
    
    def _validate_mime_type(self, file: FileStorage, metadata: dict) -> Tuple[bool, str]:
        """Validate MIME type"""
        content_type = metadata.get('content_type', 'unknown')
        expected_mime = metadata.get('expected_mime_type', 'unknown')
        
        # Check if content type matches expected type
        if content_type != 'unknown' and expected_mime != 'unknown':
            if content_type != expected_mime and not content_type.startswith('audio/'):
                return False, f"Content type mismatch. Expected {expected_mime}, got {content_type}"
        
        return True, "MIME type valid"
    
    def _validate_audio_content(self, file: FileStorage, metadata: dict) -> Tuple[bool, str]:
        """Basic audio content validation"""
        try:
            # Read first few bytes to check if it's actually audio
            file.seek(0)
            header = file.read(1024)  # Read first 1KB
            file.seek(0)  # Reset file pointer
            
            if not header:
                return False, "File appears to be empty"
            
            # Basic audio file signature checks
            audio_signatures = {
                b'RIFF': 'wav',  # WAV files start with RIFF
                b'ID3': 'mp3',   # MP3 files might start with ID3
                b'\xff': 'mp3',  # MP3 files might start with 0xFF
                b'fLaC': 'flac', # FLAC files start with fLaC
                b'OggS': 'ogg',  # OGG files start with OggS
            }
            
            # Check for known audio signatures
            is_audio = False
            for signature, format_name in audio_signatures.items():
                if header.startswith(signature):
                    is_audio = True
                    break
            
            if not is_audio:
                # If no signature found, check if it contains non-text data
                try:
                    header.decode('ascii')
                    return False, "File does not appear to be audio data"
                except UnicodeDecodeError:
                    # Binary data, likely audio
                    pass
            
            return True, "Audio content appears valid"
            
        except Exception as e:
            return False, f"Error reading audio content: {str(e)}"
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return sorted(self.SUPPORTED_FORMATS.keys())
    
    def get_mime_type(self, filename: str) -> str:
        """Get MIME type for filename"""
        file_ext = os.path.splitext(filename.lower())[1]
        return self.SUPPORTED_FORMATS.get(file_ext, 'application/octet-stream')

# Global validator instance
audio_validator = AudioValidator()

# Convenience functions
def validate_voice_file(file: FileStorage, max_size_mb: int = 10) -> Tuple[bool, str, dict]:
    """
    Validate voice search audio file
    
    Args:
        file: Uploaded audio file
        max_size_mb: Maximum file size in MB
        
    Returns:
        tuple: (is_valid: bool, message: str, metadata: dict)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    validator = AudioValidator(max_size_bytes)
    return validator.validate_audio_file(file)

def get_audio_metadata(file: FileStorage) -> dict:
    """Get audio file metadata without validation"""
    validator = AudioValidator()
    return validator._extract_file_metadata(file)

def is_audio_file(filename: str) -> bool:
    """Check if filename has supported audio extension"""
    return os.path.splitext(filename.lower())[1] in AudioValidator.SUPPORTED_FORMATS
