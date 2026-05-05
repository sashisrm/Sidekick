"""
Seed script: creates a demo user + realistic industrial automation test data
for YOKOGAWA, SIEMENS, SCHNEIDER ELECTRIC, and ABB as competitors.

Run inside the backend container:
  docker exec sidekick-backend-1 python seed_data.py
"""

import asyncio, json, uuid, os
from datetime import datetime, timezone
from pathlib import Path

# ── DB setup ────────────────────────────────────────────────────────────────
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db.models import Base, User, Product, Document, Competitor, CompetitorSnapshot, ScrapeStatus
from passlib.context import CryptContext

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sidekick:sidekick_pass@postgres:5432/sidekick_db"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Demo user ────────────────────────────────────────────────────────────────
DEMO_USER = {
    "email": "demo@sidekick.io",
    "name":  "Demo User",
    "password": "SideKick@2024",
    "role": "admin",
}

# ── Our product line (fictional IntelliProcess brand) ────────────────────────
OUR_PRODUCTS = [
    {
        "name": "IntelliProcess DCS",
        "category": "Distributed Control System",
        "features": {
            "tags": 250000,
            "redundancy": "Hot-standby dual controller",
            "protocols": ["HART", "FOUNDATION Fieldbus", "PROFIBUS", "OPC-UA", "Modbus"],
            "hmi": "Web-based, HTML5, multi-monitor",
            "safety": "SIL 3 certified (IEC 61511)",
            "cloud": "AWS / Azure hybrid historian",
            "engineering": "Graphical FBD, SFC, ST, IL, LD",
            "cybersecurity": "IEC 62443-3-3 Level 2",
            "industries": ["Oil & Gas", "Refining", "Chemical", "Power", "Mining"],
        },
        "pricing": {
            "starter": "$85,000 (up to 2,000 I/O)",
            "professional": "$220,000 (up to 25,000 I/O)",
            "enterprise": "Custom (250,000+ I/O, multi-site)",
        },
    },
    {
        "name": "IntelliSafe SIS",
        "category": "Safety Instrumented System",
        "features": {
            "sil_rating": "SIL 3",
            "standard": "IEC 61511 / IEC 61508",
            "response_time": "< 50 ms",
            "protocols": ["HART", "PROFIBUS PA", "OPC-UA"],
            "voting": "1oo1, 1oo2, 2oo3, 2oo4",
            "diagnostics": "Online self-test, continuous",
            "integration": "Seamless with IntelliProcess DCS",
        },
        "pricing": {
            "base": "$45,000 (per safety loop group)",
            "enterprise": "Custom SIL 3 projects",
        },
    },
    {
        "name": "IntelliField Transmitter IFT-900",
        "category": "Pressure / Differential Pressure Transmitter",
        "features": {
            "accuracy": "±0.025% of span",
            "rangeability": "200:1",
            "output": "4–20 mA HART 7, FOUNDATION Fieldbus, PROFIBUS PA",
            "materials": "316L SS, Hastelloy C-276, Monel",
            "approvals": ["ATEX", "IECEx", "FM", "CSA", "SIL 2"],
            "display": "Local LCD with backlight",
            "diagnostics": "Plugged impulse line detection",
        },
        "pricing": {
            "standard": "$1,200 – $2,800",
            "custom_materials": "$3,500+",
        },
    },
]

