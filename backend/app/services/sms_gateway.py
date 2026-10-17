
"""
app/services/sms_gateway.py
---------------------------
SMS gateway service for the Disaster Relief Medical Donation Module.

Functions:
  - parse_inbound_sms()
  - _dispatch_textlk()
  - _dispatch_sms()
  - process_incoming_sms()
  - send_direct_sms()
  - broadcast_emergency_sms()
  - get_gateway_telecom_status()

Outbound SMS provider (primary):
  - Text.lk REST API v3  (https://app.text.lk/api/v3/sms/send)
  - Configure TEXTLK_ENABLED and TEXTLK_API_TOKEN in backend/.env
  - SMSGo.lk configuration retained in settings for backward compatibility
    but is NOT called when TEXTLK_ENABLED=true.

Phone numbers:
  - Internal normalised format: +94771234567
  - Text.lk API format:         94771234567  (strip leading '+')

IMPORTANT:
  - TEXTLK_ENABLED=false (default): no external HTTP call is made; status = "simulated".
  - TEXTLK_ENABLED=true: live Text.lk API is called, credits are deducted.
  - TextLKDemo sender ID is for testing only; use a registered sender ID in production.
  - An API acceptance response does NOT confirm handset delivery.
    Confirmed delivery requires a separate delivery-report callback (not yet implemented).
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.models.sms_log import SMSMessageLog
from app.models.notification import Notification
from app.models.sos import SOSRequest
from app.models.victim import Victim
from app.models.user import User
from app.models.role import Role, RoleEnum
from app.models.camp import MedicalCamp
from app.services.victim_service import calculate_vulnerability_score
from app.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sri Lankan disaster hotspot geo-lookup table
# ---------------------------------------------------------------------------

LOCATION_GEO_LOOKUP: Dict[str, Dict[str, Any]] = {
    "ranala": {
        "lat": 6.9364, "lng": 79.9572, "district": "Colombo",
        "ds": "Kaduwela", "gn": "Ranala"
    },
    "kaduwela": {
        "lat": 6.9236, "lng": 80.0022, "district": "Colombo",
        "ds": "Kaduwela", "gn": "Kaduwela Central"
    },
    "kolonnawa": {
        "lat": 6.9344, "lng": 79.8864, "district": "Colombo",
        "ds": "Kolonnawa", "gn": "Kolonnawa West"
    },
    "kelaniya": {
        "lat": 6.9538, "lng": 79.9189, "district": "Gampaha",
        "ds": "Kelaniya", "gn": "Kelaniya Central"
    },
    "biyagama": {
        "lat": 6.9450, "lng": 79.9800, "district": "Gampaha",
        "ds": "Biyagama", "gn": "Biyagama South"
    },
    "wellampitiya": {
        "lat": 6.9412, "lng": 79.8942, "district": "Colombo",
        "ds": "Kolonnawa", "gn": "Wellampitiya"
    },
    "hanwella": {
        "lat": 6.8924, "lng": 80.0825, "district": "Colombo",
        "ds": "Seethawaka", "gn": "Hanwella"
    },
    "avissawella": {
        "lat": 6.9531, "lng": 80.2081, "district": "Colombo",
        "ds": "Seethawaka", "gn": "Avissawella"
    },
    "nuwara eliya": {
        "lat": 6.9497, "lng": 80.7891, "district": "Nuwara Eliya",
        "ds": "Nuwara Eliya", "gn": "City"
    },
    "lakshapana": {
        "lat": 6.9050, "lng": 80.4980, "district": "Nuwara Eliya",
        "ds": "Ambagamuwa", "gn": "317 A Lakshapana"
    },
    "ambagamuwa": {
        "lat": 6.9600, "lng": 80.5200, "district": "Nuwara Eliya",
        "ds": "Ambagamuwa", "gn": "Ambagamuwa North"
    },
    "ratnapura": {
        "lat": 6.6828, "lng": 80.4034, "district": "Ratnapura",
        "ds": "Ratnapura", "gn": "Ratnapura Town"
    },
    "kalutara": {
        "lat": 6.5854, "lng": 79.9607, "district": "Kalutara",
        "ds": "Kalutara", "gn": "Kalutara North"
    },
    "colombo": {
        "lat": 6.9271, "lng": 79.8612, "district": "Colombo",
        "ds": "Colombo", "gn": "Colombo Central"
    },
    "gampaha": {
        "lat": 7.0840, "lng": 79.9942, "district": "Gampaha",
        "ds": "Gampaha", "gn": "Gampaha City"
    },
    "matara": {
        "lat": 5.9549, "lng": 80.5550, "district": "Matara",
        "ds": "Matara", "gn": "Matara City"
    },
    "galle": {
        "lat": 6.0535, "lng": 80.2210, "district": "Galle",
        "ds": "Galle", "gn": "Galle Fort"
    },
    "kandy": {
        "lat": 7.2906, "lng": 80.6337, "district": "Kandy",
        "ds": "Kandy", "gn": "Kandy City"
    },
    "kurunegala": {
        "lat": 7.4867, "lng": 80.3647, "district": "Kurunegala",
        "ds": "Kurunegala", "gn": "Kurunegala City"
    },
    "badulla": {
        "lat": 6.9934, "lng": 81.0550, "district": "Badulla",
        "ds": "Badulla", "gn": "Badulla City"
    },
}

_DEFAULT_GEO = {
    "lat": 6.9271,
    "lng": 79.8612,
    "district": "Colombo",
    "ds": "Kaduwela",
    "gn": "Ranala",
}

_PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


# ---------------------------------------------------------------------------
# Phone validation
# ---------------------------------------------------------------------------

def _validate_phone(phone: str) -> str:
    """
    Normalise a phone number to E.164.

    Accepts:
      +94771234567
      94771234567
      0771234567
      771234567

    Assumes Sri Lanka (+94) when no country code is provided.
    """
    if not isinstance(phone, str) or not phone.strip():
        raise ValueError("A recipient phone number is required.")

    p = re.sub(r"[\s\-\(\)\.]", "", phone.strip())

    if p.startswith("00"):
        p = "+" + p[2:]
    elif p.startswith("0") and len(p) == 10:
        p = "+94" + p[1:]
    elif p.startswith("94") and len(p) == 11:
        p = "+" + p
    elif not p.startswith("+"):
        p = "+94" + p

    if not _PHONE_RE.fullmatch(p):
        raise ValueError(
            f"Invalid phone number format: '{phone}'. "
            "Expected a valid number such as +94771234567."
        )

    return p


def _phone_for_smsgo(phone: str) -> str:
    """Convert validated E.164 format to SMSGo's 94XXXXXXXXX format."""
    normalised = _validate_phone(phone)
    return normalised[1:]


