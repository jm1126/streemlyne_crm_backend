from flask import Blueprint, jsonify, request
from models import Tenant
from database import db
from tenant_middleware import require_tenant as token_required

tenant_bp = Blueprint('tenant', __name__, url_prefix='/api/tenant')


@tenant_bp.route('/config', methods=['GET'])
@token_required
def get_tenant_config(current_user):
    """Get tenant configuration (for frontend)"""
    
    tenant = Tenant.query.get(current_user.tenant_id)
    
    return jsonify({
        'industry_template': tenant.industry_template,
        'enabled_modules': tenant.enabled_modules or {},
        'terminology': tenant.terminology or {},
        'pipeline_stages': tenant.pipeline_stages or {},
        'custom_fields_config': tenant.custom_fields_config or {}
    })


@tenant_bp.route('/config', methods=['PATCH'])
@token_required
def update_tenant_config(current_user):
    """Update tenant configuration (admin only)"""
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    tenant = Tenant.query.get(current_user.tenant_id)
    data = request.get_json()
    
    # Update industry template
    if 'industry_template' in data:
        tenant.industry_template = data['industry_template']
    
    # Update enabled modules
    if 'enabled_modules' in data:
        tenant.enabled_modules = data['enabled_modules']
    
    # Update terminology
    if 'terminology' in data:
        tenant.terminology = data['terminology']
    
    # Update pipeline stages
    if 'pipeline_stages' in data:
        tenant.pipeline_stages = data['pipeline_stages']
    
    db.session.commit()
    
    return jsonify(tenant.to_dict())