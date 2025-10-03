class DataQualityReport:
    def __init__(self):
        self.column_stats = {}
        self.outliers = {}
        self.patterns = {}
        self.correlations = {}
        self.errors = []
        
class ColumnQuality:
    def __init__(self):
        self.missing_count = 0
        self.missing_pct = 0.0
        self.unique_count = 0
        self.unique_pct = 0.0
        self.outliers = []
        self.patterns = {}
        self.data_type = None
        self.special_type = None
        self.validation_errors = []