# ── Competitor snapshots ─────────────────────────────────────────────────────
COMPETITORS = [
    {
        "company_name": "Yokogawa Electric",
        "website_url": "https://www.yokogawa.com",
        "snapshot": {
            "pricing_tiers": {
                "CENTUM VP Starter":     "$95,000 – $130,000 (up to 3,000 I/O)",
                "CENTUM VP Standard":    "$240,000 – $480,000 (up to 50,000 I/O)",
                "CENTUM VP Enterprise":  "Custom quote (> 50,000 I/O, multi-domain)",
                "ProSafe-RS SIS":        "$52,000 base + $8,000/safety group",
                "EJA-E Transmitter":     "$1,400 – $3,200 standard range",
            },
            "key_features": [
                "CENTUM VP DCS – 300,000 I/O capacity, dual-redundant FCS controllers",
                "ProSafe-RS – SIL 3 certified safety system, tight DCS integration",
                "EJA-E series – ±0.04% accuracy, BRAIN / HART / FF / PA output",
                "FAST/TOOLS SCADA for pipeline and utility applications",
                "OpreX platform: cloud historian, digital twin, AI analytics",
                "Exaquantum plant historian – high-speed data collection",
                "Fieldmate device management with NAMUR NE107 diagnostics",
                "Strong in Oil & Gas, LNG, Refining, Chemical, Power",
            ],
            "target_segments": [
                "Oil & Gas upstream / midstream / downstream",
                "LNG liquefaction and regasification plants",
                "Chemical and petrochemical complexes",
                "Power generation (thermal, nuclear, renewable)",
                "Pharmaceutical and food & beverage (GAMP 5)",
            ],
            "integrations": [
                "SAP Plant Maintenance", "OSIsoft PI System", "AWS IoT Greengrass",
                "Microsoft Azure IoT Hub", "NAMUR Open Architecture (NOA)",
                "OPC-UA, MQTT, PROFIBUS, FOUNDATION Fieldbus, HART 7",
            ],
            "scraped_claims": [
                "Over 30,000 CENTUM systems installed globally",
                "#1 market share in Japan; top-3 globally in DCS",
                "IA2IA (Industrial Automation to Intelligent Automation) roadmap",
                "Lifecycle services: 20+ year support commitment",
                "Cyber-security: IEC 62443 certified engineering process",
            ],
            "confidence": "high",
            "pages_crawled": 18,
        },
    },
    {
        "company_name": "Siemens AG",
        "website_url": "https://www.siemens.com/process-automation",
        "snapshot": {
            "pricing_tiers": {
                "SIMATIC PCS 7 Entry":    "$70,000 – $110,000 (AS 410 controller)",
                "SIMATIC PCS 7 Standard": "$180,000 – $420,000 (AS 412 / 416)",
                "SIMATIC PCS 7 High-End": "Custom (AS 417 / 419, unlimited tags)",
                "PCS neo (cloud-native)":  "Subscription-based; contact Siemens",
                "SIMATIC S7-1500 PLC":    "$2,800 – $18,000 per CPU module",
                "WinCC Unified SCADA":    "$12,000 per server (runtime license)",
                "SITRANS P410 Transmitter": "$980 – $2,600",
            },
            "key_features": [
                "SIMATIC PCS 7 – proven DCS, AS 410–419 automation servers, unlimited I/O",
                "PCS neo – browser-based, containerized, cloud-native next-gen DCS",
                "SIMATIC S7-1500 – high-speed PLC with integrated safety (F-CPU)",
                "WinCC Unified – HTML5 SCADA, scalable from panel to enterprise",
                "SIMIT simulation platform for virtual commissioning",
                "TIA Portal – single engineering framework for PLC, HMI, drives, safety",
                "SITRANS field instruments – pressure, flow, level, temperature",
                "Industrial Edge – on-premise edge computing with cloud connectivity",
                "Mindsphere (now Siemens Xcelerator) IIoT platform",
            ],
            "target_segments": [
                "Chemical and pharma (FDA 21 CFR Part 11 compliant)",
                "Oil & Gas and energy",
                "Water / wastewater utilities",
                "Food & beverage",
                "Automotive and discrete manufacturing (PLC/SCADA focus)",
            ],
            "integrations": [
                "SAP S/4HANA via MES integration", "AVEVA PI System",
                "Siemens Xcelerator cloud platform", "Microsoft Azure Digital Twins",
                "PROFINET, PROFIBUS DP/PA, IO-Link, HART, OPC-UA, MQTT",
            ],
            "scraped_claims": [
                "Largest automation company by revenue globally",
                "TIA Portal: 350,000+ engineers worldwide",
                "PCS neo: zero-install engineering, works in any browser",
                "Digital twin-first approach with SIMIT and NX integration",
                "IEC 62443-4-1 certified development process",
            ],
            "confidence": "high",
            "pages_crawled": 20,
        },
    },
    {
        "company_name": "Schneider Electric",
        "website_url": "https://www.se.com/process-automation",
        "snapshot": {
            "pricing_tiers": {
                "EcoStruxure Foxboro DCS Entry":    "$80,000 – $125,000",
                "EcoStruxure Foxboro DCS Standard": "$210,000 – $500,000",
                "EcoStruxure Triconex SIS":         "$55,000 base + SIL certification",
                "Modicon M580 ePAC":                "$4,500 – $22,000 per rack",
                "EcoStruxure Operator Advisor":     "$8,500 per operator station",
                "Foxboro Pressure Transmitter IAP":  "$1,100 – $2,900",
            },
            "key_features": [
                "Foxboro DCS – heritage DBS-based, now EcoStruxure integrated",
                "Triconex TMR Safety – Triple Modular Redundant SIL 3 SIS",
                "Modicon M580 – Ethernet-native ePAC (hybrid PLC/DCS)",
                "EcoStruxure Plant – IIOT architecture: Edge > Control > Apps",
                "AVEVA System Platform (former Wonderware) for SCADA/MES",
                "Asset Advisor: AI-driven predictive maintenance alerts",
                "Ampla MES for production management and OEE tracking",
                "Cybersecurity services: Claroty partnership, network monitoring",
            ],
            "target_segments": [
                "Oil & Gas (Triconex strong in SIS market)",
                "Chemical and life sciences",
                "Water and wastewater (Modicon ePAC popular)",
                "Metals, mining and minerals",
                "Data centers and buildings (cross-sell with EcoStruxure Building)",
            ],
            "integrations": [
                "AVEVA PI System (native)", "Microsoft Azure via EcoStruxure Cloud",
                "SAP Plant Maintenance connector", "Claroty OT security platform",
                "PROFIBUS, HART, FOUNDATION Fieldbus, Modbus TCP, DNP3, IEC 61850",
            ],
            "scraped_claims": [
                "Triconex: over 13,000 SIS installations globally, zero safety failures claimed",
                "EcoStruxure: 2.2 million connected assets on the platform",
                "Foxboro DCS: 40+ year installed base in refining and petrochemicals",
                "Net-Zero commitment: all products carbon-neutral by 2025",
                "Certified Functional Safety Management per IEC 61508",
            ],
            "confidence": "high",
            "pages_crawled": 17,
        },
    },
    {
        "company_name": "ABB Ltd",
        "website_url": "https://new.abb.com/control-systems",
        "snapshot": {
            "pricing_tiers": {
                "System 800xA Entry":       "$90,000 – $140,000 (small system)",
                "System 800xA Standard":    "$250,000 – $600,000 (mid-size)",
                "System 800xA Enterprise":  "Custom (unlimited controllers, multi-site)",
                "ABB Ability SIS":          "$60,000 base (Hi-Integrity controller)",
                "AC500 PLC":                "$3,200 – $25,000 per CPU",
                "ABB Ability Symphony Plus":"Custom (power / water utility DCS)",
                "ABB 265 Pressure Transmitter": "$1,050 – $2,750",
            },
            "key_features": [
                "System 800xA – unified DCS+SIS+ESD on single platform, 500k I/O",
                "ABB Ability: IIoT platform with asset health, remote monitoring",
                "Hi-Integrity SIS – SIL 3 rated, integrated into 800xA",
                "Symphony Plus – specialized DCS for power gen and water",
                "AC500 PLC – modular, safety and standard variants, wide temp range",
                "Freelance DCS – compact mid-range DCS for smaller plants",
                "ABB Ability Genix: AI/ML analytics platform for process optimization",
                "Collaborative Operations Centers: remote expert services",
                "Strong drives portfolio (ACS880) natively integrated with 800xA",
            ],
            "target_segments": [
                "Oil & Gas and petrochemicals",
                "Pulp & Paper (strong historical installed base)",
                "Metals and mining",
                "Power generation and distribution utilities",
                "Marine and offshore platforms",
            ],
            "integrations": [
                "OSIsoft PI System (certified connector)", "SAP PM / S/4HANA",
                "Microsoft Azure IoT and Digital Twins", "ABB Ability cloud",
                "PROFIBUS, PROFINET, HART, FOUNDATION Fieldbus, OPC-UA, MQTT",
                "IEC 61850 (power automation)", "Modbus TCP/RTU",
            ],
            "scraped_claims": [
                "System 800xA: 10,000+ systems in 100 countries",
                "ABB: largest installed base in pulp & paper DCS globally",
                "First DCS vendor to achieve IEC 62443-3-3 SL2 certification",
                "ABB Ability Genix reduces unplanned downtime by up to 25% (claimed)",
                "Remote Operations: 24/7 global support from 5 collaborative centers",
            ],
            "confidence": "high",
            "pages_crawled": 19,
        },
    },
]