def _phone_for_textlk(phone: str) -> str:
    """Convert validated E.164 format to Text.lk's 94XXXXXXXXX format (no leading '+')."""
    normalised = _validate_phone(phone)
    return normalised[1:]


# ---------------------------------------------------------------------------
# Text.lk outbound dispatch (primary provider)
# ---------------------------------------------------------------------------

def _dispatch_textlk(to: str, body: str) -> Dict[str, Any]:
    """
    Send an SMS through the Text.lk REST API v3.

    TEXTLK_ENABLED=false (default):
        Returns a simulated status dict; no HTTP request is made.

    TEXTLK_ENABLED=true:
        Sends the SMS via https://app.text.lk/api/v3/sms/send using
        Bearer-token authentication.

    Status distinctions:
        "simulated" — integration disabled; no external call made.
        "sent"      — Text.lk accepted the request (not confirmed delivery).
        "failed"    — Text.lk rejected or the network was unreachable.

    Note: Text.lk may return status="Delivered" inside the data payload for
    the current session, but this reflects provider-side queuing, NOT
    confirmed handset delivery.  Do NOT report a message as delivered to
    end-users based solely on this response.
    """
    if not settings.TEXTLK_ENABLED:
        logger.info(
            "[TEXTLK-SIMULATE] Text.lk disabled. Recipient ending=%s",
            to[-4:] if to else "unknown",
        )
        return {
            "status": "simulated",
            "sid": None,
            "provider": "TEXTLK_SIMULATOR",
            "environment": "local",
            "message": "Text.lk is disabled (TEXTLK_ENABLED=false); no SMS was sent.",
        }

    api_token = settings.TEXTLK_API_TOKEN.strip()
    if not api_token:
        logger.error("[TEXTLK] API token is missing.")
        return {
            "status": "failed",
            "sid": None,
            "provider": "TEXTLK",
            "message": "Text.lk API token is not configured (TEXTLK_API_TOKEN is empty).",
        }

    if not body or not body.strip():
        return {
            "status": "failed",
            "sid": None,
            "provider": "TEXTLK",
            "message": "SMS message cannot be empty.",
        }

    try:
        recipient = _phone_for_textlk(to)
    except ValueError as exc:
        return {
            "status": "failed",
            "sid": None,
            "provider": "TEXTLK",
            "message": str(exc),
        }

    sender_id = settings.TEXTLK_SENDER_ID.strip() or "TextLKDemo"

    payload: Dict[str, Any] = {
        "recipient": recipient,
        "sender_id": sender_id,
        "type": "plain",
        "message": body.strip(),
    }

    request_data = json.dumps(payload).encode("utf-8")
    request = Request(
        settings.TEXTLK_API_URL,
        data=request_data,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=settings.TEXTLK_TIMEOUT_SECONDS,
        ) as response:
            response_text = response.read().decode("utf-8")
            http_status = response.status

        try:
            response_json = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(
                "[TEXTLK] Provider returned invalid JSON (HTTP %s).",
                http_status,
            )
            return {
                "status": "failed",
                "sid": None,
                "provider": "TEXTLK",
                "message": "Text.lk returned an invalid JSON response.",
                "http_status": http_status,
            }

        if http_status < 200 or http_status >= 300:
            logger.error("[TEXTLK] Request failed with HTTP %s.", http_status)
            return {
                "status": "failed",
                "sid": None,
                "provider": "TEXTLK",
                "message": "Text.lk rejected the SMS request.",
                "http_status": http_status,
                "raw_response": response_json,
            }

        # Text.lk v3 returns {"status": "success", "data": {"uid": ..., "status": ...}}
        top_status = str(response_json.get("status", "")).lower()
        data = response_json.get("data") or {}
        uid = data.get("uid") or data.get("id")

        if top_status != "success":
            logger.warning("[TEXTLK] Provider reported an unsuccessful request.")
            return {
                "status": "failed",
                "sid": uid,
                "provider": "TEXTLK",
                "message": str(
                    response_json.get("message")
                    or response_json.get("error")
                    or "Text.lk reported that the SMS was not accepted."
                ),
                "raw_response": response_json,
            }

        logger.info(
            "[TEXTLK] Request accepted. Recipient ending=%s uid=%s",
            recipient[-4:],
            uid,
        )

        # "sent" means provider accepted the request — NOT confirmed handset delivery.
        return {
            "status": "sent",
            "sid": uid,
            "provider": "TEXTLK",
            "environment": "live",
            "message": (
                "Text.lk accepted the SMS request. "
                "Delivery to handset is not yet confirmed."
            ),
            "raw_response": response_json,
        }

    except HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""

        logger.error("[TEXTLK] HTTP error %s.", exc.code)

        try:
            parsed_error = json.loads(error_body) if error_body else {}
        except json.JSONDecodeError:
            parsed_error = {}

        error_message = (
            parsed_error.get("message")
            or parsed_error.get("error")
            or f"Text.lk returned HTTP {exc.code}."
        )

        return {
            "status": "failed",
            "sid": None,
            "provider": "TEXTLK",
            "message": str(error_message),
            "http_status": exc.code,
        }

    except (URLError, TimeoutError) as exc:
        logger.error("[TEXTLK] Network or timeout error: %s", type(exc).__name__)
        return {
            "status": "failed",
            "sid": None,
            "provider": "TEXTLK",
            "message": "Could not connect to Text.lk. Check network and API URL.",
        }

    except Exception:
        logger.exception("[TEXTLK] Unexpected dispatch error.")
        return {
            "status": "failed",
            "sid": None,
            "provider": "TEXTLK",
            "message": "Unexpected error while sending the SMS via Text.lk.",
        }


