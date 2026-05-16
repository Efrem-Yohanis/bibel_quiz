# app/database_patch.py
"""
Compatibility patch for SQLAlchemy with Python 3.14
This must be imported before any SQLAlchemy imports
"""
import sys
import typing

# Monkey patch typing.Generic to work with SQLAlchemy on Python 3.14
if sys.version_info >= (3, 14):
    if hasattr(typing, 'Generic'):
        original_init_subclass = typing.Generic.__init_subclass__
        
        def patched_init_subclass(cls, *args, **kwargs):
            # Remove problematic attributes before calling super
            problematic_attrs = ['__static_attributes__', '__firstlineno__']
            saved_attrs = {}
            for attr in problematic_attrs:
                if hasattr(cls, attr):
                    saved_attrs[attr] = getattr(cls, attr)
                    delattr(cls, attr)
            
            try:
                result = original_init_subclass(cls, *args, **kwargs)
            finally:
                # Restore attributes
                for attr, value in saved_attrs.items():
                    setattr(cls, attr, value)
            
            return result
        
        typing.Generic.__init_subclass__ = patched_init_subclass