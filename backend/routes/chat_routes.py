from flask import Blueprint, request, jsonify, g
from database import db
from models import ChatHistory, ChatConversation, ChatMessage
from tenant_middleware import require_tenant
from datetime import datetime
import uuid

chat_bp = Blueprint('chat', __name__)

# ----------------------------------
# Simple Chat History (JSON-based)
# ----------------------------------

@chat_bp.route('/chat/sessions', methods=['GET'])
@require_tenant
def get_chat_sessions():
    """Get all chat sessions for current user"""
    # CRITICAL: Filter by both tenant_id AND user_id for individual isolation
    sessions = ChatHistory.query.filter_by(
        tenant_id=g.tenant_id,
        user_id=g.user_id  # User-specific filtering
    ).order_by(ChatHistory.updated_at.desc()).all()
    
    return jsonify([s.to_dict() for s in sessions]), 200


@chat_bp.route('/chat/sessions/<string:session_id>', methods=['GET'])
@require_tenant
def get_chat_session(session_id):
    """Get specific chat session"""
    # CRITICAL: Verify session belongs to current user AND tenant
    session = ChatHistory.query.filter_by(
        session_id=session_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id  # Security: User can only access their own chats
    ).first()
    
    if not session:
        return jsonify({'error': 'Chat session not found'}), 404
    
    return jsonify(session.to_dict()), 200


@chat_bp.route('/chat/sessions', methods=['POST'])
@require_tenant
def create_chat_session():
    """Create new chat session"""
    data = request.get_json()
    
    session_id = data.get('session_id') or str(uuid.uuid4())
    title = data.get('title', 'New Chat')
    messages = data.get('messages', [])
    context = data.get('context', {})
    
    # Create session for current user
    chat_session = ChatHistory(
        tenant_id=g.tenant_id,
        user_id=g.user_id,  # CRITICAL: Set user_id
        session_id=session_id,
        title=title,
        messages=messages,
        context=context
    )
    
    db.session.add(chat_session)
    db.session.commit()
    
    return jsonify(chat_session.to_dict()), 201


@chat_bp.route('/chat/sessions/<string:session_id>', methods=['PUT'])
@require_tenant
def update_chat_session(session_id):
    """Update chat session (add messages)"""
    # CRITICAL: Verify session belongs to current user
    session = ChatHistory.query.filter_by(
        session_id=session_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).first()
    
    if not session:
        return jsonify({'error': 'Chat session not found'}), 404
    
    data = request.get_json()
    
    # Update messages
    if 'messages' in data:
        session.messages = data['messages']
    
    # Update title
    if 'title' in data:
        session.title = data['title']
    
    # Update context
    if 'context' in data:
        session.context = data['context']
    
    session.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(session.to_dict()), 200


@chat_bp.route('/chat/sessions/<string:session_id>', methods=['DELETE'])
@require_tenant
def delete_chat_session(session_id):
    """Delete chat session"""
    # CRITICAL: Verify session belongs to current user
    session = ChatHistory.query.filter_by(
        session_id=session_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).first()
    
    if not session:
        return jsonify({'error': 'Chat session not found'}), 404
    
    db.session.delete(session)
    db.session.commit()
    
    return jsonify({'message': 'Chat session deleted'}), 200


# ----------------------------------
# Structured Chat (Conversation-based)
# ----------------------------------

@chat_bp.route('/chat/conversations', methods=['GET'])
@require_tenant
def get_conversations():
    """Get all conversations for current user"""
    conversations = ChatConversation.query.filter_by(
        tenant_id=g.tenant_id,
        user_id=g.user_id  # User-specific
    ).order_by(ChatConversation.updated_at.desc()).all()
    
    return jsonify([c.to_dict() for c in conversations]), 200


@chat_bp.route('/chat/conversations', methods=['POST'])
@require_tenant
def create_conversation():
    """Create new conversation"""
    data = request.get_json()
    
    conversation = ChatConversation(
        tenant_id=g.tenant_id,
        user_id=g.user_id,
        title=data.get('title', 'New Conversation')
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    return jsonify(conversation.to_dict()), 201


@chat_bp.route('/chat/conversations/<string:conversation_id>', methods=['GET'])
@require_tenant
def get_conversation(conversation_id):
    """Get conversation with all messages"""
    # CRITICAL: Verify conversation belongs to current user
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    # Get all messages
    messages = ChatMessage.query.filter_by(
        conversation_id=conversation_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'conversation': conversation.to_dict(),
        'messages': [m.to_dict() for m in messages]
    }), 200


@chat_bp.route('/chat/conversations/<string:conversation_id>/messages', methods=['POST'])
@require_tenant
def add_message(conversation_id):
    """Add message to conversation"""
    # CRITICAL: Verify conversation belongs to current user
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    data = request.get_json()
    
    message = ChatMessage(
        tenant_id=g.tenant_id,
        user_id=g.user_id,
        conversation_id=conversation_id,
        role=data.get('role', 'user'),
        content=data.get('content', ''),
        function_calls=data.get('function_calls'),
        tool_results=data.get('tool_results')
    )
    
    db.session.add(message)
    
    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify(message.to_dict()), 201


@chat_bp.route('/chat/conversations/<string:conversation_id>', methods=['DELETE'])
@require_tenant
def delete_conversation(conversation_id):
    """Delete conversation and all its messages"""
    # CRITICAL: Verify conversation belongs to current user
    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).first()
    
    if not conversation:
        return jsonify({'error': 'Conversation not found'}), 404
    
    db.session.delete(conversation)  # Cascade will delete messages too
    db.session.commit()
    
    return jsonify({'message': 'Conversation deleted'}), 200


# ----------------------------------
# Utility Routes
# ----------------------------------

@chat_bp.route('/chat/clear-all', methods=['DELETE'])
@require_tenant
def clear_all_chats():
    """Clear all chat history for current user"""
    # Delete all sessions for this user
    ChatHistory.query.filter_by(
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).delete()
    
    # Delete all conversations for this user (messages cascade)
    ChatConversation.query.filter_by(
        tenant_id=g.tenant_id,
        user_id=g.user_id
    ).delete()
    
    db.session.commit()
    
    return jsonify({'message': 'All chat history cleared'}), 200