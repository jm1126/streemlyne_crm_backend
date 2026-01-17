# backend/routes/drawing_analyser.py

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from functools import wraps
import os
import uuid
from datetime import datetime
import logging

from models import db, Drawing, CuttingList, Customer, Job
from services.ocr_dimension_extractor import OCRDimensionExtractor
from services.nesting_optimizer import NestingOptimizer  # We'll create this next

drawing_bp = Blueprint('drawing_analyser', __name__)
logger = logging.getLogger(__name__)

# Initialize OCR service
ocr_extractor = OCRDimensionExtractor()

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'drawings')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def require_module(module_name):
    """Middleware to check if tenant has access to this module"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant_id = request.headers.get('X-Tenant-ID')
            
            # Check if tenant has cutting_list_generator module enabled
            from models import Tenant
            tenant = Tenant.query.filter_by(id=tenant_id).first()
            
            if not tenant:
                return jsonify({'error': 'Tenant not found'}), 404
            
            enabled_modules = tenant.enabled_modules or {}
            if not enabled_modules.get(module_name):
                return jsonify({'error': f'Module {module_name} not enabled for this tenant'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@drawing_bp.route('/api/drawing-analyser/upload', methods=['POST'])
@require_module('cutting_list_generator')
def upload_drawing():
    """
    Upload a technical drawing and extract cutting list
    
    Expected FormData:
        - file: Drawing file (image/pdf)
        - customer_id: Optional customer ID
        - job_id: Optional job ID
        - project_name: Optional project name
    
    Returns:
        - drawing_id: UUID
        - status: 'processing' | 'completed' | 'failed'
        - cutting_list: Extracted table data
        - preview_url: URL to view drawing
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, PDF'}), 400
    
    try:
        # Generate unique filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        logger.info(f"📁 File saved: {file_path}")
        
        # Read file bytes for OCR
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
        
        # Extract dimensions using OCR
        logger.info("🤖 Starting OCR extraction...")
        ocr_result = ocr_extractor.extract_dimensions(image_bytes)
        
        logger.info(f"✅ OCR completed using method: {ocr_result.get('method')}")
        
        # Create Drawing record
        drawing = Drawing(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            customer_id=request.form.get('customer_id'),
            job_id=request.form.get('job_id'),
            project_name=request.form.get('project_name', 'Untitled Project'),
            original_filename=file.filename,
            file_path=file_path,
            status='completed' if ocr_result.get('success') else 'failed',
            ocr_method=ocr_result.get('method'),
            raw_ocr_output=ocr_result.get('raw_output'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(drawing)
        db.session.flush()  # Get drawing.id
        
        # Create CuttingList records from table data
        cutting_list_items = []
        
        if ocr_result.get('success') and ocr_result.get('table_data'):
            table_data = ocr_result['table_data']
            
            # Skip header row
            for row in table_data[1:]:
                if len(row) < 7:
                    continue  # Skip incomplete rows
                
                cutting_item = CuttingList(
                    id=str(uuid.uuid4()),
                    drawing_id=drawing.id,
                    component_type=row[0],
                    part_name=row[1],
                    overall_unit_width=self._parse_dimension(row[2]),
                    component_width=self._parse_dimension(row[3]),
                    height=self._parse_dimension(row[4]),
                    quantity=self._parse_quantity(row[5]),
                    material_thickness=self._parse_dimension(row[6]),
                    edge_banding_notes=row[7] if len(row) > 7 else None,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(cutting_item)
                cutting_list_items.append(cutting_item)
        
        db.session.commit()
        
        logger.info(f"✅ Drawing saved: {drawing.id} with {len(cutting_list_items)} cutting items")
        
        return jsonify({
            'success': True,
            'drawing_id': drawing.id,
            'status': drawing.status,
            'ocr_method': drawing.ocr_method,
            'table_markdown': ocr_result.get('table_markdown'),
            'cutting_list': [item.to_dict() for item in cutting_list_items],
            'preview_url': f'/api/drawing-analyser/{drawing.id}/preview'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Upload failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@drawing_bp.route('/api/drawing-analyser/<drawing_id>', methods=['GET'])
@require_module('cutting_list_generator')
def get_drawing(drawing_id):
    """Get drawing details and cutting list"""
    tenant_id = request.headers.get('X-Tenant-ID')
    
    drawing = Drawing.query.filter_by(
        id=drawing_id,
        tenant_id=tenant_id
    ).first()
    
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    return jsonify(drawing.to_dict(include_cutting_list=True))


@drawing_bp.route('/api/drawing-analyser', methods=['GET'])
@require_module('cutting_list_generator')
def list_drawings():
    """List all drawings for tenant with filters"""
    tenant_id = request.headers.get('X-Tenant-ID')
    
    # Query params
    customer_id = request.args.get('customer_id')
    job_id = request.args.get('job_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    query = Drawing.query.filter_by(tenant_id=tenant_id)
    
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if job_id:
        query = query.filter_by(job_id=job_id)
    if status:
        query = query.filter_by(status=status)
    
    total = query.count()
    drawings = query.order_by(Drawing.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'drawings': [d.to_dict() for d in drawings]
    })


@drawing_bp.route('/api/drawing-analyser/<drawing_id>/preview', methods=['GET'])
@require_module('cutting_list_generator')
def preview_drawing(drawing_id):
    """Get drawing image file"""
    tenant_id = request.headers.get('X-Tenant-ID')
    
    drawing = Drawing.query.filter_by(
        id=drawing_id,
        tenant_id=tenant_id
    ).first()
    
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    if not os.path.exists(drawing.file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(drawing.file_path)


@drawing_bp.route('/api/drawing-analyser/<drawing_id>/optimize', methods=['POST'])
@require_module('cutting_list_generator')
def optimize_nesting(drawing_id):
    """
    Run nesting optimization on cutting list
    
    Request body:
        - sheet_width: Standard sheet width (default 2440mm)
        - sheet_height: Standard sheet height (default 1220mm)
        - blade_width: Saw blade width (default 3mm)
    
    Returns:
        - optimized_layouts: List of sheet layouts
        - material_utilization: Percentage
        - waste_area: Total waste in mm²
    """
    tenant_id = request.headers.get('X-Tenant-ID')
    
    drawing = Drawing.query.filter_by(
        id=drawing_id,
        tenant_id=tenant_id
    ).first()
    
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    # Get optimization parameters
    data = request.json or {}
    sheet_width = data.get('sheet_width', 2440)
    sheet_height = data.get('sheet_height', 1220)
    blade_width = data.get('blade_width', 3)
    
    # Get cutting list items
    cutting_items = CuttingList.query.filter_by(drawing_id=drawing_id).all()
    
    if not cutting_items:
        return jsonify({'error': 'No cutting list found'}), 404
    
    # Convert to format for optimizer
    pieces = []
    for item in cutting_items:
        for _ in range(item.quantity):
            pieces.append({
                'id': item.id,
                'width': item.component_width,
                'height': item.height,
                'name': item.part_name
            })
    
    # Run optimization
    optimizer = NestingOptimizer(
        sheet_width=sheet_width,
        sheet_height=sheet_height,
        blade_width=blade_width
    )
    
    result = optimizer.optimize(pieces)
    
    # Update drawing with optimization result
    drawing.optimization_result = result
    drawing.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(result)


@drawing_bp.route('/api/drawing-analyser/<drawing_id>', methods=['DELETE'])
@require_module('cutting_list_generator')
def delete_drawing(drawing_id):
    """Delete drawing and associated cutting list"""
    tenant_id = request.headers.get('X-Tenant-ID')
    
    drawing = Drawing.query.filter_by(
        id=drawing_id,
        tenant_id=tenant_id
    ).first()
    
    if not drawing:
        return jsonify({'error': 'Drawing not found'}), 404
    
    # Delete file
    if os.path.exists(drawing.file_path):
        os.remove(drawing.file_path)
    
    # Delete from database (cascade will delete cutting list items)
    db.session.delete(drawing)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Drawing deleted'})


# Helper methods
def _parse_dimension(value):
    """Extract numeric dimension from string like '900' or '900mm' or 'N/A'"""
    if not value or value == 'N/A':
        return None
    
    # Remove non-numeric characters except decimal point
    numeric_str = ''.join(c for c in str(value) if c.isdigit() or c == '.')
    
    try:
        return float(numeric_str) if '.' in numeric_str else int(numeric_str)
    except:
        return None

def _parse_quantity(value):
    """Extract quantity from string"""
    try:
        return int(''.join(c for c in str(value) if c.isdigit()))
    except:
        return 1


# Make helper methods accessible
drawing_bp._parse_dimension = _parse_dimension
drawing_bp._parse_quantity = _parse_quantity