# ── Document text content ────────────────────────────────────────────────────
DOCUMENTS = [
    {
        "filename": "IntelliProcess_DCS_Datasheet.txt",
        "content": """IntelliProcess DCS — Product Datasheet v4.2
============================================================

OVERVIEW
--------
IntelliProcess DCS is a next-generation Distributed Control System designed for
large-scale continuous process industries. Built on an open, standards-based
architecture, it delivers unmatched scalability, cybersecurity, and integration
with cloud analytics platforms.

KEY SPECIFICATIONS
------------------
• Maximum I/O capacity       : 250,000 tags (single domain)
• Controller redundancy      : Hot-standby dual controllers, <5 ms failover
• Scan cycle (standard I/O)  : 100 ms (configurable down to 10 ms)
• Engineering languages      : IEC 61131-3 (FBD, SFC, ST, IL, LD)
• HMI                        : HTML5 web-based, supports up to 32 monitors
• Communication protocols    : HART 7, FOUNDATION Fieldbus H1/HSE,
                               PROFIBUS DP/PA, OPC-UA, OPC-DA, Modbus TCP/RTU,
                               MQTT, REST API
• Historian                  : Integrated, 10 million tags/s storage rate
• Cloud integration          : AWS IoT Greengrass, Azure IoT Hub, native connectors
• Cybersecurity              : IEC 62443-3-3 Security Level 2 certified
• Safety integration         : Native integration with IntelliSafe SIS (SIL 3)
• Operating temperature      : 0°C to 60°C (controller cabinet)
• Power supply               : 24 VDC redundant, <15 W per I/O card

HARDWARE MODULES
----------------
• IPD-CP410 Controller       : Dual-core ARM, 2 GB RAM, 8 GB eMMC
• IPD-AI816 Analog Input     : 16 ch, 4-20 mA / 0-10 V / HART, 16-bit ADC
• IPD-AO808 Analog Output    : 8 ch, 4-20 mA HART, 16-bit DAC
• IPD-DI832 Digital Input    : 32 ch, 24 VDC, opto-isolated
• IPD-DO816 Digital Output   : 16 ch, 24 VDC, 0.5 A per channel
• IPD-FI401 FF H1 Interface  : 4-segment FOUNDATION Fieldbus H1 coupler

PRICING (2024 LIST PRICE)
--------------------------
Starter Package (up to 2,000 I/O)    : USD 85,000
  Includes: 1× CP410, 8× I/O cards, 2 engineering stations, basic historian

Professional (up to 25,000 I/O)      : USD 220,000
  Includes: Redundant controllers, 40× I/O cards, cloud historian, 5 HMI stations

Enterprise (250,000+ I/O, multi-site): Custom — contact sales@intelliprocess.com
  Includes: Multi-domain, global historian, AI analytics, 24/7 support SLA

ANNUAL MAINTENANCE
------------------
• Software updates & patches : 18% of license cost
• Hardware swap program      : Available at 12% annually
• 24/7 remote support        : Included in Professional and Enterprise tiers

CERTIFICATIONS
--------------
• CE, UL, CSA, ATEX Zone 2 / IECEx, FM Class I Div 2
• IEC 62443-3-3 SL2 (cybersecurity)
• IEC 61511 (functional safety management process)
• ISO 9001:2015 (quality management)

INDUSTRIES SERVED
-----------------
Oil & Gas (upstream, midstream, downstream), Refining, Petrochemicals,
Chemical manufacturing, Power generation, Mining & Minerals, Pulp & Paper

TARGET CUSTOMER PROFILE
------------------------
• Greenfield projects requiring modern architecture
• Brownfield upgrades from legacy DCS (migration tools available)
• Plants needing SIS + DCS on a single integrated platform
• Organizations pursuing digital transformation / cloud historian migration
""",
    },
    {
        "filename": "IntelliProcess_Pricing_Guide_Q1_2024.txt",
        "content": """IntelliProcess — Commercial Pricing Guide Q1 2024
(CONFIDENTIAL — Internal Use Only)
============================================================

STANDARD PRICE LIST
--------------------

1. IntelliProcess DCS
   ┌─────────────────────────────────┬─────────────────────────────┐
   │ Package                         │ List Price (USD)            │
   ├─────────────────────────────────┼─────────────────────────────┤
   │ Starter (≤ 2,000 I/O)          │ $85,000                     │
   │ Professional (≤ 25,000 I/O)    │ $220,000                    │
   │ Enterprise (> 25,000 I/O)      │ Custom (min. $400,000)      │
   └─────────────────────────────────┴─────────────────────────────┘

   Add-on modules:
   • Redundant historian cluster      : +$18,000
   • Cloud historian (AWS/Azure)      : +$12,000/year subscription
   • AI analytics module              : +$25,000
   • Cybersecurity monitoring add-on  : +$9,500/year

2. IntelliSafe SIS
   ┌─────────────────────────────────┬─────────────────────────────┐
   │ Configuration                   │ List Price (USD)            │
   ├─────────────────────────────────┼─────────────────────────────┤
   │ Base system (1 safety group)    │ $45,000                     │
   │ Per additional safety group     │ +$8,500                     │
   │ SIL 2 certification package     │ +$12,000                    │
   │ SIL 3 certification package     │ +$22,000                    │
   └─────────────────────────────────┴─────────────────────────────┘

3. IntelliField IFT-900 Transmitter
   ┌─────────────────────────────────┬─────────────────────────────┐
   │ Output / Option                 │ List Price (USD)            │
   ├─────────────────────────────────┼─────────────────────────────┤
   │ 4-20 mA + HART 7               │ $1,200                      │
   │ FOUNDATION Fieldbus H1          │ $1,550                      │
   │ PROFIBUS PA                     │ $1,500                      │
   │ Hastelloy C-276 wetted parts    │ +$650                       │
   │ ATEX / IECEx approval           │ +$280                       │
   │ SIL 2 functional safety         │ +$420                       │
   └─────────────────────────────────┴─────────────────────────────┘

DISCOUNT STRUCTURE
------------------
• Distributor / system integrator   : 25% off list
• Volume (> 50 transmitters/order)  : additional 10% off
• Strategic account (> $1M/year)    : negotiated 30-35% off list
• Competitive displacement bonus     : extra 8% if replacing Yokogawa / ABB / Siemens

COMPETITIVE WIN RATES (Q4 2023)
--------------------------------
• vs Yokogawa CENTUM VP    : 38% win rate (strength: pricing, cloud)
• vs Siemens PCS 7         : 44% win rate (strength: open architecture)
• vs Schneider Foxboro      : 51% win rate (strength: SIS integration)
• vs ABB 800xA              : 41% win rate (strength: mid-range value)

KEY DIFFERENTIATORS FOR SALES
-------------------------------
1. Cloud-native historian included (competitors charge extra)
2. Single vendor for DCS + SIS (no integration surcharge)
3. HTML5 HMI — zero-client deployment, no per-seat licensing
4. Flat I/O pricing (no tag-count licensing after initial tier)
5. IEC 62443 SL2 certified out-of-the-box

SUPPORT & SERVICES PRICING
----------------------------
• Annual software maintenance        : 18% of license
• Remote monitoring (24/7)          : $2,800/month per site
• On-site engineer (proactive visit) : $2,200/day + expenses
• Migration from legacy DCS          : $45,000 – $180,000 project
• Operator training (3-day)          : $3,500 per attendee
""",
    },
    {
        "filename": "IntelliProcess_Competitive_Battle_Card.txt",
        "content": """IntelliProcess vs Competitors — Field Battle Card
============================================================
Version: Q1 2024 | For Sales Team Use Only

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vs YOKOGAWA CENTUM VP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THEIR STRENGTHS:
  ✓ Largest installed base in LNG and refining
  ✓ ProSafe-RS SIS is well-proven
  ✓ OpreX platform has strong analytics story
  ✓ Long lifecycle support (20+ years)

OUR ADVANTAGES:
  ✓ 15-25% lower total cost of ownership (include cloud historian)
  ✓ HTML5 HMI — zero per-seat licensing vs Yokogawa's HIS station model
  ✓ Faster I/O card hot-swap: <2 min vs Yokogawa's 8 min (documented)
  ✓ Native SIS integration on same controller backplane
  ✓ IEC 62443 SL2 certified; Yokogawa at SL1 for standard offering

HOW TO BEAT THEM:
  → Lead with TCO calculator — show 5-year cloud historian savings
  → Challenge their HIS licensing model (can be $50k+ premium)
  → Highlight our NAMUR NOA open architecture roadmap

WATCH OUT FOR:
  → Their proSafe-RS SIS is extremely trusted in Japan-origin plants
  → Long-standing relationships at Owner Operator level

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vs SIEMENS SIMATIC PCS 7 / PCS neo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THEIR STRENGTHS:
  ✓ TIA Portal ecosystem: largest installed PLC base in discrete
  ✓ PCS neo is genuinely cloud-native (container-based)
  ✓ SIMIT simulation — best-in-class virtual commissioning
  ✓ Deep SAP integration and global brand recognition

OUR ADVANTAGES:
  ✓ Process-first design; PCS 7 is showing its age (2008 architecture)
  ✓ No per-tag licensing after initial tier (Siemens charges by AS type)
  ✓ Better HART pass-through and field device diagnostics
  ✓ Our migration tooling handles PROFIBUS to HART 7 conversion
  ✓ PCS neo is still maturing — limited reference sites (< 50 globally)

HOW TO BEAT THEM:
  → Emphasize that PCS neo is not yet proven at > 10,000 I/O scale
  → Show our NAMUR NE107 diagnostics superiority
  → Use TÜV-certified SIL comparison to highlight SIS value

WATCH OUT FOR:
  → TIA Portal lock-in is strong if customer uses S7-1500 PLCs
  → Siemens can bundle drives + DCS at deep discount

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vs SCHNEIDER FOXBORO / TRICONEX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THEIR STRENGTHS:
  ✓ Triconex TMR SIS has 13,000+ installations — brand trust is huge
  ✓ Foxboro DCS has a 40-year installed base in refining
  ✓ AVEVA integration for SCADA/MES (strong digital story)
  ✓ Claroty partnership for OT security is differentiating

OUR ADVANTAGES:
  ✓ Foxboro DCS architecture is genuinely older (FBM-based)
  ✓ Our HMI is superior — Foxboro's IA Series UI is dated
  ✓ Integrated DCS+SIS at lower combined cost
  ✓ Cloud historian included; SE charges per AVEVA tag

HOW TO BEAT THEM:
  → Point out Foxboro is in "sustain mode" — R&D spend shifting to EcoStruxure
  → Our SIS uses same engineering environment — SE's requires separate Triconex tools
  → Show 5-year OPEX comparison including AVEVA licensing

WATCH OUT FOR:
  → Triconex is near-impossible to displace if SIS is already installed
  → Schneider often packages EcoStruxure at aggressive bundle pricing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vs ABB SYSTEM 800xA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THEIR STRENGTHS:
  ✓ System 800xA: most unified DCS+SIS+ESD+Drives platform
  ✓ Dominant in pulp & paper; very strong in power generation
  ✓ Collaborative Operations Centers: genuine remote support value
  ✓ ABB Ability Genix AI analytics is industry-leading

OUR ADVANTAGES:
  ✓ 800xA has complex licensing (Aspect Objects can escalate quickly)
  ✓ Our engineering time is 20-30% faster (flat FBD vs Aspect-based)
  ✓ Cloud historian standard; ABB's remote access requires Ability subscription
  ✓ Better price/performance in the 5,000 – 50,000 I/O range

HOW TO BEAT THEM:
  → Run a licensing exercise on 800xA Aspect Objects — quickly becomes expensive
  → Highlight our faster engineering environment for brownfield projects
  → Their drives integration is a lock-in story — counter with open OPC-UA

WATCH OUT FOR:
  → In pulp & paper and power, ABB loyalty is extremely high
  → ABB's service network in remote regions is very strong
""",
    },
]


