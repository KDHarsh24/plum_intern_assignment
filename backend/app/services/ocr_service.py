"""
Document Processor - OCR using Tesseract (Free & Open Source)
Extracts text from images and PDFs of medical documents
"""
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import pytesseract

from app.config import TESSERACT_CMD, UPLOAD_DIR

# Configure Tesseract path for Windows
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


class DocumentProcessor:
    """Handles OCR extraction from medical documents"""
    
    def __init__(self):
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
    
    def process_document(self, file_path: str) -> Tuple[str, float]:
        """
        Extract text from a document using OCR
        Returns: (extracted_text, confidence_score)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        ext = file_path.suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported format: {ext}")
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        else:
            return self._process_image(file_path)
    
    def _process_image(self, image_path: Path) -> Tuple[str, float]:
        """Process a single image with OCR"""
        try:
            image = Image.open(image_path)
            
            # Preprocess for better OCR
            image = self._preprocess_image(image)
            
            # Get OCR data with confidence
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence
            confidences = [int(c) for c in ocr_data['conf'] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Get text
            text = pytesseract.image_to_string(image)
            
            return text.strip(), avg_confidence / 100
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return "", 0.0
    
    def _process_pdf(self, pdf_path: Path) -> Tuple[str, float]:
        """Process PDF by converting to images first"""
        try:
            # Try to import pdf2image
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            all_text = []
            all_confidences = []
            
            for image in images:
                image = self._preprocess_image(image)
                text = pytesseract.image_to_string(image)
                all_text.append(text)
                
                # Get confidence
                ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                confidences = [int(c) for c in ocr_data['conf'] if int(c) > 0]
                if confidences:
                    all_confidences.extend(confidences)
            
            combined_text = "\n\n--- Page Break ---\n\n".join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            
            return combined_text.strip(), avg_confidence / 100
            
        except ImportError:
            # Fallback: try to read PDF as text
            return self._extract_pdf_text(pdf_path)
        except Exception as e:
            print(f"PDF Processing Error: {e}")
            return "", 0.0
    
    def _extract_pdf_text(self, pdf_path: Path) -> Tuple[str, float]:
        """Fallback PDF text extraction without images"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text.strip(), 0.8  # Assume decent confidence for text PDFs
        except:
            return "", 0.0
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too small
        min_dimension = 1000
        if min(image.size) < min_dimension:
            ratio = min_dimension / min(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def process_multiple_documents(self, file_paths: List[str]) -> Tuple[str, float]:
        """Process multiple documents and combine results"""
        all_texts = []
        all_confidences = []
        
        for path in file_paths:
            text, confidence = self.process_document(path)
            if text:
                all_texts.append(f"=== Document: {Path(path).name} ===\n{text}")
                all_confidences.append(confidence)
        
        combined_text = "\n\n".join(all_texts)
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        return combined_text, avg_confidence


# Singleton instance
document_processor = DocumentProcessor()
