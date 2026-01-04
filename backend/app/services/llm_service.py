"""
LLM Extraction Service - Using Ollama (Free & Local)
Extracts structured data from OCR text using open-source LLMs
"""
import json
import re
import requests
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas import ExtractedData


class LLMExtractor:
    """
    Extracts structured medical data from OCR text using Ollama (free local LLM)
    Supports: Mistral, Llama3, Phi3, etc.
    """
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = OLLAMA_MODEL
        self.timeout = 120  # seconds
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temp for consistent extraction
                        "num_predict": 2000
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.ConnectionError:
            print(f"Warning: Ollama not running at {self.base_url}. Using fallback extraction.")
            return None
        except Exception as e:
            print(f"LLM Error: {e}")
            return None
    
    def extract_medical_data(self, ocr_text: str) -> ExtractedData:
        """
        Extract structured medical information from OCR text
        """
        prompt = self._build_extraction_prompt(ocr_text)
        llm_response = self._call_ollama(prompt)
        
        if llm_response:
            extracted = self._parse_llm_response(llm_response)
            return extracted
        else:
            # Fallback to regex-based extraction
            return self._fallback_extraction(ocr_text)
    
    def _build_extraction_prompt(self, ocr_text: str) -> str:
        """Build the extraction prompt for the LLM"""
        return f"""You are a medical document data extractor. Extract information from this OCR text of medical documents (prescriptions, bills, test reports).

OCR TEXT:
{ocr_text}

Extract and return ONLY a valid JSON object with these fields (use null if not found):
{{
    "patient_name": "full name of patient",
    "doctor_name": "full name of doctor",
    "doctor_reg_number": "registration number like KA/12345/2015",
    "hospital_name": "hospital or clinic name",
    "diagnosis": "medical diagnosis or chief complaint",
    "treatment_date": "date in YYYY-MM-DD format",
    "medicines": ["list of prescribed medicines"],
    "tests": ["list of diagnostic tests"],
    "total_amount": 0.00,
    "bill_items": [
        {{"description": "item name", "amount": 0.00}}
    ],
    "confidence": 0.0 to 1.0 based on data clarity
}}

Important rules:
1. Extract EXACT values from the text
2. For amounts, extract numbers only (no currency symbols)
3. For dates, convert to YYYY-MM-DD format
4. Doctor registration format is typically: STATE/NUMBER/YEAR (e.g., KA/12345/2015)
5. Return ONLY the JSON, no other text

JSON:"""

    def _parse_llm_response(self, response: str) -> ExtractedData:
        """Parse LLM response into ExtractedData"""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return ExtractedData(
                    patient_name=data.get("patient_name"),
                    doctor_name=data.get("doctor_name"),
                    doctor_reg_number=data.get("doctor_reg_number"),
                    hospital_name=data.get("hospital_name"),
                    diagnosis=data.get("diagnosis"),
                    treatment_date=data.get("treatment_date"),
                    medicines=data.get("medicines", []),
                    tests=data.get("tests", []),
                    total_amount=float(data.get("total_amount", 0) or 0),
                    bill_items=data.get("bill_items", []),
                    confidence=float(data.get("confidence", 0.7))
                )
        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON parse error: {e}")
        
        return ExtractedData(confidence=0.3)
    
    def _fallback_extraction(self, ocr_text: str) -> ExtractedData:
        """
        Regex-based fallback extraction when LLM is unavailable
        """
        text_lower = ocr_text.lower()
        
        # Extract patient name
        patient_name = None
        patient_patterns = [
            r"patient\s*(?:name)?[:\s]+([A-Za-z\s]+?)(?:\n|age|sex|$)",
            r"name[:\s]+([A-Za-z\s]+?)(?:\n|age|$)",
            r"mr\.?\s+([A-Za-z\s]+)",
            r"mrs\.?\s+([A-Za-z\s]+)",
        ]
        for pattern in patient_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                patient_name = match.group(1).strip()
                break
        
        # Extract doctor name
        doctor_name = None
        doctor_patterns = [
            r"dr\.?\s+([A-Za-z\s\.]+?)(?:\n|mbbs|md|$)",
            r"doctor[:\s]+([A-Za-z\s]+?)(?:\n|$)",
        ]
        for pattern in doctor_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                doctor_name = match.group(1).strip()
                break
        
        # Extract doctor registration number
        reg_number = None
        reg_pattern = r"([A-Z]{2}/\d{4,6}/\d{4})"
        match = re.search(reg_pattern, ocr_text)
        if match:
            reg_number = match.group(1)
        
        # Extract amounts
        amount_pattern = r"(?:total|amount|rs\.?|₹)\s*[:\s]*(\d+(?:,\d+)?(?:\.\d{2})?)"
        amounts = re.findall(amount_pattern, ocr_text, re.IGNORECASE)
        total_amount = 0
        if amounts:
            # Take the largest amount as total
            amounts = [float(a.replace(',', '')) for a in amounts]
            total_amount = max(amounts)
        
        # Extract date
        treatment_date = None
        date_patterns = [
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
            r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                treatment_date = match.group(1)
                break
        
        # Extract diagnosis
        diagnosis = None
        diag_patterns = [
            r"diagnosis[:\s]+([^\n]+)",
            r"complaint[s]?[:\s]+([^\n]+)",
            r"c/o[:\s]+([^\n]+)",
        ]
        for pattern in diag_patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                diagnosis = match.group(1).strip()
                break
        
        # Extract medicines (after Rx)
        medicines = []
        rx_match = re.search(r"rx[:\s]*([\s\S]+?)(?:advice|next|follow|$)", ocr_text, re.IGNORECASE)
        if rx_match:
            med_text = rx_match.group(1)
            # Look for medicine-like patterns
            med_lines = [line.strip() for line in med_text.split('\n') if line.strip()]
            medicines = med_lines[:10]  # Limit to 10
        
        # Calculate confidence based on what was extracted
        fields_found = sum([
            bool(patient_name),
            bool(doctor_name),
            bool(reg_number),
            bool(total_amount),
            bool(diagnosis)
        ])
        confidence = min(0.3 + (fields_found * 0.12), 0.85)
        
        return ExtractedData(
            patient_name=patient_name,
            doctor_name=doctor_name,
            doctor_reg_number=reg_number,
            hospital_name=None,
            diagnosis=diagnosis,
            treatment_date=treatment_date,
            medicines=medicines,
            tests=[],
            total_amount=total_amount,
            bill_items=[],
            confidence=confidence
        )
    
    def analyze_claim_validity(self, extracted_data: ExtractedData, claim_amount: float) -> Dict[str, Any]:
        """
        Use LLM to analyze if the claim appears valid
        """
        prompt = f"""Analyze this medical claim for potential issues:

Claimed Amount: ₹{claim_amount}
Extracted Bill Amount: ₹{extracted_data.total_amount}
Diagnosis: {extracted_data.diagnosis}
Medicines: {', '.join(extracted_data.medicines or ['None'])}
Tests: {', '.join(extracted_data.tests or ['None'])}
Doctor Registration: {extracted_data.doctor_reg_number}

Check for:
1. Does the bill amount match the claim?
2. Are medicines appropriate for the diagnosis?
3. Is the doctor registration valid format (STATE/NUMBER/YEAR)?
4. Any red flags for fraud?

Return JSON:
{{
    "is_valid": true/false,
    "issues": ["list of issues found"],
    "fraud_risk": "low/medium/high",
    "confidence": 0.0-1.0
}}

JSON:"""
        
        response = self._call_ollama(prompt)
        if response:
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        # Fallback analysis
        issues = []
        if extracted_data.total_amount and abs(extracted_data.total_amount - claim_amount) > 100:
            issues.append("Claimed amount differs significantly from bill")
        
        if not extracted_data.doctor_reg_number:
            issues.append("Doctor registration number not found")
        elif not re.match(r"[A-Z]{2}/\d{4,6}/\d{4}", extracted_data.doctor_reg_number):
            issues.append("Invalid doctor registration format")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "fraud_risk": "low" if len(issues) == 0 else "medium",
            "confidence": 0.6
        }


# Singleton instance
llm_extractor = LLMExtractor()
