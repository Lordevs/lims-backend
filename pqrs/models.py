from mongoengine import Document, fields
from datetime import datetime
from bson import ObjectId


class PQR(Document):
    """
    Procedure Qualification Record (PQR) model
    Contains comprehensive welding procedure qualification data
    """
    type = fields.StringField(max_length=100, required=True)
    basic_info = fields.DictField()  # JSON field for basic information
    joints = fields.DictField()  # JSON field for joints data
    joint_design_sketch = fields.ListField(fields.StringField(max_length=500))  # List of image file paths
    base_metals = fields.DictField()  # JSON field for base metals data
    filler_metals = fields.DictField()  # JSON field for filler metals data
    positions = fields.DictField()  # JSON field for positions data
    preheat = fields.DictField()  # JSON field for preheat data
    post_weld_heat_treatment = fields.DictField()  # JSON field for PWHT data
    gas = fields.DictField()  # JSON field for gas data
    electrical_characteristics = fields.DictField()  # JSON field for electrical data
    techniques = fields.DictField()  # JSON field for techniques data
    welding_parameters = fields.DictField()  # JSON field for welding parameters
    tensile_test = fields.DictField()  # JSON field for tensile test data
    guided_bend_test = fields.DictField()  # JSON field for guided bend test data
    toughness_test = fields.DictField()  # JSON field for toughness test data
    fillet_weld_test = fields.DictField()  # JSON field for fillet weld test data
    other_tests = fields.DictField()  # JSON field for other tests data
    welder_id = fields.ObjectIdField(required=True)  # Reference to Welder._id
    mechanical_testing_conducted_by = fields.StringField(max_length=200, required=True)
    lab_test_no = fields.StringField(max_length=100, required=True)
    law_name = fields.StringField(max_length=200, required=True)
    signatures = fields.DictField()  # JSON field for signatures data
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'pqrs',
        'indexes': [
            'type',
            'welder_id',
            'law_name',
            'mechanical_testing_conducted_by',
            'lab_test_no',
            'is_active',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"PQR - {self.law_name} ({self.lab_test_no})"