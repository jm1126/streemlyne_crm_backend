# ============================================================
# CORE MODELS - Always Available
# ============================================================

from .core import (
    # Enums
    STAGE_ENUM, 
    CONTACT_MADE_ENUM, 
    PREFERRED_CONTACT_ENUM,
    DOCUMENT_TEMPLATE_TYPE_ENUM, 
    PAYMENT_METHOD_ENUM,
    AUDIT_ACTION_ENUM, 
    ASSIGNMENT_TYPE_ENUM,
    
    # Tenant & Users
    Tenant, 
    User, 
    LoginAttempt, 
    Session,
    
    # CRM Core
    Customer, 
    Opportunity, 
    Job,
    
    # Teams
    Team, 
    TeamMember, 
    Salesperson,
    
    # Schedule
    Assignment,
    
    # Utilities
    generate_job_reference,
)

# Proposals & Financial
from .core_proposals import (
    Product, 
    ProductCategory,
    Proposal, 
    ProposalItem,
    Invoice, 
    InvoiceLineItem,
    Payment,
)

# Documents & Activities
from .core_documents import (
    OpportunityDocument, 
    Activity, 
    OpportunityNote,
    DocumentTemplate, 
    FormSubmission, 
    CustomerFormData,
    DataImport, 
    AuditLog, 
    VersionedSnapshot,
    ChatConversation, 
    ChatMessage, 
    ChatHistory,
)


# ============================================================
# MODULE MODELS - Optional (Industry-Specific)
# ============================================================

# Education Module
try:
    from .modules.education import (
        TestResult, 
        Certificate, 
        TrainingBatch, 
        PTIForm
    )
    EDUCATION_MODULE_AVAILABLE = True
except ImportError:
    # Education module not installed or enabled
    EDUCATION_MODULE_AVAILABLE = False
    TestResult = None
    Certificate = None
    TrainingBatch = None
    PTIForm = None

# Interior Design Module
try:
    from .modules.interior_design import (
        Project, 
        KitchenChecklist, 
        BedroomChecklist,
        MaterialOrder, 
        CuttingList, 
        ApplianceCatalog, 
        DrawingDocument,
        Drawing  # NEW - Drawing Analyser
    )
    INTERIOR_MODULE_AVAILABLE = True
except ImportError:
    # Interior design module not installed or enabled
    INTERIOR_MODULE_AVAILABLE = False
    Project = None
    KitchenChecklist = None
    BedroomChecklist = None
    MaterialOrder = None
    CuttingList = None
    ApplianceCatalog = None
    DrawingDocument = None
    Drawing = None  # NEW


# ============================================================
# EXPORT ALL MODELS
# ============================================================

__all__ = [
    # Enums
    'STAGE_ENUM', 'CONTACT_MADE_ENUM', 'PREFERRED_CONTACT_ENUM',
    'DOCUMENT_TEMPLATE_TYPE_ENUM', 'PAYMENT_METHOD_ENUM',
    'AUDIT_ACTION_ENUM', 'ASSIGNMENT_TYPE_ENUM',
    
    # Core Models
    'Tenant', 'User', 'LoginAttempt', 'Session',
    'Customer', 'Opportunity', 'Job',
    'Team', 'TeamMember', 'Salesperson',
    'Assignment',
    
    # Financial
    'Product', 'ProductCategory',
    'Proposal', 'ProposalItem',
    'Invoice', 'InvoiceLineItem',
    'Payment',
    
    # Documents
    'OpportunityDocument', 'Activity', 'OpportunityNote',
    'DocumentTemplate', 'FormSubmission', 'CustomerFormData',
    'DataImport', 'AuditLog', 'VersionedSnapshot',
    
    # Chat
    'ChatConversation', 'ChatMessage', 'ChatHistory',
    
    # Utilities
    'generate_job_reference',
    
    # Module availability flags
    'EDUCATION_MODULE_AVAILABLE',
    'INTERIOR_MODULE_AVAILABLE',
]

# Add education models to exports if available
if EDUCATION_MODULE_AVAILABLE:
    __all__.extend([
        'TestResult', 'Certificate', 'TrainingBatch', 'PTIForm'
    ])

# Add interior design models to exports if available
if INTERIOR_MODULE_AVAILABLE:
    __all__.extend([
        'Project', 'KitchenChecklist', 'BedroomChecklist',
        'MaterialOrder', 'CuttingList', 'ApplianceCatalog', 'DrawingDocument',
        'Drawing'  # NEW
    ])


# ============================================================
# HELPER FUNCTION TO CHECK MODULE AVAILABILITY
# ============================================================

def is_module_available(module_name: str) -> bool:
    """
    Check if a module is available
    
    Args:
        module_name: 'education' or 'interior_design'
    
    Returns:
        bool: True if module is available
    """
    if module_name == 'education':
        return EDUCATION_MODULE_AVAILABLE
    elif module_name == 'interior_design':
        return INTERIOR_MODULE_AVAILABLE
    return False


def get_available_modules() -> list:
    """
    Get list of available modules
    
    Returns:
        list: List of available module names
    """
    modules = []
    if EDUCATION_MODULE_AVAILABLE:
        modules.append('education')
    if INTERIOR_MODULE_AVAILABLE:
        modules.append('interior_design')
    return modules