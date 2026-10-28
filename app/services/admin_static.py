from flask import Blueprint, send_from_directory
import os
admin_static_bp = Blueprint('admin_static', __name__)

@admin_static_bp.route('/admin')
@admin_static_bp.route('/admin/')
def admin_dashboard():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return send_from_directory(os.path.join(root, 'admin'), 'index.html')

@admin_static_bp.route('/admin/<path:path>')
def admin_files(path):
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return send_from_directory(os.path.join(root, 'admin'), path)