# ---------------------------------------------------------------------------
# Primary dispatch router — calls Text.lk when enabled, SMSGo otherwise
# ---------------------------------------------------------------------------

def _dispatch_sms(to: str, body: str) -> Dict[str, Any]:
    """
    Route outbound SMS to the appropriate provider.

    Priority:
      1. TEXTLK_ENABLED=true  → calls _dispatch_textlk()
      2. SMSGO_ENABLED=true   → calls the SMSGo.lk API (legacy path)
      3. Both disabled         → returns simulated result (no HTTP request)

    SMSGO_ENABLED=false:
        Returns simulated status and does not contact the provider.

    SMSGO_ENABLED=true with an sg_test_ key:
        Sends a sandbox API request; SMSGo simulates delivery without
        sending a real SMS to the mobile network.


    SMSGO_ENABLED=true with a live key:
        Sends the message through the live SMSGo API.
    """
    # ---- Text.lk (primary provider) ----------------------------------------
    if settings.TEXTLK_ENABLED:
        return _dispatch_textlk(to, body)
    # ---- SMSGo (legacy fallback) --------------------------------------------
    if not settings.SMSGO_ENABLED:
        logger.info(
            "[SMS-SIMULATE] Both Text.lk and SMSGo disabled. Recipient ending=%s",
            to[-4:] if to else "unknown",
        )
        return {
            "status": "simulated",
            "sid": None,
            "provider": "SMSGO_SIMULATOR",
            "environment": "local",
            "message": "SMS disabled (TEXTLK_ENABLED=false, SMSGO_ENABLED=false); no SMS was sent.",
        }

    api_key = settings.SMSGO_API_KEY.strip()
    if not api_key:
        logger.error("[SMSGO] API key is missing.")
        return {
            "status": "failed",
            "sid": None,
            "provider": "SMSGO",
            "message": "SMSGo API key is not configured.",
        }

    if not body or not body.strip():
        return {
            "status": "failed",
            "sid": None,
            "provider": "SMSGO",
            "message": "SMS message cannot be empty.",
        }

    try:
        recipient = _phone_for_smsgo(to)
    except ValueError as exc:
        return {
            "status": "failed",
            "sid": None,
            "provider": "SMSGO",
            "message": str(exc),
        }

    payload: Dict[str, Any] = {
        "to": recipient,
        "message": body.strip(),
    }

    # SMSGo uses the account's approved default mask when mask is omitted.
    mask = settings.SMSGO_MASK.strip()
    if mask:
        payload["mask"] = mask

    request_data = json.dumps(payload).encode("utf-8")
    request = Request(
        settings.SMSGO_API_URL,
        data=request_data,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(
            request,
            timeout=settings.SMSGO_TIMEOUT_SECONDS,
        ) as response:
            response_text = response.read().decode("utf-8")
            http_status = response.status

        try:
            response_json = json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(
                "[SMSGO] Provider returned invalid JSON (HTTP %s).",
                http_status,
            )
            return {
                "status": "failed",
                "sid": None,
                "provider": "SMSGO",
                "message": "SMSGo returned an invalid response.",
                "http_status": http_status,
            }

        if http_status < 200 or http_status >= 300:
            logger.error("[SMSGO] Request failed with HTTP %s.", http_status)
            return {
                "status": "failed",
                "sid": None,
                "provider": "SMSGO",
                "message": "SMSGo rejected the SMS request.",
                "http_status": http_status,
                "raw_response": response_json,
            }

        if not response_json.get("success"):
            logger.warning("[SMSGO] Provider reported an unsuccessful request.")
            return {
                "status": "failed",
                "sid": None,
                "provider": "SMSGO",
                "message": str(
                    response_json.get("message")
                    or response_json.get("error")
                    or "SMSGo reported that the SMS was not accepted."
                ),
                "raw_response": response_json,
            }

        data = response_json.get("data") or {}
        message_id = data.get("id") or data.get("serverRef")
        environment = str(response_json.get("environment", "")).lower()
        key_is_test = api_key.startswith("sg_test_")
        is_sandbox = key_is_test or environment == "sandbox"

        provider_status = str(data.get("status", "")).lower()
        if provider_status == "failed":
            status = "failed"
        elif is_sandbox:
            # Sandbox delivery is simulated, not a real mobile SMS.
            status = "simulated"
        else:
            # "sent" here means accepted by the provider, not confirmed
            # handset delivery.
            status = "sent"

        logger.info(
            "[SMSGO] Request processed. Recipient ending=%s status=%s",
            recipient[-4:],
            status,
        )

        return {
            "status": status,
            "sid": message_id,
            "provider": "SMSGO_SANDBOX" if is_sandbox else "SMSGO",
            "environment": "sandbox" if is_sandbox else "live",
            "message": (
                "Sandbox SMS simulated successfully."
                if is_sandbox and status != "failed"
                else "SMSGo accepted the SMS request."
                if status == "sent"
                else "SMSGo reported a failed SMS request."
            ),
            "raw_response": response_json,
        }

    except HTTPError as exc:
        # Read the provider's error response without exposing the API key.
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""

        logger.error("[SMSGO] HTTP error %s.", exc.code)

        try:
            parsed_error = json.loads(error_body) if error_body else {}
        except json.JSONDecodeError:
            parsed_error = {}

        error_message = (
            parsed_error.get("message")
            or parsed_error.get("error")
            or f"SMSGo returned HTTP {exc.code}."
        )

        return {
            "status": "failed",
            "sid": None,
            "provider": "SMSGO",
            "message": str(error_message),
            "http_status": exc.code,
        }

    except (URLError, TimeoutError) as exc:
        logger.error("[SMSGO] Network or timeout error: %s", type(exc).__name__)
        return {
            "status": "failed",
            "sid": None,
            "provider": "SMSGO",
            "message": "Could not connect to SMSGo. Check the network and API URL.",
        }

    except Exception:
        logger.exception("[SMSGO] Unexpected dispatch error.")
        return {
            "status": "failed",
            "sid": None,
            "provider": "SMSGO",
            "message": "Unexpected error while sending the SMS.",
        }


# ---------------------------------------------------------------------------
# Geographic helpers
# ---------------------------------------------------------------------------

def geocode_from_text(text: str) -> Dict[str, Any]:
    """Find a known Sri Lankan hotspot mentioned in text."""
    lower = text.lower()

    for loc_key, meta in LOCATION_GEO_LOOKUP.items():
        if loc_key in lower:
            return meta.copy()

    return _DEFAULT_GEO.copy()


# ---------------------------------------------------------------------------
# SMS intent parser
# ---------------------------------------------------------------------------

def parse_inbound_sms(text: str) -> Dict[str, Any]:
    """
    Parse an inbound SMS into a structured intent.

    Supported intents:
      HELP
      STATUS_CHECK
      CAMP_QUERY
      VICTIM_REGISTRATION
      SOS_TRIGGER
    """
    clean_text = text.strip()
    upper = clean_text.upper()

    if upper.startswith(("HELP", "INFO", "?")):
        return {"intent": "HELP", "action": "reply_help"}

    if upper.startswith("STATUS"):
        match = re.search(r"STATUS\s*#?(\d+)?", upper)
        sos_id = int(match.group(1)) if match and match.group(1) else None
        return {
            "intent": "STATUS_CHECK",
            "sos_id": sos_id,
            "action": "check_status",
        }

    if upper.startswith("CAMP"):
        geo = geocode_from_text(clean_text)
        return {
            "intent": "CAMP_QUERY",
            "district": geo["district"],
            "action": "query_camps",
        }

    if upper.startswith(("REG", "REGISTER")):
        tokens = re.split(r"[,;|\n]+", clean_text)
        if len(tokens) == 1:
            tokens = clean_text.split()

        tokens = [token.strip() for token in tokens if token.strip()]
        if tokens and tokens[0].upper() in ("REG", "REGISTER"):
            tokens = tokens[1:]

        full_name = "SMS Registered Victim"
        nic = None
        district = "Colombo"
        family_count = 1
        medical_needs = None

        if len(tokens) >= 1:
            full_name = tokens[0]

        if len(tokens) >= 2:
            if re.fullmatch(r"(?:\d{9}[VvXx]|\d{12})", tokens[1]):
                nic = tokens[1]
            else:
                district = tokens[1]

        if len(tokens) >= 3:
            if not nic and re.fullmatch(
                r"(?:\d{9}[VvXx]|\d{12})", tokens[2]
            ):
                nic = tokens[2]
            elif district == "Colombo":
                district = tokens[2]

        if len(tokens) >= 4:
            try:
                digits = re.findall(r"\d+", tokens[3])
                if digits:
                    family_count = max(1, int(digits[0]))
            except (ValueError, IndexError):
                pass

        if len(tokens) >= 5:
            medical_needs = " ".join(tokens[4:])

        geo = geocode_from_text(f"{district} {clean_text}")

        return {
            "intent": "VICTIM_REGISTRATION",
            "full_name": full_name,
            "nic": nic,
            "district": geo["district"],
            "ds_division": geo["ds"],
            "gn_division": geo["gn"],
            "latitude": geo["lat"],
            "longitude": geo["lng"],
            "family_count": family_count,
            "medical_needs": medical_needs,
            "action": "register_victim",
        }

    urgency = 4
    urgency_match = re.search(r"\b([1-5])\b", clean_text)

    if urgency_match:
        urgency = int(urgency_match.group(1))
    elif any(
        word in upper
        for word in [
            "CRITICAL", "DYING", "ROOF", "IMMEDIATE",
            "URGENT", "DROWNING", "TRAPPED",
        ]
    ):
        urgency = 5

    people_match = re.search(
        r"(\d+)\s*(?:people|persons|family|members|individuals|"
        r"victims|adults|kids|children)?",
        clean_text,
        re.I,
    )
    affected_people = int(people_match.group(1)) if people_match else 2
    affected_people = min(max(affected_people, 1), 999)

    has_elderly = any(
        word in upper
        for word in [
            "ELDERLY", "OLD", "SENIOR", "GRANDMOTHER",
            "GRANDFATHER", "BEDRIDDEN",
        ]
    )
    has_children = any(
        word in upper
        for word in [
            "CHILD", "CHILDREN", "BABY", "INFANT",
            "KIDS", "SON", "DAUGHTER",
        ]
    )
    has_disabled = any(
        word in upper
        for word in [
            "DISABLED", "WHEELCHAIR", "PARALYZED",
            "HANDICAPPED", "BLIND",
        ]
    )

    medical_keywords = [
        "insulin", "asthma", "inhaler", "first aid", "bandages",
        "saline", "oxygen", "water", "food", "medicine", "tablets",
        "fever", "heart", "dialysis", "blood", "wound", "fracture",
        "delivery", "pregnant",
    ]
    found_meds = [
        keyword.title()
        for keyword in medical_keywords
        if keyword in clean_text.lower()
    ]
    medical_summary = (
        ", ".join(found_meds)
        if found_meds
        else "General Emergency Medical & Relief Assistance"
    )

    geo = geocode_from_text(clean_text)

    return {
        "intent": "SOS_TRIGGER",
        "urgency_level": urgency,
        "affected_people": affected_people,
        "district": geo["district"],
        "ds_division": geo["ds"],
        "gn_division": geo["gn"],
        "latitude": geo["lat"],
        "longitude": geo["lng"],
        "has_elderly": has_elderly,
        "has_children": has_children,
        "has_disabled": has_disabled,
        "medical_needs": medical_summary,
        "action": "trigger_sos",
    }


# ---------------------------------------------------------------------------
# Inbound SMS processing pipeline
# ---------------------------------------------------------------------------

def process_incoming_sms(
    sender: str,
    message_text: str,
    recipient: str,
    provider: str,
    db: Session,
) -> Tuple[SMSMessageLog, Dict[str, Any]]:
    """
    Process an inbound SMS:
      1. Normalise sender.
      2. Log inbound message.
      3. Parse intent.
      4. Execute the appropriate domain action.
      5. Generate an auto-reply.
      6. Send the reply through SMSGo.
      7. Log outbound SMS and notification records.
    """
    try:
        sender_clean = _validate_phone(sender)
    except ValueError as exc:
        logger.warning("[SMS-INBOUND] Invalid sender number: %s", exc)
        sender_clean = sender.strip()

    message_text = message_text.strip()
    parsed = parse_inbound_sms(message_text)
    intent = parsed.get("intent", "UNKNOWN")

    inbound_log = SMSMessageLog(
        direction="inbound",
        sender=sender_clean,
        recipient=recipient,
        message_text=message_text,
        message_type="EMERGENCY_SOS" if intent == "SOS_TRIGGER" else intent,
        parsed_intent=intent,
        parsed_payload_json=json.dumps(parsed),
        status="received",
        gateway_provider=provider,
    )
    db.add(inbound_log)
    db.flush()

    auto_reply = ""
    sos_id = None
    victim_id = None
    ml_priority = None

    if intent == "SOS_TRIGGER":
        user = db.query(User).filter(User.phone == sender_clean).first()

        if not user:
            victim_role = (
                db.query(Role)
                .filter(Role.name == RoleEnum.victim)
                .first()
            )
            role_id = victim_role.id if victim_role else 2

            user = User(
                full_name=f"SMS Sender ({sender_clean[-4:]})",
                email=(
                    f"sms_{re.sub(r'[^0-9]', '', sender_clean)}"
                    "@sms.dr.relief.lk"
                ),
                hashed_password="SMS_UNAUTHENTICATED_ACCOUNT",
                phone=sender_clean,
                address=f"{parsed['gn_division']}, {parsed['district']}",
                role_id=role_id,
                is_active=True,
            )
            db.add(user)
            db.flush()

        urgency = parsed["urgency_level"]
        affected = parsed["affected_people"]

        ml_priority = round(
            min(
                urgency * 17.5
                + affected * 2.5
                + (10 if parsed["has_elderly"] else 0)
                + (10 if parsed["has_disabled"] else 0)
                + (5 if parsed["has_children"] else 0),
                99.5,
            ),
            1,
        )

        sos = SOSRequest(
            user_id=user.id,
            latitude=parsed["latitude"],
            longitude=parsed["longitude"],
            district=parsed["district"],
            ds_division=parsed["ds_division"],
            gn_division=parsed["gn_division"],
            address_text=f"Reported via SMS: {message_text[:120]}",
            urgency_level=urgency,
            affected_people=affected,
            affected_families=max(1, affected // 4),
            has_elderly=parsed["has_elderly"],
            has_children=parsed["has_children"],
            has_disabled=parsed["has_disabled"],
            medical_needs_summary=parsed["medical_needs"],
            priority_score=ml_priority,
            status="active",
        )
        db.add(sos)
        db.flush()

        sos_id = sos.id
        inbound_log.sos_request_id = sos.id
        inbound_log.status = "processed"

        auto_reply = (
            f"[{settings.SMS_SENDER_NAME}] SOS #{sos.id} RECEIVED. "
            f"Priority: {ml_priority}/100 (Urgency {urgency}/5). "
            f"Location: {parsed['district']}. "
            f"Shortcode: {settings.SMS_EMERGENCY_SHORTCODE}"
        )

    elif intent == "VICTIM_REGISTRATION":
        vuln_score = calculate_vulnerability_score(
            family_members_count=parsed.get("family_count", 1),
            evacuation_status="trapped_in_house",
            immediate_medical_needs=parsed.get("medical_needs"),
        )

        existing_victim = (
            db.query(Victim)
            .filter(Victim.phone == sender_clean)
            .first()
        )

        if existing_victim:
            victim_id = existing_victim.id
            auto_reply = (
                f"[{settings.SMS_SENDER_NAME}] Already registered: "
                f"{existing_victim.full_name} (ID #{existing_victim.id}). "
                "Send SOS with your location for emergency dispatch."
            )
        else:
            victim = Victim(
                full_name=parsed.get("full_name", "SMS Victim"),
                phone=sender_clean,
                nic=parsed.get("nic"),
                district=parsed.get("district", "Colombo"),
                ds_division=parsed.get("ds_division"),
                gn_division=parsed.get("gn_division"),
                latitude=parsed.get("latitude", 6.9271),
                longitude=parsed.get("longitude", 79.8612),
                family_members_count=parsed.get("family_count", 1),
                immediate_medical_needs=parsed.get("medical_needs"),
                vulnerability_score=vuln_score,
                registered_via="sms_gateway",
                evacuation_status="trapped_in_house",
            )
            db.add(victim)
            db.flush()

            victim_id = victim.id
            inbound_log.victim_id = victim.id
            inbound_log.status = "processed"

            auto_reply = (
                f"[{settings.SMS_SENDER_NAME}] Registered: "
                f"{victim.full_name} (ID #{victim.id}, {victim.district}). "
                f"Vulnerability score: {vuln_score}%."
            )

    elif intent == "STATUS_CHECK":
        requested_id = parsed.get("sos_id")
        sos = None

        if requested_id:
            sos = (
                db.query(SOSRequest)
                .filter(SOSRequest.id == requested_id)
                .first()
            )
        else:
            user = (
                db.query(User)
                .filter(User.phone == sender_clean)
                .first()
            )
            if user:
                sos = (
                    db.query(SOSRequest)
                    .filter(SOSRequest.user_id == user.id)
                    .order_by(SOSRequest.created_at.desc())
                    .first()
                )

        inbound_log.status = "processed"

        if sos:
            sos_id = sos.id
            auto_reply = (
                f"[{settings.SMS_SENDER_NAME}] SOS #{sos.id}: "
                f"Status '{sos.status.upper()}'. "
                f"Priority: {sos.priority_score}/100. "
                f"Location: {sos.district}."
            )
        else:
            auto_reply = (
                f"[{settings.SMS_SENDER_NAME}] No SOS found for your number. "
                f"Emergency: {settings.SMS_EMERGENCY_SHORTCODE}"
            )

    elif intent == "CAMP_QUERY":
        district = parsed.get("district", "Colombo")
        camps = (
            db.query(MedicalCamp)
            .filter(
                MedicalCamp.district == district,
                MedicalCamp.status.in_(["approved", "operational"]),
            )
            .limit(3)
            .all()
        )

        inbound_log.status = "processed"

        if camps:
            camp_info = ", ".join(
                [f"{camp.name} (Capacity: {camp.estimated_capacity})"
                 for camp in camps]
            )
            auto_reply = (
                f"[{settings.SMS_SENDER_NAME}] Camps in {district}: "
                f"{camp_info}. Emergency: "
                f"{settings.SMS_EMERGENCY_SHORTCODE}"
            )
        else:
            auto_reply = (
                f"[{settings.SMS_SENDER_NAME}] No approved camps active "
                f"in {district}. Emergency: "
                f"{settings.SMS_EMERGENCY_SHORTCODE}"
            )

    elif intent == "HELP":
        inbound_log.status = "processed"
        auto_reply = (
            f"[{settings.SMS_SENDER_NAME}] Commands: "
            "SOS <urgency> <location> <people> <needs>; "
            "REG <name> <NIC> <district> <family size>; "
            "STATUS; CAMP <district>; HELP. "
            f"Emergency: {settings.SMS_EMERGENCY_SHORTCODE}"
        )

    else:
        inbound_log.status = "processed"
        auto_reply = (
            f"[{settings.SMS_SENDER_NAME}] Message received. "
            "For commands, reply HELP. "
            f"Emergency: {settings.SMS_EMERGENCY_SHORTCODE}"
        )

    dispatch_result = _dispatch_sms(to=sender_clean, body=auto_reply)

    outbound_log = SMSMessageLog(
        direction="outbound",
        sender=settings.SMS_SENDER_NAME,
        recipient=sender_clean,
        message_text=auto_reply,
        message_type="SYSTEM_CONFIRMATION",
        parsed_intent=intent,
        sos_request_id=sos_id,
        victim_id=victim_id,
        status=dispatch_result["status"],
        gateway_provider=dispatch_result["provider"],
        raw_payload=json.dumps(dispatch_result),
    )
    db.add(outbound_log)

    notif = Notification(
        recipient_user_id=None,
        channel="SMS",
        message_type=f"SMS_{intent}",
        recipient_target=sender_clean,
        message_content=auto_reply,
        dispatch_status=dispatch_result["status"],
    )
    db.add(notif)
    db.commit()

    result_summary: Dict[str, Any] = {
        "intent": intent,
        "sender_phone": sender_clean,
        "urgency_level": parsed.get("urgency_level", 4),
        "extracted_district": parsed.get("district"),
        "extracted_location": (
            parsed.get("gn_division") or parsed.get("district")
        ),
        "affected_people": parsed.get(
            "affected_people", parsed.get("family_count", 1)
        ),
        "medical_needs": parsed.get("medical_needs"),
        "ml_priority_score": ml_priority,
        "sos_id": sos_id,
        "victim_id": victim_id,
        "auto_reply_message": auto_reply,
        "sms_dispatch_status": dispatch_result["status"],
        "sms_sid": dispatch_result.get("sid"),
        "sms_provider": dispatch_result["provider"],
        "action_taken": (
            f"Parsed {intent}; SMS status "
            f"{dispatch_result['status']} via "
            f"{dispatch_result['provider']}."
        ),
    }

    return inbound_log, result_summary


# ---------------------------------------------------------------------------
# Direct outbound SMS
# ---------------------------------------------------------------------------

def send_direct_sms(
    recipient: str,
    message: str,
    message_type: str,
    db: Session,
) -> SMSMessageLog:
    """Send and log an SMS to one recipient."""
    recipient_clean = _validate_phone(recipient)

    message_clean = message.strip()
    if not message_clean:
        raise ValueError("SMS message cannot be empty.")

    dispatch_result = _dispatch_sms(
        to=recipient_clean,
        body=message_clean,
    )

    sms = SMSMessageLog(
        direction="outbound",
        sender=settings.SMS_SENDER_NAME,
        recipient=recipient_clean,
        message_text=message_clean,
        message_type=message_type,
        status=dispatch_result["status"],
        gateway_provider=dispatch_result["provider"],
        raw_payload=json.dumps(dispatch_result),
    )
    db.add(sms)

    notif = Notification(
        channel="SMS",
        message_type=message_type,
        recipient_target=recipient_clean,
        message_content=message_clean,
        dispatch_status=dispatch_result["status"],
    )
    db.add(notif)
    db.commit()
    db.refresh(sms)

    return sms


# ---------------------------------------------------------------------------
# Emergency broadcast SMS
# ---------------------------------------------------------------------------

def broadcast_emergency_sms(
    message: str,
    district: Optional[str],
    role: Optional[str],
    urgency: str,
    db: Session,
) -> int:
    """
    Broadcast to registered victims/users matching the requested filters.

    Returns the number of unique recipients processed.
    No fake fallback phone numbers are used.
    """
    recipients: List[str] = []

    victim_query = db.query(Victim).filter(Victim.phone.isnot(None))
    if district:
        victim_query = victim_query.filter(
            Victim.district.ilike(f"%{district}%")
        )

    for victim in victim_query.all():
        try:
            phone = _validate_phone(victim.phone)
            if phone not in recipients:
                recipients.append(phone)
        except (ValueError, AttributeError):
            logger.warning(
                "[BROADCAST] Skipping invalid victim phone."
            )

    user_query = db.query(User).filter(
        User.phone.isnot(None),
        User.is_active.is_(True),
    )

    if role:
        target_role = db.query(Role).filter(Role.name == role).first()
        if target_role:
            user_query = user_query.filter(
                User.role_id == target_role.id
            )

    for user in user_query.all():
        try:
            phone = _validate_phone(user.phone)
            if phone not in recipients:
                recipients.append(phone)
        except (ValueError, AttributeError):
            logger.warning(
                "[BROADCAST] Skipping invalid user phone."
            )

    if not recipients:
        logger.warning(
            "[BROADCAST] No registered recipients matched the filters."
        )
        return 0

    formatted_msg = (
        f"[EMERGENCY ALERT - {urgency.upper()}] "
        f"{message.strip()} — Disaster Relief Command."
    )

    processed_count = 0

    for recipient in recipients:
        dispatch_result = _dispatch_sms(
            to=recipient,
            body=formatted_msg,
        )

        sms = SMSMessageLog(
            direction="outbound",
            sender=settings.SMS_SENDER_NAME,
            recipient=recipient,
            message_text=formatted_msg,
            message_type="BROADCAST_ALERT",
            status=dispatch_result["status"],
            gateway_provider=dispatch_result["provider"],
            raw_payload=json.dumps(dispatch_result),
        )
        db.add(sms)

        notif = Notification(
            channel="SMS",
            message_type=f"BROADCAST_{urgency.upper()}",
            recipient_target=recipient,
            message_content=formatted_msg,
            dispatch_status=dispatch_result["status"],
        )
        db.add(notif)
        processed_count += 1

    db.commit()
    return processed_count


# ---------------------------------------------------------------------------
# Gateway status
# ---------------------------------------------------------------------------

def get_gateway_telecom_status(db: Session) -> Dict[str, Any]:
    """Return SMS gateway metrics and recent dispatch status counts."""
    inbound_count = (
        db.query(SMSMessageLog)
        .filter(SMSMessageLog.direction == "inbound")
        .count()
    )
    outbound_count = (
        db.query(SMSMessageLog)
        .filter(SMSMessageLog.direction == "outbound")
        .count()
    )
    sent_count = (
        db.query(SMSMessageLog)
        .filter(SMSMessageLog.status == "sent")
        .count()
    )
    sim_count = (
        db.query(SMSMessageLog)
        .filter(SMSMessageLog.status == "simulated")
        .count()
    )
    failed_count = (
        db.query(SMSMessageLog)
        .filter(SMSMessageLog.status == "failed")
        .count()
    )
    active_alerts = (
        db.query(SOSRequest)
        .filter(SOSRequest.status == "active")
        .count()
    )

    # Determine active provider mode
    if settings.TEXTLK_ENABLED:
        if not settings.TEXTLK_API_TOKEN.strip():
            mode = "CONFIGURATION ERROR — TEXTLK_API_TOKEN is empty"
            provider = "Text.lk (token missing)"
        else:
            mode = "LIVE — Text.lk Enabled"
            provider = "Text.lk API v3 (https://app.text.lk/api/v3/sms/send)"
    elif settings.SMSGO_ENABLED:
        if settings.SMSGO_API_KEY.startswith("sg_test_"):
            mode = "SANDBOX — SMSGo Test Key (legacy fallback)"
            provider = "SMSGo Sandbox (No real SMS sent)"
        elif settings.SMSGO_API_KEY.startswith("sg_live_"):
            mode = "LIVE — SMSGo Enabled (legacy fallback)"
            provider = "SMSGo Live API"
        else:
            mode = "CONFIGURATION ERROR — Check SMSGo API Key"
            provider = "SMSGo (key type not recognised)"
    else:
        mode = "SIMULATION — Text.lk and SMSGo both disabled"
        provider = "LOCAL SIMULATOR (no real SMS sent)"

    success_rate = (
        round((sent_count + sim_count) / outbound_count * 100, 1)
        if outbound_count > 0
        else 0.0
    )

    return {
        "gateway_status": f"ONLINE — {mode}",
        "active_carrier": provider,
        "textlk_enabled": settings.TEXTLK_ENABLED,
        "smsgo_enabled": settings.SMSGO_ENABLED,
        "provider": "TEXTLK" if settings.TEXTLK_ENABLED else "SMSGO",
        "total_inbound_processed": inbound_count,
        "total_outbound_processed": outbound_count,
        "sent_count": sent_count,
        "simulated_count": sim_count,
        "failed_count": failed_count,
        "active_emergency_alerts": active_alerts,
        "dispatch_success_rate": success_rate,
        "supported_keywords": [
            "SOS", "REG", "STATUS", "CAMP", "HELP", "INFO"
        ],
    }
