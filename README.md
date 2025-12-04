# Verisca - Agricultural Insurance Assessment Platform

Revolutionary mobile-first agricultural insurance assessment platform that digitizes the complete USDA crop loss adjustment methodology for African markets.

## 🌟 Features

- **GPS-Guided Sampling**: Automated sample point generation with GPS navigation
- **USDA Methodology**: Complete implementation of FCIC-25080 stand reduction calculations
- **100% Offline Capable**: Full assessment workflow works without internet
- **Multi-Tenant**: Complete data isolation for multiple insurance companies
- **Automated Reporting**: Professional PDF reports with maps, photos, and calculations
- **Audit Trail**: Complete tracking of all assessments and calculations

## 📋 MVP Scope (Phase 1)

- ✅ Maize crop only
- ✅ Stand reduction assessment method
- ✅ Drought peril
- ✅ Basic claim management
- ✅ GPS sampling and navigation
- ✅ Offline mobile assessment
- ✅ Automated PDF reports
- ✅ Bidirectional sync

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL 15+ with PostGIS
- **ORM**: SQLAlchemy with GeoAlchemy2
- **Authentication**: JWT tokens
- **PDF Generation**: ReportLab

### Mobile
- **Framework**: Flutter
- **Offline Database**: SQLite with Drift ORM
- **State Management**: BLoC pattern
- **GPS**: geolocator package
- **Camera**: camera package

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL 15+ with PostGIS
- Flutter SDK 3.0+
- pgAdmin (for database management)

### Quick Start

1. **Follow the Setup Guide**: See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions

2. **Database Setup**:
   - Create PostgreSQL database on Render
   - Enable PostGIS extension
   - Load schema via pgAdmin

3. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate  # Windows
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   - Copy `backend/.env.example` to `backend/.env`
   - Update DATABASE_URL with Render connection string
   - Set SECRET_KEY to a random string

5. **Run Backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Test API**:
   - Open http://127.0.0.1:8000
   - API Docs: http://127.0.0.1:8000/api/docs

## 📁 Project Structure

```
Verisca/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API endpoints
│   │   ├── core/              # Config, security
│   │   ├── db/                # Database session
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── main.py            # FastAPI app
│   ├── requirements.txt
│   └── .env.example
├── mobile/                     # Flutter mobile app (coming soon)
├── database/                   # Database scripts
│   └── seed_data/             # Initial data
├── SETUP_GUIDE.md             # Detailed setup instructions
└── README.md                  # This file
```

## 🔐 Authentication

The API uses JWT tokens for authentication with multi-tenant support.

**Login Endpoint**: `POST /api/v1/auth/login`

```json
{
  "username": "assessor@zimre.co.zw",
  "password": "password",
  "tenant_code": "ZIMRE"
}
```

**Response**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {...},
  "tenant": {...}
}
```

## 📊 Database Schema

30+ tables including:
- **Multi-tenancy**: tenants, users, roles
- **Crop Management**: crops, crop_varieties, growth_stages
- **Spatial Data**: farms, fields (with PostGIS geometry)
- **Assessment**: claims, assessment_sessions, sample_points
- **Evidence**: photos with GPS tags
- **Calculations**: audit trail of all calculations
- **Sync**: offline sync queue and conflict resolution

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Specific test suites
pytest tests/test_calculation_engine.py -v
pytest tests/test_sampling_engine.py -v
```

## 📖 Documentation

- [Setup Guide](SETUP_GUIDE.md) - Step-by-step setup instructions
- [Implementation Plan](implementation_plan.md) - Complete 8-week development plan
- [API Docs](http://127.0.0.1:8000/api/docs) - Interactive API documentation (when server running)

## 🗺️ Roadmap

### Phase 1 (Current - 8 weeks)
- [x] Database schema with PostGIS
- [x] Backend authentication
- [ ] Claims management API
- [ ] GPS sampling engine
- [ ] Stand reduction calculations
- [ ] Mobile app foundation
- [ ] Offline sync
- [ ] PDF report generation

### Phase 2 (Future)
- Additional assessment methods (hail, weight, tonnage)
- Multiple crops (wheat, soybeans, etc.)
- Computer vision for damage assessment
- Advanced analytics dashboard
- iOS mobile app

## 🤝 Contributing

This is a private project for agricultural insurance companies in Africa.

## 📄 License

Proprietary - All rights reserved

## 📧 Contact

For questions or support, contact the development team.

---

**Built with ❤️ for African agriculture**
