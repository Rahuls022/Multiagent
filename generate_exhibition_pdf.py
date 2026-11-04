import sys
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(36, letter[1] - 30, letter[0] - 36, letter[1] - 30)
        self.drawString(36, letter[1] - 25, "Autonomous DevOps Swarm — 8-Agent Architecture Exhibition Guide")
        
        # Footer line
        self.line(36, 35, letter[0] - 36, 35)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 22, page_text)
        self.drawString(36, 22, "Confidential — Academic & Technical Project Exhibition")
        self.restoreState()

def build_pdf(filename="Autonomous_DevOps_Swarm_Exhibition_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SectionHeading1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionHeading2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0f172a')
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1e293b')
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor('#0284c7')
    )

    elements = []

    # Title block
    elements.append(Paragraph("Autonomous DevOps Swarm", title_style))
    elements.append(Paragraph("Complete 8-Agent Architecture & Live Demonstration Exhibition Guide", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # Section 1: The 30-Second Elevator Pitch
    elements.append(Paragraph("1. The 30-Second Elevator Pitch (For Judges & Stall Visitors)", h1_style))
    pitch_text = (
        "<b>\"Welcome! Our project is the Autonomous DevOps Swarm</b> — an intelligent multi-agent platform where "
        "<b>8 specialized AI agents</b> act as a complete, autonomous software engineering and operations department.<br/><br/>"
        "When an operator gives a single business prompt — like <i>'Build a Juice Centre website with online ordering and cart'</i> — "
        "the 8 agents automatically collaborate: extracting requirements, writing domain-specific full-stack code, validating AST syntax, "
        "enforcing quality test coverage, auditing cybersecurity vulnerabilities, compiling release manifests, deploying an isolated live server, "
        "and running an automated Self-Healing Engine when runtime faults occur.<br/><br/>"
        "You can view the resulting application running live right now in our built-in interactive Website Viewer!\""
    )
    pitch_table = Table([[Paragraph(pitch_text, callout_style)]], colWidths=[letter[0] - 72])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fdf4')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#22c55e')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(pitch_table)
    elements.append(Spacer(1, 8))

    # Section 2: Why We Built This
    elements.append(Paragraph("2. Why We Built This: Problem vs Solution", h1_style))
    comp_data = [
        [
            Paragraph("Traditional Software Development", table_header_style),
            Paragraph("Our Autonomous DevOps Swarm", table_header_style)
        ],
        [
            Paragraph("Handoffs between architects, programmers, QA testers, security auditors, and SREs cause communication delays and human error.", table_cell_style),
            Paragraph("<b>Autonomous 8-Agent Swarm:</b> Specialized agents collaborate in real-time through an observable orchestration blackboard pipeline.", table_cell_style)
        ],
        [
            Paragraph("Standard LLM code tools output generic, disconnected snippets (e.g. giving an electronics store template when asked for a Juice Centre).", table_cell_style),
            Paragraph("<b>Domain-Aware Full-Stack Generation:</b> Dynamically creates real product catalogs, live interactive carts, checkout modals, and SQLite persistence.", table_cell_style)
        ],
        [
            Paragraph("When code breaks in production, engineers spend hours debugging stack traces and deploying hotfixes.", table_cell_style),
            Paragraph("<b>Real-Time Self-Healing Engine:</b> Detects runtime failures, diagnoses root cause, generates verified patches, and stores solutions in persistent memory.", table_cell_style)
        ]
    ]
    comp_table = Table(comp_data, colWidths=[(letter[0]-72)/2, (letter[0]-72)/2])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(comp_table)
    elements.append(Spacer(1, 10))

    # Section 3: The 8-Agent Architecture
    elements.append(Paragraph("3. How All 8 Agents Work in Synchrony", h1_style))
    elements.append(Paragraph(
        "The swarm is divided into two synchronized 4-agent teams: the <b>Collaborative Dev Team</b> (responsible for creation) "
        "and the <b>Operations & Reliability Swarm</b> (responsible for security, deployment, and autonomous maintenance).",
        body_style
    ))
    elements.append(Spacer(1, 4))

    agents_data = [
        [
            Paragraph("Agent Name & Team", table_header_style),
            Paragraph("Specialized Skill / Standard", table_header_style),
            Paragraph("Role & Core Responsibility in Swarm", table_header_style)
        ],
        # Phase 1: Collaborative Dev Team
        [
            Paragraph("<b>1. Planning Agent</b><br/><font color='#2563eb'>Dev Team</font>", table_cell_style),
            Paragraph("<code>writing-plans</code><br/><i>(skills.sh)</i>", table_cell_style),
            Paragraph("<b>Technical Product Manager & Architect:</b> Reads user request, extracts industry domain (Juice Centre, Store, Clinic), designs DB schema, decomposes tasks, and plans endpoints.", table_cell_style)
        ],
        [
            Paragraph("<b>2. Coding Agent</b><br/><font color='#2563eb'>Dev Team</font>", table_cell_style),
            Paragraph("<code>frontend-design</code><br/><i>(skills.sh)</i>", table_cell_style),
            Paragraph("<b>Senior Full-Stack Developer:</b> Writes clean UI and backend logic. Generates domain catalogs (e.g. Orange, Mango juices), real +/- cart math, checkout modal, and REST endpoints.", table_cell_style)
        ],
        [
            Paragraph("<b>3. Build Agent</b><br/><font color='#2563eb'>Dev Team</font>", table_cell_style),
            Paragraph("<code>systematic-debugging</code><br/><i>(skills.sh)</i>", table_cell_style),
            Paragraph("<b>Build Engineer:</b> Performs Abstract Syntax Tree (AST) validation to guarantee zero syntax defects, validates imports, checks package configs, and prevents broken builds.", table_cell_style)
        ],
        [
            Paragraph("<b>4. Testing Agent</b><br/><font color='#2563eb'>Dev Team</font>", table_cell_style),
            Paragraph("<code>verification-before-completion</code><br/><i>(skills.sh)</i>", table_cell_style),
            Paragraph("<b>QA Automation Lead:</b> Enforces 'evidence before assertions.' Executes automated unit and integration tests, measures test coverage (>80%), and certifies code quality.", table_cell_style)
        ],
        # Phase 2: Operations & Reliability Swarm
        [
            Paragraph("<b>5. Security Agent</b><br/><font color='#16a34a'>Ops Swarm</font>", table_cell_style),
            Paragraph("<code>SAST & Secret Auditing</code>", table_cell_style),
            Paragraph("<b>Cybersecurity Auditor:</b> Scans source code for OWASP vulnerabilities, audits Role-Based Access Control (RBAC), and verifies no API tokens or passwords are leak-exposed.", table_cell_style)
        ],
        [
            Paragraph("<b>6. Release Agent</b><br/><font color='#16a34a'>Ops Swarm</font>", table_cell_style),
            Paragraph("<code>Release Manifest Assembly</code>", table_cell_style),
            Paragraph("<b>Release Manager:</b> Packages versioned release manifests, manages artifact hashes, verifies rollback points, and gates approvals before deployment.", table_cell_style)
        ],
        [
            Paragraph("<b>7. Deploy Agent</b><br/><font color='#16a34a'>Ops Swarm</font>", table_cell_style),
            Paragraph("<code>Dynamic Server Provisioning</code>", table_cell_style),
            Paragraph("<b>Cloud & Deployment Engineer:</b> Allocates isolated workspace port, initiates background runtime process, and exposes the live URL for instant browser inspection.", table_cell_style)
        ],
        [
            Paragraph("<b>8. Monitor & Self-Healing</b><br/><font color='#16a34a'>Ops Swarm</font>", table_cell_style),
            Paragraph("<code>Runtime Telemetry & Healing</code>", table_cell_style),
            Paragraph("<b>SRE & Autonomous Healer:</b> Continuously tracks health metrics. Upon defect detection, triggers the Self-Healing engine to diagnose root-cause, patch code, and log fix in SQLite memory.", table_cell_style)
        ]
    ]

    agents_table = Table(agents_data, colWidths=[120, 110, letter[0] - 72 - 230])
    agents_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(agents_table)
    elements.append(Spacer(1, 12))

    # Page Break for Demo & Q&A
    elements.append(PageBreak())

    # Section 4: Live Demonstration Script for Judges
    elements.append(Paragraph("4. Step-by-Step Live Demonstration Script for Judges", h1_style))
    elements.append(Paragraph(
        "Follow these 4 clear steps during the exhibition demo. Speak the exact sentences provided for maximum impact.",
        body_style
    ))
    elements.append(Spacer(1, 4))

    demo_steps = [
        ("Step 1: Open Dashboard & Demonstrate Persistent Login",
         "\"First, we have enterprise-grade persistent security. Even if I refresh the page or restart the backend server, my authenticated session remains completely active via salted PBKDF2 hashing and signed tokens.\"",
         "Show the Swarm DevOps Control dashboard with your logged-in operator account. Hit refresh (F5) to prove zero session loss."),
        
        ("Step 2: Launch a Mission & Watch the 8-Agent Swarm",
         "\"Now, let's submit a business requirement: 'Create a website for a Juice Centre to accept online orders with fresh juice products, cart, and checkout.' Watch the live timeline as all 8 agents activate in sequence.\"",
         "Click Launch Mission. Show the timeline lighting up in real-time as Planning, Coding, Build, Testing, Security, Release, Deploy, and Monitor agents complete each stage."),
        
        ("Step 3: Open the Live Website Viewer / Workbench",
         "\"Notice that unlike standard AI chats that just print raw markdown snippets, our Swarm launches an actual live preview server. Let's switch to the Website Preview tab to interact with the generated site.\"",
         "Switch to Website Preview tab. Click 'Add to Cart' on Orange and Mango juice, adjust quantities with (+/-), open the Checkout Modal, and show the source file tree in the sidebar."),
        
        ("Step 4: Demonstrate the Self-Healing Engine & Failure Memory",
         "\"Now let's demonstrate the swarm's autonomous resilience. In our Self-Healing tab, if a defect or syntax bug occurs, the Monitor Agent flags it, the Healing Agent analyzes the stack trace, applies a git patch, verifies it, and permanently logs the healed incident in our SQLite memory.\"",
         "Switch to the Self-Healing & Failure Memory tab and display the failure resolution log showing root-cause, patch diff, and verification status.")
    ]

    for title, say, act in demo_steps:
        step_content = [
            Paragraph(f"<b>{title}</b>", h2_style),
            Paragraph(f"<b>What to Say:</b> <i>{say}</i>", body_style),
            Paragraph(f"<b>What to Do on Screen:</b> {act}", body_style),
            Spacer(1, 4)
        ]
        elements.append(KeepTogether(step_content))

    elements.append(Spacer(1, 6))

    # Section 5: Judge Q&A Cheat Sheet
    elements.append(Paragraph("5. Judge Q&A Cheat Sheet (Prepared Answers)", h1_style))
    
    qas = [
        ("Q1: How do the 8 agents communicate with each other?",
         "Answer: They communicate through a structured blackboard architecture coordinated by the Development and Operations Supervisors. Each agent consumes validated JSON outputs from the preceding agent, eliminating ambiguity and avoiding free-form chat loops."),
        
        ("Q2: What prevents the Coding Agent from outputting generic, irrelevant templates?",
         "Answer: We integrated specialized skills like frontend-design from skills.sh and multi-domain heuristic classifiers. The Planning Agent first identifies the exact domain (e.g. food/beverage vs healthcare), which strictly binds the Coding Agent's catalog, calculations, and styles."),
        
        ("Q3: Where is the data stored and persisted?",
         "Answer: User credentials, mission pipelines, preview server metadata, and self-healing memory are persistently stored in our unified SQLite engine (devops_swarm.db), with seamless compatibility for MongoDB in containerized enterprise deployments."),
        
        ("Q4: Is the generated website really running or just an iframe mockup?",
         "Answer: It is a genuine, running web server. The Deploy Agent allocates an isolated port and workspace directory on disk. You can inspect the actual generated files in the Workbench and interact with real cart calculations in real-time.")
    ]

    for q, a in qas:
        qa_content = [
            Paragraph(f"<b>{q}</b>", h2_style),
            Paragraph(a, body_style),
            Spacer(1, 3)
        ]
        elements.append(KeepTogether(qa_content))

    doc.build(elements, canvasmaker=NumberedCanvas)
    print(f"SUCCESS: Generated {filename} ({os.path.getsize(filename)} bytes)")

if __name__ == "__main__":
    build_pdf()
