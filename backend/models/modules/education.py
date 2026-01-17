import uuid
import sys
import os
from datetime import datetime

# Add parent directory to path (go up 2 levels: modules/ -> models/ -> backend/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import db


# ============================================================
# TEST GRADING SYSTEM
# ============================================================

class TestResult(db.Model):
    """
    AI-powered test grading results
    Stores student test performance with question-by-question breakdown
    """
    __tablename__ = 'education_test_results'
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Instructor who graded
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))  # Student
    
    # Participant Information
    participant_name = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    date = db.Column(db.String(100))
    place = db.Column(db.String(255))
    test_type = db.Column(db.String(100))  # Pre-test, Post-test, Final Exam
    
    # Test Details
    mhe_type = db.Column(db.String(50), nullable=False)  # BOPT, FORKLIFT, REACH_TRUCK, STACKER
    total_marks_obtained = db.Column(db.Integer, nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(20), nullable=False)  # Pass/Fail
    
    # Test Data (JSON)
    answers_json = db.Column(db.Text)  # Student's answers
    details_json = db.Column(db.Text)  # Question-by-question breakdown
    image_base64 = db.Column(db.Text)  # Base64 encoded image of test paper
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='test_results')
    customer = db.relationship('Customer', backref='test_results')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f"<TestResult {self.id} - {self.participant_name} - {self.mhe_type} - {self.grade}>"
    
    def to_dict(self):
        """Convert test result to dictionary"""
        import json
        
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'participant_name': self.participant_name,
            'company': self.company,
            'date': self.date,
            'place': self.place,
            'test_type': self.test_type,
            'mhe_type': self.mhe_type,
            'total_marks_obtained': self.total_marks_obtained,
            'total_marks': self.total_marks,
            'percentage': self.percentage,
            'grade': self.grade,
            'answers': json.loads(self.answers_json) if self.answers_json else {},
            'details': json.loads(self.details_json) if self.details_json else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# CERTIFICATE MANAGEMENT
# ============================================================

class Certificate(db.Model):
    """
    Certificate tracking for training completion
    Manages certificate generation, dispatch, and validity
    """
    __tablename__ = 'education_certificates'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))  # Student
    test_result_id = db.Column(db.Integer, db.ForeignKey('education_test_results.id'))
    
    # Certificate Details
    certificate_number = db.Column(db.String(100), unique=True)
    certificate_type = db.Column(db.String(100))  # Training Completion, PTI, Safety, etc.
    issue_date = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    
    # Status Tracking
    status = db.Column(db.String(50))  # Created, Dispatched, Received
    dispatch_date = db.Column(db.DateTime)
    dispatch_method = db.Column(db.String(50))  # Email, Courier, In-person
    recipient = db.Column(db.String(255))
    tracking_number = db.Column(db.String(100))
    
    # Certificate Data
    certificate_data = db.Column(db.JSON)  # Student info, course details, marks
    certificate_url = db.Column(db.String(500))  # PDF storage location
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='certificates')
    test_result = db.relationship('TestResult', backref='certificates')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<Certificate {self.certificate_number} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'customer_id': self.customer_id,
            'test_result_id': self.test_result_id,
            'certificate_number': self.certificate_number,
            'certificate_type': self.certificate_type,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'status': self.status,
            'dispatch_date': self.dispatch_date.isoformat() if self.dispatch_date else None,
            'dispatch_method': self.dispatch_method,
            'recipient': self.recipient,
            'tracking_number': self.tracking_number,
            'certificate_data': self.certificate_data,
            'certificate_url': self.certificate_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# BATCH TRAINING MANAGEMENT
# ============================================================

class TrainingBatch(db.Model):
    """
    Training batch management for group training sessions
    Tracks participants, schedule, and batch capacity
    """
    __tablename__ = 'education_training_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Batch Info
    batch_number = db.Column(db.String(100), unique=True)
    batch_name = db.Column(db.String(255))
    course_type = db.Column(db.String(100))  # Forklift, Reach Truck, BOPT, Stacker
    
    # Schedule
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    duration_days = db.Column(db.Integer)
    
    # Capacity
    max_participants = db.Column(db.Integer)
    enrolled_count = db.Column(db.Integer, default=0)
    
    # Instructor & Venue
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    venue = db.Column(db.String(255))
    venue_address = db.Column(db.Text)
    
    # Status
    status = db.Column(db.String(50))  # Scheduled, Ongoing, Completed, Cancelled
    
    # Batch Data (participants list, materials needed, etc.)
    batch_data = db.Column(db.JSON)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    instructor = db.relationship('User', backref='training_batches')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<TrainingBatch {self.batch_number} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'batch_number': self.batch_number,
            'batch_name': self.batch_name,
            'course_type': self.course_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'duration_days': self.duration_days,
            'max_participants': self.max_participants,
            'enrolled_count': self.enrolled_count,
            'instructor_id': self.instructor_id,
            'venue': self.venue,
            'venue_address': self.venue_address,
            'status': self.status,
            'batch_data': self.batch_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================
# PTI FORMS (Practical Training Instructor)
# ============================================================

class PTIForm(db.Model):
    """
    Practical Training Instructor forms
    Records practical training assessment and instructor sign-off
    """
    __tablename__ = 'education_pti_forms'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))  # Student
    
    # PTI Details
    pti_number = db.Column(db.String(100), unique=True)
    participant_name = db.Column(db.String(255))
    company = db.Column(db.String(255))
    equipment_type = db.Column(db.String(100))  # MHE type
    
    # Training Records
    training_date = db.Column(db.DateTime)
    training_hours = db.Column(db.Float)
    practical_assessment = db.Column(db.JSON)  # Checklist items with pass/fail
    
    # Instructor Sign-off
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    instructor_signature = db.Column(db.Text)  # Base64 signature image
    sign_off_date = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(50))  # Draft, Approved, Archived
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='pti_forms')
    instructor = db.relationship('User', backref='pti_forms')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<PTIForm {self.pti_number} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'customer_id': self.customer_id,
            'pti_number': self.pti_number,
            'participant_name': self.participant_name,
            'company': self.company,
            'equipment_type': self.equipment_type,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'training_hours': self.training_hours,
            'practical_assessment': self.practical_assessment,
            'instructor_id': self.instructor_id,
            'sign_off_date': self.sign_off_date.isoformat() if self.sign_off_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }