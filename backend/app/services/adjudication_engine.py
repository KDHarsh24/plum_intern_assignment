"""
Adjudication Rules Engine - Decision making based on policy_terms.json and adjudication_rules.md
Implements all claim validation, coverage verification, and limit checks
"""
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.schemas import ExtractedData, AdjudicationResult, ClaimStatus, ClaimCategory


class PolicyTerms:
    """Policy configuration loaded from policy_terms.json"""
    
    def __init__(self):
        self.policy_data = self._load_policy()
    
    def _load_policy(self) -> Dict:
        """Load policy terms from JSON file"""
        policy_path = Path(__file__).parent.parent.parent.parent / "policy_terms.json"
        try:
            with open(policy_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default policy if file not found
            return self._default_policy()
    
    def _default_policy(self) -> Dict:
        """Default policy terms"""
        return {
            "policy_id": "PLUM_OPD_2024",
            "coverage_details": {
                "annual_limit": 50000,
                "per_claim_limit": 5000,
                "family_floater_limit": 150000,
                "consultation_fees": {"covered": True, "sub_limit": 2000, "copay_percentage": 10},
                "diagnostic_tests": {"covered": True, "sub_limit": 10000},
                "pharmacy": {"covered": True, "sub_limit": 15000, "branded_drugs_copay": 30},
                "dental": {"covered": True, "sub_limit": 10000, "cosmetic_procedures": False},
                "vision": {"covered": True, "sub_limit": 5000},
                "alternative_medicine": {"covered": True, "sub_limit": 8000}
            },
            "waiting_periods": {
                "initial_waiting": 30,
                "pre_existing_diseases": 365,
                "specific_ailments": {"diabetes": 90, "hypertension": 90}
            },
            "exclusions": [
                "Cosmetic procedures", "Weight loss treatments", "Infertility treatments",
                "Experimental treatments", "Self-inflicted injuries"
            ],
            "claim_requirements": {
                "submission_timeline_days": 30,
                "minimum_claim_amount": 500
            }
        }
    
    @property
    def annual_limit(self) -> float:
        return self.policy_data["coverage_details"]["annual_limit"]
    
    @property
    def per_claim_limit(self) -> float:
        return self.policy_data["coverage_details"]["per_claim_limit"]
    
    @property
    def minimum_claim_amount(self) -> float:
        return self.policy_data["claim_requirements"]["minimum_claim_amount"]
    
    def get_sub_limit(self, category: str) -> float:
        """Get sub-limit for a category"""
        category_map = {
            "consultation": "consultation_fees",
            "diagnostic": "diagnostic_tests",
            "pharmacy": "pharmacy",
            "dental": "dental",
            "vision": "vision",
            "alternative": "alternative_medicine"
        }
        key = category_map.get(category, category)
        details = self.policy_data["coverage_details"].get(key, {})
        return details.get("sub_limit", self.per_claim_limit)
    
    def get_copay(self, category: str, is_branded: bool = False) -> float:
        """Get co-pay percentage for a category"""
        coverage = self.policy_data["coverage_details"]
        
        if category == "consultation":
            return coverage["consultation_fees"].get("copay_percentage", 0) / 100
        elif category == "pharmacy" and is_branded:
            return coverage["pharmacy"].get("branded_drugs_copay", 0) / 100
        
        return 0.0
    
    def get_network_discount(self, category: str) -> float:
        """Get network discount percentage"""
        coverage = self.policy_data["coverage_details"]
        if category == "consultation":
            return coverage["consultation_fees"].get("network_discount", 0) / 100
        return 0.0
    
    def get_waiting_period(self, condition: str = None) -> int:
        """Get waiting period in days"""
        waiting = self.policy_data["waiting_periods"]
        
        if condition:
            condition_lower = condition.lower()
            specific = waiting.get("specific_ailments", {})
            for ailment, days in specific.items():
                if ailment in condition_lower:
                    return days
        
        return waiting.get("initial_waiting", 30)
    
    def is_excluded(self, treatment: str) -> bool:
        """Check if treatment is in exclusions list"""
        exclusions = self.policy_data.get("exclusions", [])
        treatment_lower = treatment.lower()
        
        exclusion_keywords = {
            "cosmetic": ["cosmetic", "beauty", "whitening", "aesthetic"],
            "weight_loss": ["weight loss", "slimming", "obesity treatment", "bariatric"],
            "infertility": ["infertility", "ivf", "fertility"],
            "experimental": ["experimental", "trial", "investigational"],
            "self_inflicted": ["self-inflicted", "suicide attempt"],
            "vitamins": ["vitamin", "supplement", "multivitamin"]
        }
        
        for excl in exclusions:
            excl_lower = excl.lower()
            if excl_lower in treatment_lower:
                return True
            
            # Check keywords
            for key, keywords in exclusion_keywords.items():
                    if key in excl_lower:
                        for kw in keywords:
                            if kw in treatment_lower:
                                return True

            # As a fallback, check all exclusion keywords directly (catch spacing/underscore mismatches)
            for keywords in exclusion_keywords.values():
                for kw in keywords:
                    if kw in treatment_lower:
                        return True
                    # also match on first token of keyword (catch 'obesity' from 'obesity treatment')
                    first_tok = kw.split()[0]
                    if first_tok and first_tok in treatment_lower:
                        return True
        
        return False
    
    def requires_pre_auth(self, treatment: str) -> bool:
        """Check if treatment requires pre-authorization"""
        pre_auth_treatments = ["mri", "ct scan", "surgery", "hospitalization"]
        treatment_lower = treatment.lower()
        return any(t in treatment_lower for t in pre_auth_treatments)


class AdjudicationEngine:
    """
    Main adjudication engine implementing all rules from adjudication_rules.md
    """
    
    def __init__(self):
        self.policy = PolicyTerms()
        self.rejection_reasons = []
        self.notes = []
    
    def adjudicate_claim(
        self,
        claim_amount: float,
        claim_category: str,
        treatment_date: datetime,
        extracted_data: ExtractedData,
        ytd_claimed: float = 0.0,
        policy_start_date: datetime = None,
        is_network_hospital: bool = False,
        has_pre_auth: bool = False,
        previous_claims_today: int = 0
    ) -> AdjudicationResult:
        """
        Main adjudication flow implementing 5-step process
        """
        self.rejection_reasons = []
        self.notes = []
        
        claim_id = f"CLM_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Calculate confidence from extracted data
        base_confidence = extracted_data.confidence if extracted_data else 0.5
        
        # Step 1: Basic Eligibility Check
        eligibility_result = self._check_eligibility(
            treatment_date, policy_start_date, extracted_data
        )
        if not eligibility_result["eligible"]:
            return AdjudicationResult(
                claim_id=claim_id,
                decision=ClaimStatus.REJECTED,
                approved_amount=0,
                rejection_reasons=self.rejection_reasons,
                confidence_score=base_confidence,
                notes="; ".join(self.notes),
                next_steps="Please review the rejection reasons and submit corrected documentation."
            )
        
        # Step 2: Document Validation
        doc_result = self._validate_documents(extracted_data)
        if not doc_result["valid"]:
            return AdjudicationResult(
                claim_id=claim_id,
                decision=ClaimStatus.REJECTED,
                approved_amount=0,
                rejection_reasons=self.rejection_reasons,
                confidence_score=base_confidence * 0.8,
                notes="; ".join(self.notes),
                next_steps="Please resubmit with complete and legible documents."
            )
        
        # Step 3: Coverage Verification
        coverage_result = self._verify_coverage(claim_category, extracted_data, has_pre_auth)
        if not coverage_result["covered"]:
            return AdjudicationResult(
                claim_id=claim_id,
                decision=ClaimStatus.REJECTED,
                approved_amount=0,
                rejection_reasons=self.rejection_reasons,
                confidence_score=base_confidence,
                notes="; ".join(self.notes),
                next_steps=coverage_result.get("next_steps", "This treatment is not covered under your policy.")
            )
        
        # Step 4: Limit Validation & Amount Calculation
        limit_result = self._validate_limits(
            claim_amount, claim_category, ytd_claimed, is_network_hospital
        )
        
        # Step 5: Check for Manual Review triggers
        manual_review_triggers = self._check_manual_review_triggers(
            claim_amount, base_confidence, previous_claims_today, extracted_data
        )
        
        if manual_review_triggers:
            return AdjudicationResult(
                claim_id=claim_id,
                decision=ClaimStatus.MANUAL_REVIEW,
                approved_amount=0,
                rejection_reasons=manual_review_triggers,
                confidence_score=base_confidence,
                notes="; ".join(self.notes),
                next_steps="Your claim has been flagged for manual review. Our team will contact you within 2-3 business days.",
                breakdown=limit_result.get("breakdown")
            )
        
        # Determine final decision
        approved_amount = limit_result["approved_amount"]
        
        if approved_amount <= 0:
            return AdjudicationResult(
                claim_id=claim_id,
                decision=ClaimStatus.REJECTED,
                approved_amount=0,
                rejection_reasons=self.rejection_reasons,
                confidence_score=base_confidence,
                notes="; ".join(self.notes),
                next_steps="Your claim exceeds the policy limits."
            )
        
        if approved_amount < claim_amount:
            # If only adjustment is co-pay, treat as approved with deduction
            adjustments = limit_result.get('adjustments', [])
            if len(adjustments) == 1 and (adjustments[0].lower().startswith('co-pay') or adjustments[0].lower().startswith('network discount')):
                decision = ClaimStatus.APPROVED
                next_steps = f"Your claim of ₹{approved_amount:.2f} has been approved after adjustments."
            else:
                decision = ClaimStatus.PARTIAL
                next_steps = f"Partial approval: ₹{approved_amount:.2f} of ₹{claim_amount:.2f} claimed. " + \
                             f"Difference due to: {', '.join(adjustments)}"
        else:
            decision = ClaimStatus.APPROVED
            next_steps = f"Your claim of ₹{approved_amount:.2f} has been approved. " + \
                         "Amount will be credited within 3-5 business days."
        
        return AdjudicationResult(
            claim_id=claim_id,
            decision=decision,
            approved_amount=approved_amount,
            rejection_reasons=self.rejection_reasons,
            confidence_score=min(base_confidence * 1.1, 0.95),  # Boost confidence for successful processing
            notes="; ".join(self.notes),
            next_steps=next_steps,
            breakdown=limit_result.get("breakdown")
        )
    
    def _check_eligibility(
        self,
        treatment_date: datetime,
        policy_start_date: datetime = None,
        extracted_data: ExtractedData = None
    ) -> Dict[str, Any]:
        """Step 1: Basic Eligibility Check"""
        
        # Default policy start if not provided (assume 1 year ago)
        if policy_start_date is None:
            policy_start_date = datetime.now() - timedelta(days=365)
        
        # Check if policy was active on treatment date
        if treatment_date < policy_start_date:
            self.rejection_reasons.append("POLICY_INACTIVE")
            self.notes.append("Treatment date is before policy start date")
            return {"eligible": False}
        
        # Check waiting period
        days_since_start = (treatment_date - policy_start_date).days
        
        # Check for pre-existing conditions in diagnosis
        if extracted_data and extracted_data.diagnosis:
            diagnosis_lower = extracted_data.diagnosis.lower()
            
            # Check specific waiting periods
            waiting_periods = self.policy.policy_data["waiting_periods"].get("specific_ailments", {})
            for condition, wait_days in waiting_periods.items():
                if condition in diagnosis_lower:
                    if days_since_start < wait_days:
                        self.rejection_reasons.append("WAITING_PERIOD")
                        self.notes.append(f"{condition.title()} has a {wait_days}-day waiting period. " +
                                         f"Only {days_since_start} days since policy start.")
                        return {"eligible": False}
        
        # Check initial waiting period
        initial_waiting = self.policy.policy_data["waiting_periods"].get("initial_waiting", 30)
        if days_since_start < initial_waiting:
            self.rejection_reasons.append("WAITING_PERIOD")
            self.notes.append(f"Initial waiting period of {initial_waiting} days not completed")
            return {"eligible": False}
        
        return {"eligible": True}
    
    def _validate_documents(self, extracted_data: ExtractedData) -> Dict[str, Any]:
        """Step 2: Document Validation"""
        
        if not extracted_data:
            self.rejection_reasons.append("MISSING_DOCUMENTS")
            self.notes.append("No documents provided for processing")
            return {"valid": False}
        
        # Check if critical data was extracted
        if extracted_data.confidence < 0.3:
            self.rejection_reasons.append("ILLEGIBLE_DOCUMENTS")
            self.notes.append("Documents are too unclear to process")
            return {"valid": False}
        
        # Validate doctor registration number format (allow multi-segment prefixes like AYUR/KL/...)
        if extracted_data.doctor_reg_number:
            reg_pattern = r"^[A-Z]+(?:/[A-Z]+)*/\d{4,6}/\d{4}$"
            if not re.match(reg_pattern, extracted_data.doctor_reg_number):
                self.rejection_reasons.append("DOCTOR_REG_INVALID")
                self.notes.append(f"Invalid doctor registration format: {extracted_data.doctor_reg_number}")
                return {"valid": False}
        
        # Check for prescription (required for most claims) — require either medicines/tests or doctor info
        if not extracted_data.medicines and not extracted_data.tests and not extracted_data.doctor_name and not extracted_data.doctor_reg_number:
            self.rejection_reasons.append("MISSING_DOCUMENTS")
            self.notes.append("Prescription from registered doctor is required")
            return {"valid": False}
        
        return {"valid": True}
    
    def _verify_coverage(
        self,
        claim_category: str,
        extracted_data: ExtractedData,
        has_pre_auth: bool = False
    ) -> Dict[str, Any]:
        """Step 3: Coverage Verification"""
        
        # Check if category is covered
        coverage = self.policy.policy_data["coverage_details"]
        category_map = {
            "consultation": "consultation_fees",
            "diagnostic": "diagnostic_tests",
            "pharmacy": "pharmacy",
            "dental": "dental",
            "vision": "vision",
            "alternative": "alternative_medicine"
        }
        
        category_key = category_map.get(claim_category, claim_category)
        category_coverage = coverage.get(category_key, {})
        
        if not category_coverage.get("covered", True):
            self.rejection_reasons.append("SERVICE_NOT_COVERED")
            self.notes.append(f"{claim_category} is not covered under this policy")
            return {"covered": False}
        
        # Check exclusions
        if extracted_data and extracted_data.diagnosis:
            if self.policy.is_excluded(extracted_data.diagnosis):
                self.rejection_reasons.append("EXCLUDED_CONDITION")
                self.notes.append(f"Treatment for '{extracted_data.diagnosis}' is excluded")
                return {"covered": False, "next_steps": "This condition is in the policy exclusions list."}
        
        # Check for treatments in medicines/tests
        if extracted_data:
            for item in (extracted_data.medicines or []) + (extracted_data.tests or []):
                # Allow vitamins/supplements when prescribed for deficiency (heuristic)
                item_l = item.lower()
                if "vitamin" in item_l or "supplement" in item_l:
                    if not (extracted_data.diagnosis and "deficiency" in extracted_data.diagnosis.lower()):
                        # do not treat generic vitamins as excluded unless diagnosis indicates deficiency
                        continue

                if self.policy.is_excluded(item):
                    self.rejection_reasons.append("EXCLUDED_CONDITION")
                    self.notes.append(f"'{item}' is excluded from coverage")
                    return {"covered": False}
        
        # Check pre-authorization requirements
        if extracted_data and extracted_data.tests:
            for test in extracted_data.tests:
                if self.policy.requires_pre_auth(test) and not has_pre_auth:
                    self.rejection_reasons.append("PRE_AUTH_MISSING")
                    self.notes.append(f"Pre-authorization required for '{test}'")
                    return {
                        "covered": False,
                        "next_steps": f"Please obtain pre-authorization for {test} and resubmit."
                    }
        
        # Check cosmetic procedures for dental
        if claim_category == "dental" and extracted_data and extracted_data.diagnosis:
            cosmetic_dental = ["whitening", "bleaching", "cosmetic", "veneer"]
            if any(cd in extracted_data.diagnosis.lower() for cd in cosmetic_dental):
                self.rejection_reasons.append("EXCLUDED_CONDITION")
                self.notes.append("Cosmetic dental procedures are not covered")
                return {"covered": False}
        
        return {"covered": True}
    
    def _validate_limits(
        self,
        claim_amount: float,
        claim_category: str,
        ytd_claimed: float,
        is_network_hospital: bool = False
    ) -> Dict[str, Any]:
        """Step 4: Limit Validation"""
        
        adjustments = []
        breakdown = {
            "original_amount": claim_amount,
            "adjustments": []
        }
        
        approved_amount = claim_amount
        
        # Check minimum claim amount
        if claim_amount < self.policy.minimum_claim_amount:
            self.rejection_reasons.append("BELOW_MIN_AMOUNT")
            self.notes.append(f"Claim amount ₹{claim_amount} is below minimum ₹{self.policy.minimum_claim_amount}")
            return {"approved_amount": 0, "adjustments": ["Below minimum claim amount"]}
        
        # Apply network discount (if applicable)
        if is_network_hospital:
            discount = self.policy.get_network_discount(claim_category)
            if discount > 0:
                discount_amount = approved_amount * discount
                approved_amount = approved_amount - discount_amount
                adjustments.append(f"Network discount: {discount*100:.0f}%")
                breakdown["adjustments"].append({
                    "type": "network_discount",
                    "percentage": discount * 100,
                    "amount": -discount_amount
                })
        
        # Apply co-pay
        copay = self.policy.get_copay(claim_category)
        # Do not apply co-pay for network hospitals (cashless behavior)
        if is_network_hospital:
            copay = 0.0
        if copay > 0:
            copay_amount = approved_amount * copay
            approved_amount = approved_amount - copay_amount
            adjustments.append(f"Co-pay: {copay*100:.0f}%")
            breakdown["adjustments"].append({
                "type": "copay",
                "percentage": copay * 100,
                "amount": -copay_amount
            })
        
        # Check per-claim limit
        per_claim_limit = self.policy.per_claim_limit
        # Strict rejection rule: non-dental claims above global per-claim limit are rejected
        if claim_amount > per_claim_limit and claim_category != "dental":
            self.rejection_reasons.append("PER_CLAIM_EXCEEDED")
            self.notes.append(f"Amount exceeds per-claim limit of ₹{per_claim_limit}")
            return {"approved_amount": 0, "adjustments": ["Per-claim limit exceeded"]}
        # If a category-specific sub-limit exists and is higher than global per-claim limit,
        # prefer the category sub-limit (e.g., dental may have higher sub-limit)
        sub_limit_val = self.policy.get_sub_limit(claim_category)
        apply_per_claim = True
        if sub_limit_val and sub_limit_val > per_claim_limit:
            apply_per_claim = False

        if apply_per_claim and approved_amount > per_claim_limit:
            excess = approved_amount - per_claim_limit
            approved_amount = per_claim_limit
            adjustments.append(f"Per-claim limit: ₹{per_claim_limit}")
            self.rejection_reasons.append("PER_CLAIM_EXCEEDED")
            self.notes.append(f"Amount exceeds per-claim limit of ₹{per_claim_limit}")
            breakdown["adjustments"].append({
                "type": "per_claim_limit",
                "limit": per_claim_limit,
                "amount": -excess
            })
        
        # Check sub-limit (skip enforcement for network hospitals on consultation to allow cashless behavior)
        sub_limit = self.policy.get_sub_limit(claim_category)
        if not (is_network_hospital and claim_category == "consultation"):
            if approved_amount > sub_limit:
                excess = approved_amount - sub_limit
                approved_amount = sub_limit
                adjustments.append(f"Sub-limit ({claim_category}): ₹{sub_limit}")
                self.rejection_reasons.append("SUB_LIMIT_EXCEEDED")
                breakdown["adjustments"].append({
                    "type": "sub_limit",
                    "category": claim_category,
                    "limit": sub_limit,
                    "amount": -excess
                })
        
        # Check annual limit
        remaining_annual = self.policy.annual_limit - ytd_claimed
        if approved_amount > remaining_annual:
            if remaining_annual <= 0:
                self.rejection_reasons.append("ANNUAL_LIMIT_EXCEEDED")
                self.notes.append("Annual limit already exhausted")
                return {"approved_amount": 0, "adjustments": ["Annual limit exhausted"], "breakdown": breakdown}
            
            excess = approved_amount - remaining_annual
            approved_amount = remaining_annual
            adjustments.append(f"Annual limit remaining: ₹{remaining_annual}")
            self.rejection_reasons.append("ANNUAL_LIMIT_EXCEEDED")
            breakdown["adjustments"].append({
                "type": "annual_limit",
                "remaining": remaining_annual,
                "amount": -excess
            })
        
        breakdown["final_amount"] = approved_amount
        
        return {
            "approved_amount": round(approved_amount, 2),
            "adjustments": adjustments,
            "breakdown": breakdown
        }
    
    def _check_manual_review_triggers(
        self,
        claim_amount: float,
        confidence: float,
        previous_claims_today: int,
        extracted_data: ExtractedData
    ) -> List[str]:
        """Check if claim should go to manual review"""
        triggers = []
        
        # High value claims (>₹25,000)
        if claim_amount > 25000:
            triggers.append("HIGH_VALUE_CLAIM")
            self.notes.append(f"High value claim: ₹{claim_amount}")
        
        # Low confidence extraction
        if confidence < 0.5:
            triggers.append("LOW_CONFIDENCE")
            self.notes.append(f"Low extraction confidence: {confidence:.0%}")
        
        # Multiple claims same day (potential fraud)
        if previous_claims_today >= 2:
            triggers.append("FRAUD_INDICATOR")
            self.notes.append("Multiple claims submitted on same day")
        
        # Missing critical information
        if extracted_data:
            if not extracted_data.doctor_reg_number:
                triggers.append("MISSING_DOCTOR_REG")
                self.notes.append("Doctor registration number not found")
        
        return triggers


# Singleton instance
adjudication_engine = AdjudicationEngine()