async def main():
    async with AsyncSessionLocal() as session:
        # ── Create user ──────────────────────────────────────────────────────
        from sqlalchemy import select, text
        result = await session.execute(
            select(User).where(User.email == DEMO_USER["email"])
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=DEMO_USER["email"],
                name=DEMO_USER["name"],
                hashed_password=pwd_ctx.hash(DEMO_USER["password"]),
                role=DEMO_USER["role"],
            )
            session.add(user)
            await session.flush()
            print(f"✅ Created user: {user.email}")
        else:
            print(f"ℹ️  User already exists: {user.email}")

        # ── Create products ──────────────────────────────────────────────────
        for p in OUR_PRODUCTS:
            result = await session.execute(
                select(Product).where(
                    Product.user_id == user.id,
                    Product.name == p["name"]
                )
            )
            existing = result.scalar_one_or_none()
            if not existing:
                # Merge pricing into features dict since Product has no pricing column
                features = dict(p.get("features", {}))
                if p.get("pricing"):
                    features["pricing"] = p["pricing"]
                product = Product(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    name=p["name"],
                    category=p.get("category", ""),
                    description=p.get("category", ""),
                    features=features,
                    linked_document_ids=[],
                )
                session.add(product)
                print(f"✅ Created product: {p['name']}")
            else:
                print(f"ℹ️  Product exists: {p['name']}")

        # ── Write & register document files ──────────────────────────────────
        upload_dir = Path("/app/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)

        for doc_data in DOCUMENTS:
            result = await session.execute(
                select(Document).where(
                    Document.user_id == user.id,
                    Document.filename == doc_data["filename"]
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"ℹ️  Document exists: {doc_data['filename']}")
                continue

            # Write file to disk
            file_path = upload_dir / doc_data["filename"]
            file_path.write_text(doc_data["content"], encoding="utf-8")
            file_size = len(doc_data["content"].encode("utf-8"))

            from db.models import FileType, DocumentStatus
            doc = Document(
                id=str(uuid.uuid4()),
                user_id=user.id,
                filename=doc_data["filename"],
                original_filename=doc_data["filename"],
                file_type=FileType.txt,
                status=DocumentStatus.pending,
                file_size_bytes=file_size,
                file_path=str(file_path),
            )
            session.add(doc)
            await session.flush()
            print(f"✅ Registered document: {doc_data['filename']} ({file_size:,} bytes)")

            # Queue for ingestion
            try:
                import arq
                redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
                redis = await arq.create_pool(arq.connections.RedisSettings.from_dsn(redis_url))
                await redis.enqueue_job("ingest_document", doc.id)
                await redis.close()
                print(f"   ↳ Queued for ingestion: {doc.id}")
            except Exception as e:
                print(f"   ↳ Could not queue ingestion (will need manual trigger): {e}")

        # ── Create competitors + snapshots ───────────────────────────────────
        for comp_data in COMPETITORS:
            result = await session.execute(
                select(Competitor).where(
                    Competitor.user_id == user.id,
                    Competitor.company_name == comp_data["company_name"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                competitor = existing
                print(f"ℹ️  Competitor exists: {comp_data['company_name']}")
            else:
                competitor = Competitor(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    company_name=comp_data["company_name"],
                    website_url=comp_data["website_url"],
                    scrape_status=ScrapeStatus.ready,
                    last_scraped_at=datetime.utcnow(),
                )
                session.add(competitor)
                await session.flush()
                print(f"✅ Created competitor: {comp_data['company_name']}")

            # Check if snapshot exists
            result = await session.execute(
                select(CompetitorSnapshot).where(
                    CompetitorSnapshot.competitor_id == competitor.id
                )
            )
            snap_exists = result.scalar_one_or_none()

            if not snap_exists:
                snap = comp_data["snapshot"]
                snapshot = CompetitorSnapshot(
                    id=str(uuid.uuid4()),
                    competitor_id=competitor.id,
                    pricing_tiers=snap.get("pricing_tiers", {}),
                    key_features=snap.get("key_features", []),
                    target_segments=snap.get("target_segments", []),
                    integration_list=snap.get("integrations", []),
                    scraped_claims=snap.get("scraped_claims", []),
                    confidence=snap.get("confidence", "medium"),
                    is_current=True,
                )
                session.add(snapshot)
                print(f"   ↳ Added snapshot ({snap.get('confidence')} confidence)")
            else:
                print(f"   ↳ Snapshot already exists")

        await session.commit()
        print("\n🎉 Seed complete!")
        print(f"\n   Login:    {DEMO_USER['email']}")
        print(f"   Password: {DEMO_USER['password']}")
        print(f"   URL:      http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
