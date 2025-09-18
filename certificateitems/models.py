from mongoengine import Document, fields, EmbeddedDocument
from datetime import datetime
from bson import ObjectId


class ImageInfo(EmbeddedDocument):
    """
    Embedded document for image information within specimen sections
    """
    image_url = fields.StringField(max_length=500)
    caption = fields.StringField(max_length=500)


class SpecimenSection(EmbeddedDocument):
    """
    Embedded document for specimen section information within certificate items
    Contains test results and images for each specimen tested
    """
    test_results = fields.StringField(required=True)  # JSON string containing test data
    images_list = fields.ListField(fields.EmbeddedDocumentField(ImageInfo))
    specimen_id = fields.ObjectIdField(required=True)  # Reference to Specimen._id
    equipment_name = fields.StringField(max_length=200)  # Equipment used for testing
    equipment_calibration = fields.StringField(max_length=100)  # Equipment calibration info


class CertificateItem(Document):
    """
    Certificate Item model for managing detailed test results against certificates
    Links Certificates with Specimens and contains detailed testing data
    Each certificate can have multiple items for different tests/specimens
    """
    certificate_id = fields.ObjectIdField(required=True)  # Reference to Certificate._id
    sample_preparation_method = fields.StringField(max_length=200)
    material_grade = fields.StringField(max_length=200)
    temperature = fields.StringField(max_length=50)
    humidity = fields.StringField(max_length=50)
    po = fields.StringField(max_length=100)  # Purchase Order
    mtc_no = fields.StringField(max_length=100)  # Material Test Certificate Number
    heat_no = fields.StringField(max_length=100)  # Heat Number
    comments = fields.StringField()
    specimen_sections = fields.ListField(fields.EmbeddedDocumentField(SpecimenSection), required=True)
    
    # Audit fields
    created_at = fields.DateTimeField(default=datetime.now)
    updated_at = fields.DateTimeField(default=datetime.now)
    is_active = fields.BooleanField(default=True)
    
    meta = {
        'collection': 'certificate_items',
        'indexes': [
            'certificate_id',
            'material_grade',
            'specimen_sections.specimen_id',
            'created_at',
            'is_active'
        ]
    }
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.certificate_id} - {len(self.specimen_sections)} specimens - {self.material_grade}"