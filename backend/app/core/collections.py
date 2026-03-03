"""
Urban Cortex AI – Firestore Collection Name Constants
=======================================================

Centralized collection naming convention for Firestore.
All collection names are:
  - lowercase
  - plural
  - underscore_separated (where multi-word)

These constants MUST be used everywhere instead of raw strings
to prevent typos and ensure consistency across the codebase.

Mapping to PRD collections (Section 5.1):
  - users          → User profiles with role metadata
  - bins           → Waste bin IoT data + predictions
  - trucks         → Fleet truck entities
  - routes         → Computed collection routes
  - complaints     → Citizen-submitted complaints
  - investigations → Admin investigations linked to complaints
  - cities         → Multi-city scalability support
"""

from __future__ import annotations


class Collections:
    """Firestore collection name constants."""

    # PRD Section 5.1: users (Collection)
    USERS = "users"

    # PRD Section 5.1: bins (Collection)
    BINS = "bins"

    # PRD Section 5.1: trucks (Collection)
    TRUCKS = "trucks"

    # PRD Section 5.1: routes (Collection)
    ROUTES = "routes"

    # PRD Section 5.1: complaints (Collection)
    COMPLAINTS = "complaints"

    # PRD Section 5.1: investigations (Collection)
    INVESTIGATIONS = "investigations"

    # PRD Section 5.1: cities (Collection)
    CITIES = "cities"

    # Internal system collection (not in PRD – used for health checks)
    SYSTEM_HEALTH_CHECK = "_system_health_check"
