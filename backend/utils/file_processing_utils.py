"""
File processing optimizations for large CSV/XLSX files
"""

import os
import pandas as pd
from io import StringIO
from werkzeug.datastructures import FileStorage
from typing import Dict, Any, List
import tempfile

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size
CHUNK_SIZE = 10000  # Process files in chunks of 10,000 rows

class FileProcessingError(Exception):
    """Custom exception for file processing errors"""
    pass

def validate_file_size(file: FileStorage) -> None:
    """Validate file size to prevent memory exhaustion"""
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > MAX_FILE_SIZE:
            raise FileProcessingError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")

def process_csv_streaming(file: FileStorage, required_columns: List[str] = None) -> pd.DataFrame:
    """Process CSV file in streaming mode to avoid memory exhaustion"""
    validate_file_size(file)
    
    try:
        # Reset file pointer
        file.seek(0)
        
        # Read first chunk to validate structure
        first_chunk = pd.read_csv(file, nrows=5)
        
        if required_columns:
            missing_columns = set(required_columns) - set(first_chunk.columns)
            if missing_columns:
                raise FileProcessingError(f"Missing required columns: {missing_columns}")
        
        # Reset and read full file with chunking if needed
        file.seek(0)
        
        # For files under 10MB, read normally
        if hasattr(file, 'content_length') and file.content_length < 10 * 1024 * 1024:
            return pd.read_csv(file)
        
        # For larger files, process in chunks
        chunks = []
        for chunk in pd.read_csv(file, chunksize=CHUNK_SIZE):
            chunks.append(chunk)
            
        return pd.concat(chunks, ignore_index=True)
        
    except pd.errors.EmptyDataError:
        raise FileProcessingError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise FileProcessingError(f"CSV parsing error: {str(e)}")
    except Exception as e:
        raise FileProcessingError(f"Error processing CSV: {str(e)}")

def process_excel_streaming(file: FileStorage, required_columns: List[str] = None) -> pd.DataFrame:
    """Process Excel file with memory optimization"""
    validate_file_size(file)
    
    try:
        # Reset file pointer
        file.seek(0)
        
        # Read Excel file
        df = pd.read_excel(file)
        
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise FileProcessingError(f"Missing required columns: {missing_columns}")
        
        return df
        
    except Exception as e:
        raise FileProcessingError(f"Error processing Excel file: {str(e)}")

def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Optimize DataFrame memory usage"""
    # Convert object columns to category where appropriate
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].nunique() / len(df) < 0.5:  # If cardinality is low
            df[col] = df[col].astype('category')
    
    # Convert numeric columns to smallest possible dtype
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')
    
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')
    
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize data"""
    # Remove completely empty rows
    df = df.dropna(how='all')
    
    # Strip whitespace from string columns
    for col in df.select_dtypes(include=['object', 'category']).columns:
        df[col] = df[col].astype(str).str.strip()
    
    return df

def safe_file_processing(file: FileStorage, file_type: str, required_columns: List[str] = None) -> Dict[str, Any]:
    """Safe file processing with comprehensive error handling"""
    try:
        # Validate file
        if not file or not file.filename:
            raise FileProcessingError("No file provided")
        
        # Check file extension
        allowed_extensions = {'csv', 'xlsx', 'xls'}
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise FileProcessingError(f"Unsupported file type: {file_ext}. Allowed: {allowed_extensions}")
        
        # Process based on file type
        if file_type == 'csv':
            df = process_csv_streaming(file, required_columns)
        elif file_type in ['xlsx', 'xls']:
            df = process_excel_streaming(file, required_columns)
        else:
            raise FileProcessingError(f"Unsupported file type: {file_type}")
        
        # Optimize and clean data
        df = optimize_dataframe(df)
        df = clean_data(df)
        
        return {
            'status': 'success',
            'data': df,
            'rows': len(df),
            'columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'filename': file.filename
        }
        
    except FileProcessingError as e:
        return {
            'status': 'error',
            'message': str(e),
            'filename': getattr(file, 'filename', 'unknown')
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Unexpected error processing file: {str(e)}",
            'filename': getattr(file, 'filename', 'unknown')
        }

def get_file_stats(file: FileStorage) -> Dict[str, Any]:
    """Get file statistics for monitoring"""
    return {
        'filename': file.filename,
        'content_type': file.content_type,
        'size': getattr(file, 'content_length', 0),
        'size_mb': getattr(file, 'content_length', 0) / (1024 * 1024)
    }
