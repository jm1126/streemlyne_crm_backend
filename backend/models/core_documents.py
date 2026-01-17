import uuid
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db


# ============================================================
# DOCUMENTS & ACTIVITIES
# ============================================================

class OpportunityDocument(db.Model):
    """Documents attached to opportunities"""
    __tablename__ = 'opportunity_documents'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    opportunity_id = db.Column(db.String(36), db.ForeignKey('opportunities.id'), nullable=False)
    
    # File Info
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    category = db.Column(db.String(50))
    
    # Audit
    uploaded_by = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    opportunity = db.relationship('Opportunity', back_populates='documents')
    tenant = db.relationship('Tenant')

    def __repr__(self):
        return f'<OpportunityDocument {self.filename}>'


class Activity(db.Model):
    """Activities and tasks for opportunities"""
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    opportunity_id = db.Column(db.String(36), db.ForeignKey('opportunities.id'), nullable=False)
    
    # Activity Details
    activity_type = db.Column(db.String(50), nullable=False)  # meeting, call, email, task
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Schedule
    scheduled_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, Cancelled
    
    # Assignment
    assigned_to = db.Column(db.String(200))
    created_by = db.Column(db.String(200))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    opportunity = db.relationship('Opportunity', back_populates='activities')

    def __repr__(self):
        return f'<Activity {self.title}>'


class OpportunityNote(db.Model):
    """Notes for opportunities"""
    __tablename__ = 'opportunity_notes'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    opportunity_id = db.Column(db.String(36), db.ForeignKey('opportunities.id'), nullable=False)
    
    content = db.Column(db.Text, nullable=False)
    note_type = db.Column(db.String(50), default='general')
    author = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    opportunity = db.relationship('Opportunity', back_populates='notes_list')
    tenant = db.relationship('Tenant')

    def __repr__(self):
        return f'<OpportunityNote {self.id}>'


# ============================================================
# TEMPLATES
# ============================================================

class DocumentTemplate(db.Model):
    """Document templates library"""
    __tablename__ = 'document_templates'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    name = db.Column(db.String(120), nullable=False)
    template_type = db.Column(db.String(50), nullable=False)  # Invoice, Receipt, Proposal, Contract, etc.
    file_path = db.Column(db.String(500), nullable=False)
    merge_fields = db.Column(db.JSON)
    
    uploaded_by = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tenant = db.relationship('Tenant')

    def __repr__(self):
        return f'<DocumentTemplate {self.name}>'


# ============================================================
# FORMS & SUBMISSIONS
# ============================================================

class FormSubmission(db.Model):
    """Form submissions from external sources"""
    __tablename__ = 'form_submissions'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))
    
    form_data = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(100))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime)

    # Relationships
    customer = db.relationship('Customer', back_populates='form_submissions')

    def __repr__(self):
        return f'<FormSubmission {self.id}>'


class CustomerFormData(db.Model):
    """Customer-specific form data"""
    __tablename__ = 'customer_form_data'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False)
    
    form_data = db.Column(db.Text, nullable=False)
    token_used = db.Column(db.String(64), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='form_data')
    tenant = db.relationship('Tenant')

    def __repr__(self):
        return f'<CustomerFormData {self.id} for Customer {self.customer_id}>'


# ============================================================
# DATA IMPORT
# ============================================================

class DataImport(db.Model):
    """Track bulk data imports"""
    __tablename__ = 'data_imports'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True, index=True)
    
    filename = db.Column(db.String(255), nullable=False)
    import_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='processing')
    records_processed = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_log = db.Column(db.Text)
    
    imported_by = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<DataImport {self.filename} ({self.status})>'


# ============================================================
# AUDIT & VERSIONING
# ============================================================

class AuditLog(db.Model):
    """Audit trail for all entity changes"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True, index=True)
    
    entity_type = db.Column(db.String(120), nullable=False)
    entity_id = db.Column(db.String(120), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # create, update, delete
    
    changed_by = db.Column(db.String(200))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    change_summary = db.Column(db.JSON)
    previous_snapshot = db.Column(db.JSON)
    new_snapshot = db.Column(db.JSON)

    def __repr__(self):
        return f'<AuditLog {self.entity_type} {self.entity_id} {self.action}>'


class VersionedSnapshot(db.Model):
    """Version history for entities"""
    __tablename__ = 'versioned_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=True, index=True)
    
    entity_type = db.Column(db.String(120), nullable=False)
    entity_id = db.Column(db.String(120), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255))
    snapshot = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(200))

    def __repr__(self):
        return f'<VersionedSnapshot {self.entity_type} v{self.version_number}>'


# ============================================================
# CHAT & AI CONVERSATIONS
# ============================================================

class ChatConversation(db.Model):
    """Chat conversations with AI assistant"""
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Conversation Metadata
    title = db.Column(db.String(255), default='New Conversation')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('ChatMessage', back_populates='conversation', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='chat_conversations')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<ChatConversation {self.id}: {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages) if self.messages else 0
        }


class ChatMessage(db.Model):
    """Individual messages within conversations"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('chat_conversations.id'), nullable=False, index=True)
    
    # Message Content
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    
    # Tool Usage (for AI function calls)
    function_calls = db.Column(db.JSON)  # Store tool calls made by assistant
    tool_results = db.Column(db.JSON)    # Store results from tools
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = db.relationship('ChatConversation', back_populates='messages')
    user = db.relationship('User', backref='chat_messages')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}: {self.role}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'function_calls': self.function_calls,
            'tool_results': self.tool_results,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChatHistory(db.Model):
    """
    Alternative: Simple chat history storage as JSON blobs
    Use this if you prefer simpler structure over ChatConversation + ChatMessage
    """
    __tablename__ = 'chat_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Store entire chat as JSON
    session_id = db.Column(db.String(100), nullable=False, index=True)
    messages = db.Column(db.JSON, nullable=False)  # Array of {role, content, timestamp}
    
    # Metadata
    title = db.Column(db.String(255))
    context = db.Column(db.JSON)  # Store context like customer_id, job_id, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='chat_histories')
    tenant = db.relationship('Tenant')
    
    def __repr__(self):
        return f'<ChatHistory {self.id} - Session: {self.session_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'title': self.title,
            'messages': self.messages,
            'context': self.context,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }