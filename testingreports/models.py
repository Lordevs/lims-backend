from mongoengine import Document, fields, EmbeddedDocument
from datetime import datetime
from bson import ObjectId


class TestResult(EmbeddedDocument):
    """
    Embedded document for test results within testing reports
    Contains detailed information for each welder tested
    """
    welder_id = fields.StringField(max_length=100, required=True)
    welder_name = fields.StringField(max_length=200, required=True)
    iqama_number = fields.StringField(max_length=50, required=True)
    test_coupon_id = fields.StringField(max_length=100, required=True)
    date_of_inspection = fields.StringField(max_length=20)  # Date as string (YYYY-MM-DD format)
    welding_processes = fields.StringField(max_length=200)
    type_of_welding = fields.StringField(max_length=100)  # manual/semi-auto
    backing = fields.StringField(max_length=50)  # with/without
    type_of_weld_joint = fields.StringField(max_length=200)
    thickness_product_type = fields.StringField(max_length=200)  # Plate or Pipe
    diameter_of_pipe = fields.StringField(max_length=100)
    base_metal_p_number = fields.StringField(max_length=100)
    filler_metal_electrode_spec = fields.StringField(max_length=200)  # SFA
    filler_metal_f_number = fields.StringField(max_length=100)
    filler_metal_addition_deletion = fields.StringField(max_length=200)  # GTAW/PAW
    deposit_thickness_for_each_process = fields.StringField(max_length=200)
    welding_positions = fields.StringField(max_length=200)
    vertical_progression = fields.StringField(max_length=200)
    type_of_fuel_gas = fields.StringField(max_length=200)  # OFW
    inert_gas_backing = fields.StringField(max_length=200)  # GTAW, PAW, GMAW
    transfer_mode = fields.StringField(max_length=200)  # spray, globular, or pulse to sort circuit-GMAW
    current_type_polarity = fields.StringField(max_length=100)  # AC. DCEP, DCEN
    voltage = fields.StringField(max_length=100)
    current = fields.StringField(max_length=100)
    travel_speed = fields.StringField(max_length=100)
    interpass_temperature = fields.StringField(max_length=100)
    pre_heat = fields.StringField(max_length=200)  # If Applicable
    post_weld_heat_treatment = fields.StringField(max_length=200)  # If Applicable
    result_status = fields.StringField(max_length=100, required=True)


class TestingReport(Document):
    """
    Testing report model for managing welding test reports
    Contains multiple test results for different welders
    """
    results = fields.ListField(fields.EmbeddedDocumentField(TestResult), required=True)
    prepared_by = fields.StringField(max_length=100, required=True)
    client_name = fields.StringField(max_length=200, required=True)
    project_details = fields.StringField(max_length=500)
    contract_details = fields.StringField(max_length=500)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    
    meta = {
        'collection': 'testing_reports',
        'indexes': [
            'prepared_by',
            'client_name',
            'results.welder_id',
            'results.welder_name',
            'is_active',
            'created_at'
        ]
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Testing Report - {self.client_name} ({len(self.results)} welders)"