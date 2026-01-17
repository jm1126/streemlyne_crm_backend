# ============================================================
# EDUCATION MODULE
# ============================================================
try:
    from .education import (
        TestResult,
        Certificate,
        TrainingBatch,
        PTIForm
    )
    
    EDUCATION_MODELS = [
        'TestResult', 'Certificate', 'TrainingBatch', 'PTIForm'
    ]
    
except ImportError as e:
    # Education module not installed
    print(f"Education module not available: {e}")
    EDUCATION_MODELS = []

# ============================================================
# INTERIOR DESIGN MODULE
# ============================================================
try:
    from .interior_design import (
        Project,
        KitchenChecklist,
        BedroomChecklist,
        MaterialOrder,
        CuttingList,
        ApplianceCatalog,
        DrawingDocument,
        Drawing  # NEW - Drawing Analyser
    )
    
    INTERIOR_MODELS = [
        'Project', 'KitchenChecklist', 'BedroomChecklist',
        'MaterialOrder', 'CuttingList', 'ApplianceCatalog', 
        'DrawingDocument', 'Drawing'  # NEW
    ]
    
except ImportError as e:
    # Interior design module not installed
    print(f"Interior design module not available: {e}")
    INTERIOR_MODELS = []

# ============================================================
# EXPORT ALL MODULE MODELS
# ============================================================
__all__ = EDUCATION_MODELS + INTERIOR_MODELS