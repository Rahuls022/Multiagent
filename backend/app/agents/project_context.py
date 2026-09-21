"""Intelligent project interpreter and domain context generator.

Synthesizes rich domain models, API specifications, database schemas, and
code generation parameters for any mission request.
"""

import re
from typing import Any


def project_context(request: str) -> dict[str, Any]:
    text = request.lower().strip()
    clean_name = (
        re.sub(r"^(build|create|develop|design|make|setup)\s+(a|an|the)?\s*", "", request, flags=re.IGNORECASE)
        .strip()
        .capitalize()
    )
    if not clean_name:
        clean_name = "Application Portal"

    # Domain-specific knowledge synthesis profiles
    if any(k in text for k in ["student", "school", "education", "university", "academic", "course"]):
        return {
            "name": clean_name,
            "kind": "Student Management & Academic Portal",
            "actor": "Student & Administrator",
            "entity": "student",
            "plural": "students",
            "primary_action": "manage student enrollments, track courses, view grades, and monitor academic progress",
            "features": [
                "Student Directory & Profile Management",
                "Course Registration & Enrollment Tracking",
                "Gradebook & Academic Transcript Generator",
                "Attendance & Performance Analytics Dashboard",
            ],
            "domain_models": [
                {
                    "name": "Student",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Unique student identifier"},
                        {"name": "student_code", "type": "String", "description": "Unique matriculation code (e.g. STU-2026-001)"},
                        {"name": "first_name", "type": "String", "description": "Student given name"},
                        {"name": "last_name", "type": "String", "description": "Student family name"},
                        {"name": "email", "type": "String", "description": "Institutional email address"},
                        {"name": "department", "type": "String", "description": "Academic department or major"},
                        {"name": "gpa", "type": "Float", "description": "Cumulative Grade Point Average"},
                        {"name": "status", "type": "Enum", "description": "Active | Graduated | On Leave | Suspended"},
                    ],
                },
                {
                    "name": "Course",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Course identifier"},
                        {"name": "code", "type": "String", "description": "Course catalog code (e.g. CS101)"},
                        {"name": "title", "type": "String", "description": "Course name"},
                        {"name": "credits", "type": "Integer", "description": "Academic credit value"},
                        {"name": "instructor", "type": "String", "description": "Primary faculty member"},
                    ],
                },
                {
                    "name": "Enrollment",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Enrollment record ID"},
                        {"name": "student_id", "type": "UUID", "description": "Foreign key to Student"},
                        {"name": "course_id", "type": "UUID", "description": "Foreign key to Course"},
                        {"name": "semester", "type": "String", "description": "Academic term (e.g. Fall 2026)"},
                        {"name": "grade", "type": "String", "description": "Final letter grade (A, B+, etc.)"},
                    ],
                },
            ],
            "routes": [
                {"method": "GET", "path": "/api/students", "description": "List all enrolled students with search & department filters"},
                {"method": "POST", "path": "/api/students", "description": "Register a new student profile in the portal"},
                {"method": "GET", "path": "/api/students/{id}", "description": "Retrieve detailed student profile and transcript"},
                {"method": "PATCH", "path": "/api/students/{id}", "description": "Update student status, contact info, or GPA"},
                {"method": "POST", "path": "/api/enrollments", "description": "Enroll a student in an academic course"},
                {"method": "GET", "path": "/api/courses", "description": "Browse active course catalog and credit requirements"},
            ],
            "ui": [
                "Student Directory & Metrics Cards",
                "New Student Registration Form Modal",
                "Student Detail & Academic Transcript View",
                "Course Enrollment & Grade Management Panel",
            ],
            "feature_slug": "students",
            "pascal_entity": "Student",
        }

    if any(k in text for k in ["hospital", "patient", "clinic", "health", "medical", "doctor", "appointment"]):
        return {
            "name": clean_name,
            "kind": "Healthcare & Patient Appointment Portal",
            "actor": "Patient & Healthcare Provider",
            "entity": "appointment",
            "plural": "appointments",
            "primary_action": "schedule medical consultations, manage patient medical records, and view prescription history",
            "features": [
                "Doctor Search & Availability Calendar",
                "Patient Appointment Booking & Reminders",
                "Electronic Health Records (EHR) Explorer",
                "Medical Billing & Consultation History",
            ],
            "domain_models": [
                {
                    "name": "Patient",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Patient account ID"},
                        {"name": "full_name", "type": "String", "description": "Patient full legal name"},
                        {"name": "dob", "type": "Date", "description": "Date of birth"},
                        {"name": "medical_history", "type": "Text", "description": "Allergies and pre-existing conditions"},
                    ],
                },
                {
                    "name": "Appointment",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Appointment record ID"},
                        {"name": "patient_id", "type": "UUID", "description": "Patient reference"},
                        {"name": "doctor_name", "type": "String", "description": "Attending physician"},
                        {"name": "scheduled_time", "type": "DateTime", "description": "Date and time of appointment"},
                        {"name": "reason", "type": "String", "description": "Chief medical complaint"},
                        {"name": "status", "type": "Enum", "description": "Scheduled | Completed | Cancelled"},
                    ],
                },
            ],
            "routes": [
                {"method": "GET", "path": "/api/appointments", "description": "List patient appointments by date and provider"},
                {"method": "POST", "path": "/api/appointments", "description": "Book a new consultation appointment"},
                {"method": "GET", "path": "/api/patients/{id}", "description": "Fetch patient medical profile and EHR records"},
                {"method": "PATCH", "path": "/api/appointments/{id}", "description": "Update appointment status or reschedule"},
            ],
            "ui": [
                "Appointment Calendar & Timetable",
                "Patient Registration Form",
                "Doctor Availability Cards",
                "Medical Record Detail View",
            ],
            "feature_slug": "appointments",
            "pascal_entity": "Appointment",
        }

    if any(k in text for k in ["store", "shop", "e-commerce", "ecommerce", "order", "product", "inventory"]):
        return {
            "name": clean_name,
            "kind": "E-Commerce & Order Management Platform",
            "actor": "Customer & Store Manager",
            "entity": "product order",
            "plural": "orders",
            "primary_action": "browse product catalog, manage shopping cart, process orders, and track shipments",
            "features": [
                "Product Catalog with Category Filters & Search",
                "Real-time Shopping Cart & Inventory Count",
                "Secure Checkout & Payment Gateway",
                "Order Fulfillment & Delivery Status Tracking",
            ],
            "domain_models": [
                {
                    "name": "Product",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Stock keeping unit ID"},
                        {"name": "name", "type": "String", "description": "Product title"},
                        {"name": "price", "type": "Decimal", "description": "Retail price in USD"},
                        {"name": "stock_quantity", "type": "Integer", "description": "Available inventory stock"},
                    ],
                },
                {
                    "name": "Order",
                    "fields": [
                        {"name": "id", "type": "UUID", "description": "Order reference number"},
                        {"name": "customer_email", "type": "String", "description": "Buyer contact email"},
                        {"name": "total_amount", "type": "Decimal", "description": "Total purchase cost"},
                        {"name": "status", "type": "Enum", "description": "Pending | Processing | Shipped | Delivered"},
                    ],
                },
            ],
            "routes": [
                {"method": "GET", "path": "/api/products", "description": "List available products in catalog"},
                {"method": "POST", "path": "/api/orders", "description": "Place a new order with cart items"},
                {"method": "GET", "path": "/api/orders/{id}", "description": "Check order status and tracking details"},
                {"method": "PATCH", "path": "/api/orders/{id}", "description": "Update order fulfillment stage"},
            ],
            "ui": [
                "Product Grid View",
                "Shopping Cart Drawer",
                "Checkout Summary Form",
                "Order History & Tracking Panel",
            ],
            "feature_slug": "orders",
            "pascal_entity": "Order",
        }

    # Generic dynamic fallback for any other mission
    words = [w for w in clean_name.split() if w.lower() not in ["app", "portal", "system", "platform", "manager", "tracker"]]
    main_word = words[0] if words else "Record"
    entity = main_word.lower()
    plural = f"{entity}s"
    pascal_entity = main_word.capitalize()

    return {
        "name": clean_name,
        "kind": f"{clean_name} Operations System",
        "actor": "Operator & End User",
        "entity": entity,
        "plural": plural,
        "primary_action": f"manage, create, update, and inspect {plural} efficiently",
        "features": [
            f"{clean_name} Interactive Dashboard & Analytics",
            f"Validated {pascal_entity} Creation & Form Management",
            f"Search, Filtering, and Batch Operations for {plural.capitalize()}",
            "Audit Trail, Activity Logs, and System Status Metrics",
        ],
        "domain_models": [
            {
                "name": pascal_entity,
                "fields": [
                    {"name": "id", "type": "UUID", "description": f"Unique {entity} identifier"},
                    {"name": "title", "type": "String", "description": f"Name or label of the {entity}"},
                    {"name": "status", "type": "Enum", "description": "Draft | Active | Archived | Completed"},
                    {"name": "created_at", "type": "DateTime", "description": "Creation timestamp"},
                    {"name": "updated_at", "type": "DateTime", "description": "Last modified timestamp"},
                ],
            },
            {
                "name": f"{pascal_entity}Activity",
                "fields": [
                    {"name": "id", "type": "UUID", "description": "Log record ID"},
                    {"name": f"{entity}_id", "type": "UUID", "description": f"Reference to {pascal_entity}"},
                    {"name": "action", "type": "String", "description": "Action performed (e.g. Created, Updated)"},
                    {"name": "performed_by", "type": "String", "description": "User identifier"},
                ],
            },
        ],
        "routes": [
            {"method": "GET", "path": f"/api/{plural}", "description": f"Retrieve list of {plural} with pagination"},
            {"method": "POST", "path": f"/api/{plural}", "description": f"Create a new {entity} record"},
            {"method": "GET", "path": f"/api/{plural}/{{id}}", "description": f"Fetch details for a specific {entity}"},
            {"method": "PATCH", "path": f"/api/{plural}/{{id}}", "description": f"Update properties or status of a {entity}"},
            {"method": "DELETE", "path": f"/api/{plural}/{{id}}", "description": f"Soft delete or archive a {entity}"},
        ],
        "ui": [
            f"{pascal_entity} Overview Dashboard",
            f"Create {pascal_entity} Modal Form",
            f"{pascal_entity} Details & History Timeline",
            "System Health & Metric Cards",
        ],
        "feature_slug": plural,
        "pascal_entity": pascal_entity,
    }
